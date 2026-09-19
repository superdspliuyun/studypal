# Change: study-pal

## Why

当前站点是面向"个人作品集"的品牌站（Hero / Projects / Contact 三段式），已经上线到 GitHub Pages。随着项目定位演进为"全栈 AI 学习平台"（见 `openspec/config.yaml`），需要一个能直接承载学习行为的 UI 入口。StudyPal Dashboard 是这次演进的**第一块拼图**：先把"学习者一天打开会看到什么"做到位，用 mock 数据跑通视觉与交互，等 FastAPI 后端就位后再以零成本切到真实数据。本变更不引入后端、不引入路由，**纯前端重构 + 内存 mock**，目的是把 Dashboard 这一形态从品牌站里**剥离出来**。

## What Changes

- **新增** 左侧固定 Sidebar 组件（基于现有 `Navigation.tsx` 改造，从顶部锚点条改为左侧垂直导航），包含 Dashboard / Goals / Insights / Settings 四个入口（Settings 仅占位，不实现）。
- **新增** 数据统计卡片 `StatsCards`：总学习时长、完成课程数、连续打卡天数（mock 数据）。
- **新增** 每日目标清单 `DailyGoals`：可勾选的今日学习任务列表（mock 任务，本地 useState 状态，刷新即重置）。
- **新增** AI 建议学习面板 `AISuggestionPanel`：纯静态 mock 文本，明确标注 `[AI 占位]` 字样，不调用任何模型。
- **新增** 周/月趋势图 `TrendChart`：纯 SVG 绘制 7 天柱状图 + 30 天折线图（mock 数据）。
- **新增** mock 数据层 `src/data/studyPal.ts`：类型定义 + 常量，结构贴近未来 FastAPI 响应 schema。
- **替换** `App.tsx` 顶层组合：从 `<Navigation/><Hero/><Projects/><Contact/>` 改为 `<Sidebar/><DashboardPage/>`，`DashboardPage` 内部组合上述 4 个新区件 + 一个可选的 `<HeroBackground/>` 装饰层。
- **复用保留** `useTheme` / `ThemeToggle` / `HeroBackground` / `index.css` 的 `@theme` token / 暗色机制，**零修改**。
- **移除**（功能下线，非删除文件，留作回滚参考）`Hero.tsx`、`Projects.tsx`、`ProjectCard.tsx`、`Contact.tsx`、`data/profile.ts`、`data/projects.ts` 在 App 组合里的引用。组件文件本身**暂保留**在 `src/components/` 与 `src/data/`，等回滚验证稳定后再清理。
- **更新** `index.html` 的 `<title>` / `<meta description>` / OG / Twitter card 文案为 StudyPal 定位（保留 `[Your Name]` / `[username]` 占位语法）。
- **BREAKING** 个人品牌的 `#hero` / `#projects` / `#contact` 锚点不复存在；现有外部链接（如旧 README / 引用此站点的外部页面）跳转后落空。这是预期的——新定位不再以"作品集"为入口。

## Capabilities

### New Capabilities

- `study-pal`: StudyPal Dashboard 的端到端行为契约，覆盖 Sidebar 导航、统计卡片、每日目标、AI 建议面板、周/月趋势图五个核心面板的渲染、交互、mock 数据接入与暗色适配。

### Modified Capabilities

（无。本变更不修改任何已有 capability 的需求——品牌站 capability 已被整体替换为 StudyPal，但 OpenSpec 仓库当前已清空旧 spec，不存在"被修改的现有 capability"路径。后续如有恢复品牌站的需求，应作为新 capability 处理。）

## Impact

- **受影响代码**：
  - `src/App.tsx` — 顶层组合完全重写（估计 5–10 行 → 20–30 行）。
  - `src/components/Navigation.tsx` → 改造为 `Sidebar.tsx`（保留原文件作为参考，CLS/链接语义复用）。
  - `src/components/Hero.tsx` / `Projects.tsx` / `ProjectCard.tsx` / `Contact.tsx` — 在 App 中停止引用，文件暂留。
  - `src/data/profile.ts` / `projects.ts` — 停止引用，文件暂留。
  - `src/data/studyPal.ts` — **新增**。
  - `index.html` — `<title>` / `<meta>` / OG / Twitter 文案替换为 StudyPal 定位。
- **新增依赖**：**无**。不引入 router、不引入 chart 库、不引入 fetch 客户端；图表用纯 SVG 手绘（与现有 `HeroBackground` 的 Canvas 风格保持"轻量原生"路线一致）。
- **依赖**：`react@19` / `react-dom@19` / `tailwindcss@4` 全部沿用。
- **包体积影响**：估计 +3–5 KB gzip（4 个新组件 + mock 数据 + SVG 图表代码）。当前 dist 仍 < 50 KB gzip，首屏 < 2 秒目标不受影响。
- **部署**：`npm run build` / `npm run deploy` 流程**不变**，仍然产出 `dist/` 推到 `gh-pages`。
- **SEO**：**BREAKING**。title / description / canonical / OG 全部从"个人品牌"切换到"StudyPal 学习助手"，外部分享卡片会显示新文案。
- **可访问性**：所有交互元素保持 `<nav>` / `<button>` / `aria-*` / `focus-visible` 约定；图表提供 `aria-label` 与 `<title>` 文字摘要。

### Rollback Plan（高风险变更回滚方案）

本变更属于"完整页面级重写"，归类为高风险。回滚路径：

1. **代码层**：本 change 仅在 `test-dev` 分支，未合入 `main`。回滚 = 删除 `openspec/changes/study-pal/` 目录 + revert 对 `src/` 与 `index.html` 的所有改动，恢复到 main 当前 HEAD。
2. **数据层**：本变更**无任何持久化数据**，无数据库迁移、无 localStorage 业务字段，回滚零数据成本。
3. **部署层**：GH Pages 上一个版本仍然在 `gh-pages` 分支历史中；如需立即恢复线上，可 `git checkout gh-pages && git revert <commit>` 后强制推送。
4. **验证步骤**（回滚后）：
   - `npm run build` 成功；
   - `npm run preview` 打开后能看到原 Hero / Projects / Contact；
   - Lighthouse a11y / SEO 分数 ≥ 之前的 baseline（参考 `evidence/` 目录的旧产物）。
5. **回滚 SLA**：从决策到线上恢复目标 < 30 分钟（一次 revert + 一次 gh-pages 部署）。

## Out of Scope

以下事项**显式不做**，避免 scope creep：

- **后端 API**：不创建任何 `/api/*` 端点、不引入 FastAPI、不引入 SQLite、不创建任何 Pydantic model。所有数据来自 `src/data/studyPal.ts` 内存常量。
- **AI 功能**：`AISuggestionPanel` 的内容是**硬编码的 mock 文案**，不调用任何 LLM / 第三方 AI 服务；面板内必须以 `[AI 占位]` 字样明确标识这是占位内容。
- **用户认证**：无登录态、无 session、无 token、无受保护路由、无用户菜单。Settings 入口只渲染占位文字。
- **多页面路由**：不引入 `react-router-dom` 或任何 client-side router。Sidebar 的四个入口当前**只切换 Dashboard 内的 active 高亮**，不跳转新 URL、不修改 history。
- **数据持久化**：所有交互状态（勾选目标、Sidebar 选中项）仅用 React `useState` 持有，**不写入 localStorage**；页面刷新后回到初始状态。**例外**：`useTheme` 继续按既有约定写入 localStorage（这是已有行为，不在本变更范围）。
- **国际化（i18n）**：不做。Dashboard 文案全部简体中文，硬编码在组件内，不引入 i18n 框架。
- **可访问性深度优化**：保持现有约定（`aria-label` / `focus-visible` / 键盘可达），不做 WCAG AAA 级审计或屏幕阅读器专项测试。
- **单元 / E2E 测试**：本变更不引入测试基建（`vitest` / `playwright` 等），所有验证通过 `npm run build` + `npm run preview` 手动 + 现有 `evidence/` 风格的输出快照完成。
