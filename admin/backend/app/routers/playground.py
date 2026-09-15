"""Agent 测试台：直接调用配置驱动的 Agent，观察 Trace。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..agent_runtime import run_agent
from ..database import get_db
from ..models import ChatLog
from ..schemas import ChatRequest

router = APIRouter(prefix="/api/playground", tags=["Agent 测试台"])

DEMO_SCENARIOS = [
    {"label": "🇺🇸 查订单", "text": "What's the status of my order US2024-3821?", "intent": "ORDER"},
    {"label": "🇺🇸 查物流", "text": "Where is my package with tracking number DHL9876543210?", "intent": "SHIPPING"},
    {"label": "🇺🇸 退换政策", "text": "What's your return policy? Can I return if I don't like the color?", "intent": "FAQ"},
    {"label": "🇺🇸 尺码问题", "text": "I'm not sure about sizing. What size should I get if I usually wear M?", "intent": "FAQ"},
    {"label": "🇺🇸 支付方式", "text": "What payment methods do you accept? Do you take PayPal?", "intent": "FAQ"},
    {"label": "🇺🇸 投诉反馈", "text": "I received a damaged item and I'm very disappointed. This is terrible!", "intent": "COMPLAINT"},
    {"label": "🇨🇳 查物流", "text": "我的包裹US2024-3821到哪里了？", "intent": "SHIPPING"},
    {"label": "🇨🇳 退货请求", "text": "我想退货，尺码不合适", "intent": "REFUND"},
    {"label": "🇨🇳 运费多少", "text": "寄到美国运费多少钱？", "intent": "FAQ"},
    {"label": "🇨🇳 退款请求", "text": "我要退款，订单 US2024-4521，收到的耳机有质量问题", "intent": "REFUND"},
]


@router.get("/scenarios")
def scenarios():
    return DEMO_SCENARIOS


@router.post("/chat")
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    result = run_agent(db, payload.message, log=True)
    db.commit()
    return result


@router.get("/logs")
def logs(limit: int = 20, db: Session = Depends(get_db)):
    rows = db.query(ChatLog).order_by(ChatLog.id.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "user_input": r.user_input,
            "language": r.language,
            "intent": r.intent,
            "confidence": r.confidence,
            "safety_level": r.safety_level,
            "created_at": r.created_at,
        }
        for r in rows
    ]
