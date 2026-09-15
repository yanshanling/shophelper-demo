"""概览看板：配置资产统计 + 对话分布 + 最近变更。"""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ChangeLog, ChatLog, KbCategory, KbItem, ModelConfig, PromptTemplate
from ..schemas import ChangeLogOut

router = APIRouter(prefix="/api/dashboard", tags=["概览"])


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    kb_total = db.query(KbItem).count()
    kb_published = db.query(KbItem).filter(KbItem.status == "published").count()
    kb_draft = db.query(KbItem).filter(KbItem.status == "draft").count()
    total_hits = db.query(func.coalesce(func.sum(KbItem.hit_count), 0)).scalar() or 0

    intent_rows = db.query(ChatLog.intent, func.count(ChatLog.id)).group_by(ChatLog.intent).all()
    language_rows = db.query(ChatLog.language, func.count(ChatLog.id)).group_by(ChatLog.language).all()
    safety_rows = db.query(ChatLog.safety_level, func.count(ChatLog.id)).group_by(ChatLog.safety_level).all()

    top_items = (
        db.query(KbItem).order_by(KbItem.hit_count.desc()).limit(8).all()
    )
    cat_map = {c.id: c.name for c in db.query(KbCategory).all()}

    cat_dist = (
        db.query(KbCategory.name, func.count(KbItem.id))
        .outerjoin(KbItem, KbItem.category_id == KbCategory.id)
        .group_by(KbCategory.id)
        .all()
    )

    recent_changes = db.query(ChangeLog).order_by(ChangeLog.id.desc()).limit(10).all()
    pending_review = db.query(ChatLog).filter(ChatLog.safety_level.like("%高%")).count()

    return {
        "kb": {
            "total": kb_total,
            "published": kb_published,
            "draft": kb_draft,
            "categories": db.query(KbCategory).count(),
            "total_hits": int(total_hits),
        },
        "prompts": {
            "total": db.query(PromptTemplate).count(),
            "enabled": db.query(PromptTemplate).filter(PromptTemplate.enabled.is_(True)).count(),
        },
        "models": {
            "total": db.query(ModelConfig).count(),
            "enabled": db.query(ModelConfig).filter(ModelConfig.enabled.is_(True)).count(),
        },
        "chats": {
            "total": db.query(ChatLog).count(),
            "pending_review": pending_review,
        },
        "intent_distribution": [{"name": n or "UNKNOWN", "value": c} for n, c in intent_rows],
        "language_distribution": [
            {"name": "中文" if n == "zh" else "English", "value": c} for n, c in language_rows
        ],
        "safety_distribution": [{"name": n or "未知", "value": c} for n, c in safety_rows],
        "category_distribution": [{"name": n, "value": c} for n, c in cat_dist],
        "top_items": [
            {
                "id": i.id,
                "title": i.title_zh or i.title_en,
                "category": cat_map.get(i.category_id, ""),
                "hit_count": i.hit_count or 0,
            }
            for i in top_items
        ],
        "recent_changes": [ChangeLogOut.model_validate(c).model_dump() for c in recent_changes],
    }
