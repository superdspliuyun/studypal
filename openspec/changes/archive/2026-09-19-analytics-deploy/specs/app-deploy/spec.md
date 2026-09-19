# Spec Delta

## Purpose

把 FastAPI 后端从"本地 uvicorn"演进为"Render 公网部署"，并通过 GitHub Actions 在 `backend/**` 变更时自动部署；前端继续走 GitHub Pages，前后端 CI 解耦。本规范仅约束部署产物的对外可观测行为。

## ADDED Requirements

### Requirement: Dockerfile 可构建

仓库 SHALL 在 `backend/Dockerfile` 提供容器构建文件；以 `python:3.11-slim` 为基础镜像，`pip install -r requirements.txt`，启动命令为 `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`；镜像 SHALL 在本地 `docker build` 时成功构建。

#### Scenario: 本地构建成功

- **WHEN** 在 `backend/` 下执行 `docker build -t studypal-backend .`
- **THEN** SHALL 返回成功，镜像 SHALL 暴露 `/api/*` 与 `/docs` 端点

#### Scenario: 容器启动自检（错误场景）

- **WHEN** 镜像以错误的环境变量（如 `DEEPSEEK_API_KEY` 缺失）启动
- **THEN** 容器 SHALL 进程退出且非零退出码；健康检查 SHALL 失败

### Requirement: render.yaml 声明 web service

仓库 SHALL 在根目录 `render.yaml` 声明 Render Blueprint；服务类型 SHALL 为 `web`，`rootDir` SHALL 为 `backend`，`healthCheckPath` SHALL 为 `/healthz`。

#### Scenario: Blueprint 校验通过

- **WHEN** 在 Render 控制台导入该 `render.yaml`
- **THEN** SHALL 创建一个 web service，healthCheck 路径识别 `/healthz`

### Requirement: GitHub Actions 自动部署

仓库 SHALL 在 `.github/workflows/backend-deploy.yml` 提供自动部署工作流：当 `backend/**` 或 `render.yaml` 变更 push 到 main 时 SHALL 触发构建并部署到 Render。

#### Scenario: backend 变更触发

- **WHEN** PR 合并到 main 且 diff 包含 `backend/` 下任意文件
- **THEN** workflow SHALL 跑完 build + deploy 两步

#### Scenario: 仅前端代码变动（错误场景）

- **WHEN** PR 合并到 main 且 diff 仅包含 `src/` 或 `index.html`
- **THEN** workflow SHALL NOT 被触发（`paths` 过滤器不匹配）

### Requirement: 健康检查端点

后端 SHALL 暴露 `GET /healthz` 端点，返回 HTTP 200 与 `{"status": "ok"}`；生产部署 SHALL 配置 Render health check 指向该端点。

#### Scenario: 健康检查通过

- **WHEN** Render 每 30s 调用 `/healthz`
- **THEN** SHALL 返回 HTTP 200；实例 SHALL 保持运行

#### Scenario: 健康检查失败（错误场景）

- **WHEN** 应用启动失败（如 alembic 抛错）
- **THEN** `/healthz` SHALL 返回 HTTP 503 或不可达；Render SHALL 自动重启实例

### Requirement: 环境变量透传

部署 SHALL 通过 Render 环境变量注入 `DATABASE_URL` / `JWT_SECRET` / `DEEPSEEK_API_KEY` / `CORS_ALLOW_ORIGINS`；其中 `CORS_ALLOW_ORIGINS` SHALL 包含前端 GitHub Pages 域名。

#### Scenario: CORS 放行前端域名

- **WHEN** 浏览器从 `https://<user>.github.io/my-website/` 调用 `/api/*`
- **THEN** CORS 响应 SHALL 包含正确的 `Access-Control-Allow-Origin`

#### Scenario: Secret 注入（错误场景）

- **WHEN** Render 上 `JWT_SECRET` / `DEEPSEEK_API_KEY` 留空
- **THEN** 启动 SHALL 失败（沿用 `user-auth` change 的 fail-fast 配置）

### Requirement: 前后端部署解耦

前端 `npm run build` / `npm run deploy` SHALL NOT 触发后端 workflow；后端 workflow SHALL NOT 触碰前端产物。

#### Scenario: 独立发布

- **WHEN** 仅前端 main 合并
- **THEN** 仅 GitHub Pages 发布；后端 Render 实例不变