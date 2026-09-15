"""知识库管理：分类 + 条目 CRUD + 检索测试。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..agent_runtime import detect_language, split_keywords
from ..database import get_db
from ..models import KbCategory, KbItem
from ..schemas import (
    CategoryCreate,
    CategoryOut,
    CategoryUpdate,
    ItemCreate,
    ItemOut,
    ItemUpdate,
    SearchTestRequest,
)
from ..utils import log_change

router = APIRouter(prefix="/api/kb", tags=["知识库"])


def _cat_out(cat: KbCategory, count: int) -> CategoryOut:
    data = CategoryOut.model_validate(cat)
    data.item_count = count
    return data


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    counts = dict(
        db.query(KbItem.category_id, func.count(KbItem.id)).group_by(KbItem.category_id).all()
    )
    cats = db.query(KbCategory).order_by(KbCategory.sort_order, KbCategory.id).all()
    return [_cat_out(c, counts.get(c.id, 0)) for c in cats]


@router.post("/categories", response_model=CategoryOut)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    exists = db.query(KbCategory).filter(KbCategory.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=400, detail="分类名已存在")
    cat = KbCategory(**payload.model_dump())
    db.add(cat)
    db.flush()
    log_change(db, "kb_category", cat.id, cat.name, "create")
    db.commit()
    db.refresh(cat)
    return _cat_out(cat, 0)


@router.put("/categories/{cat_id}", response_model=CategoryOut)
def update_category(cat_id: int, payload: CategoryUpdate, db: Session = Depends(get_db)):
    cat = db.get(KbCategory, cat_id)
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(cat, k, v)
    log_change(db, "kb_category", cat.id, cat.name, "update")
    db.commit()
    db.refresh(cat)
    count = db.query(KbItem).filter(KbItem.category_id == cat.id).count()
    return _cat_out(cat, count)


@router.delete("/categories/{cat_id}")
def delete_category(cat_id: int, db: Session = Depends(get_db)):
    cat = db.get(KbCategory, cat_id)
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    name = cat.name
    db.delete(cat)
    log_change(db, "kb_category", cat_id, name, "delete")
    db.commit()
    return {"success": True}


def _item_out(item: KbItem, cat_map: dict) -> ItemOut:
    data = ItemOut.model_validate(item)
    cat = cat_map.get(item.category_id)
    data.category_name = cat.name if cat else ""
    return data


@router.get("/items")
def list_items(
    category_id: int | None = None,
    keyword: str = "",
    status: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(KbItem)
    if category_id:
        q = q.filter(KbItem.category_id == category_id)
    if status:
        q = q.filter(KbItem.status == status)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(or_(
            KbItem.title_zh.like(like), KbItem.title_en.like(like),
            KbItem.answer_zh.like(like), KbItem.answer_en.like(like),
            KbItem.keywords_zh.like(like), KbItem.keywords_en.like(like),
        ))
    total = q.count()
    rows = q.order_by(KbItem.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    cat_map = {c.id: c for c in db.query(KbCategory).all()}
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_item_out(i, cat_map).model_dump() for i in rows],
    }


@router.post("/items", response_model=ItemOut)
def create_item(payload: ItemCreate, db: Session = Depends(get_db)):
    if not db.get(KbCategory, payload.category_id):
        raise HTTPException(status_code=400, detail="所属分类不存在")
    item = KbItem(**payload.model_dump())
    db.add(item)
    db.flush()
    log_change(db, "kb_item", item.id, item.title_zh or item.title_en, "create")
    db.commit()
    db.refresh(item)
    cat = db.get(KbCategory, item.category_id)
    return _item_out(item, {cat.id: cat} if cat else {})


@router.get("/items/{item_id}", response_model=ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(KbItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="条目不存在")
    cat = db.get(KbCategory, item.category_id)
    return _item_out(item, {cat.id: cat} if cat else {})


@router.put("/items/{item_id}", response_model=ItemOut)
def update_item(item_id: int, payload: ItemUpdate, db: Session = Depends(get_db)):
    item = db.get(KbItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="条目不存在")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    log_change(db, "kb_item", item.id, item.title_zh or item.title_en, "update")
    db.commit()
    db.refresh(item)
    cat = db.get(KbCategory, item.category_id)
    return _item_out(item, {cat.id: cat} if cat else {})


@router.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(KbItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="条目不存在")
    name = item.title_zh or item.title_en
    db.delete(item)
    log_change(db, "kb_item", item_id, name, "delete")
    db.commit()
    return {"success": True}


@router.post("/search-test")
def search_test(payload: SearchTestRequest, db: Session = Depends(get_db)):
    """模拟 Agent 端检索：输入一句用户问题，看会命中哪些知识库条目。"""
    lang = detect_language(payload.query) if payload.lang == "auto" else payload.lang
    text_lower = payload.query.lower()
    rows = (
        db.query(KbItem)
        .filter(KbItem.status == "published")
        .all()
    )
    cat_map = {c.id: c for c in db.query(KbCategory).all()}
    results = []
    for item in rows:
        raw = item.keywords_en if lang == "en" else item.keywords_zh
        if not raw:
            raw = item.keywords_zh if lang == "en" else item.keywords_en
        kws = split_keywords(raw)
        hit_kws = [k for k in kws if k in text_lower]
        if hit_kws:
            results.append({
                "item_id": item.id,
                "title": item.title_en if lang == "en" else item.title_zh,
                "category_name": cat_map[item.category_id].name if item.category_id in cat_map else "",
                "score": len(hit_kws),
                "hit_keywords": hit_kws,
                "answer": (item.answer_en if lang == "en" else item.answer_zh)[:300],
            })
    results.sort(key=lambda x: x["score"], reverse=True)
    return {
        "query": payload.query,
        "language": lang,
        "matched_count": len(results),
        "best": results[0] if results else None,
        "results": results[:5],
    }
