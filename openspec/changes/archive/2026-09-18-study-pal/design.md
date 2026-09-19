## Context

当前 `src/App.tsx` 把品牌站四段（Navigation / Hero / Projects / Contact）按 DOM 顺序拼成单页。本变更要把这套结构**就地改造**为 StudyPal Dashboard 形态——左侧 Sidebar 导航 + 右侧主区域呈现统计卡片 / 每日目标 / AI 建议 / 周月趋势——同时不引入路由、不引入网络请求、不引入第三方图表库。所有新行为由 `src/data/studyPal.ts` 的内存常量驱动，详见 `proposal.md - Why / What Changes`。本设计聚焦在架构与决策层面，需求层面见 `specs/study-pal/spec.md`。

## Goals / Non-Goals

**Goals（设计层面）**
- 用最小新增依赖完成 Dashboard UI（仅依赖现有 `react` / `tailwindcss`，无新 npm package）。
- 主题机制（`useTheme` + Tailwind v4 token + `<html class="dark">`）零侵入延续。
- mock 数据层结构与未来 FastAPI 响应 schema 一致，未来切换真实数据源时**只改 import 路径**，不改组件。
- 提供清晰的 view 切换机制（内部 state，无 URL 变化），为后续可选的 client-side router 切换留出低摩擦路径。

**Non-Goals（设计层面；与 proposal out-of-scope 互不重叠，专注于实现边界）**
- 不引入 react-router / wouter / 任何 router 库。
- 不引入 chart.js / recharts / victory / 任何图表库。
- 不引入 zustand / redux / jotai / Context 跨组件状态库；视图切换仅靠 App 级 `useState`。
- 不重写 `useTheme` / `ThemeToggle` / `HeroBackground` / `index.css` 任何一个文件。
- 不引入 localStorage 业务字段（仅保留 `theme` 这一既有字段）。

## Decisions

### Decision 1：Sidebar 是新文件 `Sidebar.tsx`，Navigation.tsx 暂留

**选择**：新建 `src/components/Sidebar.tsx`，不复用 `Navigation.tsx` 的 JSX。

**理由**：
- `Navigation.tsx` 是顶部水平锚点条 + 玻璃拟态背景 + 固定在 viewport top；Sidebar 是垂直导航 + 固定在 viewport left，两者在布局 / 交互 / 样式上差异巨大，硬复用会让两边都不好看。
- 保留 `Navigation.tsx` 文件作为品牌站代码考古与回滚参考，回滚零成本（删掉 Sidebar import，恢复 Navigation import 即可）。

**备选**：
- 在 `Navigation.tsx` 内加 `variant="sidebar" | "top"` prop 切换。**否决**：组件单一职责原则被破坏，且 `Navigation.tsx` 当前 commit 历史属于品牌站，混在一起未来 git blame 不清晰。

### Decision 2：图表用纯手写 SVG，不引入 chart 库

**选择**：周柱状图与月折线图均用 JSX 直接渲染 `<svg>` / `<rect>` / `<polyline>` / `<circle>`。

**理由**：
- 包体积：手写 SVG 增量约 1-2 KB gzip；最小 chart 库（recharts 等）增量 50-100 KB gzip。
- 主题适配：图表颜色用 Tailwind class（`fill-accent` / `stroke-muted`）天然跟随主题切换；chart 库通常需要手动读 CSS variable，复杂度更高。
- 与 `HeroBackground.tsx` 的 Canvas 路线风格一致：项目一贯走"原生 API + 轻量手写"路线。
- 7 柱 + 1 折线是教学级图表，自定义需求高于通用需求。

**备选**：
- 引入 `recharts`：图表功能强，但 ~80 KB gzip 不必要；主题切换需 wrapper 读 CSS var。
- 引入 `visx`：headless 更轻，但仍是新依赖；本项目当前 0 测试基建，新依赖引入与维护成本不对称。
- 用纯 CSS bar chart（`<div>` + `height: %`）：实现简单但**不能做月折线图**，且主题切换需 JS 重排。否决。

### Decision 3：view 切换用 App 级 `useState`，不引入 router / hash

**选择**：`App.tsx` 持有 `const [activeView, setActiveView] = useState<'dashboard'|'goals'|'insights'|'settings'>('dashboard')`，Sidebar 通过 prop 回调 `setActiveView`，主区域根据 `activeView` 条件渲染对应组件。

**理由**：
- 与 proposal out-of-scope 一致（不引入 router）。
- 用户视角行为不变（URL 不变、刷新重置）符合 MVP 定位。
- 未来如需切换 router，只需把 `activeView` state 替换为 `useLocation()` hook + `<Routes>`，组件树形态不变。

**备选**：
- 用 URL hash（`#dashboard` / `#goals` ...）模拟路由：浏览器前进/后退可用，但与现有 `scroll-behavior: smooth` 锚点语义冲突（hash 已经被 smooth scroll 占用）。否决。
- 用 `<dialog>` 元素做侧边弹层：交互范式与 Dashboard 期望不符。否决。

### Decision 4：Sidebar 在 < 1024px 视口下折叠为汉堡菜单

**选择**：媒体查询 `< 1024px` 时，Sidebar 改为页面顶部一条横向窄条 + 汉堡按钮；点击汉堡按钮展开为右侧抽屉（fixed + 半透明 backdrop）。

**理由**：
- `< 1024px` 是常见 tablet 断点；继续坚持 240px 宽 Sidebar 会挤压主区域到 < 600px，统计卡片和趋势图体验差。
- 汉堡抽屉是 mobile-first 通用模式，预期外行为最少。
- 不需要新依赖（`<dialog>` 元素或纯 `<div>` + state 都可）。

**备选**：
- 移动端折叠为顶部图标条（始终可见）：桌面 4 项勉强能塞下，但标签文字被截断；用户必须依赖 tooltip 学习含义。否决。
- 移动端完全隐藏 Sidebar，要求用户从主区域内的 tab 切换入口操作：破坏了 Sidebar 作为"全局导航"的语义。否决。

### Decision 5：mock 数据放 `src/data/studyPal.ts`，类型命名贴近 API

**选择**：

```ts
// src/data/studyPal.ts（结构示意，非最终实现）
export interface StudyPalData {
  stats: {
    totalLearningMinutes: number;
    completedCourses: number;
    streakDays: number;
  };
  dailyGoals: Array<{
    id: string;
    title: string;
    estimatedMinutes: number;
  }>;
  aiSuggestions: Array<{
    id: string;
    title: string;
    reason: string;
    estimatedMinutes: number;
  }>;
  weeklyTrend: Array<{ date: string; minutes: number }>;
  monthlyTrend: Array<{ date: string; minutes: number }>;
}

export const studyPalData: StudyPalData = { /* mock constants */ };
```

**理由**：
- 字段名采用 camelCase，匹配未来 FastAPI Pydantic 默认序列化（`model_config = ConfigDict(alias_generators=to_camel)`）。
- 顶层 `StudyPalData` 接口作为"整页响应"对应未来 `GET /api/study-pal/snapshot` 端点。
- 组件 `import { studyPalData } from '../data/studyPal'` 与未来 `import { useStudyPal } from '../hooks/useStudyPal'` 调用形态相似，迁移摩擦最小。

**备选**：
- 把 mock 拆成 5 个独立 export（`stats` / `dailyGoals` / `aiSuggestions` / ...）：拆得更细但违反"快照式响应"语义，未来切真实数据时需要组合 5 个 fetch。否决。

### Decision 6：`HeroBackground` 作为 Dashboard 主区域的装饰背景层

**选择**：把 `<HeroBackground />` 放在 Dashboard 主区域的 `<main>` 第一层，`-z-10` 绝对定位，铺满主区域。

**理由**：
- 延续品牌站的"科技感粒子"视觉 DNA。
- `HeroBackground.tsx` 是已有可复用组件，零修改；Canvas 性能与主题适配都已经在生产验证。
- 在 Dashboard 顶部放，让用户从品牌站过渡到 StudyPal 时视觉感受延续，不会有"换了个 App"的割裂感。

**备选**：
- 不放粒子，Dashboard 用纯静态背景：视觉降级，浪费已有组件。
- 放在 Sidebar 后面：Sidebar 已经是暗色 token 主导，粒子效果会被弱化；放在主区域信息密度更高。否决。

### 组件层级图

```
+----------------------------------------------------------------------+
|                            App.tsx                                   |
|  useState<activeView> + useTheme (via ThemeToggle inside Sidebar)    |
+--------------------+-------------------------------------------------+
                     |
        +------------+------------+
        |                         |
        v                         v
+-------------------+    +------------------------------+
|    Sidebar.tsx    |    |       DashboardPage.tsx       |
|  fixed left       |    |       (view 切换容器)         |
|  - Logo / Brand   |    |  <HeroBackground />  -z-10   |
|  - NavItem*4      |    |                              |
|  - ThemeToggle    |    |  {activeView === 'dashboard' &&
|  - (mobile:汉堡) |    |       <DashboardView />}      |
|                   |    |  {activeView === 'goals'    &&
|  Props:           |    |       <GoalsView    />}      |
|   - activeView    |    |  {activeView === 'insights' &&
|   - onChangeView  |    |       <InsightsView />}      |
|                   |    |  {activeView === 'settings' &&
|                   |    |       <SettingsView />}      |
+-------------------+    +---+----------+---------+-----+
                            |          |         |
                            v          v         v
                  +-----------+  +-----------+  +----------------+
                  | Dashboard |  |   Goals   |  |   Insights     |
                  |   View    |  |   View    |  |     View       |
                  +-----+-----+  +-----+-----+  +---+-------+----+
                        |              |              |       |
              +---------+-----+        |        +-----+---+   |
              |    StatsCards |        v        | TrendChart |
              | (3 cards)     |   +-----------+ | - Weekly  |
              +----------------+   | DailyGoals| | - Monthly|
                                   | (checklist)| +-----+-----+
                                   +-----------+       |
                                                      v
                                                +-------------+
                                                | AISuggestion|
                                                | Panel       |
                                                +-------------+

[复用未改动]
  src/hooks/useTheme.ts        <-> Sidebar.tsx (ThemeToggle button)
  src/components/ThemeToggle.tsx
  src/components/HeroBackground.tsx
  src/index.css                (Tailwind v4 tokens + dark variant)

[新增]
  src/data/studyPal.ts         (mock 数据 + TypeScript 类型)
  src/components/Sidebar.tsx
  src/components/DashboardPage.tsx
  src/components/views/DashboardView.tsx
  src/components/views/GoalsView.tsx
  src/components/views/InsightsView.tsx
  src/components/views/SettingsView.tsx
  src/components/StatsCards.tsx
  src/components/DailyGoals.tsx
  src/components/AISuggestionPanel.tsx
  src/components/TrendChart.tsx

[停止引用但保留文件]
  src/components/Navigation.tsx
  src/components/Hero.tsx
  src/components/Projects.tsx
  src/components/ProjectCard.tsx
  src/components/Contact.tsx
  src/data/profile.ts
  src/data/projects.ts
```

### API 端点规范

**本变更不新增任何 API endpoint**（与 `proposal.md - Out of Scope` 一致）。所有数据由 `src/data/studyPal.ts` 内存常量提供。

**未来 API 蓝图（不在本 change 范围，仅供 mock 数据结构对齐参考）**：

| 方法 | 路径 | 描述 | 对应 mock 字段 |
|---|---|---|---|
| `GET` | `/api/study-pal/snapshot` | 拉取单页 Dashboard 全部数据快照 | `StudyPalData` 全部 |
| `PATCH` | `/api/study-pal/goals/{id}/toggle` | 切换某个目标的完成状态 | `dailyGoals[].id` |
| `POST` | `/api/study-pal/ai-suggestions/refresh` | 刷新 AI 建议（届时真正接入 LLM） | `aiSuggestions[]` |

上述端点将由后续 change（如 `add-fastapi-backend-skeleton`）定义并实现。本变更的 `StudyPalData` 接口与上述 GET 响应 schema 保持字段同名同型，确保未来切换是 `import` 路径的纯替换。

## Risks / Trade-offs

- **[Risk] 移除品牌站 `#hero` / `#projects` / `#contact` 锚点会破坏现有外链**
  → Mitigation：本变更未合入 `main`，仍在 `test-dev` 分支；`proposal.md` 已记录 BREAKING + 回滚方案；外部引用本站的页面（README 链接、社交媒体 bio 等）需要随变更同步更新。

- **[Risk] 移动端汉堡菜单是新交互，缺少现有用户行为基线**
  → Mitigation：先按 spec 落地"桌面完整 Sidebar / 移动汉堡"二态；后续根据 Lighthouse mobile usability 报告调整。

- **[Risk] 纯手写 SVG 图表在极端数据下可能溢出或重叠**
  → Mitigation：viewBox + responsive 宽度自适应；空数据走"暂无数据"占位（见 spec `Requirement: 周/月趋势图` 错误场景）；轴标签若超过 N 项降级为每 N 项一个标签。

- **[Risk] `studyPalData` 字段命名如果未来与 FastAPI 实际 schema 不一致，迁移时会批量改动**
  → Mitigation：本设计选择 camelCase + 命名贴近常见 API 约定；后续 `add-fastapi-backend-skeleton` change 必须显式声明 Pydantic → JSON 序列化规则，并写一个 schema 对齐脚本。

- **[Risk] Settings 入口点击后只显示占位文案，可能让用户误以为是 bug**
  → Mitigation：占位文案明确包含 `[Settings 占位] 此模块在后续 change 中实现`，避免歧义。

- **[Trade-off] 不引入 chart 库 = 增加约 100-150 行 SVG 手写代码**
  → 接受。理由见 Decision 2：包体积 / 主题适配 / 与项目原生路线一致性优先。

## Migration Plan

部署 / 回滚路径已在 `proposal.md - Rollback Plan` 中给出。本节补充**开发态的逐步上线节奏**：

1. **Phase 0**（基础设施准备）：见 `tasks.md - Phase 0`，仅修改 mock 数据文件 + index.html SEO meta，**不触动 UI**。这一步完成即可独立 review，确认 mock 数据结构 OK 后再进入 Phase 1。
2. **Phase 1**（Sidebar + 视图切换骨架）：App.tsx 重写顶层组合，新增 Sidebar + DashboardPage + 4 个空 view。**Dashboard 形态"通电"但内容为占位**。这一步可以单独验证响应式 + 暗色 + 主题切换的端到端链路。
3. **Phase 2**（4 个核心面板逐一落地）：每完成一个面板停一次 review（按 CLAUDE.md「分阶段交互」）。顺序建议：StatsCards → DailyGoals → AISuggestionPanel → TrendChart。
4. **Phase 3**（收尾）：清理未引用但保留的旧组件文件、压缩产物体积、补 `evidence/` 验证产物。

每 Phase 结束后走 `tasks.md` 中标注的验证步骤（`npm run build` + `npm run preview` + 浏览器肉眼检查 + `evidence/<phase>.txt` 快照）。

## Open Questions

- **Sidebar 在 ≥ 1440px 大屏下是否要扩展为"双栏 Sidebar + 子导航"**？当前设计只支持单层 4 项；如未来 Settings / Insights 下出现子菜单，Sidebar 形态可能需要重构。建议在 Phase 1 review 时再决定。
- **统计卡片的 3 项是固定还是可配置**？当前 spec 假设固定 3 项；如果后续要做"用户自定义显示哪些指标"，会触发新的 capability。当前不解决。
