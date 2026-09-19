## Purpose

为 StudyPal 已登录用户提供与 AI 学习助手的多轮对话能力：消息以气泡形式呈现、Markdown 渲染、助手回复以流式方式逐步推送，会话与消息持久化以便刷新后继续；助手基于用户 Profile（连续学习天数 / 等级）注入个性化上下文。

## Requirements

### Requirement: 创建会话

系统 SHALL 提供创建空会话的端点；已登录用户调用后 SHALL 返回新会话的 `session_id` 与创建时间戳；会话 SHALL 归属于当前 `user_id`，跨用户 SHALL 不可见。

#### Scenario: 创建成功

- **WHEN** 已登录用户调用 `POST /api/chat/sessions`
- **THEN** 系统 SHALL 返回 HTTP 200，body 包含 `session_id`、`user_id`、`created_at`；新会话 SHALL 持久化，初始无消息

#### Scenario: 未登录调用（错误场景）

- **WHEN** 客户端未携带 access token 调用该端点
- **THEN** 系统 SHALL 返回 HTTP 401

### Requirement: 列出当前用户的会话

系统 SHALL 为已登录用户提供列出自身会话的端点；返回 SHALL 按 `updated_at` 降序、每条至少包含 `session_id`、`created_at`、`updated_at`、最近一条消息的前 100 字符作为 `preview`。

#### Scenario: 列出成功

- **WHEN** 已登录用户调用 `GET /api/chat/sessions`
- **THEN** 系统 SHALL 返回 HTTP 200，body 为会话列表；任意会话 SHALL NOT 包含其他用户的会话

#### Scenario: 无会话返回空列表（错误场景）

- **WHEN** 已登录用户从未创建过会话
- **THEN** 系统 SHALL 返回 HTTP 200 与空数组；前端 SHALL NOT 报错

#### Scenario: 未登录调用（错误场景）

- **WHEN** 客户端未携带 access token 调用该端点
- **THEN** 系统 SHALL 返回 HTTP 401

### Requirement: 拉取会话历史

系统 SHALL 为已登录用户提供拉取指定会话全部消息的端点；返回 SHALL 按 `created_at` 升序，每条消息 SHALL 包含 `message_id`、`role`（`user` / `assistant`）、`content`、`status`（`complete` / `incomplete`）、`created_at`。

#### Scenario: 拉取成功

- **WHEN** 已登录用户调用 `GET /api/chat/sessions/{session_id}/messages` 且该会话归属当前用户
- **THEN** 系统 SHALL 返回 HTTP 200 与消息列表

#### Scenario: 访问他人会话（错误场景）

- **WHEN** 已登录用户尝试访问不属于自己的会话 ID
- **THEN** 系统 SHALL 返回 HTTP 404；系统 SHALL NOT 透露该会话是否存在

#### Scenario: 未登录调用（错误场景）

- **WHEN** 客户端未携带 access token 调用该端点
- **THEN** 系统 SHALL 返回 HTTP 401

### Requirement: 流式发送用户消息

系统 SHALL 提供流式端点；客户端提交用户消息后，服务端 SHALL 先持久化 user 消息、调用 DeepSeek 生成助手回复、并以 `text/event-stream` 持续推送 assistant 消息增量；推送完成后 SHALL 持久化 assistant 完整内容并以 `event: done` 终止流；首字节 SHALL 在 1 秒内到达。

#### Scenario: 正常流式回复

- **WHEN** 已登录用户向自己的会话发送 `content` 非空的消息
- **THEN** 系统 SHALL 返回 SSE 流；流中 SHALL 包含至少 1 个 `data: {"delta": "..."}` 事件，最后一个事件 SHALL 为 `event: done`；assistant 消息 SHALL 被持久化

#### Scenario: 空消息拒绝（错误场景）

- **WHEN** 客户端提交 `content` 为空字符串或仅含空白
- **THEN** 系统 SHALL 在写库前返回 HTTP 422；不应发起 DeepSeek 调用

#### Scenario: DeepSeek 不可达（错误场景）

- **WHEN** DeepSeek API 报错或超时（> 30s 无首字节）
- **THEN** 系统 SHALL 在 SSE 流中以 `event: error` 终止；之前已收到的增量 SHALL 持久化为 `status=incomplete` 的 assistant 消息

#### Scenario: 未登录调用（错误场景）

- **WHEN** 客户端未携带 access token 调用该端点
- **THEN** 系统 SHALL 返回 HTTP 401，不发起 DeepSeek 调用

### Requirement: 助手消息 Markdown 内容

助手消息 SHALL 渲染为 Markdown（含 GFM 表格、任务列表、代码块）；系统 SHALL NOT 渲染来自助手的 `<script>` / `<iframe>` / 内联事件处理器等可执行 HTML；代码块 SHALL 标注语言以便客户端高亮。

#### Scenario: Markdown 渲染

- **WHEN** assistant 消息包含列表、表格或代码块
- **THEN** 前端 SHALL 按 Markdown 解析并展示对应结构；代码块 SHALL 带语言标签

#### Scenario: 注入被剥离（错误场景）

- **WHEN** assistant 消息包含 `<script>` 或 `onerror=` 字符串
- **THEN** 前端 SHALL 渲染为纯文本或剥除该片段；不应执行任何脚本

### Requirement: 个性化上下文注入

服务端 SHALL 在每次调用 DeepSeek 前，将当前用户 Profile 关键字段（`streak_days`、`level`、`avatar_url`）拼入系统提示词；当 Profile 缺失字段时 SHALL 省略该字段而非报错。

#### Scenario: 注入成功

- **WHEN** 用户 Profile 已存在
- **THEN** 实际发往 DeepSeek 的 `messages` 数组首条 `system` 消息 SHALL 包含 `streak_days` 与 `level` 的当前值

#### Scenario: Profile 字段缺失（错误场景）

- **WHEN** Profile 行不存在（数据迁移遗留极端情况）
- **THEN** 系统 SHALL 不中断 SSE 流，system 消息 SHALL 仅含可用字段；客户端 SHALL NOT 收到 5xx

### Requirement: API Key 不外泄

系统 SHALL 仅在后端进程内持有 `DEEPSEEK_API_KEY`；前端 SHALL NOT 通过任何渠道（URL 参数、localStorage、cookie、response body）获得该 key；后端 SHALL NOT 在日志或错误响应中输出该 key 的明文。

#### Scenario: 前端无法获取 key（错误场景）

- **WHEN** 审查前端构建产物 `dist/assets/*.js`
- **THEN** SHALL 不存在 `DEEPSEEK_API_KEY` 字面量或对应的 base64 / 加密形式

#### Scenario: 日志不泄漏（错误场景）

- **WHEN** DeepSeek 调用失败并触发后端日志
- **THEN** 日志 SHALL 仅记录状态码与错误类型；不得包含 key 明文

### Requirement: 客户端自动滚动

前端 ChatView SHALL 在新消息到达时自动滚动到列表底部；当用户主动向上滚动查看历史消息时 SHALL NOT 打断阅读（即用户位于阈值范围内才自动滚）。

#### Scenario: 持续自动滚

- **WHEN** 用户停留在底部（距底部 ≤ 64px）且新消息追加
- **THEN** 视图 SHALL 自动滚到底部

#### Scenario: 用户向上滚停止（错误场景）

- **WHEN** 用户向上滚动且距底部 > 64px
- **THEN** 新消息到达 SHALL NOT 强制滚到底部；用户阅读体验不被中断