# Design

## Context

`user-auth` change 已上线后端骨架（FastAPI + SQLAlchemy + Alembic + JWT）并归档为 `openspec/specs/user-auth/`、`openspec/specs/user-profile/`；前端 StudyPal Dashboard 用 mock 数据。本 change 在已有 `backend/` 工程上叠加 AI 对话能力：

- 数据库：复用 SQLAlchemy 2.x 同步 ORM + Alembic 迁移
- 鉴权：复用 `app.deps.get_current_user` 解析 Bearer token，所有 chat 端点强制登录
- 配置：复用 `app.config.Settings` 字段（`env` / `is_dev`），新增 DEEPSEEK_* 字段
- 前端：复用 `src/components/views/` 目录模式（已存在 Dashboard 子页面）+ Tailwind v4 token

部署现实与 user-auth 一致：前端 GitHub Pages、后端部署到支持 Python runtime 的平台，DEEPSEEK 调用必须发生在后端，前端不接触 key。

## Goals / Non-Goals

**Goals:**
- 在 backend/ 内追加 chat 模块，零迁移现有端点
- 后端代理 DeepSeek 调用并以 SSE 流式转发给前端
- 前端 ChatView 与现有 Dashboard 共存，Sidebar 新增 Chat 入口
- 全部对话持久化，刷新后可继续

**Non-Goals**（设计层面，仅补充 proposal 未涉及的边界）:
- 不引入 WebSocket（仅 SSE 单向足够）
- 不引入消息队列 / Celery（同步流式即可，本期并发量低）
- 不引入 React Router（保持现有锚点 + 内嵌 state 切换 active 视图模式）
- 不引入 prompt engineering 框架（如 langchain）—— 仅直连 OpenAI-compatible API
- 不在 deepseek.py 内做重试 / 退避（失败直接交给前端流式 error 事件）

## Decisions

### D1. SSE 而非 WebSocket

- **选择**：服务端 `StreamingResponse(..., media_type="text/event-stream")`，前端 `fetch + ReadableStream` 消费。
- **理由**：SSE 单向足够（用户 → 后端 → LLM → 后端 → 用户）、HTTP/1.1 友好、自动重连由浏览器支持、DeepSeek 自身流式协议就是 SSE。
- **备选**：WebSocket（需要双向但本期用不到）；长轮询（延迟高）。

### D2. DeepSeek OpenAI-compatible 客户端

- **选择**：用 `httpx`（已依赖）走 `client.chat.completions.create(stream=True, model=...)` 的 OpenAI SDK 风格；不引入 `openai` 包以减少依赖；自行封装 `app/services/deepseek.py`。
- **理由**：DeepSeek 的 `/v1/chat/completions` 与 OpenAI 兼容；自实现只需 ~50 行；测试时可注入 fake transport。
- **备选**：`openai` SDK（多 30MB 依赖）；手写 websocket（DeepSeek 也支持，但 SSE 更省事）。

### D3. 助手消息增量持久化策略

- **选择**：流开始前先插入 assistant 行的占位（`status=incomplete`, `content=""`），流过程中定期 UPDATE content（每 ~1s 或每 ~200 字符 batch），流结束时 status=complete。
- **理由**：中断后能保留"已收到"的部分；用户刷新页面看到的是 partial 而非空白。
- **备选**：流结束后一次性 INSERT（中断则丢失）；纯事件溯源（复杂度高）。

### D4. 流式刷新会话 updated_at

- **选择**：每次 assistant 流开始时 UPDATE `chat_sessions.updated_at = now()`，列表接口依此排序。
- **理由**：spec "新消息后排序更新" 的最简实现。
- **备选**：触发器（SQLite 支持有限）；查 messages.max(created_at)（多一次 JOIN）。

### D5. 配置 fail-fast 借鉴 user-auth

- **选择**：在 `Settings` 扩展字段 `deepseek_api_key` / `deepseek_base_url` / `deepseek_model`；模块导入时 `assert_deepseek_config()` 检测 key 是否为空字符串或占位符；生产态（`ENV != "dev"`）缺失直接抛 RuntimeError。
- **理由**：与 `assert_production_secret()` 风格一致；防止 prod 误把空 key 部署上去默默失败。
- **备选**：lazy check（路由首次调用时报错）—— 启动期失败更易暴露。

### D6. Markdown 渲染库

- **选择**：`react-markdown` + `remark-gfm`（轻量、声明式、默认安全）。
- **理由**：默认禁用 HTML、内置 code block 标签；gfm 补全表格 / 任务列表；体积 < 30KB gzipped。
- **备选**：`marked` + DOMPurify（命令式更繁琐）；`MDX`（过重）。

### D7. 前端 ChatView 与现有 Dashboard 共存

- **选择**：复用 `src/components/views/` 目录（已用于 Dashboard 子视图），新增 `ChatView.tsx`；Sidebar 在 `views: ['Dashboard', 'Goals', 'Insights', 'Settings']` 后追加 `'Chat'`，active state 切换走现有 React state（与 study-pal 规范保持一致）。
- **理由**：零路由切换、无需引入 react-router；与 study-pal 已建立的"视图在 state 中切换"模式完全一致。
- **备选**：引入 react-router-dom v7（独立 change 决策）。

### D8. 自动滚动阈值

- **选择**：使用 `useRef` 监听 scroll container；维护 `isAtBottom` state（距底部 ≤ 64px 视为底部）；流到达新 delta 时，若 `isAtBottom` 则 `scrollIntoView({ behavior: 'smooth', block: 'end' })`，否则不滚。
- **理由**：spec "持续自动滚" + "用户向上滚停止" 的最简实现。
- **备选**：`IntersectionObserver` 哨兵元素（更精准但增加组件数）。

### D9. 流式中止处理

- **选择**：用户在流未结束时点击"停止"按钮 → 前端 `AbortController.abort()` → 后端 deepseek 客户端同样 abort → SSE 关闭 → DB 中该 assistant 消息保持 `status=incomplete`。
- **理由**：spec 允许 incomplete；前端停止按钮是 UX 细节不强制写进 spec。
- **备选**：服务端超时自动 abort（30s）作为兜底；超出 30s 写入 incomplete 并 SSE `event: error`。

### D10. 错误注入面

- **选择**：deepseek.py 接受一个可选 `transport: httpx.BaseTransport` 参数；测试注入 MockTransport 返回伪造 SSE 流。
- **理由**：与 user-auth 的 in-memory SQLite 同思路，单元测试无需真打 DeepSeek。
- **备选**：respx / pytest-httpx mock（多一个 dev 依赖）。

### D11. 后端目录增量

```
backend/app/
├── services/
│   ├── __init__.py
│   ├── deepseek.py        # httpx 封装 + 流式
│   └── personalize.py     # system prompt 拼装
├── models/chat.py         # ChatSession / ChatMessage
├── schemas/chat.py        # SessionOut / MessageOut / SendMessageIn
└── routers/chat.py        # /api/chat/* 端点
backend/alembic/versions/0002_ai_chat.py
backend/tests/test_chat.py
```

```
frontend src/
├── components/views/ChatView.tsx
├── components/ChatMessage.tsx
└── lib/chatApi.ts
```

## 组件层级图

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (React 19 + Vite)                             │
│  ┌──────────────────────────────────────────────────┐   │
│  │ App.tsx                                           │   │
│  │   └── Sidebar (新增 Chat 入口)                    │   │
│  │   └── DashboardPage → views:                      │   │
│  │         ├── StatsCards / DailyGoals / ...         │   │
│  │         └── ChatView (新)                         │   │
│  │              ├── MessageList                      │   │
│  │              │    └── ChatMessage (Markdown)      │   │
│  │              ├── Composer (输入框 + 发送)          │   │
│  │              └── useChatStream (SSE 消费)          │   │
│  └──────────────────────────────────────────────────┘   │
│                │ fetch + ReadableStream (SSE)            │
│                ▼ Bearer access_token                     │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  FastAPI app  (uvicorn)                                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │ routers/chat.py                                   │   │
│  │   ├── POST /api/chat/sessions                     │   │
│  │   ├── GET  /api/chat/sessions                     │   │
│  │   ├── GET  /api/chat/sessions/{id}/messages       │   │
│  │   └── POST /api/chat/sessions/{id}/messages (SSE) │   │
│  ├──────────────────────────────────────────────────┤   │
│  │ services/personalize.py → system prompt            │   │
│  │ services/deepseek.py → httpx streaming            │   │
│  └──────────────────────────────────────────────────┘   │
│  deps.get_current_user (复用 user-auth)                 │
└─────────────────────────────────────────────────────────┘
                          │  httpx streaming
                          ▼
                  DeepSeek API (api.deepseek.com)
                          ▲
                          │  SSE response
                          │
┌─────────────────────────────────────────────────────────┐
│  SQLite (WAL)                                           │
│    ├── chat_sessions (id, user_id FK, created_at,       │
│    │                   updated_at)                      │
│    └── chat_messages (id, session_id FK, role, content, │
│                       status, created_at)               │
│  Alembic migrations: 0001_initial (user-auth) +         │
│                       0002_ai_chat (new)                │
└─────────────────────────────────────────────────────────┘
```

## API 端点规范

所有响应 JSON；4xx/5xx `{ "detail": "..." }`。流式端点单独标注。

### POST `/api/chat/sessions`

请求体：（空）
响应 200：
```json
{ "session_id": 42, "user_id": 1, "created_at": "2026-09-18T12:34:56Z", "updated_at": "..." }
```
错误：401。

### GET `/api/chat/sessions`

响应 200：
```json
[
  { "session_id": 42, "created_at": "...", "updated_at": "...", "preview": "今天学习..." },
  ...
]
```
错误：401。

### GET `/api/chat/sessions/{session_id}/messages`

响应 200：
```json
[
  { "message_id": 1, "role": "user", "content": "你好", "status": "complete", "created_at": "..." },
  { "message_id": 2, "role": "assistant", "content": "你好！...", "status": "complete", "created_at": "..." }
]
```
错误：401 / 404（他人会话或不存在）。

### POST `/api/chat/sessions/{session_id}/messages` (SSE)

请求体：`{ "content": "用户消息" }`
响应：`Content-Type: text/event-stream`，事件序列：
```
data: {"message_id": 3, "role": "assistant", "delta": "你"}

data: {"message_id": 3, "role": "assistant", "delta": "好"}

event: done
data: {"message_id": 3, "status": "complete"}
```
错误：
- 401 / 404
- 422（content 空）
- 流中失败：`event: error\ndata: {"detail": "..."}`

## Risks / Trade-offs

- **[Risk] DEEPSEEK_API_KEY 误入前端** → Mitigation：CI 加 `grep -r "DEEPSEEK_API_KEY" src/` fail；后端 .env.example 写明仅后端使用；review checklist 强制
- **[Risk] SSE 在反向代理下被缓冲** → Mitigation：部署文档说明禁用 nginx `proxy_buffering`；uvicorn 直接暴露不缓冲
- **[Risk] 流中断导致 assistant 永久 incomplete** → Mitigation：DB 记录保留 `status=incomplete`，前端 badge 提示"未完成"；用户可手动重发
- **[Risk] DeepSeek 速率限制 / 配额耗尽** → Mitigation：错误透传 429 给前端，前端展示"AI 暂时繁忙"；本期不做配额记录
- **[Risk] Markdown 注入 XSS** → Mitigation：`react-markdown` 默认禁用 HTML + `remark-gfm` 不引入危险插件；spec "注入被剥离" 强制约束
- **[Trade-off] 不引入 React Router** → 优点：零新依赖；缺点：Chat 与 Dashboard 共享同一路由锚点 / state hash。后续若需要 URL 直链（`/chat/:id`），需独立 change
- **[Trade-off] 系统提示词不带历史摘要** → 优点：实现最薄；缺点：长对话上下文膨胀。spec 只承诺注入 streak/level，未来 change 可引入摘要

## Migration Plan

- **首次部署**：
  1. 后端：`alembic upgrade head`（应用 0002_ai_chat）
  2. 注入 `DEEPSEEK_API_KEY` 等环境变量（与 JWT_SECRET 同样走平台 secret manager）
  3. 启动 uvicorn；`curl /api/chat/sessions` 在带 Bearer 时返回 200，无 token 时返回 401
- **回滚**：
  - 数据库：`alembic downgrade -1` 回退 0002
  - 代码：删除新增模块与前端 ChatView / Sidebar Chat 入口
  - 与 user-auth 同款"删除文件即可"零侵入式回滚

## Open Questions

- （无）所有会影响 spec 的取舍已在 Decisions 中给出；流式超时阈值（30s）与"停止"按钮的 UX 细节属于 tasks.md 范畴。