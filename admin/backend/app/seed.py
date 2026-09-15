"""种子数据：把原 demo/agent.py 中写死的知识库、人设 Prompt、模型配置迁移进配置库。"""

import random

from sqlalchemy.orm import Session

from .models import ChangeLog, ChatLog, KbCategory, KbItem, ModelConfig, PromptTemplate

CATEGORIES = [
    ("退换货政策", "Return & Refund Policy", "📋", 1, "退货时限、运费承担、不支持退货的商品"),
    ("物流运费", "Shipping & Delivery", "📦", 2, "配送时效、运费标准、物流查询、清关"),
    ("尺码指南", "Size Guide", "📏", 3, "服装尺码、鞋码换算、选码建议"),
    ("支付退款", "Payment & Refund", "💳", 4, "支付方式、退款到账时效"),
    ("投诉流程", "Complaint Handling", "📝", 5, "投诉处理流程与响应时效"),
]

ITEMS = [
    # 退换货政策
    ("退换货政策", "退换货基本政策", "Return & Refund Policy",
     """📋 退换货政策：
• 收到商品后 30 天内可发起退货
• 商品需保持原包装完整、未使用状态
• 质量问题退货：卖家承担退货运费
• 个人原因退货：消费者承担退货运费
• 退款将在仓库收到退货后 3-5 个工作日原路退回""",
     """📋 Return & Refund Policy:
• Returns accepted within 30 days of receiving your order
• Items must be in original packaging, unused condition
• Quality issues: we cover return shipping
• Personal reasons: buyer covers return shipping
• Refunds processed within 3-5 business days after we receive the return""",
     "退,换,退款,退货,退款政策,退换,return,exchange,refund",
     "return,refund,exchange,send back,money back"),

    ("退换货政策", "退货运费由谁承担", "Who pays return shipping",
     "质量问题导致的退货由卖家承担退货运费；因个人原因（如不喜欢、尺码不合）退货，由消费者承担退货运费。",
     "For quality issues, we cover the return shipping. For personal reasons (e.g. dislike, wrong size), the buyer covers return shipping.",
     "退货运费,运费谁出,谁承担运费,质量问题退货,return shipping,who pays shipping",
     "return shipping,who pays,quality issue,personal reason"),

    ("退换货政策", "不支持退货的商品", "Non-returnable items",
     "⚠️ 例外：内衣/泳装/耳环等个人卫生用品不支持退货；定制商品不支持退货；促销清仓商品仅支持换货。",
     "⚠️ Exceptions: Personal hygiene items (underwear, swimwear, earrings) and custom items are not eligible for return. Clearance items are exchange-only.",
     "内衣,泳装,耳环,定制商品,清仓,不支持退货,例外",
     "underwear,swimwear,earrings,custom,clearance,not eligible,exception"),

    # 物流运费
    ("物流运费", "标准配送与运费", "Standard Shipping & Fee",
     """📦 标准配送
• 处理时间：下单后 1-3 个工作日发货
• 运输时间：美国 5-10 天 / 欧洲 7-15 天 / 东南亚 5-8 天
• 运费：满 $50 包邮，不满 $50 收取 $5.99""",
     """📦 Standard Shipping
• Processing: 1-3 business days
• Transit: US 5-10 days / Europe 7-15 days / SE Asia 5-8 days
• Fee: Free over $50, $5.99 under $50""",
     "物流,运费,快递,运输,发货,配送,多久到,shipping,delivery",
     "shipping,delivery,fee,how long,arrive,standard"),

    ("物流运费", "加急配送说明", "Express Shipping",
     "【加急配送】处理时间：24 小时内发货；运输时间：美国 2-4 天 / 欧洲 3-6 天；运费：$12.99。",
     "【Express Shipping】Processing: within 24 hours; Transit: US 2-4 days / Europe 3-6 days; Fee: $12.99.",
     "加急,加急配送,快递加急,express,fast shipping,faster",
     "express,fast shipping,expedite,24 hours"),

    ("物流运费", "物流查询方式", "How to track",
     "🔍 物流查询：发货后会收到含 tracking number 的确认邮件，可在 17track.net 输入单号查询。",
     "🔍 Track your package via 17track.net using the tracking number in your confirmation email.",
     "跟踪,查询物流,怎么查物流,tracking,track,17track,单号",
     "track,tracking,17track,tracking number,where is my package"),

    ("物流运费", "关税与清关说明", "Customs & Duties",
     "跨境包裹可能产生目的地国家的关税，由收件人承担。清关通常需要 1-3 个工作日。",
     "Cross-border parcels may incur customs duties in the destination country, payable by the recipient. Customs clearance usually takes 1-3 business days.",
     "关税,清关,海关,customs,duty,tax",
     "customs,duty,tax,clearance,import fee"),

    # 尺码指南
    ("尺码指南", "服装尺码对照表", "Clothing Size Chart",
     "【服装】S: 86-91cm胸围 / M: 96-101cm / L: 106-111cm / XL: 116-121cm。不同品牌尺码可能有差异，请参考商品页 Size Chart。",
     '【Clothing】S: 34-36" bust / M: 38-40" / L: 42-44" / XL: 46-48". Sizing varies by brand — check the Size Chart on each product page.',
     "尺码,大小,size,胸围,码数,尺寸,多少码,偏大,偏小,合身",
     "size,fit,measurement,chart,bust,too big,too small,sizing"),

    ("尺码指南", "鞋码换算说明", "Shoe Size Conversion",
     "【鞋码】US6=36码(23cm) / US7=37码(23.5cm) / US8=38码(24cm) / US9=39码(25cm) / US10=41码(26cm)。脚宽建议选大一码。",
     '【Shoes】US6=EU36(9.1") / US7=EU37(9.3") / US8=EU38(9.4") / US9=EU39(9.8") / US10=EU41(10.2"). If you have wide feet, go up one size.',
     "鞋码,鞋子尺码,shoe,US码,欧码,脚宽,大一码",
     "shoe size,eu size,wide feet,go up one size,us size"),

    # 支付退款
    ("支付退款", "支持的支付方式", "Accepted Payment Methods",
     """💳 支付方式：
• PayPal / Visa / MasterCard / American Express
• Apple Pay / Google Pay
• Klarna 分期付款（仅限美国）""",
     """💳 Accepted Payment Methods:
• PayPal / Visa / MasterCard / American Express
• Apple Pay / Google Pay
• Klarna installment (US only)""",
     "支付,付款,paypal,信用卡,visa,mastercard,怎么付,支付方式,分期,klarna",
     "payment,pay,paypal,credit card,visa,mastercard,apple pay,klarna"),

    ("支付退款", "退款到账时效", "Refund Timeline",
     "⏱ 退款时效：PayPal 1-3 个工作日；信用卡 3-7 个工作日（取决于发卡行）。",
     "⏱ Refund Processing: PayPal 1-3 business days; Credit/Debit Cards 3-7 business days (depends on issuing bank).",
     "退款时效,多久到账,退款多久,到账时间,refund time",
     "refund time,how long refund,when refund,processing time"),

    # 投诉流程
    ("投诉流程", "投诉处理流程", "Complaint Handling Process",
     """📝 投诉处理流程：
1. 首先表达歉意，承认您的感受
2. 收集具体问题（拍照/描述）
3. 提供解决方案：退换/部分退款/补偿优惠券
4. 如需升级，将转接主管处理
5. 所有投诉 24 小时内首次响应""",
     """📝 Complaint Handling:
1. We first apologize and acknowledge your concerns
2. Gather specific details (photos/description)
3. Offer a solution: return/refund/coupon
4. If needed, escalate to supervisor
5. All complaints receive initial response within 24 hours""",
     "投诉,抱怨,不满意,差评,complaint,糟糕,生气,失望,举报",
     "complaint,angry,disappointed,terrible,awful,bad experience,report"),

    ("投诉流程", "投诉响应时效", "Complaint Response Time",
     "所有投诉均在 24 小时内首次响应；涉及退款的投诉将在 2 小时内转接客服专员跟进。",
     "All complaints receive an initial response within 24 hours. Complaints involving refunds are escalated to a specialist within 2 hours.",
     "投诉多久回复,响应时间,首次响应,response time,SLA",
     "response time,sla,how long complaint,first response"),
]

SYSTEM_PROMPT = """You are a professional cross-border e-commerce customer service assistant. You help overseas consumers with their questions about orders, shipping, returns, and product details.

## Your Working Style
1. Always identify the customer's real intent first (FAQ / order tracking / refund / product inquiry)
2. For policy questions (returns, shipping fees, size guides), search the knowledge base
3. For order/shipping questions, ask for the order number, then use search tools to find relevant information
4. Reply in the same language as the customer's question — current language: {language}
5. Format your replies clearly: cite policies for policy questions, show status & ETA for orders

## Safety Rules
- Never promise refunds or compensation - tell customers their request will be forwarded to the team
- Never share internal pricing or supplier information
- If a customer is angry or mentions legal action → acknowledge their frustration and offer to escalate to a human agent

## Reply Style
- Friendly and helpful tone
- Short paragraphs, bullet points when listing options
- No markdown formatting codes"""

PROMPTS = [
    ("跨境电商客服 · 人设主 Prompt", "system", SYSTEM_PROMPT, "language,intent",
     "Agent 的角色设定、工作流程、安全规则与回复风格（来自人设 Prompt v1.0）"),
    ("FAQ 政策类回复话术", "faq",
     "📚 以下是关于「{category}」的详细信息：\n\n{kb_content}\n\n还有其他需要帮您的吗？",
     "category,kb_content", "知识库命中后的回复包装话术，支持中英双语占位"),
    ("退款请求应答话术", "refund",
     "📌 已为您受理退款请求（订单 {order_id}）。退款需人工审核，客服专员将在 24 小时内通过邮件与您联系。",
     "order_id", "退款场景的标准化应答，强调「不承诺退款」的安全红线"),
    ("投诉安抚话术", "complaint",
     "非常抱歉给您带来了不好的体验！😔 我已记录您的反馈并升级至客服主管，预计 2 小时内专员与您联系。",
     "", "投诉场景的情绪安抚模板，配合 🔴 极高风险升级策略"),
]

MODELS = [
    ("GPT-4o-mini · 海外英文线", "openai", "https://api.openai.com/v1", "sk-********************",
     "gpt-4o-mini", 0.3, 1024, 1.0, "en", True, "承接海外英文咨询主力模型"),
    ("DeepSeek-V3 · 中文线", "deepseek", "https://api.deepseek.com/v1", "sk-********************",
     "deepseek-chat", 0.5, 2048, 1.0, "zh", True, "中文咨询，性价比高"),
    ("Qwen-Max · 兜底策略", "qwen", "https://dashscope.aliyuncs.com/compatible-mode/v1", "sk-********************",
     "qwen-max", 0.3, 1024, 1.0, "all", False, "英文线异常时的兜底模型"),
]

SEED_CHATS = [
    ("What's the status of my order US2024-3821?", "en", "ORDER", "🟢 低风险"),
    ("Where is my package with tracking number DHL9876543210?", "en", "SHIPPING", "🟢 低风险"),
    ("What's your return policy? Can I return if I don't like the color?", "en", "FAQ", "🟢 低风险"),
    ("I'm not sure about sizing. What size should I get if I usually wear M?", "en", "FAQ", "🟢 低风险"),
    ("What payment methods do you accept? Do you take PayPal?", "en", "FAQ", "🟢 低风险"),
    ("I received a damaged item and I'm very disappointed. This is terrible!", "en", "COMPLAINT", "🔴 极高风险"),
    ("我的包裹US2024-3821到哪里了？", "zh", "SHIPPING", "🟢 低风险"),
    ("我想退货，尺码不合适", "zh", "FAQ", "🟢 低风险"),
    ("寄到美国运费多少钱？", "zh", "FAQ", "🟢 低风险"),
    ("我要退款，订单 US2024-4521，收到的耳机有质量问题", "zh", "REFUND", "🟠 高风险"),
    ("Do you ship to Germany? How long does it take?", "en", "SHIPPING", "🟢 低风险"),
    ("你们的退货政策是什么？", "zh", "FAQ", "🟢 低风险"),
    ("退款一般多久到账？", "zh", "FAQ", "🟡 中风险"),
    ("I want to sue you, this is unacceptable!", "en", "COMPLAINT", "🔴 极高风险"),
    ("Hi, are you there?", "en", "CHITCHAT", "🟢 低风险"),
    ("你好，请问有人在吗？", "zh", "CHITCHAT", "🟢 低风险"),
]


def run_seed(db: Session) -> None:
    """幂等初始化：仅当配置库为空时写入种子数据。"""
    if db.query(KbCategory).count() > 0:
        return

    cat_map: dict[str, KbCategory] = {}
    for name, name_en, icon, order, desc in CATEGORIES:
        cat = KbCategory(name=name, name_en=name_en, icon=icon, sort_order=order, description=desc)
        db.add(cat)
        cat_map[name] = cat
    db.flush()

    for (cat_name, t_zh, t_en, a_zh, a_en, k_zh, k_en) in ITEMS:
        db.add(KbItem(
            category_id=cat_map[cat_name].id,
            title_zh=t_zh, title_en=t_en, answer_zh=a_zh, answer_en=a_en,
            keywords_zh=k_zh, keywords_en=k_en, status="published",
            hit_count=random.randint(3, 60),
        ))

    for (name, scene, content, variables, note) in PROMPTS:
        db.add(PromptTemplate(
            name=name, scene=scene, content=content, variables=variables, note=note,
            version=1, is_default=(scene == "system"),
        ))

    for (name, provider, base_url, key, model_name, temp, mt, tp, route, is_def, remark) in MODELS:
        db.add(ModelConfig(
            name=name, provider=provider, base_url=base_url, api_key=key, model_name=model_name,
            temperature=temp, max_tokens=mt, top_p=tp, route_lang=route, is_default=is_def, remark=remark,
        ))

    for text, lang, intent, level in SEED_CHATS:
        db.add(ChatLog(
            user_input=text, language=lang, intent=intent,
            confidence=round(random.uniform(0.4, 0.95), 2), safety_level=level,
            reply="（历史会话记录）",
        ))

    actions = [
        ("kb_item", 1, "退换货基本政策", "update", "运营-Amy"),
        ("prompt", 1, "跨境电商客服 · 人设主 Prompt", "update", "运营-Amy"),
        ("model", 2, "DeepSeek-V3 · 中文线", "create", "管理员-Leo"),
        ("kb_item", 5, "加急配送说明", "create", "运营-Amy"),
        ("kb_item", 12, "投诉响应时效", "update", "运营-Ken"),
    ]
    for et, eid, name, action, operator in actions:
        db.add(ChangeLog(entity_type=et, entity_id=eid, entity_name=name, action=action, operator=operator))

    db.commit()
