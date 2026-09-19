# Spec Delta

## Purpose

为 StudyPal AI 学习助手提供对话与消息的持久存储模型：`chat_sessions` 与 `chat_messages` 两表，全部消息按 user_id 强隔离，跨用户访问一律不可见；不暴露管理他人会话的接口。本规范仅约束存储层的对外可观测行为。

## ADDED Requirements

### Requirement: 会话表

系统 SHALL 维护 `chat_sessions` 表，每条记录 SHALL 归属于唯一 `user_id`（FK `users.id` ON DELETE CASCADE）；会话 SHALL 拥有 `created_at` 与 `updated_at` 两个时间戳，更新消息时 `updated_at` SHALL 自动刷新。

#### Scenario: 创建会话落库

- **WHEN** 用户调用创建会话端点
- **THEN** SHALL 写入一行 `chat_sessions`，`user_id` 等于当前 JWT 中的 `sub`

#### Scenario: 关联用户被删除（错误场景）

- **WHEN** 某 `users` 行被删除
- **THEN** 数据库 SHALL 级联删除其名下全部 `chat_sessions` 与 `chat_messages`；不应有孤立行

### Requirement: 消息表

系统 SHALL 维护 `chat_messages` 表，每条记录 SHALL 归属于唯一 `session_id`（FK `chat_sessions.id` ON DELETE CASCADE）；消息 SHALL 至少包含 `role`（`user` / `assistant`）、`content`（文本）、`status`（`complete` / `incomplete`）、`created_at`。

#### Scenario: 写入用户消息

- **WHEN** 用户在会话中发送消息
- **THEN** SHALL 写入一行 `chat_messages`，`role=user`，`status=complete`

#### Scenario: 流式追加 assistant 内容（错误场景）

- **WHEN** DeepSeek 流中途失败（连接断 / 超时 / 4xx-5xx）
- **THEN** 已收到的部分 SHALL 持久化为 `role=assistant` `status=incomplete` 的行；前端 SHALL NOT 期待该消息被自动完成

#### Scenario: 关联会话被删除（错误场景）

- **WHEN** 某 `chat_sessions` 行被删除
- **THEN** 数据库 SHALL 级联删除其全部 `chat_messages`；不应有孤立消息

### Requirement: 用户隔离

任意会话/消息查询 SHALL 限定 `user_id = current_user.id`；后端 SHALL NOT 提供跨用户查询或管理接口。

#### Scenario: 跨用户访问被拒（错误场景）

- **WHEN** 用户 A 尝试通过会话 ID 访问用户 B 的会话消息
- **THEN** SHALL 返回 HTTP 404，不应暴露"对方存在"的任何线索

#### Scenario: 列表过滤

- **WHEN** 用户调用列表会话端点
- **THEN** SHALL 仅返回 `user_id = current_user.id` 的行；其他用户的会话 SHALL 不出现

### Requirement: 更新顺序与会话新鲜度

系统 SHALL 在每次向某会话追加消息时刷新该会话的 `updated_at`，列表接口 SHALL 基于该字段排序。

#### Scenario: 新消息后排序更新

- **WHEN** 用户在旧会话中追加消息
- **THEN** 该会话在列表接口中的位置 SHALL 提升至顶端或接近顶端

#### Scenario: 无消息会话保持原序（错误场景）

- **WHEN** 用户创建一个会话但未发任何消息
- **THEN** 列表接口中该会话的 `preview` SHALL 为空字符串且 SHALL 不被任意"含消息"会话挤到其后以外