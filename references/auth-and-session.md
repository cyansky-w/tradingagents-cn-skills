# 认证与会话

当 skill 需要建立或刷新 TradingAgentsCN 部署实例的访问权限时，使用这份参考。

如果脚本可用，优先让脚本处理认证，而不是让 AI 在每次调用时自己重写登录流程。

## 输入项

- `base_url`
- 用户名/密码、App Token，或现成 Bearer Token
- 如果部署有要求，还可能需要租户、工作区或用户上下文

## 环境变量优先级

优先按以下顺序取认证配置：
1. 当前请求里明确给出的值
2. 当前会话里已经缓存的有效认证
3. 环境变量
4. 向用户询问

推荐环境变量名称：
- `TRADINGAGENTS_BASE_URL`
- `TRADINGAGENTS_USERNAME`
- `TRADINGAGENTS_PASSWORD`
- `TRADINGAGENTS_APP_TOKEN`
- `TRADINGAGENTS_BEARER_TOKEN`

如果已经拿到 `TRADINGAGENTS_BEARER_TOKEN`，优先直接尝试它。
如果没有 Bearer Token，但有用户名和密码，则走登录流程。
如果同时提供了 App Token 和用户名/密码，以部署实例实际支持的优先方式为准。

## 推荐脚本

- `scripts/ensure_tradingagents_token.py`
  负责确保当前存在可用 Token
- `scripts/invoke_tradingagents_api.py`
  负责发起实际 API 请求
- `scripts/wait_for_task.py`
  负责低频等待异步任务
- `scripts/tradingagents_client.py`
  是脚本共享的底层实现

## 会话约定

优先脚本化：

1. 先执行 `scripts/ensure_tradingagents_token.py`
2. 如果用户已提供有效 Bearer Token，脚本优先直接使用
3. 否则脚本调用登录接口拿到 Token
4. 所有受保护请求统一走 `scripts/invoke_tradingagents_api.py`
5. 如果返回 `401`，脚本自动重新认证一次，并重试一次请求
6. 第二次仍失败时，再由 AI 报告认证失败

## 安全处理

- 不要在对话里回显完整 Token
- 在日志和总结中隐藏敏感信息
- 不要把凭证写进输出物

## 探测清单

由于不同部署的接口细节可能不同，需要先确认：
- 登录路径
- Token 使用的请求头名称
- 是否使用 Cookie
- OpenAPI 是否可在未登录状态下访问
- 除用户登录外，是否还支持 App Token

## 建议探测顺序

1. 先跑 `scripts/ensure_tradingagents_token.py`
2. 再用 `scripts/invoke_tradingagents_api.py --method GET --path /auth/me`
3. 如果需要，再探健康检查、OpenAPI 或轻量业务接口
