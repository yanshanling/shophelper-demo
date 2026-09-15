"""Prompt 管理：CRUD + 版本快照 / 回滚 + 变量渲染预览。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import PromptTemplate, PromptVersion
from ..schemas import (
    PromptCreate,
    PromptOut,
    PromptRenderRequest,
    PromptUpdate,
    PromptVersionOut,
)
from ..utils import log_change

router = APIRouter(prefix="/api/prompts", tags=["Prompt 管理"])


def _snapshot(db: Session, prompt: PromptTemplate, note: str) -> None:
    db.add(PromptVersion(
        prompt_id=prompt.id, version=prompt.version, content=prompt.content, note=note
    ))


@router.get("", response_model=list[PromptOut])
def list_prompts(scene: str = "", db: Session = Depends(get_db)):
    q = db.query(PromptTemplate)
    if scene:
        q = q.filter(PromptTemplate.scene == scene)
    return q.order_by(PromptTemplate.id).all()


@router.post("", response_model=PromptOut)
def create_prompt(payload: PromptCreate, db: Session = Depends(get_db)):
    prompt = PromptTemplate(**payload.model_dump())
    db.add(prompt)
    db.flush()
    _snapshot(db, prompt, "创建初始版本")
    log_change(db, "prompt", prompt.id, prompt.name, "create")
    db.commit()
    db.refresh(prompt)
    return prompt


@router.get("/{prompt_id}", response_model=PromptOut)
def get_prompt(prompt_id: int, db: Session = Depends(get_db)):
    prompt = db.get(PromptTemplate, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt 不存在")
    return prompt


@router.put("/{prompt_id}", response_model=PromptOut)
def update_prompt(prompt_id: int, payload: PromptUpdate, db: Session = Depends(get_db)):
    prompt = db.get(PromptTemplate, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt 不存在")
    data = payload.model_dump(exclude_unset=True)
    content_changed = "content" in data and data["content"] != prompt.content
    for k, v in data.items():
        setattr(prompt, k, v)
    if content_changed:
        prompt.version = (prompt.version or 1) + 1
        db.flush()
        _snapshot(db, prompt, data.get("note") or "内容更新")
    log_change(db, "prompt", prompt.id, prompt.name, "update")
    db.commit()
    db.refresh(prompt)
    return prompt


@router.delete("/{prompt_id}")
def delete_prompt(prompt_id: int, db: Session = Depends(get_db)):
    prompt = db.get(PromptTemplate, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt 不存在")
    name = prompt.name
    db.query(PromptVersion).filter(PromptVersion.prompt_id == prompt_id).delete()
    db.delete(prompt)
    log_change(db, "prompt", prompt_id, name, "delete")
    db.commit()
    return {"success": True}


@router.get("/{prompt_id}/versions", response_model=list[PromptVersionOut])
def list_versions(prompt_id: int, db: Session = Depends(get_db)):
    return (
        db.query(PromptVersion)
        .filter(PromptVersion.prompt_id == prompt_id)
        .order_by(PromptVersion.version.desc(), PromptVersion.id.desc())
        .all()
    )


@router.post("/{prompt_id}/rollback/{version_id}", response_model=PromptOut)
def rollback(prompt_id: int, version_id: int, db: Session = Depends(get_db)):
    prompt = db.get(PromptTemplate, prompt_id)
    ver = db.get(PromptVersion, version_id)
    if not prompt or not ver or ver.prompt_id != prompt_id:
        raise HTTPException(status_code=404, detail="Prompt 或版本不存在")
    prompt.content = ver.content
    prompt.version = (prompt.version or 1) + 1
    db.flush()
    _snapshot(db, prompt, f"回滚自 v{ver.version}")
    log_change(db, "prompt", prompt.id, prompt.name, "rollback")
    db.commit()
    db.refresh(prompt)
    return prompt


@router.post("/{prompt_id}/set-default", response_model=PromptOut)
def set_default(prompt_id: int, db: Session = Depends(get_db)):
    """把某场景下的 Prompt 设为生效版本（同场景其他版本取消默认）。"""
    prompt = db.get(PromptTemplate, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt 不存在")
    db.query(PromptTemplate).filter(
        PromptTemplate.scene == prompt.scene, PromptTemplate.id != prompt_id
    ).update({"is_default": False, "enabled": False})
    prompt.is_default = True
    prompt.enabled = True
    log_change(db, "prompt", prompt.id, prompt.name, "activate")
    db.commit()
    db.refresh(prompt)
    return prompt


@router.post("/{prompt_id}/render")
def render_prompt(prompt_id: int, payload: PromptRenderRequest, db: Session = Depends(get_db)):
    """用给定变量渲染 Prompt，用于运营预览最终效果。"""
    prompt = db.get(PromptTemplate, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt 不存在")
    rendered = prompt.content
    for key, value in (payload.variables or {}).items():
        rendered = rendered.replace("{" + key + "}", str(value))
    return {"prompt_id": prompt.id, "rendered": rendered}
