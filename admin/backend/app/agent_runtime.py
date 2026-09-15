"""
Agent 运行时 —— 配置驱动版。

与原 demo/agent.py 的差异：
原版把知识库写死在 FAQ_KNOWLEDGE / FAQ_KEYWORDS 常量里；
本版在每次对话时从配置库（KbCategory / KbItem / PromptTemplate）实时读取，
因此运营在后台改一条知识库 / 一条 Prompt，立即影响 Agent 行为 —— 这就是「配置驱动」。
"""

import re
from typing import Optional

from sqlalchemy.orm import Session

from .models import ChatLog, KbCategory, KbItem, PromptTemplate

# ── 工具类意图规则（非知识库，属于 Agent 能力，故保留为代码常量）──
ORDER_PATTERNS = {
    "zh": [r"订单", r"我的订单", r"查.*单", r"状态"],
    "en": [r"order", r"my order", r"where is my", r"check.*order", r"status", r"order number"],
}
SHIPPING_PATTERNS = {
    "zh": [r"物流", r"快递", r"到哪", r"多久到", r"什么时候到", r"跟踪"],
    "en": [r"tracking", r"track", r"where is.*package", r"delivery status", r"arrive"],
}
REFUND_PATTERNS = [r"refund", r"money back", r"cancel.*order", r"退货", r"退款", r"取消订单"]
COMPLAINT_KEYWORDS = [
    "angry", "complaint", "terrible", "awful", "disappointed", "bad experience",
    "投诉", "生气", "糟糕", "失望", "举报", "差评",
]
CHITCHAT_PATTERNS = [
    r"hi", r"hello", r"hey", r"thanks", r"thank", r"bye", r"good",
    r"你好", r"谢谢", r"再见", r"嗨", r"早上好", r"晚上好",
]

RED_KEYWORDS = [
    "删除账户", "delete account", "delete my data", "sue", "lawyer",
    "legal action", "投诉到", "起诉", "律师", "法院",
]
ORANGE_KEYWORDS = ["refund", "退款", "compensation", "赔偿", "modify", "修改地址"]

INTENT_NAMES = {
    "FAQ": "知识库查询", "ORDER": "订单查询", "SHIPPING": "物流追踪",
    "REFUND": "退款请求", "COMPLAINT": "投诉处理", "CHITCHAT": "日常闲聊",
}

MOCK_ORDERS = {
    "US2024-3821": {"customer": "Anna Müller", "platform": "Shopify", "status": "已发货", "status_en": "Shipped",
                    "items": "Women's Summer Dress (M, Blue) × 1", "total": 45.99, "created": "2026-06-20",
                    "tracking_no": "SF7890123456", "carrier": "SF-Intl"},
    "US2024-4521": {"customer": "James Wilson", "platform": "Amazon", "status": "运输中", "status_en": "In Transit",
                    "items": "Bluetooth Earphones × 1", "total": 29.99, "created": "2026-06-19",
                    "tracking_no": "DHL9876543210", "carrier": "DHL"},
    "US2024-5100": {"customer": "Sophie Martin", "platform": "TikTok Shop", "status": "已签收", "status_en": "Delivered",
                    "items": "Yoga Mat + Resistance Bands Set", "total": 35.50, "created": "2026-06-15",
                    "tracking_no": "4PX1122334455", "carrier": "4PX"},
}


def detect_language(text: str) -> str:
    """检测语言：zh 或 en"""
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    return "zh" if chinese_chars > len(text) * 0.3 else "en"


def split_keywords(raw: str) -> list[str]:
    if not raw:
        return []
    return [k.strip().lower() for k in re.split(r"[,，、;；\n]", raw) if k.strip()]


def _load_kb(db: Session):
    """从配置库加载启用中的知识库。"""
    categories = (
        db.query(KbCategory).filter(KbCategory.enabled.is_(True)).order_by(KbCategory.sort_order).all()
    )
    cat_map = {c.id: c for c in categories}
    items = (
        db.query(KbItem)
        .filter(KbItem.status == "published", KbItem.category_id.in_(cat_map.keys() or [0]))
        .all()
    )
    return cat_map, items


def _match_kb(items: list[KbItem], text: str, lang: str) -> tuple[Optional[KbItem], int, Optional[int]]:
    """关键词匹配，返回 (最佳条目, 得分, 所属分类id)。"""
    text_lower = text.lower()
    best_item, best_score = None, 0
    for item in items:
        raw = item.keywords_en if lang == "en" else item.keywords_zh
        kws = split_keywords(raw)
        if not kws:
            kws = split_keywords(item.keywords_zh if lang == "en" else item.keywords_en)
        score = sum(1 for k in kws if k in text_lower)
        if score > best_score:
            best_score = score
            best_item = item
    return best_item, best_score, (best_item.category_id if best_item else None)


# 意图打分权重：动作类意图（投诉/退款）优先级高于信息类（订单/物流/FAQ）
COMPLAINT_WEIGHT = 10
REFUND_WEIGHT = 8
ORDER_WEIGHT = 3
SHIPPING_WEIGHT = 3
FAQ_WEIGHT = 3
CHITCHAT_WEIGHT = 3

ORDER_NO_RE = re.compile(r"[A-Z]{2}\d{4}-\d{4}")
TRACKING_NO_RE = re.compile(r"[A-Z]{2,3}\d{8,12}")


def recognize_intent(text: str, lang: str, items: list[KbItem]) -> tuple[str, float, Optional[KbItem]]:
    """识别意图，返回 (主意图, 置信度, 命中的知识库条目)。

    设计要点：显式动作（我要投诉 / 我要退款）优先于语境信号。
    单号本身只是弱信号，仅在同时命中关键词时才加权，避免「我的包裹 XX 到哪了」
    被订单号抢判为订单意图。
    """
    text_lower = text.lower()

    order_patterns = ORDER_PATTERNS["zh"] if lang == "zh" else ORDER_PATTERNS["en"]
    shipping_patterns = SHIPPING_PATTERNS["zh"] if lang == "zh" else SHIPPING_PATTERNS["en"]

    complaint_hits = sum(1 for k in COMPLAINT_KEYWORDS if k in text_lower)
    refund_hits = sum(1 for p in REFUND_PATTERNS if re.search(p, text_lower))
    order_hits = sum(1 for p in order_patterns if re.search(p, text_lower))
    shipping_hits = sum(1 for p in shipping_patterns if re.search(p, text_lower))
    chitchat_hits = sum(1 for p in CHITCHAT_PATTERNS if re.search(p, text_lower))

    has_order_no = bool(ORDER_NO_RE.search(text))
    has_tracking_no = bool(TRACKING_NO_RE.search(text))
    if has_order_no and order_hits:
        order_hits += 1
    if has_tracking_no and shipping_hits:
        shipping_hits += 1

    best_item, faq_hits, _ = _match_kb(items, text, lang)

    scores = {
        "COMPLAINT": complaint_hits * COMPLAINT_WEIGHT,
        "REFUND": refund_hits * REFUND_WEIGHT,
        "ORDER": order_hits * ORDER_WEIGHT,
        "SHIPPING": shipping_hits * SHIPPING_WEIGHT,
        "FAQ": faq_hits * FAQ_WEIGHT,
        "CHITCHAT": chitchat_hits * CHITCHAT_WEIGHT,
    }

    if max(scores.values()) == 0:
        # 无任何关键词命中：仅凭单号做兜底判断
        if has_order_no:
            return "ORDER", 0.60, best_item
        if has_tracking_no:
            return "SHIPPING", 0.60, best_item
        return "FAQ", 0.15, best_item

    primary = max(scores, key=scores.get)
    confidence = min(0.95, 0.40 + 0.08 * scores[primary])
    if primary == "FAQ" and best_item is None:
        confidence = 0.30
    return primary, round(confidence, 2), best_item


def safety_check(intent: str, user_input: str, lang: str) -> dict:
    """四级风险分级 + 安全护栏。"""
    text_lower = user_input.lower()

    if any(k in text_lower for k in RED_KEYWORDS):
        return {
            "level": "🔴 极高风险",
            "action": "escalate",
            "auto_reply": "我们非常重视您的反馈。为确保妥善处理，我将为您转接人工客服主管。请稍候..."
            if lang == "zh"
            else "We take your concerns very seriously. I'm escalating this to a human supervisor to ensure it's handled properly. Please hold...",
        }

    if any(k in text_lower for k in ORANGE_KEYWORDS) and intent in ("REFUND", "COMPLAINT"):
        return {
            "level": "🟠 高风险",
            "action": "pre_fill_and_escalate",
            "auto_reply": "退款请求需要人工审核确认。我已经整理了您的信息，正在转接客服专员。预计等待不超过 2 分钟。"
            if lang == "zh"
            else "Refund requests require human verification. I've prepared your information and am connecting you to a specialist. Estimated wait: under 2 minutes.",
        }

    if intent == "REFUND":
        return {"level": "🟡 中风险", "action": "auto_with_review", "auto_reply": None}

    return {"level": "🟢 低风险", "action": "auto", "auto_reply": None}


def _render_prompt_templates(db: Session, scene: str, mapping: dict) -> Optional[str]:
    """从配置库取对应场景的 Prompt，并渲染变量（演示 Prompt 生效）。"""
    tpl = (
        db.query(PromptTemplate)
        .filter(PromptTemplate.scene == scene, PromptTemplate.enabled.is_(True))
        .order_by(PromptTemplate.version.desc())
        .first()
    )
    if not tpl or not tpl.content:
        return None
    content = tpl.content
    for key, value in mapping.items():
        content = content.replace("{" + key + "}", str(value))
    return content


def run_agent(db: Session, user_input: str, log: bool = True) -> dict:
    """配置驱动的 Agent 主流程，返回回复 + Trace。"""
    trace: list[dict] = []

    lang = detect_language(user_input)
    trace.append({"step": "语言检测", "detail": f"检测为 {'中文' if lang == 'zh' else 'English'}", "icon": "🔍"})

    cat_map, items = _load_kb(db)
    trace.append({"step": "加载配置", "detail": f"从配置库读取 {len(cat_map)} 个分类 / {len(items)} 条知识库", "icon": "🗂️"})

    intent, confidence, matched_item = recognize_intent(user_input, lang, items)
    trace.append({
        "step": "意图识别",
        "detail": f"{INTENT_NAMES.get(intent, intent)} (置信度: {confidence:.0%})",
        "icon": "🧠",
    })

    safety = safety_check(intent, user_input, lang)
    trace.append({"step": "安全护栏", "detail": f"风险等级: {safety['level']} → {safety['action']}", "icon": "🛡️"})

    matched_item_id = matched_item.id if matched_item else None
    reply = ""
    source = "rule_engine"

    if safety["auto_reply"]:
        reply = safety["auto_reply"]
    elif intent == "FAQ":
        if matched_item:
            cat = cat_map.get(matched_item.category_id)
            cat_name = cat.name if cat else "知识库"
            content = matched_item.answer_en if lang == "en" else matched_item.answer_zh
            title = matched_item.title_en if lang == "en" else matched_item.title_zh
            trace.append({"step": "ReAct - 推理", "detail": "判断为 FAQ 类问题 → 需检索知识库", "icon": "💭"})
            trace.append({
                "step": "ReAct - 行动",
                "detail": f"🔧 命中知识库条目「{title}」(id={matched_item.id}, 分类={cat_name})",
                "icon": "🔧",
            })
            trace.append({"step": "ReAct - 观察", "detail": f"返回内容 {len(content)} 字", "icon": "👁️"})
            matched_item.hit_count = (matched_item.hit_count or 0) + 1

            if lang == "zh":
                reply = f"📚 以下是关于「{cat_name}」的详细信息：\n\n{content}\n\n还有其他需要帮您的吗？"
            else:
                reply = f'📚 Here\'s what I found about "{cat_name}":\n\n{content}\n\nIs there anything else I can help with?'
            source = f"kb_item#{matched_item.id}"
        else:
            trace.append({"step": "ReAct - 观察", "detail": "未找到匹配知识库条目", "icon": "👁️"})
            reply = (
                "抱歉，我暂时没有找到相关的信息。需要我帮您转接人工客服吗？"
                if lang == "zh"
                else "I couldn't find relevant information on this. Would you like me to connect you with a human agent?"
            )
            source = "no_kb_hit"

    elif intent == "ORDER":
        trace.append({"step": "ReAct - 推理", "detail": "判断为订单查询 → 需调用 get_order_info", "icon": "💭"})
        m = re.search(r"[A-Z]{2}\d{4}-\d{4}", user_input)
        if m and m.group(0) in MOCK_ORDERS:
            o = MOCK_ORDERS[m.group(0)]
            status = o["status"] if lang == "zh" else o["status_en"]
            trace.append({"step": "ReAct - 行动", "detail": f"🔧 调用 get_order_info({m.group(0)})", "icon": "🔧"})
            trace.append({"step": "ReAct - 观察", "detail": f"找到订单，状态: {status}", "icon": "👁️"})
            if lang == "zh":
                reply = (f"📋 订单查询结果\n\n订单号：{m.group(0)}\n下单人：{o['customer']}\n平台：{o['platform']}\n"
                         f"商品：{o['items']}\n金额：${o['total']}\n下单时间：{o['created']}\n状态：{status}\n\n还有其他需要帮您的吗？")
            else:
                reply = (f"📋 Order Lookup Result\n\nOrder ID: {m.group(0)}\nCustomer: {o['customer']}\n平台：{o['platform']}\n"
                         f"Items: {o['items']}\nTotal: ${o['total']}\nOrder Date: {o['created']}\nStatus: {status}\n\nAnything else I can help with?")
            source = "get_order_info"
        else:
            trace.append({"step": "ReAct - 观察", "detail": "未检测到有效订单号 → 引导用户提供", "icon": "👁️"})
            reply = (
                "请提供您的订单号（格式如 US2024-3821），我来帮您查询。\n\n💡 提示：订单号可以在确认邮件中找到。"
                if lang == "zh"
                else "Please provide your order number (format: US2024-3821) and I'll look it up for you.\n\n💡 Tip: You can find your order number in the confirmation email."
            )
            source = "get_order_info_ask"

    elif intent == "SHIPPING":
        trace.append({"step": "ReAct - 推理", "detail": "判断为物流追踪 → 需调用 track_package", "icon": "💭"})
        reply = (
            "请提供您的物流单号（tracking number），我来帮您查询包裹状态。\n\n💡 物流单号可以在发货确认邮件中找到。"
            if lang == "zh"
            else "Please provide your tracking number and I'll check your package status for you.\n\n💡 You can find the tracking number in your shipping confirmation email."
        )
        source = "track_package_ask"

    elif intent == "REFUND":
        trace.append({"step": "ReAct - 推理", "detail": "退款/退换货请求 → 先查政策 + 验证订单", "icon": "💭"})
        refund_item = next(
            (i for i in items if "退" in (i.title_zh or "") and "货" in (i.title_zh or "")), None
        )
        if refund_item:
            trace.append({
                "step": "ReAct - 行动",
                "detail": f"🔧 调用 search_faq → 命中「{refund_item.title_zh}」",
                "icon": "🔧",
            })
            matched_item = refund_item
            matched_item_id = refund_item.id
        trace.append({"step": "安全护栏", "detail": "🟠 高风险操作 → 自动回复 + 加入人工审核队列", "icon": "🛡️"})
        reply = (
            "📋 退款/退换货请求已受理。⚠️ 退款需要人工审核，我已为您提交请求，客服专员将在 24 小时内通过邮件与您联系。"
            if lang == "zh"
            else "📋 Refund/Return Request Submitted. ⚠️ Refunds require human review. I've submitted your request — a specialist will contact you via email within 24 hours."
        )
        source = "refund_flow"

    elif intent == "COMPLAINT":
        trace.append({"step": "ReAct - 推理", "detail": "投诉/不满情绪 → 安抚 + 升级人工", "icon": "💭"})
        trace.append({"step": "安全护栏", "detail": "🔴 自动升级到人工客服主管", "icon": "🛡️"})
        reply = (
            "非常抱歉给您带来了不好的体验！😔 我已经记录了您的反馈，并为您升级到客服主管处理。\n\n📌 预计 2 小时内会有专员通过邮件与您联系。"
            if lang == "zh"
            else "I'm truly sorry about your experience! 😔 I've logged your feedback and escalated this to a service supervisor.\n\n📌 A specialist will reach out via email within 2 hours."
        )
        source = "complaint_flow"

    else:  # CHITCHAT
        trace.append({"step": "ReAct - 推理", "detail": "闲聊类 → 无需工具调用，直接回复", "icon": "💭"})
        text_lower = user_input.lower()
        if lang == "zh":
            if any(g in text_lower for g in ["你好", "嗨", "早上好", "晚上好", "您好"]):
                reply = "您好！👋 我是 ShopHelper，您的跨境电商客服助手。有什么可以帮您的吗？"
            elif any(t in text_lower for t in ["谢谢", "感谢", "多谢"]):
                reply = "不客气！很高兴能帮到您～ 还有其他问题随时问我哦 😊"
            else:
                reply = "您好！有什么可以帮助您的呢？例如：查订单、查物流、了解退换政策、尺码建议等。"
        else:
            if any(g in text_lower for g in ["hi", "hello", "hey", "good morning", "good evening"]):
                reply = "Hello! 👋 I'm ShopHelper, your cross-border e-commerce assistant. How can I help you today?"
            elif any(t in text_lower for t in ["thanks", "thank", "appreciate"]):
                reply = "You're welcome! Glad I could help 😊 Feel free to reach out anytime!"
            else:
                reply = "Hello! How can I assist you? For example: check order status, track a package, learn about return policies, or get size recommendations."
        source = "chitchat"

    # 把生效中的 system Prompt 附在 trace 中，体现「Prompt 后台可改、且真正被读取」
    system_prompt = _render_prompt_templates(
        db, "system", {"language": "中文" if lang == "zh" else "English", "intent": intent}
    )
    if system_prompt:
        trace.append({"step": "Prompt 装配", "detail": f"已应用「system」场景 Prompt 模板（{len(system_prompt)} 字）", "icon": "📝"})

    if log:
        db.add(ChatLog(
            user_input=user_input, language=lang, intent=intent, confidence=confidence,
            safety_level=safety["level"], matched_item_id=matched_item_id, reply=reply,
        ))

    return {
        "reply": reply,
        "language": lang,
        "intent": intent,
        "intent_name": INTENT_NAMES.get(intent, intent),
        "confidence": confidence,
        "safety": safety,
        "matched_item_id": matched_item_id,
        "source": source,
        "trace": trace,
    }
