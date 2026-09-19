# Proposal

## Why

StudyPal 的 Dashboard 现在给的是冷冰冰的统计卡片与 AI 占位建议（`[AI 占位]` 字样），没有真正接入 LLM，用户体验缺最后一公里；上一 change `user-auth` 已经把账号与 JWT 落地，这一 change 在此基础上挂上一个真实的"AI 学习助手"对话入口，让 DeepSeek 基于用户的学习画像（连续学习天数 / 等级）给出可追问、流式呈现、带 Markdown 结构的回答，同时把会话落库以便后续做"学习回顾"与"AI 教练复盘"。

## What Changes

- 后端新增 `chat_sessions` 与 `chat_messages` 两表（user_id 外键关联 `users`，FK CASCADE），alembic 迁移 `0002_ai_chat.py`
- 后端新增 `app/routers/chat.py`，端点：
  - `POST /api/chat/sessions` —— 创建空会话
  - `GET /api/chat/sessions` —— 列出当前用户的会话（按 updated_at desc）
  - `GET /api/chat/sessions/{id}/messages` —— 拉取会话历史
  - `POST /api/chat/sessions/{id}/messages` —— 发送用户消息 + 流式（`text/event-stream`）返回助手回复；先持久化 user 与 assistant 两条消息，助手消息边生成边追加
- 后端新增 `app/services/deepseek.py`，封装 DeepSeek `chat/completions` 调用（OpenAI 兼容协议，stream=true），系统提示词由 `app/services/personalize.py` 拼装（注入 user_profile.streak_days / level 等）
- 后端读取 `DEEPSEEK_API_KEY`（来自 OS 环境变量，由 Windows 用户预设），缺失或非 dev/prod 启动时应 fail-fast（沿用 `Settings.assert_production_secret()` 的同款机制）
- 前端新增 `src/components/views/ChatView.tsx`：消息气泡列表 + 输入框 + 发送按钮 + 加载占位
- 前端新增 `src/components/ChatMessage.tsx`（PascalCase）渲染 Markdown（`react-markdown` + `remark-gfm`），自动滚动用 `useEffect` 监听 ref + `scrollIntoView`
- 前端 StudyPal Dashboard 在 Sidebar 增加 "AI 助手" 入口，复用现有 `views/` 目录模式，激活后渲染 ChatView
- 后端 CORS / 配置沿用 `user-auth` 已建立的 `app/config.py` 字段，不重复实现

## Capabilities

### New Capabilities

- `ai-chat`: StudyPal AI 学习助手的对话能力 —— 创建会话、流式发送消息、Markdown 渲染、消息持久化、DeepSeek 个性化回复；不含语音 / 文件 / 模型切换
- `chat-storage`: AI 对话与消息的存储模型 —— 会话表与消息表 schema、检索、用户隔离；不暴露给他人查询的接口

### Modified Capabilities

- （无）StudyPal 既有 `study-pal` UI 形态契约不改变 —— 仅在 Sidebar 增加一个入口并指向 ChatView；Sidebar requirement 不变更（"占位文案"场景依然保留 Settings 占位规则不变）

## Impact

- **新增后端代码**：`backend/app/models/chat.py`、`backend/app/schemas/chat.py`、`backend/app/services/deepseek.py`、`backend/app/services/personalize.py`、`backend/app/routers/chat.py`、alembic `0002_ai_chat.py`、测试 `tests/test_chat.py`
- **新增后端依赖**：`httpx`（已存在）用于 SSE 流式消费；可选 `sse-starlette` 简化 StreamingResponse 处理
- **新增前端代码**：`src/components/views/ChatView.tsx`、`src/components/ChatMessage.tsx`、可能的 `src/lib/chatApi.ts`；Sidebar 文件可能小幅扩展（增加 Chat 入口），仍为 mock Dashboard 内部结构
- **新增前端依赖**：`react-markdown` + `remark-gfm`（Markdown 渲染 + GFM 表格/任务列表）
- **新增环境变量**（后端）：`DEEPSEEK_API_KEY`（必需，无 dev 占位）、`DEEPSEEK_BASE_URL`（默认 `https://api.deepseek.com`）、`DEEPSEEK_MODEL`（默认 `deepseek-chat`）
- **现有行为**：用户认证、Profile、StudyPal Dashboard 既有渲染保持不变；前端 build 仍通过
- **数据流**：客户端 → 后端 chat 端点 → DeepSeek API（服务端代理） → SSE 回流客户端 → 后端持久化 → 客户端刷新历史
- **隐私**：客户端永远不接触 `DEEPSEEK_API_KEY`；DeepSeek 调用由后端持有 secret 发起

### Out of Scope（明确不做）

- **语音输入 / 录音 / 实时语音转文字**
- **文件上传 / 文档解析 / 图片输入**
- **模型切换 UI**：仅 DeepSeek，不暴露多模型选择
- **工具调用 / Function calling**：本 change 内不接入工具（如日历、Quiz、cards），仅做单轮/多轮 chat
- **对话分享 / 公开链接 / 多用户协作会话**
- **前端 chat 与 StudyPal Dashboard 统计卡片的深度联动**：本期聊天是独立入口，不读 streak/level 直接渲染到 Dashboard
- **管理后台 / 审计 / 滥用检测**

### 回滚方案（高风险变更）

- 失败模式 1：DeepSeek 不可达或 key 错误 → 流式响应以 `event: error` 终止，已落库的部分 assistant 消息保留 `status=incomplete`，前端按"加载失败"渲染并允许重发
- 失败模式 2：迁移破坏 → `alembic downgrade -1` 回滚 `0002_ai_chat.py`，删除 `chat_sessions` / `chat_messages`；新表无既有用户数据，影响面为空
- 失败模式 3：误把 API key 漏到前端 → CI 加 `grep -r "DEEPSEEK_API_KEY" src/` 在 PR 上 fail；本期不消费该 env，源码层即可阻断
- 整体回滚 = 删除新增的 chat router / 前端 ChatView 与 Sidebar 入口，不影响 `user-auth` 与 `user-profile` 已上线能力