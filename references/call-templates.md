# 接口调用模板

这份参考把当前已经确认的 TradingAgentsCN 调用方式整理成可直接照抄的模板。

调用前提：

- `TRADINGAGENTS_BASE_URL` 必须由当前环境或用户显式提供
- 用户名/密码或 Bearer Token 也必须来自当前环境或用户显式提供
- 不要把 skill 文档里出现过的历史实例地址、示例账号或示例 token 当作默认值

## 推荐调用方式

如果脚本可用，优先不要让 AI 自己手写登录和请求头。

### 预检脚本

```bash
python /workspace/projects/workspace/skills/tradingagents-cn/scripts/ensure_tradingagents_token.py
```

说明：

- 这是预检工具
- 适合第一次接入实例或排查认证问题
- 不是每次业务请求都必须显式执行的硬前置步骤

### 统一业务入口

```bash
python /workspace/projects/workspace/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method GET \
  --path /auth/me
```

AI 主要只需要决定：

- `--path` 用哪个正式接口
- `--method` 用什么方法
- `--body` 或 `--body-file` 传什么业务参数

`invoke_tradingagents_api.py` 会自动处理：

- Token 复用
- Token 校验
- 无有效 Token 时自动登录
- `401` 后清缓存、强制重登并重试一次

## 核心规则

- 不要手写 Bearer Token 头作为默认路径
- 不要把“脚本认证成功”混报成“业务完成”
- 对返回 `task_id` 的正式任务接口，当前会话只汇报“任务已提交”
- 对返回 `task_id` 的正式任务接口，必须把 `task_id` 立即回给用户
- 对返回 `task_id` 的正式任务接口，必须提醒用户“当前尚未完成，后续等通知”
- 任务型接口优先在请求体中带 `openclaw_notify`
- 不要在当前会话里阻塞等待异步任务完成

如果用户对生成或分析结果有偏好，不要只在解释里提到。
优先把偏好写进真实请求字段，例如：

- 股票分析：`custom_prompt`
- 交易计划模块生成：`description`、`current_rules`
- 风控规则生成：`description`、`current_rules`、`risk_style`
- 优化讨论：`user_question`、`selected_suggestions`、`conversation_history`

## 复杂请求优先使用 `--body-file`

对于交易计划、优化讨论、复杂批量请求，不建议把长 JSON 直接塞进命令行。

更稳妥的方式是：

1. 先把请求体写到一个 JSON 文件
2. 再用 `--body-file` 调用

示例：

```bash
python /workspace/projects/workspace/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /v1/trading-systems/evaluate-draft \
  --body-file /workspace/projects/workspace/skills/tradingagents-cn/examples/evaluate-draft.json
```

## 1. 登录与当前用户

登录接口保留在这里，仅用于理解和诊断，不是主业务流程模板：

- `POST /auth/login`

正式业务仍应优先走 `invoke_tradingagents_api.py`。

获取当前用户：

```bash
python /workspace/projects/workspace/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method GET \
  --path /auth/me
```

## 2. 单股分析

推荐接口：

- `POST /analysis/single`

已确认信息：

- 真实请求模型顶层字段：`symbol`、`parameters`、`openclaw_notify`
- 返回 `task_id` 时，应按异步任务处理

脚本调用模板：

```bash
python /workspace/projects/workspace/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /analysis/single \
  --body "{\"symbol\":\"000001\",\"parameters\":{\"market_type\":\"A股\",\"research_depth\":\"标准\",\"selected_analysts\":[\"fundamentals\",\"news\",\"market\"],\"include_sentiment\":true,\"include_risk\":true,\"language\":\"zh-CN\",\"quick_analysis_model\":\"qwen-turbo\",\"deep_analysis_model\":\"qwen-max\",\"engine\":\"v2\",\"custom_prompt\":\"重点看基本面质量、风险点，以及未来1到3个月的观察位\"},\"openclaw_notify\":{\"session_key\":\"hook:trading-task:single-000001\",\"channel\":\"telegram\",\"to\":\"123456789\",\"deliver\":true}}"
```

提交成功后至少要记录：

- `task_id`
- `status_url`
- `result_url`
- `notification_mode`

脚本输出会把服务端原始 JSON 放在外层返回的 `data` 字段里，因此常见提取路径是：

- `result["data"]["data"]["task_id"]`
- `result["data"]["data"]["status_url"]`
- `result["data"]["data"]["result_url"]`

## 3. 批量分析

推荐接口：

- `POST /analysis/batch`

脚本调用模板：

```bash
python /workspace/projects/workspace/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /analysis/batch \
  --body "{\"title\":\"核心候选股对比\",\"description\":\"比较多只候选股，输出排序和后续重点跟踪对象\",\"symbols\":[\"000001\",\"600519\",\"000858\"],\"parameters\":{\"market_type\":\"A股\",\"research_depth\":\"标准\",\"selected_analysts\":[\"fundamentals\",\"sector_analyst\",\"market\"],\"include_sentiment\":true,\"include_risk\":true,\"language\":\"zh-CN\",\"engine\":\"v2\",\"custom_prompt\":\"请输出排序结果，并说明最值得继续深挖的前2只股票\"},\"openclaw_notify\":{\"session_key\":\"hook:trading-task:batch-core\",\"channel\":\"telegram\",\"to\":\"123456789\",\"deliver\":true}}"
```

## 4. 分析任务状态与结果

常用官方接口：

- `GET /analysis/tasks/{task_id}/status`
- `GET /analysis/tasks/{task_id}/result`
- `GET /analysis/tasks/{task_id}/details`

推荐方式：

- 创建任务时附带 `openclaw_notify`
- 当前会话只汇报任务已提交
- 如需人工兜底，只做一次状态查询或结果读取

不要：

- 持续轮询
- 在当前会话等待到完成
- 因为缺少回调就切去未确认的同步路径

## 5. 持仓接口

### 查询持仓

```bash
python /workspace/projects/workspace/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method GET \
  --path /portfolio/positions
```

### 组合级持仓分析

```bash
python /workspace/projects/workspace/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /portfolio/analysis \
  --body "{\"include_paper\":true,\"research_depth\":\"标准\"}"
```

### 按代码做持仓分析

```bash
python /workspace/projects/workspace/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /portfolio/positions/analyze-by-code \
  --body "{\"code\":\"000001\",\"market\":\"CN\",\"research_depth\":\"标准\",\"include_add_position\":true,\"target_profit_pct\":20.0,\"total_capital\":300000,\"max_position_pct\":30.0,\"max_loss_pct\":10.0,\"risk_tolerance\":\"medium\",\"investment_horizon\":\"medium\",\"analysis_focus\":\"comprehensive\",\"position_type\":\"real\",\"use_stock_analysis\":true}"
```

如果部署返回任务标识，只记录并退出等待。

## 6. 交易复盘接口

### 单笔或整笔复盘

```bash
python /workspace/projects/workspace/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /review/trade \
  --body "{\"trade_ids\":[\"trade_id_1\",\"trade_id_2\"],\"review_type\":\"complete_trade\",\"source\":\"paper\",\"use_workflow\":true}"
```

### 周期复盘

```bash
python /workspace/projects/workspace/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /review/periodic \
  --body "{\"period_type\":\"month\",\"start_date\":\"2026-04-01\",\"end_date\":\"2026-04-30\",\"source\":\"paper\"}"
```

如果部署返回正式结果，直接解释。
如果返回任务标识或需后续结果读取，则按任务闭环处理。

## 7. 交易计划接口

### 风控规则生成

```bash
python /workspace/projects/workspace/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /v1/trading-systems/generate-risk-rules \
  --body "{\"style\":\"medium_term\",\"risk_profile\":\"balanced\",\"risk_style\":\"balanced\",\"description\":\"偏趋势交易，希望回撤受控，同时保留一部分趋势利润\",\"current_rules\":{\"stop_loss\":{\"type\":\"percentage\",\"percentage\":0.08}}}"
```

### 模块规则生成

```bash
python /workspace/projects/workspace/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /v1/trading-systems/generate-module-rules \
  --body "{\"module\":\"timing\",\"style\":\"medium_term\",\"risk_profile\":\"balanced\",\"description\":\"希望做顺势突破，减少追高和假突破\",\"current_rules\":{\"market_condition\":{\"rule\":\"大盘环境偏强\",\"description\":\"指数与情绪同步修复\"}}}"
```

### 评估草稿计划

```bash
python /workspace/projects/workspace/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /v1/trading-systems/evaluate-draft \
  --body-file /workspace/projects/workspace/skills/tradingagents-cn/examples/evaluate-draft.json
```

### 优化讨论

```bash
python /workspace/projects/workspace/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /v1/trading-systems/optimize-discussion \
  --body-file /workspace/projects/workspace/skills/tradingagents-cn/examples/optimize-discussion.json
```

## 8. 自选股接口

### 查询分组

```bash
python /workspace/projects/workspace/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method GET \
  --path /watchlist-groups
```

已确认路径：

- `GET/PUT/DELETE /watchlist-groups/{group_id}`
- `GET/POST/DELETE /watchlist-groups/{group_id}/stocks`
- `POST /watchlist-groups/{group_id}/stocks/move`

## 9. 建议的调用顺序

### 分析任务

1. 确认 `TRADINGAGENTS_BASE_URL`
2. 直接走正式业务接口
3. 如果返回 `task_id`，记录关联信息并等待回调
4. 需要时再单次读取任务结果

### 交易计划任务

1. 先走规则生成接口
2. 草稿基本成形后，再走正式评估接口
3. 需要继续改时走优化讨论接口
4. 需要保存时再创建交易计划

### 持仓和复盘任务

1. 先判断是查询还是分析
2. 查询走查询接口
3. 分析走正式分析/复盘接口
4. 若返回任务标识，则按任务闭环处理
