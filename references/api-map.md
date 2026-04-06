# 接口映射

这份文件记录当前可直接使用的 TradingAgentsCN 接口映射。

说明：
- 这里记录的是相对接口路径，不提供默认实例值
- 下文路径默认都以 `TRADINGAGENTS_BASE_URL` 为基准
- 文档页和 OpenAPI 页当前会被前端代理接管，不能单靠 `/docs` 或 `/openapi.json` 推断真实接口

## 系统基础能力

| 能力 | 路径 | 备注 |
|---|---|---|
| 登录 | `/auth/login` | 已实测可用，`POST` |
| 登出 | `/auth/logout` | 由路由常量确认 |
| 当前用户信息 | `/auth/me` | 已实测可用，需 Bearer Token |
| 刷新 Token | `/auth/refresh` | 由路由常量确认 |
| 修改密码 | `/auth/change-password` | 由路由常量确认 |
| 创建用户 | `/auth/create-user` | 由路由常量确认 |
| 重置密码 | `/auth/reset-password` | 由路由常量确认 |
| 用户列表 | `/auth/users` | 由路由常量确认 |
| 健康检查 | `/health` | 本地启动脚本和主应用都显示存在 |
| 系统信息 | `/system/info` | 主应用中存在 `/api/system/info`，相对基址为 `/system/info` |
| 文档页 | `<host>/docs` | 当前可能存在，但常被前端接管 |

## 股票分析

| 能力 | 路径 | 备注 |
|---|---|---|
| 单股分析 | `/analysis/single` | 已实测路径存在，`POST` |
| 批量分析 | `/analysis/batch` | 已实测路径存在，`POST` |
| 批量任务详情 | `/analysis/batches/{batch_id}` | 由路由常量确认 |
| 当前用户任务列表 | `/analysis/tasks` | 由路由常量确认 |
| 全部任务列表 | `/analysis/tasks/all` | 由路由常量确认 |
| 任务状态 | `/analysis/tasks/{task_id}/status` | 路由常量确认，持仓分析文案也引用了它 |
| 任务结果 | `/analysis/tasks/{task_id}/result` | 由路由常量确认 |
| 任务详情 | `/analysis/tasks/{task_id}/details` | 由路由常量确认 |
| 取消任务 | `/analysis/tasks/{task_id}/cancel` | 由路由常量确认 |
| 重试任务 | `/analysis/tasks/{task_id}/retry` | 由路由常量确认 |
| 标记失败 | `/analysis/tasks/{task_id}/mark-failed` | 由路由常量确认 |
| 用户历史分析 | `/analysis/user/history` | 由路由常量确认 |
| 队列状态 | `/analysis/user/queue-status` | 由路由常量确认 |

补充说明：
- 空 JSON 请求 `/analysis/single` 会返回 `400`，报“股票代码格式不正确或不存在”，说明接口会优先校验股票代码
- 空 JSON 请求 `/analysis/batch` 会返回 `422`，至少要求 `title`

## 交易计划

| 能力 | 路径 | 备注 |
|---|---|---|
| 查询当前激活计划 | `/v1/trading-systems/active` | 已实测可用，`GET` |
| 创建交易计划 | `/v1/trading-systems` | 由路由常量确认 |
| 查询单个交易计划 | `/v1/trading-systems/{system_id}` | 由路由常量确认 |
| 更新交易计划 | `/v1/trading-systems/{system_id}` | 由服务命名和 REST 结构推断 |
| 激活交易计划 | `/v1/trading-systems/{system_id}/activate` | 由路由常量确认 |
| 发布交易计划 | `/v1/trading-systems/{system_id}/publish` | 由路由常量确认 |
| 评估交易计划 | `/v1/trading-systems/{system_id}/evaluate` | 由路由常量确认 |
| 查询评估列表 | `/v1/trading-systems/{system_id}/evaluations` | 由路由常量确认 |
| 查询版本列表 | `/v1/trading-systems/{system_id}/versions` | 由路由常量确认 |
| 创建版本 | `/v1/trading-systems/{system_id}/versions` | 由路由常量确认 |
| 查询指定版本 | `/v1/trading-systems/versions/{version_id}` | 由路由常量确认 |
| 查询指定评估 | `/v1/trading-systems/evaluations/{evaluation_id}` | 由路由常量确认 |
| 草稿评估 | `/v1/trading-systems/evaluate-draft` | 由路由常量确认 |
| 生成风险规则 | `/v1/trading-systems/generate-risk-rules` | 已实测可用，空 JSON 也会成功返回默认风控规则 |
| 生成模块规则 | `/v1/trading-systems/generate-module-rules` | 已实测路径存在，空 JSON 返回 `422`，至少要求 `module` |
| 交易计划优化讨论 | `/v1/trading-systems/optimize-discussion` | 由路由常量确认 |

## 持仓

| 能力 | 路径 | 备注 |
|---|---|---|
| 查询持仓列表 | `/portfolio/positions` | 已实测可用，`GET` |
| 历史持仓 | `/portfolio/positions/history` | 由路由常量确认 |
| 新增持仓 | `/portfolio/positions` | REST 结构推断存在 |
| 更新持仓 | `/portfolio/positions/{position_id}` | 由路由常量确认 |
| 删除持仓 | `/portfolio/positions/{position_id}` | 由路由常量确认 |
| 批量导入持仓 | `/portfolio/positions/import` | 由路由常量确认 |
| 持仓操作 | `/portfolio/positions/operate` | 由路由常量确认 |
| 重置持仓 | `/portfolio/positions/reset` | 由路由常量确认 |
| 重置全部持仓 | `/portfolio/positions/reset-all` | 由路由常量确认 |
| 持仓分析前缓存检查 | `/portfolio/positions/check-cache` | 由路由常量确认 |
| 按代码发起持仓分析 | `/portfolio/positions/analyze-by-code` | 已实测路径存在，空 JSON 返回 `422`，至少要求 `code` |
| 按代码获取持仓分析 | `/portfolio/positions/analysis-by-code/{code}` | 由路由常量确认 |
| 单持仓分析 | `/portfolio/positions/{position_id}/analysis` | 由路由常量确认 |
| 单持仓分析历史 | `/portfolio/positions/{position_id}/analysis/history` | 由路由常量确认 |
| 组合分析列表或摘要 | `/portfolio/analysis` | 路由常量确认存在 |
| 组合分析详情 | `/portfolio/analysis/{analysis_id}` | 由路由常量确认 |
| 持仓分析任务状态 | `/portfolio/positions/analysis/{task_id}` | 由路由常量确认 |
| 持仓统计 | `/portfolio/statistics` | 由路由常量确认 |
| 账户初始化 | `/portfolio/account/initialize` | 由路由常量确认 |
| 账户摘要 | `/portfolio/account/summary` | 由路由常量确认 |
| 账户设置 | `/portfolio/account/settings` | 由路由常量确认 |
| 存款 | `/portfolio/account/deposit` | 由路由常量确认 |
| 提现 | `/portfolio/account/withdraw` | 由路由常量确认 |
| 账户流水 | `/portfolio/account/transactions` | 由路由常量确认 |

## 交易复盘

| 能力 | 路径 | 备注 |
|---|---|---|
| 创建单笔/整笔交易复盘 | `/review/trade` | 已实测路径存在，空 JSON 返回 `422`，至少要求 `trade_ids` |
| 单笔/整笔交易复盘历史 | `/review/trade/history` | 由路由常量确认 |
| 查询单个交易复盘 | `/review/trade/{review_id}` | 由路由常量确认 |
| 创建周期复盘 | `/review/periodic` | 已实测路径存在，空 JSON 返回 `422`，至少要求 `start_date` 和 `end_date` |
| 周期复盘历史 | `/review/periodic/history` | 由路由常量确认 |
| 查询单个周期复盘 | `/review/periodic/{review_id}` | 由路由常量确认 |
| 可复盘交易列表 | `/review/reviewable-trades` | 由路由常量确认 |
| 按股票代码查询交易 | `/review/trades-by-code/{code}` | 由路由常量确认 |
| 统计信息 | `/review/statistics` | 已实测可用，`GET` |
| 保存复盘为案例 | `/review/case` | 由路由常量确认 |
| 查询案例详情 | `/review/case/{review_id}` | 由路由常量确认 |
| 查询案例列表 | `/review/cases` | 由路由常量确认 |

## 自选股

| 能力 | 路径 | 备注 |
|---|---|---|
| 查询自选股分组列表 | `/watchlist-groups` | 已实测可用，`GET` |
| 创建自选股分组 | `/watchlist-groups` | REST 结构和路由常量确认存在 |
| 查询分组详情 | `/watchlist-groups/{group_id}` | 由路由常量确认 |
| 更新分组 | `/watchlist-groups/{group_id}` | 由路由常量确认 |
| 删除分组 | `/watchlist-groups/{group_id}` | 由路由常量确认 |
| 查询分组内股票 | `/watchlist-groups/{group_id}/stocks` | 由路由常量确认 |
| 增删分组内股票 | `/watchlist-groups/{group_id}/stocks` | 由路由常量确认 |
| 移动股票到其他分组 | `/watchlist-groups/{group_id}/stocks/move` | 由路由常量确认 |

## 验证来源

当前映射依据：
- 用户提供的真实实例配置
- 对环境变量指定实例上的 `/auth/login`、`/auth/me`、`/portfolio/positions`、`/review/statistics`、`/watchlist-groups`、`/v1/trading-systems/active` 的实测调用
- 对仓库内 `.pyc` 路由常量与主应用 `include_router` 挂载关系的提取

仍建议在后续条件允许时，再补一次真实 OpenAPI 导出或前端抓包，进一步确认各接口的请求体字段细节。
