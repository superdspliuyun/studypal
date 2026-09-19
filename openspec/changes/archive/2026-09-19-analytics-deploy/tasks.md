# Tasks

## 1. 数据模型与迁移

- [x] 1.1 在 `backend/app/models/learning_event.py` 定义 `LearningEvent`（id / user_id FK CASCADE / kind / minutes / created_at），并在 `models/__init__.py` re-export，verify by `python -c "from app.models.learning_event import LearningEvent"` 无异常
- [x] 1.2 写 alembic 迁移 `0003_learning_event.py`：建 `learning_events` 表 + FK CASCADE + `kind` 默认值 `'chat'` + `minutes` 默认值 `0`；`downgrade()` 删除表，verify by `cd backend && alembic upgrade head && sqlite3 studypal.db ".tables" | grep learning_events`

## 2. 聚合服务

- [x] 2.1 在 `backend/app/services/analytics.py` 实现 `aggregate_calendar(db, user_id, days)`：从 `chat_messages` 计数 × 5 + `learning_events.minutes` 求和，按 UTC 日期聚合，输出长度 `days` 的数组，verify by 单测覆盖"空 / 部分 / 全部 / 跨日不重复计算"四条路径
- [x] 2.2 在 `backend/app/services/achievements.py` 定义 5 个徽章常量 `ACHIEVEMENT_DEFS`（first_lesson / streak_3 / streak_7 / total_50 / total_100），并实现 `compute_achievements(db, user_id)` 返回列表（顺序稳定），verify by 单测覆盖"零数据 / 部分解锁 / 全部解锁"三种状态
- [x] 2.3 在 `backend/app/routers/chat.py::send_message` 旁路写入 `learning_events`（kind='chat', minutes=5）—— 在 user 消息持久化后追加，verify by 单测 `test_chat_writes_learning_event` 通过

## 3. Analytics 端点

- [x] 3.1 在 `backend/app/schemas/analytics.py` 定义 `CalendarDayOut`（date / minutes）/ `CalendarOut`（数组）/ `AchievementOut`（id / title / description / unlocked / progress / target），verify by `pytest -k schemas_analytics` 通过字段校验
- [x] 3.2 在 `backend/app/routers/analytics.py` 实现 `GET /api/analytics/calendar?days`：校验 days ∈ {30, 60, 90, 180}，调 `aggregate_calendar` 返回 JSON；`GET /api/analytics/achievements`：调 `compute_achievements` 返回 JSON；强制 `get_current_user`，verify by 单测覆盖"401 / 422 非法 days / 200 默认 90 / 跨用户不可见"
- [x] 3.3 在 `app/main.py` 注册 analytics router，verify by `/openapi.json` 出现 `/api/analytics/*` 两个端点

## 4. 前端 API 与组件

- [x] 4.1 在 `src/lib/analyticsApi.ts` 新增 `getCalendar(days)` / `getAchievements()`，从 `import.meta.env.VITE_API_BASE` + localStorage token 读，统一与 chatApi 一致风格，verify by `tsc -b` 通过
- [x] 4.2 在 `src/components/HeatmapCalendar.tsx` 实现 7×ceil(N/7) SVG 网格，5 档色阶（accent opacity: 0/15/40/70/100），空数据 muted 描边；props `{ days: CalendarDayOut[] }`，verify by `tsc -b` 通过
- [x] 4.3 在 `src/components/AchievementBadge.tsx` 实现徽章卡片（unlocked 时 accent/15 + "已解锁"，未解锁时 muted + 进度条按 progress/target 比例填充 accent），verify by `tsc -b` 通过
- [x] 4.4 在 `src/components/views/AnalyticsView.tsx` 组合：顶部"连续 N 天" + HeatmapCalendar + 5 个 AchievementBadge（map 出 5 项），verify by `tsc -b` 通过

## 5. Sidebar 与视图分派

- [x] 5.1 在 `src/components/Sidebar.tsx` 把 `SidebarView` 类型改为 `'analytics' | 'chat-advice' | 'goals'`，navItems 改为这三项；ThemeToggle 仍保留在 Sidebar 顶部，verify by `npm run dev` 后 Sidebar 仅显示 3 项
- [x] 5.2 在 `DashboardPage.tsx` 的视图分派：`activeView === 'analytics' → AnalyticsView`；`'chat-advice' → ChatView`；`'goals' → GoalsView`；其他 view key 全部下线，verify by `npm run build` 仍通过

## 6. 部署文件

- [x] 6.1 在 `backend/Dockerfile` 写标准 Dockerfile（python:3.11-slim + pip install + `CMD ["sh","-c","alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]`），verify by 语法肉眼检查；本地 Docker 可选
- [x] 6.2 在 `render.yaml` 写 Blueprint：services[0].type=web, rootDir=backend, healthCheckPath=/healthz, envVars 透传 `DATABASE_URL` / `JWT_SECRET` / `DEEPSEEK_API_KEY` / `CORS_ALLOW_ORIGINS`，verify by YAML 语法解析
- [x] 6.3 在 `.github/workflows/backend-deploy.yml` 写 workflow：`on.push.paths: ['backend/**','render.yaml']`，步骤 `docker build → render deploy-hook 调用`（用 Render API key secrets），verify by YAML 语法解析

## 7. CI 与文档

- [x] 7.1 在根目录 `README.md` 增补"部署"小节：列出 Render 一键部署步骤、环境变量清单、health check URL、域名映射说明
- [x] 7.2 在既有 `.github/workflows/secret-scan.yml` 增加对 `analytics` / `achievements` 触点关键词的扫描（确保后端常量不在前端出现），verify by 本地 `grep -r "ACHIEVEMENT_DEFS" src/` 应为空

## 8. 端到端验证

- [x] 8.1 后端：`cd backend && pytest` 全绿（含 user-auth 24 + ai-chat 15 + analytics ≥ 8 tests），verify by 终端输出 `N passed, 0 failed`
- [x] 8.2 前端：`npm run build` 成功，verify by 终端 dist 大小报告（增量 < 30KB gzipped）
- [x] 8.3 手动冒烟（dev 环境）：
  1. 启动后端 `uvicorn app.main:app --reload`
  2. 启动前端 `npm run dev`
  3. 注册新账号 → 发 3 条消息 → 切到"学习数据"入口 → 应看到 heatmap 当日有色 + "连续 1 天" + first_lesson 已解锁
  4. 直接访问 `/api/analytics/achievements` 带 token → 返回 5 项
  5. `grep -r ACHIEVEMENT_DEFS src/` 无匹配
- [x] 8.4 部署冒烟（可选，需 Render 账号）：
  1. Push 到 main → workflow 自动 deploy
  2. `curl https://<service>.onrender.com/healthz` 返回 200
  3. 在前端 `VITE_API_BASE=https://<service>.onrender.com` 重新 build + deploy GitHub Pages
  4. 跨域 fetch 验证 CORS header 正确