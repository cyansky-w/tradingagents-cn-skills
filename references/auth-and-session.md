# 认证与会话

当 skill 需要确认 TradingAgentsCN 的访问权限保障是否正常时，使用这份参考。

核心原则：

- 认证是脚本层责任
- AI 不应把“显式登录”当成主业务流程
- 只有脚本兜不住时，才把问题升级为用户可见的认证失败

## 输入项

- `base_url`
- 用户名/密码、App Token，或现成 Bearer Token
- 如果部署有要求，还可能需要租户、工作区或用户上下文

## 环境变量优先级

优先按以下顺序取认证配置：

1. 当前请求里明确给出的值
2. 当前会话里已存在的 Bearer Token 或有效缓存
3. 环境变量
4. 向用户询问

推荐环境变量名称：

- `TRADINGAGENTS_BASE_URL`
- `TRADINGAGENTS_USERNAME`
- `TRADINGAGENTS_PASSWORD`
- `TRADINGAGENTS_APP_TOKEN`
- `TRADINGAGENTS_BEARER_TOKEN`

如果已经拿到 `TRADINGAGENTS_BEARER_TOKEN`，优先直接尝试它。
如果没有 Bearer Token，但有用户名和密码，则允许脚本自动登录。

## 推荐脚本

- `scripts/ensure_tradingagents_token.py`
  - 预检脚本，用来确保当前存在可用 Token
- `scripts/invoke_tradingagents_api.py`
  - 正式业务入口，所有受保护请求优先统一走它
- `scripts/tradingagents_client.py`
  - 共享底层实现，负责 Token 校验、缓存和自动重登

## 已确认的脚本保障

当前脚本链路已经具备以下机制：

1. 优先验证环境变量 Bearer Token
2. Bearer Token 无效时，尝试本地缓存 Token
3. 缓存 Token 无效时，自动调用 `/auth/login`
4. 发起受保护业务请求时，如果收到 `401`：
   - 清除缓存
   - 强制重新登录
   - 重试一次原请求
5. 第二次仍失败时，再把错误返回给 AI

所以：

- “先手动登录，再手动带 Token 调接口”不是推荐流程
- 正式业务请求默认只需要调用 `invoke_tradingagents_api.py`
- `ensure_tradingagents_token.py` 适合作为环境预检，而不是每次业务请求的硬前置步骤

## 建议使用方式

### 预检模式

适用于：

- 第一次接入某个实例
- 怀疑环境变量配置错误
- 需要快速区分“服务不可达”和“脚本认证失败”

顺序：

1. 确认 `TRADINGAGENTS_BASE_URL`
2. 跑 `scripts/ensure_tradingagents_token.py`
3. 如有需要，再用 `scripts/invoke_tradingagents_api.py --method GET --path /auth/me` 做一次轻量确认

### 正式业务模式

适用于：

- 已明确要调用正式业务接口

顺序：

1. 直接调用 `scripts/invoke_tradingagents_api.py`
2. 让脚本自行处理 Token 复用、校验和过期重登
3. 只有请求最终失败时，再汇报认证阶段问题

## 安全处理

- 不要在对话里回显完整 Token
- 在日志和总结中隐藏敏感信息
- 不要把凭证写进输出物

## 状态用词

对外汇报时，应区分：

- 服务可达
- 脚本认证成功
- 业务接口可访问

不要把以上任一状态混报为“分析已完成”。

## 诊断边界

只有在这些情况下，才需要显式提到登录层：

- `TRADINGAGENTS_BASE_URL` 缺失或明显错误
- Bearer Token、缓存 Token 和用户名/密码都不可用
- `401` 在自动重登后仍然失败
- 当前部署的认证契约与 skill 文档明显不一致
