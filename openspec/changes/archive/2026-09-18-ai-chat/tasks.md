# Tasks

## 1. 后端依赖与配置

- [x] 1.1 在 `backend/requirements.txt` 追加 `sse-starlette>=2.0,<3.0` 与 `pydantic[email]>=2.9,<3.0`（如未包含），verify by `pip install -r backend/requirements.txt` 安装成功
- [x] 1.2 在 `backend/.env.example` 追加 `DEEPSEEK_API_KEY=`、`DEEPSEEK_BASE_URL=https://api.deepseek.com`、`DEEPSEEK_MODEL=deepseek-chat`；并在 `app/config.py` 增加 `Settings.deepseek_api_key / deepseek_base_url / deepseek_model` 三个字段，新增 `Settings.assert_deepseek_config()` 方法（生产态缺失 key 时启动失败），verify by `ENV=dev` 启动不抛错、`ENV=prod` 且 key 为空字符串时抛 `RuntimeError`
- [x] 1.3 在 `app/main.py` 确认 CORS allow_headers 包含 `text/event-stream`（默认 `*` 已覆盖，verify by `curl -H "Origin: http://localhost:5173" -H "Accept: text/event-stream" -i`）

## 2. 数据模型与迁移

- [x] 2.1 在 `backend/app/models/chat.py` 定义 `ChatSession`（id / user_id FK CASCADE / created_at / updated_at）与 `ChatMessage`（id / session_id FK CASCADE / role / content / status / created_at），并在 `models/__init__.py` re-export，verify by `python -c "from app.models.chat import ChatSession, ChatMessage"` 无异常
- [x] 2.2 写 alembic 迁移 `0002_ai_chat.py`：建 `chat_sessions` 与 `chat_messages` 表 + 外键 CASCADE + `chat_sessions.updated_at` 默认值；update `downgrade()` 删除两表；verify by `alembic upgrade head && sqlite3 studypal.db ".tables" | grep chat_` 同时输出 `chat_sessions` 与 `chat_messages`

## 3. 服务层

- [x] 3.1 在 `backend/app/services/__init__.py` 空包；新增 `services/personalize.py` 实现 `build_system_prompt(user, profile) -> str`，将 `streak_days` / `level` / `avatar_url` 拼入系统提示词（缺失字段跳过），verify by `pytest backend/tests/services/test_personalize.py::test_injects_known_fields` 与 `test_missing_fields_skipped` 通过
- [x] 3.2 新增 `services/deepseek.py`：实现 `async def stream_chat(messages, *, transport=None) -> AsyncIterator[str]`，用 `httpx.AsyncClient` POST `chat/completions` (stream=true, model=settings.deepseek_model)，逐 chunk 解析 `choices[0].delta.content` 并 yield；模块顶部检查 `assert_deepseek_config()`，verify by 注入 MockTransport 返回伪造 SSE 流，`pytest` 验证解析至少 yield 两个 delta
- [x] 3.3 在 `services/deepseek.py` 暴露 `DeepSeekError(Exception)` 类，包装 4xx/5xx 与超时；流式失败时让上层 router 把已 yield 的内容写入 incomplete，verify by 单测覆盖"网络断开 → 抛 DeepSeekError"

## 4. Schemas 与 Router

- [x] 4.1 在 `backend/app/schemas/chat.py` 定义 `SessionOut` / `SessionListItem` / `MessageOut` / `SendMessageIn`（content `min_length=1`），verify by `pytest -k schemas_chat` 通过字段校验
- [x] 4.2 在 `backend/app/routers/chat.py` 实现 `POST /api/chat/sessions` 与 `GET /api/chat/sessions`：强制登录、查询过滤 `user_id == current.id`、创建会话后立即 `db.refresh()` 拿 id；verify by `pytest backend/tests/test_chat.py::test_create_and_list_session` 通过
- [x] 4.3 在 `routers/chat.py` 实现 `GET /api/chat/sessions/{session_id}/messages`：先 `db.get(ChatSession, session_id)`，若不存在或 `user_id != current.id` 返回 404；返回 messages 升序，verify by `test_get_messages_own` 与 `test_get_messages_other_user_404` 通过
- [x] 4.4 在 `routers/chat.py` 实现 `POST /api/chat/sessions/{session_id}/messages` 流式端点：写 user message → 写 assistant 占位（`status=incomplete`, `content=""`）→ 异步迭代 `deepseek.stream_chat(...)` → 每收到 delta 累积并 UPDATE content → 流结束 UPDATE status=complete + UPDATE session.updated_at → 失败时 UPDATE assistant.status=incomplete 并 SSE `event: error`；verify by 注入 MockTransport 单测覆盖"完整流 / 中断流 → incomplete / 空 content 422 / 他人 session 404"四条路径
- [x] 4.5 在 `app/main.py` 注册 chat router（`app.include_router(chat_router.router)`），verify by `uvicorn app.main:app` 后 `/openapi.json` 含 `/api/chat/*` 路径

## 5. 前端基础设施

- [x] 5.1 安装 `react-markdown` 与 `remark-gfm`：`npm i react-markdown remark-gfm`（不指定版本，使用最新兼容 React 19 的 minor），verify by `package.json` 出现两依赖 + `npm run build` 通过
- [x] 5.2 在 `src/lib/chatApi.ts` 新增 fetch 封装：`listSessions()` / `createSession()` / `listMessages(id)` / `sendMessageStream(id, content, onDelta) -> AbortController`；统一从 `import.meta.env.VITE_API_BASE` 拼 URL；从 `localStorage.getItem('studypal_access_token')` 取 token；verify by `tsc -b` 编译通过
- [x] 5.3 在 `src/components/ChatMessage.tsx` 实现气泡组件（`role === 'user'` 右对齐 + accent 背景、`role === 'assistant'` 左对齐 + muted 背景）；用 `<ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>` 渲染 assistant 文本；verify by `tsc -b` 通过

## 6. ChatView 主组件

- [x] 6.1 在 `src/components/views/ChatView.tsx` 实现 `ChatView`：维护 `messages: ChatMessageUI[]` state + `isStreaming` 标志；进入页面时按需 `createSession` / `listMessages`；verifies by `tsc -b` 通过
- [x] 6.2 在 `ChatView` 内嵌 `<MessageList>` + `<Composer>` 子组件（或同文件内部组件）—— `MessageList` 含 `useRef` + `useEffect` 自动滚（`isAtBottom` 阈值 64px）；`Composer` 含 textarea + 发送按钮 + 停止按钮（流中显示）；verify by 手动打开 dev server（`npm run dev`）确认：
  - 初始空会话显示"开始对话吧"占位
  - 发送后用户消息立即出现，assistant 消息边流边增长
  - 向上滚动后停止按钮存在且可点击终止
- [x] 6.3 实现"发送"按钮 → 调用 `sendMessageStream(id, content, delta => appendDelta(...))`，onComplete 更新 status=complete、onError 显示 toast 或 inline 错误；verify by 同上手测路径：连续发送两条消息，第二条接续第一条上下文

## 7. Sidebar 接入

- [x] 7.1 在现有 Sidebar 文件（`src/components/Sidebar.tsx`）的视图列表追加 `'Chat'` 入口（图标与 Dashboard 现有图标同款风格）；active state 切换走现有 React state，verify by `npm run dev` 后点击 Chat 入口出现 ChatView，点击 Dashboard 回到原 view
- [x] 7.2 在 `App.tsx` / DashboardPage.tsx 的视图分派中加 `if (active === 'chat') return <ChatView />`，确保其余视图渲染不变，verify by `npm run build` 仍通过且 bundle 大小增量 < 60KB gzipped

## 8. 端到端验证

- [x] 8.1 后端：`cd backend && pytest` 全绿（含 user-auth 既有 24 tests 与本 change 新增 tests），verify by 终端输出 `N passed, 0 failed`
- [x] 8.2 前端：`npm run build` 成功且产物体积与 user-auth 归档前对比增量 < 60KB gzipped，verify by 终端 dist 大小报告
- [x] 8.3 手动冒烟（dev 环境）：
  1. 启动后端 `uvicorn app.main:app --reload`
  2. 启动前端 `npm run dev`
  3. 浏览器注册新账号 → 进 Dashboard → 切到 Chat → 发"今天学什么好" → 应看到 DeepSeek 个性化回复（含 streak/level 注入痕迹）
  4. 刷新页面 → 会话仍在 → 历史消息仍能展开
  5. `grep -r DEEPSEEK_API_KEY dist/` 不返回任何匹配（前端零泄漏）
- [x] 8.4 CI 守卫：在根目录 `.github/workflows/secret-scan.yml`（如不存在则新建）添加 `run: ! grep -r "DEEPSEEK_API_KEY" src/ || (echo "secret leak in src/" && exit 1)`，verify by 本地手动执行 grep 返回空退出码 0