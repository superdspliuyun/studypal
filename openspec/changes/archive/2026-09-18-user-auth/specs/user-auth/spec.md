# Spec Delta

## Purpose

为 StudyPal 提供自管账号与 JWT 身份层：用户使用邮箱与密码注册和登录，服务端颁发短时效 access token 与长时效 refresh token，受保护端点通过 Bearer access token 校验身份。本规范仅约束外部可观测行为，不限定实现细节。

## ADDED Requirements

### Requirement: 用户注册

系统 SHALL 提供邮箱+密码注册端点；当邮箱未被占用、邮箱格式合法、且密码长度 ≥ 8 字符时，系统 SHALL 创建账号并返回 access token 与 refresh token。响应 SHALL 包含 `user_id`、`email`、`access_token`、`refresh_token`、`token_type`（值固定为 `bearer`）。

#### Scenario: 注册成功

- **WHEN** 客户端提交未注册过的合法邮箱与 ≥ 8 字符密码
- **THEN** 系统 SHALL 返回 HTTP 201 与上述字段；新建账号 SHALL 持久化，邮箱 SHALL 唯一索引

#### Scenario: 邮箱已存在（错误场景）

- **WHEN** 客户端使用已被占用的邮箱再次注册
- **THEN** 系统 SHALL 返回 HTTP 409，错误消息 SHALL 不泄露既有账号的任何字段（哈希、ID 等）

#### Scenario: 邮箱格式非法（错误场景）

- **WHEN** 客户端提交不符合 RFC 5322 邮箱格式的字符串
- **THEN** 系统 SHALL 返回 HTTP 422

#### Scenario: 密码长度不足（错误场景）

- **WHEN** 客户端提交长度 < 8 字符的密码
- **THEN** 系统 SHALL 返回 HTTP 422

### Requirement: 用户登录

系统 SHALL 提供邮箱+密码登录端点；当且仅当邮箱存在且密码哈希校验通过时，系统 SHALL 颁发新的 access token 与 refresh token。

#### Scenario: 登录成功

- **WHEN** 已注册用户提交正确的邮箱与密码
- **THEN** 系统 SHALL 返回 HTTP 200 与 access token、refresh token、token type `bearer`

#### Scenario: 凭据无效（错误场景）

- **WHEN** 客户端提交不存在的邮箱、已注册邮箱但密码错误
- **THEN** 系统 SHALL 返回 HTTP 401 与统一的错误消息 `invalid credentials`；消息 SHALL 不区分两种失败原因

#### Scenario: 邮箱格式非法（错误场景）

- **WHEN** 客户端提交不符合 RFC 5322 邮箱格式的字符串
- **THEN** 系统 SHALL 返回 HTTP 422

### Requirement: Access token 刷新

系统 SHALL 提供独立的刷新端点，接收 refresh token，校验通过后 SHALL 颁发新的 access token；当 refresh token 包含合法签名且未过期时调用成功；refresh token 自身 SHALL 仅在签发方密钥轮换或自然过期时失效，本期不维护服务器端黑名单。

#### Scenario: 刷新成功

- **WHEN** 客户端提交有效且未过期的 refresh token
- **THEN** 系统 SHALL 返回 HTTP 200 与新 access token；refresh token SHOULD 在响应中复用同一个（除非 refresh rotation 在未来 change 中引入）

#### Scenario: refresh token 无效（错误场景）

- **WHEN** 客户端提交签名错误、已过期、被篡改或缺失的 refresh token
- **THEN** 系统 SHALL 返回 HTTP 401 与错误消息 `invalid refresh token`

#### Scenario: 使用 access token 刷新（错误场景）

- **WHEN** 客户端将 access token 提交到 refresh 端点
- **THEN** 系统 SHALL 返回 HTTP 401（token 类型不匹配）

### Requirement: 受保护端点的 Bearer 认证

系统 SHALL 在所有需要登录身份的端点上校验 `Authorization: Bearer <access_token>` 头；当 access token 缺失、签名错误或已过期时 SHALL 返回 HTTP 401，且 SHALL NOT 泄露请求体内的任何业务字段。

#### Scenario: 合法 access token 通过

- **WHEN** 客户端携带有效 access token 访问受保护端点
- **THEN** 系统 SHALL 进入对应业务处理，并将当前 `user_id` 注入到请求上下文

#### Scenario: 缺失 Authorization 头（错误场景）

- **WHEN** 客户端未携带 `Authorization` 头访问受保护端点
- **THEN** 系统 SHALL 返回 HTTP 401

#### Scenario: token 已过期（错误场景）

- **WHEN** 客户端携带已过期的 access token 访问受保护端点
- **THEN** 系统 SHALL 返回 HTTP 401 与错误消息 `token expired`

### Requirement: 密码存储安全

系统 SHALL 在数据库中以单向哈希形式存储用户密码，原始密码 SHALL NOT 出现在日志、错误消息或数据库查询结果中；哈希算法 SHALL 为 bcrypt 或同等强度的自适应哈希函数。

#### Scenario: 数据库中无明文密码

- **WHEN** 审计任意用户记录
- **THEN** 密码字段 SHALL 仅为哈希字符串；登录失败响应 SHALL NOT 不包含密码字段