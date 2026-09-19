# Spec Delta

## Purpose

为 StudyPal 已登录用户提供成就徽章系统：基于学习日历聚合结果实时判定 5 个预定义徽章的解锁状态与进度，前端以卡片列表呈现，未解锁徽章灰显并展示进度条。

## ADDED Requirements

### Requirement: 获取成就列表

系统 SHALL 提供 `GET /api/analytics/achievements` 端点；响应 SHALL 为长度 5 的数组，每项 SHALL 包含 `id` / `title` / `description` / `unlocked`（bool）/ `progress`（整数 ≥ 0）/ `target`（整数 > 0）。

#### Scenario: 已登录用户获取列表

- **WHEN** 已登录用户调用该端点
- **THEN** 系统 SHALL 返回 HTTP 200 与长度 5 的数组；任何徽章 SHALL NOT 缺失字段

#### Scenario: 未登录调用（错误场景）

- **WHEN** 客户端未携带 access token 调用
- **THEN** 系统 SHALL 返回 HTTP 401

### Requirement: 徽章定义（5 个）

系统 SHALL 定义且仅定义以下 5 个徽章（id 固定）：
- `first_lesson`：累计至少 1 条 chat 用户消息
- `streak_3`：连续学习天数 ≥ 3
- `streak_7`：连续学习天数 ≥ 7
- `total_50`：累计 chat 用户消息数 ≥ 50
- `total_100`：累计 chat 用户消息数 ≥ 100

每个徽章 SHALL 在响应中按上述顺序稳定排列。

#### Scenario: 顺序稳定

- **WHEN** 同一用户重复调用该端点
- **THEN** 两次响应 SHALL 在 id 字段上完全一致；顺序不应随机

### Requirement: 解锁判定

`unlocked` SHALL 为 true 当且仅当该徽章的进度达到 `target`；否则 SHALL 为 false 且 `progress` SHALL 等于"当前累计值"（不超 target）。

#### Scenario: 解锁达成

- **WHEN** 用户累计 chat 用户消息数为 50
- **THEN** `total_50` SHALL 出现在响应中，`unlocked` 为 true，`progress` 与 `target` 均 ≥ 50

#### Scenario: 未解锁进度可观察（错误场景）

- **WHEN** 用户累计 chat 用户消息数为 27
- **THEN** `total_50` SHALL 出现在响应中，`unlocked` 为 false，`progress` SHALL 为 27，`target` SHALL 为 50

### Requirement: 进度刷新

用户每次新的 chat 用户消息落库后，下次调用 `/api/analytics/achievements` SHALL 反映新进度；后端 SHALL NOT 维护缓存层（每次实时计算）。

#### Scenario: 实时刷新

- **WHEN** 用户先调一次成就（progress=27），再发一条 chat 用户消息，再调一次
- **THEN** 第二次 `total_50.progress` SHALL 为 28

### Requirement: 用户隔离

成就列表 SHALL 仅反映当前用户自己的行为；不应暴露其他用户的任何累计值。

#### Scenario: 跨用户不可见（错误场景）

- **WHEN** 用户 A 与 B 都注册后，A 调成就
- **THEN** 响应 SHALL 仅基于 A 的数据；B 的累计 SHALL NOT 影响 A 的徽章状态

### Requirement: 前端徽章卡片

前端 SHALL 渲染徽章卡片：未解锁时背景 `muted`、图标置灰、底部进度条按 `progress / target` 比例填充 `accent`；解锁时背景 `accent/15`、图标着色、`unlocked=true` 文案。

#### Scenario: 未解锁灰显

- **WHEN** 某徽章 `unlocked == false`
- **THEN** 卡片 SHALL 渲染灰底 + 进度条

#### Scenario: 解锁高亮

- **WHEN** 某徽章 `unlocked == true`
- **THEN** 卡片 SHALL 渲染 accent 底色 + "已解锁"文案