# Shophelper 演示版

跨境电商智能客服 Agent 演示项目。基于 ReAct 架构，支持中英双语，实现意图识别、订单查询、物流追踪、FAQ 检索与四级安全护栏。

本仓库包含两部分：

| 目录 | 内容 |
|---|---|
| `demo.html` | 早期单页演示（Agent 对话静态 Demo） |
| `admin/` | **运营管理后台**：知识库 / Prompt / 大模型配置的可视化管理（前后端分离） |

## 管理后台（admin/）

解决"Agent 配置硬编码在代码里，运营改不动"的问题——把知识库、Prompt、模型配置全部外置为配置库，运营在后台增删改查，Agent 运行时实时读取，改一条 FAQ 无需发版。

### 功能模块

- **概览仪表盘**：配置资产统计、意图分布、知识库命中 TOP、最近变更时间线
- **知识库管理**：分类树 + 条目 CRUD、中英双语字段与关键词、发布/草稿/停用状态、检索测试（模拟 Agent 端命中预览）
- **Prompt 管理**：人设与场景话术编辑、变量占位符、版本快照 + 一键回滚、渲染预览
- **大模型接入**：OpenAI 兼容协议、供应商 / Key / 参数配置、按语言线路路由（英文线 / 中文线 / 兜底）、连通性测试
- **Agent 测试台**：实时对话 + ReAct Trace 逐步回放 + 配置溯源（命中哪条知识库、走哪个 Prompt、触发哪级安全策略）

### 技术栈与架构

```
React 18 + Ant Design 5 + Vite  ──/api──▶  FastAPI + SQLAlchemy + SQLite（配置库）
                                                │
                                                ▼
                                    Agent 运行时（配置驱动，替代硬编码常量）
```

- 后端：FastAPI + SQLAlchemy 2.x，首次启动自动建表并播种演示数据（5 分类 / 13 条知识库条目 / 4 个 Prompt / 3 条模型配置）
- 前端：React 18 + Ant Design 5 + TypeScript + Vite，开发模式经 Vite 代理 `/api` 到后端

### 本地运行

```powershell
# 1. 后端（端口 8000）
cd admin/backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# 2. 前端（端口 5173）
cd admin/frontend
npm install
npm run dev
```

打开 http://localhost:5173 即可使用。数据库文件 `admin/backend/data/admin.db` 首次启动自动生成（已加入 .gitignore）。

### 设计要点

1. **配置外置**：原 demo 中写死的 `FAQ_KNOWLEDGE` / 意图关键词 / 人设 Prompt 全部迁入数据模型，Agent 改为运行时读配置
2. **意图识别**：动作类意图（投诉 / 退款）优先于语境信号，单号仅作弱信号，避免误判
3. **模型接入抽象**：统一 OpenAI 兼容协议，换模型只改配置不碰代码
4. **说明**：当前版本为演示定位，模型配置仅做管理界面存储，Agent 回复仍走规则引擎；接口层已预留 LLM 调用位置
