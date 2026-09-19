# Tasks

## 1. 后端工程脚手架

- [x] 1.1 创建 `backend/` 目录树（含 `app/`、`app/models/`、`app/schemas/`、`app/routers/`、`tests/`、`alembic/versions/`）并写入空 `__init__.py`，verify by `find backend -type f` 输出符合 design.md D8 的目录布局
- [x] 1.2 创建 `backend/pyproject.toml` 与 `backend/requirements.txt`，依赖固定到次版本（fastapi、uvicorn[standard]、sqlalchemy>=2.0、alembic、pydantic>=2、pydantic-settings、passlib[bcrypt]、python-jose[cryptography]、email-validator、pytest、httpx），verify by `python -m venv .venv && pip install -r backend/requirements.txt` 安装成功
- [x] 1.3 创建 `backend/.env.example`（`DATABASE_URL=sqlite:///./studypal.db`、`JWT_SECRET=<dev-only-placeholder>`、`JWT_ACCESS_TTL_MIN=15`、`JWT_REFRESH_TTL_DAY=7`、`CORS_ALLOW_ORIGINS=http://localhost:5173`）并写入 `.gitignore` 忽略 `.env` 与 `*.db`，verify by `grep -F JWT_SECRET backend/.env.example` 输出非空

## 2. 数据库与迁移

- [x] 2.1 在 `backend/app/db.py` 实现 SQLAlchemy `engine` / `SessionLocal` / `Base`，并启用 `PRAGMA journal_mode=WAL` 与 `PRAGMA foreign_keys=ON`，verify by `python -c "from backend.app.db import engine; print(engine.url)"` 打印预期 DSN
- [x] 2.2 在 `backend/app/models/user.py` 与 `backend/app/models/profile.py` 定义 `User`（id / email UNIQUE / password_hash / created_at）与 `UserProfile`（user_id FK CASCADE / avatar_url / streak_days=0 / level=1 / updated_at），verify by `python -c "from backend.app.models.user import User; from backend.app.models.profile import UserProfile"` 导入无异常
- [x] 2.3 初始化 Alembic（`backend/alembic.ini` + `backend/alembic/env.py` 指向 `app.db.Base` 与 `app.config.settings.DATABASE_URL`），verify by `cd backend && alembic revision --autogenerate -m "initial"` 生成首个迁移文件
- [x] 2.4 手写 0001 初始迁移：建 `users` 与 `user_profiles` 两表，user_profiles.user_id 设 UNIQUE 与外键 CASCADE，verify by `cd backend && alembic upgrade head && sqlite3 studypal.db ".tables"` 同时输出 `users` 与 `user_profiles`

## 3. 配置、安全与依赖注入

- [x] 3.1 在 `backend/app/config.py` 用 `pydantic-settings.BaseSettings` 读 `DATABASE_URL` / `JWT_SECRET` / `JWT_ACCESS_TTL_MIN` / `JWT_REFRESH_TTL_DAY` / `CORS_ALLOW_ORIGINS` / `ENV`，并在生产态（`ENV != "dev"`）检测到占位 `JWT_SECRET` 时启动失败，verify by `unset JWT_SECRET && ENV=dev python -c "from backend.app.config import settings"` 不抛错、`ENV=prod python ...` 抛 `RuntimeError`
- [x] 3.2 在 `backend/app/security.py` 实现 `hash_password` / `verify_password`（passlib bcrypt，cost=12）与 `create_access_token` / `create_refresh_token` / `decode_token`（HS256，payload 强制 `sub` + `typ` + `exp`），verify by `pytest backend/tests/test_security.py::test_roundtrip` 通过
- [x] 3.3 在 `backend/app/deps.py` 实现 `get_db`（yield SessionLocal）与 `get_current_user`（解析 `Authorization: Bearer` 头，调用 `decode_token`，校验 `typ="access"`，查 DB 拿 User），verify by 单测覆盖"缺失头 / 签名错 / typ=refresh / 过期 / user 不存在"五种 401 路径

## 4. Auth 路由

- [x] 4.1 在 `backend/app/schemas/auth.py` 定义 `RegisterIn`（email 用 `EmailStr`、password `min_length=8`）、`LoginIn`、`TokenPair`、`RefreshIn`，verify by `pytest -k schemas_auth` 通过字段校验断言
- [x] 4.2 在 `backend/app/routers/auth.py` 实现 `POST /api/auth/register`：校验 → 邮箱去小写 → 查重 → 哈希 → 写 User + UserProfile → 返回 201 + TokenPair；冲突返回 409 + `email already registered`，verify by `pytest backend/tests/test_auth.py::test_register_success` 与 `test_register_duplicate_email` 通过
- [x] 4.3 在 `backend/app/routers/auth.py` 实现 `POST /api/auth/login`：校验 → 取 User（按 email）→ `verify_password` → 返回 200 + TokenPair；任何失败统一 401 `invalid credentials`，verify by `pytest backend/tests/test_auth.py::test_login_success`、`test_login_wrong_password`、`test_login_unknown_email_same_message` 通过
- [x] 4.4 在 `backend/app/routers/auth.py` 实现 `POST /api/auth/refresh`：`decode_token` 校验 `typ="refresh"` → 颁发新 access token；签名错 / 过期 / typ 错均返回 401 `invalid refresh token`，verify by `pytest backend/tests/test_auth.py::test_refresh_success`、`test_refresh_with_access_token_rejected`、`test_refresh_expired_rejected` 通过

## 5. Profile 路由

- [x] 5.1 在 `backend/app/schemas/profile.py` 定义 `ProfileOut`（user_id / email / avatar_url / streak_days / level）与 `ProfileUpdate`（仅 `avatar_url: str max_length=2048`），verify by `pytest -k schemas_profile` 通过
- [x] 5.2 在 `backend/app/routers/profile.py` 实现 `GET /api/users/me`：调用 `get_current_user` → 返回 ProfileOut；未认证返回 401，verify by `pytest backend/tests/test_profile.py::test_get_me_success`、`test_get_me_unauthorized` 通过
- [x] 5.3 在 `backend/app/routers/profile.py` 实现 `PATCH /api/users/me`：应用 `avatar_url` 更新（忽略 `streak_days` / `level` 字段）→ 返回更新后的 ProfileOut；超过长度返回 422，verify by `pytest backend/tests/test_profile.py::test_patch_avatar_success`、`test_patch_avatar_too_long`、`test_patch_streak_and_level_ignored` 通过
- [x] 5.4 在 `backend/app/static/avatars/default.png` 放占位头像（1x1 PNG 或 silhouette），并把 `/static` mount 到 FastAPI，verify by `curl http://localhost:8000/static/avatars/default.png -I` 返回 200

## 6. 应用装配与端到端验证

- [x] 6.1 在 `backend/app/main.py` 创建 FastAPI 实例，挂载 CORS、StaticFiles、`/api/auth` 与 `/api/users` 两个 router，verify by `cd backend && uvicorn app.main:app --port 8000` 后 `curl http://localhost:8000/openapi.json` 返回 200 且包含 5 个 operationId
- [x] 6.2 在根目录 `README.md` 增补"后端"小节：列出 `backend/requirements.txt` 安装步骤、`alembic upgrade head`、`uvicorn` 启动命令、`VITE_API_BASE` 对接说明；同步在 `package.json` 增加 `scripts.backend:install` / `scripts.backend:test` 脚本入口（不破坏既有 `build` / `deploy`），verify by `npm run build` 仍然成功且不引用任何后端模块
- [x] 6.3 跑完整测试：`cd backend && pytest`，并 `npm run build`，两者均需通过；record outcome：本地 `pytest` 全绿、`npm run build` 产物体积与本次变更前一致（前端零影响）

## 7. 验证：与既有系统零冲突

- [x] 7.1 确认根目录 `index.html` / `src/` 下无任何新增文件或修改（除 README 与可选 package.json 脚本），verify by `git status` 仅显示 `backend/` 与 `README.md`（+ `package.json` 若调整了 scripts）三类变更
- [x] 7.2 确认前端的 `VITE_API_BASE` 未被消费（仅文档化），verify by `grep -r VITE_API_BASE src/` 在前端源码路径下无匹配（仅 README / docs 可有）