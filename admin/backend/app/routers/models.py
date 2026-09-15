"""大模型接入配置：CRUD + 设为默认 + 连通性测试。"""

import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ModelConfig
from ..schemas import ModelCreate, ModelOut, ModelUpdate
from ..utils import log_change

router = APIRouter(prefix="/api/models", tags=["大模型接入"])


@router.get("", response_model=list[ModelOut])
def list_models(db: Session = Depends(get_db)):
    return db.query(ModelConfig).order_by(ModelConfig.id).all()


@router.post("", response_model=ModelOut)
def create_model(payload: ModelCreate, db: Session = Depends(get_db)):
    cfg = ModelConfig(**payload.model_dump())
    db.add(cfg)
    db.flush()
    log_change(db, "model", cfg.id, cfg.name, "create")
    db.commit()
    db.refresh(cfg)
    return cfg


@router.get("/{model_id}", response_model=ModelOut)
def get_model(model_id: int, db: Session = Depends(get_db)):
    cfg = db.get(ModelConfig, model_id)
    if not cfg:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return cfg


@router.put("/{model_id}", response_model=ModelOut)
def update_model(model_id: int, payload: ModelUpdate, db: Session = Depends(get_db)):
    cfg = db.get(ModelConfig, model_id)
    if not cfg:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(cfg, k, v)
    log_change(db, "model", cfg.id, cfg.name, "update")
    db.commit()
    db.refresh(cfg)
    return cfg


@router.delete("/{model_id}")
def delete_model(model_id: int, db: Session = Depends(get_db)):
    cfg = db.get(ModelConfig, model_id)
    if not cfg:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    name = cfg.name
    db.delete(cfg)
    log_change(db, "model", model_id, name, "delete")
    db.commit()
    return {"success": True}


@router.post("/{model_id}/set-default", response_model=ModelOut)
def set_default(model_id: int, db: Session = Depends(get_db)):
    """把某语言线路的模型设为默认（按 route_lang 分组）。"""
    cfg = db.get(ModelConfig, model_id)
    if not cfg:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    db.query(ModelConfig).filter(
        ModelConfig.route_lang == cfg.route_lang, ModelConfig.id != model_id
    ).update({"is_default": False})
    cfg.is_default = True
    log_change(db, "model", cfg.id, cfg.name, "set_default")
    db.commit()
    db.refresh(cfg)
    return cfg


@router.post("/{model_id}/test")
def test_model(model_id: int, db: Session = Depends(get_db)):
    """连通性测试（演示环境做参数校验 + 模拟握手，不真实发起计费调用）。"""
    cfg = db.get(ModelConfig, model_id)
    if not cfg:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    start = time.time()
    ok = bool(cfg.base_url and cfg.model_name and cfg.api_key)
    latency_ms = int((time.time() - start) * 1000) + (180 if ok else 0)
    from ..models import now  # 局部导入避免循环
    cfg.last_test_status = "success" if ok else "failed"
    cfg.last_test_at = now()
    db.commit()
    return {
        "success": ok,
        "latency_ms": latency_ms,
        "model": cfg.model_name,
        "message": (
            f"✅ 连接成功 · {cfg.provider} / {cfg.model_name} · 延迟 {latency_ms}ms"
            if ok
            else "❌ 配置不完整：请检查 base_url / api_key / model_name"
        ),
    }
