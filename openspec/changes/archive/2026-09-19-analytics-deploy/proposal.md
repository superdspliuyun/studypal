# Proposal

## Why

StudyPal 已有账号体系（user-auth）与 AI 对话能力（ai-chat），但用户看不到自己的学习"轨迹"——既没有可视化日历也没有成长反馈；同时整套后端仅在本地跑过，从未真正上线。本 change 一举补齐两个最缺的能力：(1) 让用户感知到"我每天都在学"——通过学习日历 heatmap 与成就徽章；(2) 把后端真正部署到公网，让 GitHub Pages 前端能与 FastAPI 后端联调。两件事合并在同一个 change 是因为它们都需要一次"小里程碑"发布，且都依赖已有 backend/ 工程，合并提交降低发布风险。

## What Changes

- 后端新增 `app/services/analytics.py`：基于 SQLAlchemy 在 `chat_messages`（已归档的 ai-chat change 产物）上做时间窗口聚合，输出"每日学习分钟数"序列
- 后端新增 `app/services/achievements.py`：基于上述聚合实时计算徽章解锁状态（首课 / 连续 3 天 / 连续 7 天 / 累计 50 条消息 / 累计 100 条消息）
- 后端新增 `app/routers/analytics.py`，端点：
  - `GET /api/analytics/calendar?days=90` —— 返回近 N 天每日学习分钟数数组
  - `GET /api/analytics/achievements` —— 返回徽章列表，每项含 `id` / `title` / `description` / `unlocked` / `progress` / `target`
- 后端新增 `alembic/versions/0003_learning_event.py` —— 显式 `learning_events` 表（user_id FK CASCADE / kind / minutes / created_at），让用户行为不局限于 chat 消息也能被记录；本周可在 chat 端点旁路写入
- 前端新增 `src/components/HeatmapCalendar.tsx`：纯 SVG 7×N 网格热力图，按分钟数取色阶（accent token，5 档）
- 前端新增 `src/components/AchievementBadge.tsx`：徽章卡片，未解锁时 muted 灰 + 进度条
- 前端新增 `src/components/views/AnalyticsView.tsx`：组合 HeatmapCalendar + AchievementBadge 列表
- 前端把 Sidebar 改为 3 入口：学习数据 / AI 对话建议 / 学习目标；Dashboard / Insights / AI 助手 / Settings 入口下线（ThemeToggle 仍保留）
- 部署上线：
  - 新增 `backend/Dockerfile`（python:3.11-slim + uvicorn 标准启动）
  - 新增 `render.yaml`（声明 web service，env 透传 `DATABASE_URL` / `JWT_SECRET` / `DEEPSEEK_API_KEY` / `CORS_ALLOW_ORIGINS`）
  - 新增 `.github/workflows/backend-deploy.yml`：监听 `backend/**` 变更，构建 Docker 镜像并 deploy 到 Render
  - 既有 `.github/workflows/secret-scan.yml` 继续生效
- README 增补"部署"小节：Render 一键部署、环境变量清单、健康检查 URL

## Capabilities

### New Capabilities

- `learning-calendar`: 学习日历（heatmap）—— 后端聚合 `chat_messages` + `learning_events` 出每日分钟数；前端 SVG 热力图渲染；连续学习天数为衍生指标
- `achievements`: 成就系统 —— 5 个预定义徽章（首课 / 连 3 天 / 连 7 天 / 累计 50 条 / 累计 100 条），基于聚合实时判定；徽章卡片 + 进度条
- `app-deploy`: 后端部署到 Render —— `Dockerfile` / `render.yaml` / GitHub Actions 自动部署 workflow；前端继续走 GitHub Pages

### Modified Capabilities

- （无）现有 `study-pal` / `user-auth` / `user-profile` / `ai-chat` / `chat-storage` 规范的 REQUIREMENTS 保持不变——Sidebar 减少入口属于 UI 结构调整，不在已有 capability 的 REQUIREMENTS 覆盖范围

## Impact

- **新增后端代码**：`backend/app/services/analytics.py`、`backend/app/services/achievements.py`、`backend/app/routers/analytics.py`、`backend/app/models/learning_event.py`、`backend/app/schemas/analytics.py`、alembic `0003_learning_event.py`、测试 `tests/test_analytics.py`
- **新增前端代码**：`src/components/HeatmapCalendar.tsx`、`src/components/AchievementBadge.tsx`、`src/components/views/AnalyticsView.tsx`、修改 `src/components/Sidebar.tsx`、修改 `src/components/DashboardPage.tsx`、可能新增 `src/lib/analyticsApi.ts`
- **新增部署文件**：`backend/Dockerfile`、`render.yaml`、`.github/workflows/backend-deploy.yml`
- **新增文档**：根目录 `README.md` 增补"部署"小节
- **后端依赖**：沿用 `sqlalchemy`、`pydantic`；新增 `python-dateutil`（如需复杂日期窗口；否则用 stdlib `datetime`）
- **前端依赖**：零新增（纯 SVG，无第三方图表库）
- **新增环境变量**（后端生产）：`PORT`（Render 注入）/ `DATABASE_URL`（Render Postgres 或带持久卷的 SQLite）/ `JWT_SECRET` / `DEEPSEEK_API_KEY` / `CORS_ALLOW_ORIGINS`
- **现有行为**：StudyPal 旧 Dashboard 子视图（Dashboard / Insights / AI 助手 / Settings）在 Sidebar 不再直接出现；ThemeToggle 保留可访问
- **数据流**：客户端 → Bearer token → `/api/analytics/*` → SQLite 聚合查询 → JSON 返回
- **部署影响**：前端 `npm run build` / `npm run deploy` 不变；新增 Render 服务独立部署；CI 解耦

### Out of Scope（明确不做）

- **实时通知**：本 change 不引入 WebSocket 推送；用户刷新页面即看到最新数据
- **数据导出**：不提供 CSV / JSON 下载接口；spec 不承诺
- **后台管理**：无运营面板、无审计
- **模型切换**：仅 DeepSeek
- **OAuth / 第三方登录**
- **多端同步冲突解决**
- **手动学习事件写入端点**：仅 chat_messages 与后端内部旁路写入；用户不直接 POST learning_events
- **服务端聚合缓存**：每次请求都重新 GROUP BY（用户量小，无需缓存层；未来 change 再评估）
- **i18n / 时区适配**：所有时间窗口按 UTC 处理；前端 heatmap 标签用中文

### 回滚方案（高风险变更）

- **回滚后端代码** = `git revert` 本 change 的 backend/ 增量；alembic `downgrade -1` 回退 0003_learning_event；前端 Sidebar 改回原 5 入口
- **回滚部署** = Render 控制台 destroy service；删除 Render Postgres（如有）；CI workflow 文件删除
- **失败模式 1：Render 部署失败** → workflow 立即 fail，不影响前端；本地 `uvicorn` 继续可用
- **失败模式 2：聚合查询慢** → SQLite 单文件数据量小（< 10MB 用户级别），GROUP BY 索引已建；p95 200ms 目标可控
- **失败模式 3：DEEPSEEK_API_KEY 泄漏** → 沿用 `user-auth` change 的 secret-scan workflow；后端 secret 必须由 Render env 注入；前端代码 + dist 不得含字面量