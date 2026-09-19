## Purpose

StudyPal 是个人学习 Dashboard 的 UI 形态契约：在浏览器中呈现左侧 Sidebar 导航、顶部统计卡片、每日目标清单、AI 建议面板与周/月趋势图，让用户在没有后端的情况下也能体验学习平台的完整视觉与交互。所有数据来自 `src/data/studyPal.ts` 的 mock 常量，行为契约聚焦在渲染、交互、暗色适配与边界兜底。

## ADDED Requirements

### Requirement: 左侧 Sidebar 导航

系统 SHALL 在视口左侧渲染一条固定宽度的垂直导航栏，包含 Dashboard / Goals / Insights / Settings 四个入口；用户点击任一入口 SHALL 切换 Dashboard 主区域的 active 高亮并更新主区域顶部标题，URL SHALL NOT 变化。

#### Scenario: 初始 active 状态

- **WHEN** Dashboard 首次加载完成
- **THEN** Dashboard 入口 SHALL 处于 active 高亮态，顶部标题区 SHALL 显示与 Dashboard 入口一致的文案

#### Scenario: 切换入口

- **WHEN** 用户点击 Goals 入口
- **THEN** Goals 入口 SHALL 进入 active 态，Dashboard 顶部标题 SHALL 更新为 Goals 相关文案，主区域内容 SHALL 切换至 Goals 视图

#### Scenario: Settings 入口占位（错误场景）

- **WHEN** 用户点击 Settings 入口
- **THEN** 主区域 SHALL 渲染占位文案 `[Settings 占位] 此模块在后续 change 中实现`，浏览器 SHALL NOT 抛出未捕获错误

### Requirement: 数据统计卡片

系统 SHALL 在 Dashboard 顶部渲染三张统计卡片，分别为总学习时长、已完成课程数、连续打卡天数；数据 SHALL 来自 `src/data/studyPal.ts` 中 `stats` 常量。

#### Scenario: 正常渲染

- **WHEN** Dashboard 视图加载完成
- **THEN** 系统 SHALL 渲染三张卡片，每张 SHALL 包含一个数值与一个中文标签，且数值 SHALL ≥ 0

#### Scenario: 学习时长格式化

- **WHEN** 卡片显示总学习时长
- **THEN** 若 ≥ 60 分钟 SHALL 显示为 `X 小时`，若 < 60 分钟 SHALL 显示为 `X 分钟`

#### Scenario: mock 数据缺失（错误场景）

- **WHEN** `src/data/studyPal.ts` 中 `stats` 为空对象或缺字段
- **THEN** 受影响卡片 SHALL 显示 `[数据待接入]`，浏览器 SHALL NOT 抛出未捕获错误

### Requirement: 每日目标清单

系统 SHALL 在 Goals 视图下渲染当日任务清单，每条任务 SHALL 可勾选/取消；勾选状态 SHALL 仅存于 React 组件本地 state，页面刷新后 SHALL 回到初始未勾选态。

#### Scenario: 勾选任务

- **WHEN** 用户点击某条任务的复选框
- **THEN** 该任务 SHALL 标记为完成（视觉上 SHALL 出现删除线或对勾），顶部计数器 SHALL 显示 `已完成 X/Y`

#### Scenario: 全部完成

- **WHEN** 所有任务均被勾选
- **THEN** 计数器 SHALL 显示 `已完成 N/N`，Goals 视图顶部 SHOULD 显示鼓励文案 `[今日目标已达成]`

#### Scenario: 空清单兜底（错误场景）

- **WHEN** `src/data/studyPal.ts` 中 `dailyGoals` 为空数组
- **THEN** 清单区 SHALL 显示 `今日暂无目标`，浏览器 SHALL NOT 渲染空白区域或抛错

### Requirement: AI 建议学习面板

系统 SHALL 在 Insights 视图下渲染 AI 建议面板，面板内 SHALL 显示 2-4 条学习建议，每条 SHALL 包含 `title` / `reason` / `estimatedMinutes` 三个字段；面板顶部 SHALL 显示 `[AI 占位]` 字样以明示数据非真实 AI 生成。

#### Scenario: 正常渲染

- **WHEN** Insights 视图加载完成
- **THEN** 面板 SHALL 渲染至少 2 条建议，且每条 SHALL 完整渲染上述三个字段

#### Scenario: 数据缺失降级（错误场景）

- **WHEN** `src/data/studyPal.ts` 中 `aiSuggestions` 为空数组
- **THEN** 面板 SHALL 显示 `[AI 占位] 暂无建议`，浏览器 SHALL NOT 抛错

### Requirement: 周/月趋势图

系统 SHALL 在 Insights 视图下渲染两个 SVG 图表：周视图（近 7 天柱状图，X 轴为日期缩写，Y 轴为学习分钟数）与月视图（近 30 天折线图，X 轴为日期缩写，Y 轴为学习分钟数）；图表描边/填充 SHALL 通过 Tailwind v4 token（`accent` / `muted`）解析，主题切换后 SHALL 自动跟随。

#### Scenario: 图表渲染

- **WHEN** Insights 视图加载完成
- **THEN** 周视图 SHALL 渲染 7 个 `<rect>` 柱，月视图 SHALL 渲染一条 `<polyline>` 折线加若干 `<circle>` 数据点

#### Scenario: 空数据兜底（错误场景）

- **WHEN** `src/data/studyPal.ts` 中 `weeklyTrend` 或 `monthlyTrend` 为空数组
- **THEN** 对应图表 SHALL 显示 `暂无数据` 文本占位，浏览器 SHALL NOT 渲染空 `<svg>` 或抛错

#### Scenario: 主题切换适配

- **WHEN** 用户点击 ThemeToggle 在明/暗之间切换
- **THEN** 图表颜色 SHALL 在 ≤ 1 秒内跟随主题变更，无旧主题颜色残留

### Requirement: 主题与现有 token 继承

Dashboard SHALL 复用现有 `useTheme` hook 与 `<html class="dark">` 驱动机制；任何新增组件 SHALL 使用 Tailwind v4 `@theme` token（`background` / `foreground` / `muted` / `accent` / `accent-hover` / `border`），禁止硬编码颜色值。

#### Scenario: 系统暗色偏好默认

- **WHEN** 浏览器 `prefers-color-scheme` 为 dark 且 `localStorage` 中无用户偏好
- **THEN** Dashboard SHALL 以暗色模式渲染，且 SHALL NOT 出现亮色闪烁

#### Scenario: localStorage 不可用（错误场景）

- **WHEN** `localStorage` 抛出 SecurityError（如隐私模式）
- **THEN** Dashboard SHALL 仍能正常渲染并响应 ThemeToggle 点击，仅 SHALL NOT 持久化偏好

### Requirement: 响应式布局

Dashboard SHALL 在 ≥ 1024px 视口下显示完整左侧 Sidebar（宽度 ≥ 240px，包含文字标签）；在 < 1024px 视口下 SHALL 折叠为顶部一条横向简化的导航条，主区域 SHALL 占据剩余宽度。

#### Scenario: 桌面布局

- **WHEN** 视口宽度 ≥ 1024px
- **THEN** Sidebar SHALL 显示完整文字标签（Dashboard / Goals / Insights / Settings），且 SHALL 固定在视口左侧

#### Scenario: 移动布局

- **WHEN** 视口宽度 < 1024px
- **THEN** Sidebar SHALL 折叠为顶部横向图标条或汉堡按钮，主区域 SHALL 占满视口宽度且 SHALL 不出现横向滚动

### Requirement: mock 数据结构稳定性

`src/data/studyPal.ts` SHALL 导出 TypeScript 类型 `StudyPalData` 与常量 `studyPalData: StudyPalData`；该类型的字段命名 SHALL 与未来 FastAPI 端点的 JSON 响应 schema 一致，便于后续无缝替换为真实数据源。

#### Scenario: 类型导出可用

- **WHEN** 其他模块 `import { StudyPalData } from '../data/studyPal'`
- **THEN** TypeScript 编译 SHALL 通过，且 SHALL 暴露 `stats` / `dailyGoals` / `aiSuggestions` / `weeklyTrend` / `monthlyTrend` 五个字段类型
