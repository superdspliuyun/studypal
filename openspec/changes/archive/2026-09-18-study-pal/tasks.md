# Tasks: study-pal

> 实施纪律（来自 CLAUDE.md `## OpenSpec 协作规则 → 分阶段交互`）：
> 每完成一个 Phase **必须停下来**，总结变更、改动文件、新增组件，等用户 review 后再开始下一 Phase。
> Phase 内的子任务可连续推进，但跨 Phase 必停。

---

## Phase 0 — 基础设施准备（mock 数据 + SEO meta）

> 本 Phase 不触动 UI，仅落数据层与 SEO 文档。完成后即可单独 review 数据结构是否合适，再进入 Phase 1。

- [x] 0.1 新建 `src/data/studyPal.ts`，导出 `StudyPalData` 接口（5 字段：`stats` / `dailyGoals` / `aiSuggestions` / `weeklyTrend` / `monthlyTrend`，全部 camelCase）与 `studyPalData` 常量（含合理 mock 数值，至少 3 张卡片 / 3 个目标 / 3 条 AI 建议 / 7 天 / 30 天趋势点）；验证：`npx tsc -b` 通过 + 在任一组件临时 `import { studyPalData }` 后 console.log 输出无 undefined
- [x] 0.2 更新 `index.html` 的 `<title>` / `<meta name="description">` / canonical / OG / Twitter card 文案为 StudyPal 定位（占位符 `[Your Name]` / `[username]` 语法保留）；验证：`npm run build` 通过 + `npm run preview` 后浏览器 DevTools 抓 `<head>` 看到新文案

### Phase 0 验证

- [x] 0.V `npm run build` 通过；浏览器打开本地预览，`index.html` 页面 head 区域 SEO 文案显示新 StudyPal 文案；`src/data/studyPal.ts` 在 TypeScript 严格模式下无报错；产出 `evidence/study-pal-phase-0.txt` 记录（1）mock 数据 5 个字段示例值，（2）build 产物大小，（3）`<head>` 关键 meta 内容

---

## Phase 1 — Sidebar + 视图切换骨架

> 本 Phase 完成后 Dashboard 形态"通电"——Sidebar + 4 个空 view + 主题切换 + 响应式布局全部到位，但每个 view 只有标题占位。

- [x] 1.1 新建 `src/components/Sidebar.tsx`：桌面端 (≥ 1024px) 渲染宽度 240px 的 fixed left 垂直导航栏，包含 Brand 名 + 4 个 NavItem（Dashboard / Goals / Insights / Settings）+ ThemeToggle；移动端 (< 1024px) 折叠为顶部一条 56px 横向窄条 + 汉堡按钮，点击展开为 fixed right 抽屉（带 backdrop 点击关闭）；所有颜色走 Tailwind token（`bg-background` / `text-foreground` / `border-border` / `hover:text-accent`），零内联 style；Props 接 `activeView` 与 `onChangeView`；验证：浏览器桌面 1280px / 平板 800px / 手机 375px 三档视口肉眼检查 Sidebar 形态正确 + 点击 NavItem 触发 `onChangeView` 回调
- [x] 1.2 新建 `src/components/views/{DashboardView,GoalsView,InsightsView,SettingsView}.tsx` 四个文件，每个 view 渲染一个 `<section>` + `<h2>` 标题占位 + 一句话说明当前阶段（例如 GoalsView：`"每日目标（待 Phase 2.2 落地）"`）；验证：分别打开每个文件肉眼看到对应文案
- [x] 1.3 新建 `src/components/DashboardPage.tsx`，持 `useState<'dashboard'|'goals'|'insights'|'settings'>('dashboard')` + 顶部标题区根据 activeView 切换 + 主区域条件渲染 4 个 view + 在主区域最底层放 `<HeroBackground />`（`absolute inset-0 -z-10`）；Props 接 `onChangeView` 回调转给 Sidebar；验证：父组件传入 `onChangeView` 后 Sidebar 点击能切换 view + 标题区同步更新
- [x] 1.4 重写 `src/App.tsx`：把 `<Navigation/><Hero/><Projects/><Contact/>` 替换为 `<Sidebar activeView={...} onChangeView={...} /><DashboardPage onChangeView={...} />`，view state 提升到 App 层；旧组件 `Navigation/Hero/Projects/ProjectCard/Contact` 与 `data/profile.ts`、`data/projects.ts` **暂保留**但停止引用；验证：`npm run build` 通过 + `npm run preview` 后浏览器看到左侧 Sidebar + 右侧主区域 + 4 个 view 可切换 + 主题切换正常
- [x] 1.5 检查 `index.html` 的 `scroll-behavior: smooth` 是否会与 Phase 2 之后的内部 view 切换冲突（如果 view 切换通过 DOM 显示/隐藏，不影响 scroll 行为；记录当前行为即可）；验证：浏览器手动测试 Sidebar 切换 view 时页面是否平滑滚动（不应该）

### Phase 1 验证

- [x] 1.V `npm run build` 通过；`npm run preview` 启动后：
  - 桌面 1280px：Sidebar 完整可见，4 个 NavItem 切换流畅，标题区同步；
  - 平板 800px：Sidebar 折叠为顶部窄条 + 汉堡按钮；
  - 手机 375px：汉堡按钮可点开抽屉 + backdrop 关闭；
  - 主题切换：明亮/暗黑双态均正常，`<html class="dark">` 切换后 Sidebar 颜色全部跟随；
  - 旧 `Navigation.tsx` 等文件未被任何 `import` 引用（grep 验证）；
  产出 `evidence/study-pal-phase-1.txt` 快照（每个验证点的截图或文字描述）

---

## Phase 2 — 4 个核心面板实现

> 本 Phase 拆分 4 个子阶段，每完成一个核心面板停一次 review（符合 CLAUDE.md「分阶段交互」）。每个子阶段都验证完再进下一个。

### Phase 2.1 — StatsCards

- [x] 2.1.1 新建 `src/components/StatsCards.tsx`，从 `studyPalData.stats` 读 3 个字段，渲染 3 张并排卡片（grid 1→3 cols），每张卡片：上半 icon 占位 + 下半数值 + 中文标签；token 走 `bg-background` / `border-border` / `text-foreground` / `text-muted`；Props 接 `stats: StudyPalData['stats']`；验证：Dashboard 视图渲染 3 张卡 + 数值可见
- [x] 2.1.2 在 StatsCards 内部处理学习时长格式化（`≥ 60` 显示 `X 小时`，`< 60` 显示 `X 分钟`），用 `Intl.NumberFormat` 或手写 `Math.floor`；验证：手动修改 `studyPalData.stats.totalLearningMinutes` 分别为 30 / 90 / 0 三档，`npm run preview` 后浏览器卡片显示对应单位
- [x] 2.1.3 处理 mock 数据缺失降级：当 `stats` 为 `{}` 或任一字段为 `undefined` 时，该卡片显示 `[数据待接入]` 文本，**不抛错**；验证：临时把 `studyPalData.stats` 改成 `{}`，浏览器控制台无报错 + 卡片显示占位

### Phase 2.2 — DailyGoals

- [x] 2.2.1 新建 `src/components/DailyGoals.tsx`，从 `studyPalData.dailyGoals` 读数组，渲染 `<ul>` 列表，每项：复选框 + 标题 + 预计分钟数；Props 接 `goals: StudyPalData['dailyGoals']`；验证：Goals 视图渲染列表 + 复选框可点击（视觉态变化）
- [x] 2.2.2 在 GoalsView 内部用 `useState<Set<string>>` 持有已勾选 id，点击复选框 toggle，标题加删除线样式（`line-through text-muted`）+ 顶部计数器显示 `已完成 X/Y`；状态**不写 localStorage**，刷新即重置；验证：勾选/取消 3 个任务 + 计数器正确同步 + 刷新页面后回到未勾选
- [x] 2.2.3 处理空清单兜底：`dailyGoals.length === 0` 时显示 `今日暂无目标`；验证：临时把 `studyPalData.dailyGoals` 设为 `[]`，浏览器显示占位文案且无空 `<ul>` 渲染

### Phase 2.3 — AISuggestionPanel

- [x] 2.3.1 新建 `src/components/AISuggestionPanel.tsx`，从 `studyPalData.aiSuggestions` 读数组，渲染建议卡片列表 + 顶部固定一行 `[AI 占位]` 字样（半透明小标签）；每条卡片含 `title` / `reason` / `estimatedMinutes` 三字段；Props 接 `suggestions: StudyPalData['aiSuggestions']`；验证：Insights 视图渲染至少 2 条建议 + 顶部占位标签可见
- [x] 2.3.2 处理空数据降级：`suggestions.length === 0` 时显示 `[AI 占位] 暂无建议`；验证：临时把 `studyPalData.aiSuggestions` 设为 `[]`，浏览器显示占位文案

### Phase 2.4 — TrendChart

- [x] 2.4.1 在 `src/components/TrendChart.tsx` 内实现**周视图**（weekly）：从 `studyPalData.weeklyTrend` 读 7 个点，渲染 `<svg viewBox="0 0 280 100">` + 7 个 `<rect>` 柱（每个柱宽 28px、间隔 12px、Y 高度按 `minutes / maxMinutes * 80` 计算）；柱颜色 `fill-accent`，背景网格线 `stroke-muted/30`；Props 接 `weekly: StudyPalData['weeklyTrend']`；验证：Insights 视图渲染 7 个矩形柱 + Y 轴高度比例合理
- [x] 2.4.2 在 TrendChart 内追加**月视图**（monthly）：从 `studyPalData.monthlyTrend` 读 30 个点，渲染 `<svg viewBox="0 0 600 120">` + `<polyline>`（点连成线）+ `<circle>` 数据点；折线 `stroke-accent`，数据点 `fill-accent`，下方半透明 `fill-accent/20` 做面积视觉（可选）；Props 接 `monthly: StudyPalData['monthlyTrend']`；验证：浏览器显示连续折线 + 数据点可见
- [x] 2.4.3 验证主题切换：点击 ThemeToggle 在明/暗之间切换，图表颜色（柱 / 折线 / 数据点）应在 ≤ 1 秒内跟随；验证：手动点击 ThemeToggle 5 次，浏览器肉眼检查每次切换图表颜色都更新
- [x] 2.4.4 处理空数据兜底：weekly 或 monthly 任一为空数组时，对应 SVG 区域显示 `暂无数据` 文本（绝对定位在 svg 中央），不渲染空 svg；验证：分别清空两个数组 + 浏览器显示对应占位

### Phase 2 验证

- [x] 2.V 4 个核心面板全部完成 + `npm run build` 通过；浏览器 `npm run preview` 启动，逐项勾选 `specs/study-pal/spec.md` 中的所有 `#### Scenario`（含错误场景），全部通过；产出 `evidence/study-pal-phase-2.txt` 快照（含每个场景的实测结果）

---

## Phase 3 — 收尾

- [x] 3.1 删除停止引用的旧组件文件：`src/components/{Navigation,Hero,Projects,ProjectCard,Contact}.tsx` 与 `src/data/{profile,projects}.ts`（grep 整个 src/ 确认无 import 后删除）；验证：`grep -r "from '../components/Navigation\|from '../components/Hero\|from '../data/profile\|from '../data/projects'" src/` 返回空 + `npm run build` 通过
- [x] 3.2 比较新旧 dist 体积：`npm run build` 后 `du -sh dist/assets/*.js`（或 `ls -la dist/assets/`）记录 JS 总大小；与 baseline（commit `08eae2d` 的 dist 大小，参考 `evidence/build-01-output.txt`）对比，**增量应 ≤ 5KB gzip**；验证：产出对比表写入 `evidence/study-pal-dist-size.txt`
- [x] 3.3 运行 `npm run lint`（oxlint）确认新增文件无 lint error；验证：lint 输出 exit code 0

### Phase 3 验证（终态）

- [x] 3.V `npm run build` 通过 + `npm run preview` 启动 + 浏览器完整跑一遍：
  - 桌面 1280px：Sidebar / StatsCards / DailyGoals / AISuggestion / TrendChart 全部渲染正常；
  - 主题切换：明/暗双态正常；
  - 响应式：手机 375px 汉堡菜单正常；
  - 5 个 spec Requirements 全部场景（含错误场景）勾选通过；
  产出 `evidence/study-pal-phase-3.txt` 终态快照（含 dist 大小对比、lint 结果、所有 spec 场景勾选表）

---

## 跨 Phase 总览

| Phase | 主要产出 | 验证产物 | 预计工作量 |
|---|---|---|---|
| 0 | `src/data/studyPal.ts` + `index.html` SEO | `evidence/study-pal-phase-0.txt` | ~30 min |
| 1 | Sidebar + DashboardPage + 4 空 view | `evidence/study-pal-phase-1.txt` | ~2 h |
| 2.1 | StatsCards | （在 2.V 合并） | ~1 h |
| 2.2 | DailyGoals | （在 2.V 合并） | ~1 h |
| 2.3 | AISuggestionPanel | （在 2.V 合并） | ~30 min |
| 2.4 | TrendChart（SVG） | （在 2.V 合并） | ~2 h |
| 3 | 清理旧文件 + 体积对比 + lint | `evidence/study-pal-phase-3.txt` | ~30 min |

合计：~7-8 小时（按单个 task ≤ 2 h 约束切分）

---

## 复用检查清单（每个新建组件开工前先确认）

新建下列组件前，**先 grep 确认无重复实现**：

- [x] Sidebar.tsx：确认 `Navigation.tsx` 没有可改造复用的部分（已确认：差异大，新建）
- [x] StatsCards.tsx：确认无现有"指标卡片"组件（grep `Card\|Stats\|Metric`）
- [x] DailyGoals.tsx：确认无现有"列表 + 复选框"组件（grep `Checkbox\|List\|Goal`）
- [x] AISuggestionPanel.tsx：确认无现有"建议 / 提示"组件（grep `Suggestion\|Hint\|Tip`）
- [x] TrendChart.tsx：确认无现有图表组件（grep `Chart\|Graph\|svg`）

每个新建组件开工前，对照 `src/components/` 与 `src/hooks/` 跑一次 `grep`，零命中再开始。
