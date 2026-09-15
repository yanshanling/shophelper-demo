"""跨境电商客服 Agent · 运营管理后台 —— FastAPI 入口。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models  # noqa: F401  确保模型注册到 Base.metadata
from .database import Base, SessionLocal, engine
from .routers import dashboard, knowledge, models as models_router, playground, prompts
from .seed import run_seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        run_seed(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="跨境电商客服 Agent · 运营管理后台 API",
    description="知识库 / Prompt / 大模型接入 的配置管理中心",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for _router in (dashboard, knowledge, prompts, models_router, playground):
    app.include_router(_router.router)


@app.get("/api/health", tags=["系统"])
def health():
    return {"status": "ok", "service": "cross-border-cs-agent-admin"}
