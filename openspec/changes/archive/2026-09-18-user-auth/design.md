# Design

## Context

StudyPal 已上线的前端品牌站与 mock Dashboard 不依赖任何后端；当前仓库仅包含前端 `src/`、`index.html`、GitHub Pages 部署流水线（详见 proposal.md — Why）。本 change 引入**首个**后端工程 `backend/`（FastAPI + SQLite + Alembic），提供账号基础设施。本次变更**仅新增后端代码**，不修改前端构建产物、不耦合到现有任何 React 组件；前端通过未来的 change 消费 `VITE_API_BASE` 接入。

部署现实约束：GitHub Pages 不能运行 FastAPI，后端须部署到 Render / Fly.io / Railway / Cloud Run 等支持 Python runtime 的平台；前后端 CI 解耦，后端构建不影响 `npm run build` / `npm run deploy`。

## Goals / Non-Goals

**Goals:**
- 在 `backend/` 内落地 FastAPI 应用骨架、SQLAlchemy 模型、Alembic 迁移、端点实现、测试
- 提供与 `specs/user-auth/spec.md` 与 `specs/user-profile/spec.md` 一一对应的实现行为
- 通过环境变量注入敏感配置（`JWT_SECRET` 等），开发态提供 `.env.example`
- 提供本地一键启动 + 测试命令（`uvicorn` 与 `pytest`）

**Non-Goals**（设计层面，仅补充 proposal.md 未涉及的边界）:
- 不引入消息总线、不引入后台任务队列
- 不引入 Redis；refresh token 不维护服务端黑名单
- 不引入 OAuth provider SDK、不引入社交登录 redirect 端点
- 不引入 admin 路由（与 proposal.md 一致）

## Decisions

### D1. 单体 FastAPI + 单进程 uvicorn

- **选择**：FastAPI 单体应用 + uvicorn 单 worker。
- **理由**：本期用户量与端点数量都极小；引入 ASGI 多 worker 或独立 worker 队列会过早复杂化。
- **备选**：Starlette + 手写中间件、Litestar、Django REST Framework —— 均更重或更适合已有 Django 生态；与"最薄身份层"目标不符。

### D2. SQLAlchemy 2.x 同步 ORM（不用 async）

- **选择**：SQLAlchemy 2.x 同步 API + sync session。
- **理由**：SQLite 同步性能足以覆盖本期并发量；同步代码更易调试与测试；FastAPI 在 sync 路由里通过线程池执行，不会阻塞事件循环。
- **备选**：SQLAlchemy Async + aiosqlite —— 复杂度更高，收益在 SQLite 单文件场景下不显著。

### D3. Alembic 维护 schema

- **选择**：Alembic 迁移随代码入仓；初始迁移 `0001_initial.py` 同时建 `users` 与 `user_profiles` 两表。
- **理由**：schema 演进留痕；CI 与生产部署走 `alembic upgrade head`。
- **备选**：手动 `Base.metadata.create_all()` —— 不留版本痕迹，无法回滚。

### D4. JWT 库与算法

- **选择**：`python-jose[cryptography]` 签发/校验 JWT，HS256 对称算法。
- **理由**：与 FastAPI 生态文档一致；HS256 在单服务部署下足够；密钥单一来源注入环境变量即可。
- **备选**：`PyJWT`（API 类似，无明显优劣）；RS256（多服务时更合适，本期不需要）。

### D5. 密码哈希：passlib + bcrypt

- **选择**：`passlib[bcrypt]`（内部走 bcrypt，cost factor 默认 12）。
- **理由**：passlib 自动处理 salt 与算法版本前缀（`$2b$...`），便于未来 cost factor 升级。
- **备选**：argon2（更现代但增加 wheel 兼容复杂度）；hashlib 自实现（绝对禁止，spec 已禁止）。

### D6. Pydantic v2 schema

- **选择**：Pydantic v2 作为请求/响应模型与配置（`pydantic-settings`）来源。
- **理由**：FastAPI 原生支持；v2 性能更高、API 更稳。
- **备选**：marshmallow / dataclasses + 手写校验 —— 与 FastAPI 解耦更弱。

### D7. CORS 允许列表走环境变量

- **选择**：`CORS_ALLOW_ORIGINS`（CSV），默认开发态包含 `http://localhost:5173`（前端 Vite dev server）。
- **理由**：用户约束要求前后端在同一仓库内开发；生产态由部署平台注入 GitHub Pages 域名。

### D8. 后端目录布局

```
backend/
├── app/
│   ├── main.py                # FastAPI 实例 + 路由挂载 + CORS
│   ├── config.py              # pydantic-settings 读 env
│   ├── db.py                  # SQLAlchemy engine / SessionLocal / Base
│   ├── deps.py                # get_db, get_current_user
│   ├── security.py            # JWT 签发 / 校验 / 密码哈希
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py            # SQLAlchemy User
│   │   └── profile.py         # SQLAlchemy UserProfile
│   ├── schemas/
│   │   ├── auth.py            # RegisterIn / LoginIn / TokenPair / RefreshIn
│   │   └── profile.py         # ProfileOut / ProfileUpdate
│   └── routers/
│       ├── auth.py            # /api/auth/*
│       └── profile.py         # /api/users/me
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial.py
├── tests/
│   ├── conftest.py            # 内存 SQLite + 依赖覆盖
│   ├── test_auth.py
│   └── test_profile.py
├── alembic.ini
├── pyproject.toml
├── requirements.txt
├── .env.example
└── README.md
```

**理由**：每个模块单一职责；`routers/` 与 `schemas/` 拆分便于测试；alembic 走标准目录。

### D9. 测试栈：pytest + httpx ASGITransport

- **选择**：pytest + httpx.AsyncClient + FastAPI ASGITransport；测试库用内存 SQLite（`sqlite:///:memory:`）+ dependency override。
- **理由**：httpx.AsyncClient 与 FastAPI TestClient 等价但更现代；纯 Python 测试栈不需要浏览器。
- **备选**：FastAPI TestClient（基于 requests）—— 仍然可用，本设计倾向 httpx 因为后端将来若加 SSE/WebSocket 更顺手。

### D10. 默认占位头像

- **选择**：在 `backend/app/static/avatars/default.png` 放置一张 1x1 PNG（或开源 silhouette），Profile 初始 `avatar_url` 为 `/static/avatars/default.png`。
- **理由**：spec 要求"服务端默认占位"；本地静态文件服务由 FastAPI `StaticFiles` mount 在 `/static`。

## 组件层级图

```
┌────────────────────────────────────────────────────────┐
│  Frontend (existing, unchanged)                        │
│    └── src/   (React + Vite, consumes VITE_API_BASE)   │
└────────────────────────────────────────────────────────┘
                       │  HTTPS / JSON
                       ▼
┌────────────────────────────────────────────────────────┐
│  FastAPI app  (uvicorn)                                │
│  ┌──────────────────────────────────────────────────┐  │
│  │ main.py                                           │  │
│  │   ├── CORS middleware                             │  │
│  │   ├── router: /api/auth   (auth.py)               │  │
│  │   ├── router: /api/users  (profile.py)            │  │
│  │   └── StaticFiles /static                         │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │ deps.py                                           │  │
│  │   ├── get_db()      ─► SessionLocal               │  │
│  │   └── get_current_user()  ─► OAuth2PasswordBearer  │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │ security.py                                       │  │
│  │   ├── hash_password / verify_password (bcrypt)    │  │
│  │   ├── create_access_token (HS256, typ=access)     │  │
│  │   └── create_refresh_token (HS256, typ=refresh)   │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │ routers/auth.py                                   │  │
│  │   ├── POST /api/auth/register                     │  │
│  │   ├── POST /api/auth/login                        │  │
│  │   └── POST /api/auth/refresh                      │  │
│  ├──────────────────────────────────────────────────┤  │
│  │ routers/profile.py                                │  │
│  │   ├── GET  /api/users/me                          │  │
│  │   └── PATCH /api/users/me                         │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
                       │  SQLAlchemy 2.x
                       ▼
┌────────────────────────────────────────────────────────┐
│  SQLite (single file, WAL mode)                        │
│    ├── users (id, email UNIQUE, password_hash, ...)     │
│    └── user_profiles (user_id FK, avatar_url,          │
│                       streak_days, level)              │
│  Alembic manages migrations                            │
└────────────────────────────────────────────────────────┘
```

## API 端点规范

所有响应均为 JSON；4xx/5xx 响应包含 `{ "detail": "<message>" }`，除非特别说明。

### POST `/api/auth/register`

请求体：
```json
{ "email": "user@example.com", "password": "string≥8" }
```
响应 201：
```json
{
  "user_id": 1,
  "email": "user@example.com",
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer"
}
```
错误：
- 409 `email already registered`
- 422 字段校验失败（邮箱格式 / 密码长度）

副作用：创建 `users` 行 + `user_profiles` 行（avatar 占位、`streak_days=0`、`level=1`）。

### POST `/api/auth/login`

请求体：`{ "email", "password" }`
响应 200：与 register 相同结构。
错误：
- 401 `invalid credentials`（不区分用户不存在 / 密码错误）

### POST `/api/auth/refresh`

请求体：`{ "refresh_token": "<jwt>" }`
响应 200：
```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```
错误：
- 401 `invalid refresh token`（签名错 / 过期 / token type ≠ refresh）

### GET `/api/users/me`

请求头：`Authorization: Bearer <access_token>`
响应 200：
```json
{
  "user_id": 1,
  "email": "user@example.com",
  "avatar_url": "/static/avatars/default.png",
  "streak_days": 0,
  "level": 1
}
```
错误：401（缺失 / 过期 / 签名错）。

### PATCH `/api/users/me`

请求头：`Authorization: Bearer <access_token>`
请求体（仅允许 `avatar_url`，其他字段将被忽略）：
```json
{ "avatar_url": "https://cdn.example.com/avatars/me.png" }
```
响应 200：与 GET `/api/users/me` 相同。
错误：
- 401（同上）
- 422 `avatar_url` 长度 > 2048

## Risks / Trade-offs

- **[Risk] JWT_SECRET 泄漏** → Mitigation：生产部署必须显式注入（部署平台 secret manager）；开发态 `.env.example` 仅放占位；启动时若检测到占位密钥直接拒绝运行（除 `ENV=dev`）。
- **[Risk] SQLite 单写并发瓶颈** → Mitigation：启用 WAL（`PRAGMA journal_mode=WAL`）；本期并发极低；若未来迁移到 Postgres，ORM 与 Alembic 配置已与引擎解耦，迁移成本可控。
- **[Risk] bcrypt cost factor 导致登录 p95 超 200ms** → Mitigation：默认 cost=12，CI 加一个性能断言若 p95 > 200ms 则失败；后续可下调到 10。
- **[Risk] 客户端误把 access token 当 refresh token 用** → Mitigation：JWT payload 强制 `typ` 字段（`access` / `refresh`），刷新端点在校验时强制 `typ=refresh`。
- **[Risk] 注册接口被脚本批量灌水** → Mitigation：本期不引入 rate limit（spec 未要求）；在 README 中标注"未来 change 引入"。
- **[Trade-off] 不维护 refresh token 黑名单** → 优点：实现最薄；缺点：refresh token 泄漏后最长可用 7 天。未来若引入登出或多设备会话管理，需要新增 `revoked_tokens` 表。

## Migration Plan

- **首次部署**：
  1. 创建后端服务（Render/Fly 等），注入 `DATABASE_URL`、`JWT_SECRET`、`CORS_ALLOW_ORIGINS`
  2. 启动命令：`alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  3. 验证：`curl /api/users/me` 返回 401；`curl -X POST /api/auth/register ...` 返回 201
- **回滚**：
  - 删除 `backend/` 目录 + 丢弃 SQLite 文件，前端零影响
  - 若已上线：删除后端服务实例 + 丢弃 SQLite 文件
  - schema 回滚走 `alembic downgrade -1`，并同步删除对应运行时读取路径

## Open Questions

（无。所有会影响 spec / 设计的取舍已在 Decisions 中确定；剩余的工程细节（如 CI 如何触发后端构建）属于 tasks.md 范畴。）