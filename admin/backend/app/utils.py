"""通用工具。"""

from sqlalchemy.orm import Session

from .models import ChangeLog


def log_change(db: Session, entity_type: str, entity_id: int, entity_name: str,
               action: str, operator: str = "运营") -> None:
    """记录一条操作审计日志。"""
    db.add(ChangeLog(
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        action=action,
        operator=operator,
    ))
