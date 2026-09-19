# Spec Delta

## Purpose

为已登录 StudyPal 用户提供自身学习画像（头像、连续学习天数、用户等级）的读取与头像更新能力。连续学习天数与等级的初始值由注册流程确定，业务增长口径由后续 change 引入；本期不开放客户端直接修改这两个字段。

## ADDED Requirements

### Requirement: 读取当前用户 Profile

系统 SHALL 为已登录用户提供读取自身 Profile 的端点，响应 SHALL 包含 `user_id`、`email`、`avatar_url`、`streak_days`、`level` 五个字段。

#### Scenario: 已登录用户读取自身

- **WHEN** 客户端携带有效 access token 访问读取端点
- **THEN** 系统 SHALL 返回 HTTP 200 与上述五个字段；`streak_days` SHALL ≥ 0，`level` SHALL ≥ 1

#### Scenario: 未登录读取（错误场景）

- **WHEN** 客户端未携带 access token 或 token 无效访问读取端点
- **THEN** 系统 SHALL 返回 HTTP 401

#### Scenario: 读取他人 Profile（错误场景）

- **WHEN** 客户端尝试通过任何 ID 路径读取其他用户的 Profile
- **THEN** 系统 SHALL 返回 HTTP 404（路径不存在）；系统 SHALL NOT 暴露"查他人"端点

### Requirement: 更新当前用户头像

系统 SHALL 为已登录用户提供更新自身头像 URL 的端点；客户端 SHALL 提交 `avatar_url`（绝对 URL 或相对路径字符串）；提交后 SHALL 立即对该用户的读取端点可见。

#### Scenario: 更新成功

- **WHEN** 已登录用户提交长度 ≤ 2048 字符的 `avatar_url`
- **THEN** 系统 SHALL 返回 HTTP 200，且后续读取 SHALL 返回该值

#### Scenario: URL 长度超限（错误场景）

- **WHEN** 客户端提交长度 > 2048 字符的 `avatar_url`
- **THEN** 系统 SHALL 返回 HTTP 422

#### Scenario: 未登录更新（错误场景）

- **WHEN** 客户端未携带 access token 提交更新请求
- **THEN** 系统 SHALL 返回 HTTP 401，且 SHALL NOT 应用任何部分更新

### Requirement: Profile 字段不可越权修改

`streak_days` 与 `level` SHALL 仅由服务端内部写入，外部客户端 SHALL NOT 通过任何端点直接修改这两个字段。

#### Scenario: 提交 streak_days / level 更新（错误场景）

- **WHEN** 客户端在更新请求体中包含 `streak_days` 或 `level` 字段
- **THEN** 系统 SHALL 忽略这两个字段（保持原值），仅应用 `avatar_url`；响应 SHALL 返回最终态的 `streak_days` 与 `level`

### Requirement: Profile 初始值

系统 SHALL 在用户注册成功时为该用户创建 Profile 记录，`streak_days` 初始为 `0`，`level` 初始为 `1`，`avatar_url` 初始为占位字符串 `/static/avatars/default.png`（或等价的服务端默认占位）。

#### Scenario: 注册即读取

- **WHEN** 新注册用户首次访问读取端点
- **THEN** `streak_days` SHALL 为 `0`，`level` SHALL 为 `1`，`avatar_url` SHALL 为默认占位