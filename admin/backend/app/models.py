"""数据模型：知识库 / Prompt / 大模型配置 / 变更日志 / 对话日志。"""

import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Float,
)
from sqlalchemy.orm import relationship

from .database import Base


def now() -> datetime.datetime:
    return datetime.datetime.now()


# ═══════════════════════════════════════════════════════════
# 一、知识库
# ═══════════════════════════════════════════════════════════


class KbCategory(Base):
    """知识库分类（如：退换货政策 / 物流运费）。"""

    __tablename__ = "kb_category"

    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)  # 分类名（业务标识，中英一致）
    name_en = Column(String(64), default="")
    description = Column(Text, default="")
    icon = Column(String(16), default="📁")
    sort_order = Column(Integer, default=0)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)

    items = relationship(
        "KbItem", back_populates="category", cascade="all, delete-orphan"
    )


class KbItem(Base):
    """知识库条目（双向内容的 FAQ 条目）。"""

    __tablename__ = "kb_item"

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("kb_category.id"), nullable=False)
    title_zh = Column(String(200), default="")
    title_en = Column(String(200), default="")
    answer_zh = Column(Text, default="")
    answer_en = Column(Text, default="")
    keywords_zh = Column(Text, default="")  # 逗号分隔
    keywords_en = Column(Text, default="")  # 逗号分隔
    status = Column(String(16), default="published")  # published / draft / disabled
    hit_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)

    category = relationship("KbCategory", back_populates="items")


# ═══════════════════════════════════════════════════════════
# 二、Prompt 模板
# ═══════════════════════════════════════════════════════════


class PromptTemplate(Base):
    """Prompt 模板（人设 / 安全规则 / 场景话术），支持版本化。"""

    __tablename__ = "prompt_template"

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    scene = Column(String(32), default="system")  # system / faq / order / refund / complaint
    content = Column(Text, default="")
    variables = Column(Text, default="")  # 逗号分隔的占位符，如 {customer_name}
    version = Column(Integer, default=1)
    is_default = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)
    note = Column(Text, default="")
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)


class PromptVersion(Base):
    """Prompt 版本快照（用于历史对比与回滚）。"""

    __tablename__ = "prompt_version"

    id = Column(Integer, primary_key=True)
    prompt_id = Column(Integer, ForeignKey("prompt_template.id"), nullable=False)
    version = Column(Integer, default=1)
    content = Column(Text, default="")
    note = Column(Text, default="")
    operator = Column(String(64), default="运营")
    created_at = Column(DateTime, default=now)


# ═══════════════════════════════════════════════════════════
# 三、大模型接入配置
# ═══════════════════════════════════════════════════════════


class ModelConfig(Base):
    """大模型接入配置（OpenAI 兼容协议）。"""

    __tablename__ = "model_config"

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)  # 配置别名，如「GPT-4o 海外英文线」
    provider = Column(String(64), default="openai")  # openai / deepseek / qwen / azure / ollama
    base_url = Column(String(256), default="https://api.openai.com/v1")
    api_key = Column(String(256), default="")
    model_name = Column(String(128), default="gpt-4o-mini")
    temperature = Column(Float, default=0.3)
    max_tokens = Column(Integer, default=1024)
    top_p = Column(Float, default=1.0)
    route_lang = Column(String(16), default="all")  # all / zh / en：多语言路由
    is_default = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)
    remark = Column(Text, default="")
    last_test_status = Column(String(32), default="")  # success / failed
    last_test_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)


# ═══════════════════════════════════════════════════════════
# 四、变更日志 & 对话日志
# ═══════════════════════════════════════════════════════════


class ChangeLog(Base):
    """操作审计日志（谁在什么时候改了什么）。"""

    __tablename__ = "change_log"

    id = Column(Integer, primary_key=True)
    entity_type = Column(String(32), default="")  # kb_item / prompt / model
    entity_id = Column(Integer, default=0)
    entity_name = Column(String(200), default="")
    action = Column(String(32), default="")  # create / update / delete
    operator = Column(String(64), default="运营")
    created_at = Column(DateTime, default=now)


class ChatLog(Base):
    """测试台对话日志（用于概览看板统计）。"""

    __tablename__ = "chat_log"

    id = Column(Integer, primary_key=True)
    user_input = Column(Text, default="")
    language = Column(String(8), default="")
    intent = Column(String(32), default="")
    confidence = Column(Float, default=0.0)
    safety_level = Column(String(32), default="")
    matched_item_id = Column(Integer, nullable=True)
    reply = Column(Text, default="")
    created_at = Column(DateTime, default=now)
