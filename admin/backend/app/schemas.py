"""Pydantic 请求 / 响应模型。"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ═══════════════════════════════════════════════════════════
# 知识库
# ═══════════════════════════════════════════════════════════


class CategoryBase(BaseModel):
    name: str
    name_en: str = ""
    description: str = ""
    icon: str = "📁"
    sort_order: int = 0
    enabled: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    name_en: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    enabled: Optional[bool] = None


class CategoryOut(CategoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    item_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ItemBase(BaseModel):
    category_id: int
    title_zh: str = ""
    title_en: str = ""
    answer_zh: str = ""
    answer_en: str = ""
    keywords_zh: str = ""
    keywords_en: str = ""
    status: str = "published"


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    category_id: Optional[int] = None
    title_zh: Optional[str] = None
    title_en: Optional[str] = None
    answer_zh: Optional[str] = None
    answer_en: Optional[str] = None
    keywords_zh: Optional[str] = None
    keywords_en: Optional[str] = None
    status: Optional[str] = None


class ItemOut(ItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    hit_count: int = 0
    category_name: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SearchTestRequest(BaseModel):
    query: str
    lang: str = "auto"


# ═══════════════════════════════════════════════════════════
# Prompt
# ═══════════════════════════════════════════════════════════


class PromptBase(BaseModel):
    name: str
    scene: str = "system"
    content: str = ""
    variables: str = ""
    enabled: bool = True
    note: str = ""


class PromptCreate(PromptBase):
    pass


class PromptUpdate(BaseModel):
    name: Optional[str] = None
    scene: Optional[str] = None
    content: Optional[str] = None
    variables: Optional[str] = None
    enabled: Optional[bool] = None
    note: Optional[str] = None


class PromptOut(PromptBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    version: int = 1
    is_default: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PromptRenderRequest(BaseModel):
    variables: dict = {}


class PromptVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    prompt_id: int
    version: int
    content: str
    note: str
    operator: str
    created_at: Optional[datetime] = None


# ═══════════════════════════════════════════════════════════
# 大模型配置
# ═══════════════════════════════════════════════════════════


class ModelBase(BaseModel):
    name: str
    provider: str = "openai"
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.3
    max_tokens: int = 1024
    top_p: float = 1.0
    route_lang: str = "all"
    enabled: bool = True
    remark: str = ""


class ModelCreate(ModelBase):
    pass


class ModelUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    route_lang: Optional[str] = None
    enabled: Optional[bool] = None
    remark: Optional[str] = None


class ModelOut(ModelBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_default: bool = False
    last_test_status: str = ""
    last_test_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ═══════════════════════════════════════════════════════════
# 测试台
# ═══════════════════════════════════════════════════════════


class ChatRequest(BaseModel):
    message: str


class ChangeLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    entity_type: str
    entity_id: int
    entity_name: str
    action: str
    operator: str
    created_at: Optional[datetime] = None
