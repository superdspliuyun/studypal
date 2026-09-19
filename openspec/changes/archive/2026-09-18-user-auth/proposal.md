# Proposal

## Why

StudyPal 目前是纯前端品牌站 + mock 学习 Dashboard，没有任何后端或身份层；要让它从"展示型 Demo"演进为"真正的学习平台"，用户必须能注册、登录，并在跨设备/跨刷新后保持自己的学习画像（连续学习天数、用户等级、头像）。这个 change 引入最薄的一层账号基础设施 —— FastAPI + SQLite + JWT —— 不引入后台、不引入多租户、不引入复杂 RBAC，刚好够支撑后续学习数据 change 复用同一身份。

## What Changes

- 新增 FastAPI 后端工程（Python 包 `backend/`），与现有前端 `src/` 平级共存；前端构建 (`npm run build` / `npm run deploy`) 不受影响
- 引入 SQLite 3 作为持久层，使用 Alembic 维护 schema 版本化迁移
- 引入 JWT 双 token 体系：access token（短时效，~15min）+ refresh token（长时效，~7d），刷新走独立端点
- 密码使用 bcrypt（或同等强度的 `passlib` 哈希）单向哈希存储，登录失败返回统一 401 文本，不区分"用户不存在"与"密码错误"
- 暴露用户 Profile 端点：头像 URL（默认占位）、连续学习天数 `streak_days`（初始 0）、用户等级 `level`（初始 1）
- 前端通过 `VITE_API_BASE` 读取后端域名；本次 change 仅在后端完成实现，前端接入留待后续 change

## Capabilities

### New Capabilities

- `user-auth`: 用户注册、登录、JWT access/refresh token 颁发与刷新；包含密码哈希、token 校验与受保护路由的认证依赖
- `user-profile`: 已登录用户的 Profile CRUD 读端点 —— 头像、连续学习天数、用户等级；不包含管理他人 Profile 的能力

### Modified Capabilities

- （无）现有 `study-pal` 规范描述的是前端 UI 形态契约，本次不改变其 REQUIREMENTS；Profile 字段后续接入 Dashboard 统计卡片将由独立 change 处理

## Impact

- **新增代码**：`backend/` 目录（FastAPI app、SQLAlchemy model、Pydantic schema、Alembic 配置与初始迁移、测试）
- **新增依赖**：FastAPI / uvicorn / SQLAlchemy 2.x / Alembic / passlib[bcrypt] / python-jose（JWT 签发与校验）/ pytest；通过 `backend/requirements.txt` 与根目录 README 文档化
- **新增环境变量**（后端）：`DATABASE_URL`（默认 `sqlite:///./studypal.db`）、`JWT_SECRET`（生产必须显式注入）、`JWT_ACCESS_TTL_MIN` / `JWT_REFRESH_TTL_DAY`、CORS allow_origins
- **新增环境变量**（前端）：`VITE_API_BASE` —— **本次不消费，仅在文档中说明**，前端接入留待后续 change
- **现有行为**：前端构建、部署、视觉、Dashboard 渲染逻辑保持不变；StudyPal Dashboard 仍使用 mock 数据
- **部署影响**：GitHub Pages 不承载 FastAPI，后端需部署到 Render / Fly.io / Railway / Cloud Run 等支持 Python runtime 的平台；前后端解耦，可独立发布

### Out of Scope（明确不做）

- **后台管理**：无 admin 角色、无运营面板、无用户封禁/解封接口
- **OAuth / 第三方登录**：仅自管账号 + 密码
- **邮箱验证、找回密码、短信验证**：本期不实现；登录失败统一返回 401
- **多设备登录会话管理**：本期不维护 refresh token 黑名单/会话表，refresh token 仅依赖签名与过期时间校验
- **RBAC / 细粒度权限**：只有一个匿名角色与一个登录角色
- **前端接入**：本期不修改 `src/` 下任何前端代码；Profile 字段对接 Dashboard 卡片留待独立 change
- **学习行为埋点**：连续学习天数 / 等级的口径与写入入口在 Profile 规范中固定为初始值 0 / 1，实际增长逻辑由后续 change 引入

### 回滚方案（高风险变更）

本 change 是"新增后端工程 + 新增数据库"，不修改前端任何现有代码，**回滚 = 删除 `backend/` 目录 + 丢弃 SQLite 文件**，前端零影响。数据库迁移一旦上线，**只增不减 / 只改兼容项**；若必须回滚破坏性 schema，流程为：

1. `alembic downgrade -1` 回退最近一次迁移
2. 删除新引入的列对应的运行时读取路径
3. 重新部署后端
4. 受影响用户需重新注册（不提供数据迁移回退）