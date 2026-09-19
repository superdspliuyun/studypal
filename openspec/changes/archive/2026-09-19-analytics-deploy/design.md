# Design

## Context

`user-auth` 与 `ai-chat` 已落地账号 + JWT + DeepSeek 流式对话 + chat_messages 持久化；本 change 在此之上叠加：

- 后端：`chat_messages` 数据已存在；新增显式 `learning_events` 表 + 聚合服务（每日分钟数 + 累计条数 + 连续天数）
- 前端：复用现有 `views/` 目录模式与 Tailwind v4 token；新增 heatmap + 徽章卡片；Sidebar 精简为 3 入口
- 部署：FastAPI 当前仅在本地 `uvicorn` 跑过；目标 Render 免费层

部署现实（沿用 user-auth / ai-chat）：GitHub Pages 仅托管静态文件；FastAPI 必须部署在 Render 等支持 Python runtime 的平台；前端通过 `VITE_API_BASE` 指向后端域名；前后端 CI 解耦。

## Goals / Non-Goals

**Goals:**
- 在 backend/ 内新增 analytics 模块，零迁移现有端点
- 前端 analytics 视图与 ChatView / GoalsView 共存；Sidebar 收敛到 3 入口
- 通过 GitHub Actions 把 backend 自动部署到 Render

**Non-Goals**（设计层面）：
- 不引入聚合缓存（Redis / 内存 LRU）
- 不引入 cron / 定时任务
- 不引入推送服务（WebSocket / SSE 推送新成就）
- 不引入多区域部署 / CDN
- 不引入 Render Postgres；先用 SQLite + Render 持久卷（成本最低）

## Decisions

### D1. 聚合数据源：`chat_messages` 计数 + `learning_events` 求和

- **选择**：在 `services/analytics.py` 用单条 SQL 同时聚合两个表（UNION ALL 或两个 subquery 后求和）；1 条用户消息 = 5 分钟常量
- **理由**：复用已有表结构，不破坏 ai-chat 契约；新增 `learning_events` 仅作为旁路写入点
- **备选**：仅用 `chat_messages`（最薄）；仅用 `learning_events`（需另写学习事件端点）

### D2. 学习事件表 schema

- **选择**：`learning_events(id, user_id FK CASCADE, kind, minutes, created_at)`，`kind` 为字符串枚举（'chat' / 'goal_completed' / 'manual'，本期实际只写 'chat'）
- **理由**：保留扩展空间；chat 端点旁路 INSERT 一行 `kind='chat' minutes=5` 即可
- **备选**：纯前端发"自定义事件"端点（本期不做）

### D3. 连续学习天数由前端计算

- **选择**：后端只返回每日 `minutes` 数组；前端从末尾向前数到第一个 0
- **理由**：定义简单、无歧义；后端无需维护"当前 streak"状态机
- **备选**：后端 SQL 计算并返回 `current_streak`（需要窗口函数）

### D4. heatmap 渲染：纯 SVG 7×N 网格

- **选择**：纯 SVG 矩形，无第三方库；5 档色阶使用 Tailwind v4 token `accent` 的不同 opacity
- **理由**：零依赖；色阶与现有暗色/亮色主题自动适配
- **备选**：`react-calendar-heatmap`（多 30KB 依赖）；`d3`（杀鸡用牛刀）

### D5. 成就引擎：纯函数 + 实时计算

- **选择**：`services/achievements.py::compute_achievements(user_id, db)` 返回 5 项徽章 dict；不缓存
- **理由**：SQLite 单文件足够快；用户量小；spec 明确要求实时
- **备选**：维护 `user_achievements` 表（写入慢、需一致性维护）

### D6. Sidebar 收敛到 3 入口

- **选择**：Dashboard / Insights / AI 助手 / Settings 在 Sidebar 不再作为可点击入口；ThemeToggle 保留；点击谁触发哪个 view 由 DashboardPage 内 `switch` 决定
- **理由**：用户明确要求；本期 UI 精简
- **备选**：保留 5 入口（拒绝用户要求）；子菜单折叠（UI 更复杂）

### D7. 部署目标：Render Web Service

- **选择**：Render 免费层（postgres-free、cron-free 即可）+ Docker 镜像；`render.yaml` Blueprint 一键部署
- **理由**：用户约束要求 GitHub 体系；Render 是 GitHub Actions 集成最成熟的免费 PaaS
- **备选**：Fly.io（需要 flyctl + fly.toml）；Railway（API 简单但 GitHub Action 集成较弱）；自建 VPS（运维成本高）

### D8. Dockerfile 基础镜像

- **选择**：`python:3.11-slim`，`pip install --no-cache-dir -r requirements.txt`
- **理由**：与本地 dev Python 版本一致；slim 镜像 ~150MB
- **备选**：`python:3.11-alpine`（更小但 bcrypt wheel 兼容差）

### D9. CI 解耦：paths 过滤器

- **选择**：`backend-deploy.yml` `on.push.paths: backend/** + render.yaml`；既有 `secret-scan.yml` 继续监听 PR
- **理由**：前端 commit 不触发后端部署；后端 commit 不触发前端 deploy
- **备选**：单一 workflow + `if: contains(...)`（复杂且易错）

### D10. 数据库持久化：Render 持久卷（免费 1GB）

- **选择**：`studypal.db` 写到 `/var/data/studypal.db`，Render 持久卷挂载到 `/var/data`
- **理由**：免费层够用；零外部依赖；alembic upgrade head 在容器启动时跑
- **备选**：Render Postgres（最低 $7/月，免费层无）；外部 SQLite 托管（Turso）

### D11. CORS 自动注入前端域名

- **选择**：在 Render env 配 `CORS_ALLOW_ORIGINS=https://<user>.github.io,http://localhost:5173`
- **理由**：dev + prod 都覆盖
- **备选**：代码写死 GitHub Pages 域名（不灵活）

### D12. 后端目录增量

```
backend/app/
├── models/learning_event.py    # LearningEvent ORM
├── schemas/analytics.py        # CalendarOut / CalendarDayOut / AchievementOut
├── services/
│   ├── analytics.py            # GROUP BY 聚合
│   └── achievements.py         # 5 徽章定义 + compute
└── routers/analytics.py        # GET /api/analytics/{calendar,achievements}
backend/alembic/versions/0003_learning_event.py
backend/tests/test_analytics.py
backend/Dockerfile             # 🆕
render.yaml                    # 🆕
.github/workflows/backend-deploy.yml  # 🆕
```

```
frontend src/
├── components/
│   ├── HeatmapCalendar.tsx
│   ├── AchievementBadge.tsx
│   └── Sidebar.tsx             # 改：3 入口
├── components/views/
│   ├── AnalyticsView.tsx       # 🆕
│   ├── ChatView.tsx            # 改：view key 从 'ai' 改为 'chat-advice'
│   ├── GoalsView.tsx           # 不动
│   └── DashboardPage.tsx       # 改：视图分派
└── lib/analyticsApi.ts         # 🆕
```

## 组件层级图

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (React 19 + Vite, GitHub Pages)               │
│  ┌──────────────────────────────────────────────────┐   │
│  │ App.tsx                                           │   │
│  │   └── Sidebar (3 entries: 学习数据/AI对话建议/学习目标)│  │
│  │   └── DashboardPage → views:                      │   │
│  │         ├── AnalyticsView (新)                    │   │
│  │         │   ├── HeatmapCalendar (SVG)             │   │
│  │         │   └── AchievementBadge × 5              │   │
│  │         ├── ChatView (复用 ai-chat)               │   │
│  │         └── GoalsView (复用 study-pal)            │   │
│  └──────────────────────────────────────────────────┘   │
│                │ Bearer access_token + VITE_API_BASE    │
└─────────────────────────────────────────────────────────┘
                          │ HTTPS
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Render Web Service (Docker: python:3.11-slim)         │
│  ┌──────────────────────────────────────────────────┐   │
│  │ FastAPI app  (uvicorn 0.0.0.0:$PORT)             │   │
│  │   ├── routers/auth.py        (user-auth)          │   │
│  │   ├── routers/profile.py     (user-profile)       │   │
│  │   ├── routers/chat.py        (ai-chat)            │   │
│  │   └── routers/analytics.py 🆕                     │   │
│  │        ├── GET  /api/analytics/calendar           │   │
│  │        └── GET  /api/analytics/achievements       │   │
│  │ services/analytics.py     → GROUP BY date         │   │
│  │ services/achievements.py   → 5 徽章定义            │   │
│  └──────────────────────────────────────────────────┘   │
│  deps.get_current_user (复用 user-auth)                  │
└─────────────────────────────────────────────────────────┘
                          │  SQLAlchemy 2.x
                          ▼
┌─────────────────────────────────────────────────────────┐
│  SQLite (/var/data/studypal.db, 持久卷)                  │
│    users / user_profiles / chat_sessions / chat_messages│
│    + learning_events 🆕 (id, user_id FK, kind, minutes, │
│                          created_at)                    │
│  Alembic: 0001 + 0002 + 0003_learning_event             │
└─────────────────────────────────────────────────────────┘
```

## API 端点规范

### GET `/api/analytics/calendar`

Query：`days` ∈ {30, 60, 90, 180}，默认 90
响应 200：
```json
[
  { "date": "2026-06-20", "minutes": 0 },
  { "date": "2026-06-21", "minutes": 15 },
  ...
  { "date": "2026-09-18", "minutes": 25 }
]
```
错误：401 / 422（非法 days）。

### GET `/api/analytics/achievements`

响应 200：
```json
[
  { "id": "first_lesson", "title": "初次启航", "description": "发出第一条消息",
    "unlocked": true, "progress": 1, "target": 1 },
  { "id": "streak_3", "title": "三日连击", "description": "连续学习 3 天",
    "unlocked": false, "progress": 1, "target": 3 },
  { "id": "streak_7", "title": "七日打卡", "description": "连续学习 7 天",
    "unlocked": false, "progress": 1, "target": 7 },
  { "id": "total_50", "title": "五十答问", "description": "累计 50 条消息",
    "unlocked": false, "progress": 27, "target": 50 },
  { "id": "total_100", "title": "百答大成", "description": "累计 100 条消息",
    "unlocked": false, "progress": 27, "target": 100 }
]
```
错误：401。

## Risks / Trade-offs

- **[Risk] Render 免费层冷启动慢** → Mitigation：spec 仅要求 `/healthz` 200；冷启动不阻塞首次注册（user-auth 的 422 走预先 fail-fast）
- **[Risk] SQLite 单文件数据量增长** → Mitigation：学习事件保留 90 天足够；chat_messages 长期保留；alembic 可在后续 change 添加归档
- **[Risk] Render 持久卷快照策略** → Mitigation：本期每周手工 pg_dump；自动化 backup 留待后续 change
- **[Risk] Sidebar 减少入口导致旧用户找不到 Dashboard / Settings** → Mitigation：README 增补 changelog；ThemeToggle 仍可在 Sidebar 顶部访问
- **[Trade-off] 不引入聚合缓存** → 优点：实现最薄；缺点：每次请求 O(N) SQL。本期用户量 < 1k，p95 < 200ms 可控
- **[Trade-off] Sidebar 仅 3 入口** → 优点：UI 聚焦；缺点：Insights 视图下线（其 mock 数据本就用不到）

## Migration Plan

- **首次部署**：
  1. Render 控制台导入 `render.yaml`，创建 web service
  2. 在 Render dashboard 配置 secrets：`DATABASE_URL`（`/var/data/studypal.db` 持久卷）、`JWT_SECRET`、`DEEPSEEK_API_KEY`、`CORS_ALLOW_ORIGINS`
  3. Render deploy：build image → alembic upgrade head → uvicorn
  4. 验证：`curl https://<service>.onrender.com/healthz` 返回 200
- **回滚**：
  - 数据库：`alembic downgrade -1` 回退 0003_learning_event
  - 代码：删除新增 analytics 模块 / 前端 AnalyticsView 与 Sidebar 收敛
  - 部署：Render 控制台 destroy service
  - 与 user-auth / ai-chat 同款"删除文件即可"零侵入式回滚

## Open Questions

- （无）所有会影响 spec 的取舍已在 Decisions 中给出；Sidebar 旧入口的下线由用户在 change 描述中明确，无歧义。