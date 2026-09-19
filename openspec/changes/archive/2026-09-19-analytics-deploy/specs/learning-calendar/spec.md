# Spec Delta

## Purpose

为 StudyPal 已登录用户提供"学习日历"视图：以 heatmap 形式呈现用户近 N 天每日学习分钟数，连续学习天数为衍生指标；所有数据由后端从 `chat_messages` + `learning_events` 聚合后返回。

## ADDED Requirements

### Requirement: 获取学习日历数据

系统 SHALL 提供 `GET /api/analytics/calendar?days=N` 端点（N 接受 30 / 60 / 90 / 180，默认 90）；响应 SHALL 为长度为 N 的数组，按日期升序，每项 SHALL 包含 `date`（YYYY-MM-DD）与 `minutes`（整数 ≥ 0）；未登录 SHALL 返回 HTTP 401。

#### Scenario: 默认 90 天

- **WHEN** 已登录用户不带 `days` 参数调用
- **THEN** 系统 SHALL 返回 HTTP 200，长度恰好为 90 的数组；最后一项日期 SHALL 为调用当日（按 UTC）

#### Scenario: 自定义 30 天

- **WHEN** 已登录用户带 `days=30` 调用
- **THEN** 系统 SHALL 返回 HTTP 200，长度恰好为 30

#### Scenario: 非法 days 值（错误场景）

- **WHEN** 已登录用户带 `days=10`（不在白名单）调用
- **THEN** 系统 SHALL 返回 HTTP 422

#### Scenario: 未登录调用（错误场景）

- **WHEN** 客户端未携带 access token 调用
- **THEN** 系统 SHALL 返回 HTTP 401

### Requirement: 数据源与聚合口径

`minutes` SHALL 等于"当日 UTC 内 `chat_messages` 的用户消息条数 × 单位分钟常量 + 当日 `learning_events.minutes` 之和"；单位分钟常量 SHALL 固定为 5（一条用户消息视为 5 分钟学习投入）。

#### Scenario: 仅 chat 消息产生分钟数

- **WHEN** 用户当日向 AI 助手发送 3 条消息且无 learning_events
- **THEN** 该日 `minutes` SHALL 为 15

#### Scenario: learning_events 计入

- **WHEN** 用户当日发送 0 条消息但 learning_events 记录 20 分钟
- **THEN** 该日 `minutes` SHALL 为 20

#### Scenario: 跨日不重复计算（错误场景）

- **WHEN** 用户在 2026-09-18 23:30 UTC 发送消息，在 2026-09-19 00:30 UTC 发送另一条
- **THEN** 18 日与 19 日的 `minutes` SHALL 分别按各自 UTC 日聚合，不互相计入

### Requirement: 用户隔离

任意 `GET /api/analytics/calendar` 调用 SHALL 仅聚合当前用户的 `chat_messages` 与 `learning_events`；不应返回任何其他用户的数据。

#### Scenario: 跨用户不可见

- **WHEN** 用户 A 调用
- **THEN** 响应 SHALL 仅包含 A 的聊天与学习事件；用户 B 的数据 SHALL NOT 出现

### Requirement: 连续学习天数

前端 SHALL 基于 calendar 数组自行计算"连续学习天数"——从数组末项向前数，直到遇到首个 `minutes == 0` 的日期为止；该连续段长度 SHALL 在 AnalyticsView 顶部以"连续 N 天"形式呈现。

#### Scenario: 全活跃

- **WHEN** calendar 数组末尾连续 7 天 `minutes > 0`
- **THEN** AnalyticsView SHALL 显示"连续 7 天"

#### Scenario: 当日为 0（错误场景）

- **WHEN** calendar 数组最末项 `minutes == 0`
- **THEN** AnalyticsView SHALL 显示"连续 0 天"（不向历史回溯）

### Requirement: heatmap 渲染

前端 SHALL 以 SVG 网格渲染 heatmap，7 行 × ceil(N/7) 列；每个单元格 SHALL 根据当日 `minutes` 取 5 档颜色（accent token）；空数据（`minutes == 0`）SHALL 用 `border` token 描边。

#### Scenario: 5 档色阶

- **WHEN** 单元格 `minutes` 落在不同档位
- **THEN** SHALL 渲染对应色阶（0/1-10/11-30/31-60/61+），不应出现颜色超出 5 档

#### Scenario: 空数据降级（错误场景）

- **WHEN** 某日 `minutes == 0`
- **THEN** 单元格 SHALL 渲染 muted 描边样式而非错误