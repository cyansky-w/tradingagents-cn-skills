# 接口调用模板

这份参考把当前已经确认的 TradingAgentsCN 调用方式整理成可直接照抄的模板。

当前推荐实例：
- `TRADINGAGENTS_BASE_URL=http://124.222.83.243/api`

当前默认账号：
- 用户名：`admin`
- 密码：`admin123`

## 推荐调用方式

如果脚本可用，优先不要让 AI 自己手写登录和请求头。

### 先确保 Token

```bash
python docs/skills/tradingagents-cn/scripts/ensure_tradingagents_token.py
```

### 再统一通过脚本发请求

```bash
python docs/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method GET \
  --path /auth/me
```

AI 以后主要只需要决定：
- `--path` 用哪个接口
- `--method` 用什么方法
- `--body` 或 `--body-file` 传什么业务参数

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
python docs/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /v1/trading-systems/evaluate-draft \
  --body-file docs/skills/tradingagents-cn/examples/evaluate-draft.json
```

```bash
python docs/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /v1/trading-systems/optimize-discussion \
  --body-file docs/skills/tradingagents-cn/examples/optimize-discussion.json
```

## 1. 登录

虽然脚本会自动处理登录，但为了让 AI 知道底层逻辑，仍保留真实登录接口：

- `POST /auth/login`

登录成功后，返回中会有：
- `data.access_token`
- `data.refresh_token`

实测返回结构：

```json
{
  "success": true,
  "data": {
    "access_token": "...",
    "refresh_token": "...",
    "expires_in": 0,
    "user": {}
  },
  "message": "登录成功"
}
```

## 2. 获取当前用户信息

### 脚本调用

```bash
python docs/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method GET \
  --path /auth/me
```

### 实测返回的 `data` 字段

```json
[
  "id",
  "username",
  "email",
  "name",
  "is_admin",
  "roles",
  "preferences"
]
```

## 3. 单股分析

### 推荐接口

- `POST /analysis/single`

### 已确认信息

- 这条接口已实测存在
- 空 JSON 会返回股票代码格式错误，说明会优先校验股票代码
- 真实请求模型：
  - 顶层字段：`symbol`、`parameters`
  - `parameters` 字段：
    - `market_type`
    - `analysis_date`
    - `research_depth`
    - `selected_analysts`
    - `custom_prompt`
    - `include_sentiment`
    - `include_risk`
    - `language`
    - `quick_analysis_model`
    - `deep_analysis_model`
    - `engine`
    - `workflow_id`

### 脚本调用模板

```bash
python docs/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /analysis/single \
  --body "{\"symbol\":\"000001\",\"parameters\":{\"market_type\":\"A股\",\"research_depth\":\"标准\",\"include_sentiment\":true,\"include_risk\":true,\"language\":\"zh-CN\",\"quick_analysis_model\":\"qwen-turbo\",\"deep_analysis_model\":\"qwen-max\",\"engine\":\"v2\",\"custom_prompt\":\"重点看基本面质量、风险点，以及未来1到3个月的观察位\"}}"
```

## 4. 批量分析

### 推荐接口

- `POST /analysis/batch`

### 已确认信息

- 空 JSON 返回 `422`
- 至少要求字段：`title`
- 真实请求模型：
  - 顶层字段：`title`、`description`、`symbols`、`parameters`
  - `symbols` 最多 `10` 个

### 脚本调用模板

```bash
python docs/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /analysis/batch \
  --body "{\"title\":\"核心候选股对比\",\"description\":\"比较多只候选股，输出排序和后续重点跟踪对象\",\"symbols\":[\"000001\",\"600519\",\"000858\"],\"parameters\":{\"market_type\":\"A股\",\"research_depth\":\"标准\",\"include_sentiment\":true,\"include_risk\":true,\"language\":\"zh-CN\",\"engine\":\"v2\",\"custom_prompt\":\"请输出排序结果，并说明最值得继续深挖的前2只股票\"}}"
```

## 5. 分析任务状态与结果

### 常用接口

- `GET /analysis/tasks/{task_id}/status`
- `GET /analysis/tasks/{task_id}/result`
- `GET /analysis/tasks/{task_id}/details`

### 推荐轮询频率

不要在创建任务后立刻连续请求状态接口。

默认节奏：
- 第一次检查放在 `30` 秒后
- 后续默认每 `30` 到 `60` 秒一次
- 不要快于每 `30` 秒一次

按分析深度建议：
- `快速`、`基础`
  `30` 秒后首次检查，之后每 `30` 秒一次
- `标准`
  `30` 秒后首次检查，之后每 `30` 到 `45` 秒一次
- `深度`、`全面`
  `45` 秒后首次检查，之后每 `45` 到 `60` 秒一次

停止规则：
- `completed` 就立刻取结果
- `failed` / `error` 就立刻停止
- 超过最长等待后，不要死等，向用户说明任务仍在后台运行并返回 `task_id`

建议最长等待：
- `快速`、`基础`：`6` 分钟
- `标准`：`12` 分钟
- `深度`：`18` 分钟
- `全面`：`30` 分钟

### 脚本调用模板

```bash
python docs/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method GET \
  --path /analysis/tasks/TASK_ID/status
```

更推荐：

```bash
python docs/skills/tradingagents-cn/scripts/wait_for_task.py \
  --task-id TASK_ID \
  --depth 标准
```

### 轮询示例

下面是一个适合 `标准` 分析的等待节奏：

1. 创建任务
2. 用 `wait_for_task.py` 等待
3. 脚本会在 `30` 秒后首次检查状态
4. 如果还在 `pending` 或 `running`，脚本会再每 `30` 到 `45` 秒查一次
5. 一旦 `completed`，脚本会自动再取 `/analysis/tasks/{task_id}/result`
6. 一旦 `failed`，脚本会停止并返回错误信息

## 6. 持仓接口

### 已实测可用

- `GET /portfolio/positions`

```bash
python docs/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method GET \
  --path /portfolio/positions
```

### 组合级持仓分析

- `POST /portfolio/analysis`
- 真实字段：
  - `include_paper`
  - `research_depth`

```bash
python docs/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /portfolio/analysis \
  --body "{\"include_paper\":true,\"research_depth\":\"标准\"}"
```

### 按代码做持仓分析

- `POST /portfolio/positions/analyze-by-code`
- 空 JSON 返回 `422`
- 至少要求字段：`code`
- 真实请求字段：
  - `code`
  - `market`
  - `research_depth`
  - `include_add_position`
  - `target_profit_pct`
  - `total_capital`
  - `max_position_pct`
  - `max_loss_pct`
  - `risk_tolerance`
  - `investment_horizon`
  - `analysis_focus`
  - `position_type`
  - `use_stock_analysis`

```bash
python docs/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /portfolio/positions/analyze-by-code \
  --body "{\"code\":\"000001\",\"market\":\"CN\",\"research_depth\":\"标准\",\"include_add_position\":true,\"target_profit_pct\":20.0,\"total_capital\":300000,\"max_position_pct\":30.0,\"max_loss_pct\":10.0,\"risk_tolerance\":\"medium\",\"investment_horizon\":\"medium\",\"analysis_focus\":\"comprehensive\",\"position_type\":\"real\",\"use_stock_analysis\":true}"
```

## 7. 交易复盘接口

### 单笔或整笔复盘

- `POST /review/trade`
- 空 JSON 返回 `422`
- 至少要求字段：`trade_ids`
- 真实字段：
  - `trade_ids`
  - `review_type`
  - `code`
  - `source`
  - `trading_system_id`
  - `use_workflow`

```bash
python docs/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /review/trade \
  --body "{\"trade_ids\":[\"trade_id_1\",\"trade_id_2\"],\"review_type\":\"complete_trade\",\"source\":\"paper\",\"use_workflow\":true}"
```

### 周期复盘

- `POST /review/periodic`
- 空 JSON 返回 `422`
- 至少要求字段：`start_date`、`end_date`
- 真实字段：
  - `period_type`
  - `start_date`
  - `end_date`
  - `source`

```bash
python docs/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /review/periodic \
  --body "{\"period_type\":\"month\",\"start_date\":\"2026-04-01\",\"end_date\":\"2026-04-30\",\"source\":\"paper\"}"
```

## 8. 自选股接口

### 已实测可用

- `GET /watchlist-groups`

```bash
python docs/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method GET \
  --path /watchlist-groups
```

### 已确认路径

- `GET/PUT/DELETE /watchlist-groups/{group_id}`
- `GET/POST/DELETE /watchlist-groups/{group_id}/stocks`
- `POST /watchlist-groups/{group_id}/stocks/move`

## 9. 交易计划接口

### 已实测可用

- `GET /v1/trading-systems/active`

```bash
python docs/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method GET \
  --path /v1/trading-systems/active
```

### 风控规则生成

- `POST /v1/trading-systems/generate-risk-rules`
- 空 JSON 也会成功返回默认风控规则
- 真实字段：
  - `style`
  - `risk_profile`
  - `risk_style`
  - `description`
  - `current_rules`

```bash
python docs/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /v1/trading-systems/generate-risk-rules \
  --body "{\"style\":\"medium_term\",\"risk_profile\":\"balanced\",\"risk_style\":\"balanced\",\"description\":\"偏趋势交易，希望回撤受控，同时保留一部分趋势利润\",\"current_rules\":{\"stop_loss\":{\"type\":\"percentage\",\"percentage\":0.08}}}"
```

### 模块规则生成

- `POST /v1/trading-systems/generate-module-rules`
- 空 JSON 返回 `422`
- 至少要求字段：`module`
- 已确认支持的 `module`：
  - `stock_selection`
  - `timing`
  - `risk_management`

```bash
python docs/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /v1/trading-systems/generate-module-rules \
  --body "{\"module\":\"timing\",\"style\":\"medium_term\",\"risk_profile\":\"balanced\",\"description\":\"希望做顺势突破，减少追高和假突破\",\"current_rules\":{\"market_condition\":{\"rule\":\"大盘环境偏强\",\"description\":\"指数与情绪同步修复\"}}}"
```

### 评估草稿计划

- `POST /v1/trading-systems/evaluate-draft`
- 请求体就是一份 `TradingSystemCreate`

推荐优先使用 `--body-file`：

```bash
python docs/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /v1/trading-systems/evaluate-draft \
  --body-file docs/skills/tradingagents-cn/examples/evaluate-draft.json
```

```bash
python docs/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /v1/trading-systems/evaluate-draft \
  --body "{\"name\":\"趋势波段系统\",\"description\":\"中线趋势跟随，优先做强势行业龙头\",\"style\":\"medium_term\",\"risk_profile\":\"balanced\",\"stock_selection\":{\"must_have\":[{\"rule\":\"最近60日相对强度靠前\",\"description\":\"优先选强势股\"}],\"exclude\":[{\"rule\":\"业绩爆雷或财务异常\",\"description\":\"避免基本面大雷\"}],\"bonus\":[{\"rule\":\"行业景气上行\",\"description\":\"提高成功率\"}]},\"timing\":{\"market_condition\":{\"rule\":\"大盘环境偏强\",\"description\":\"指数和情绪同步改善\"},\"entry_signals\":[{\"signal\":\"突破\",\"condition\":\"放量突破平台高点\"}],\"confirmation\":[{\"rule\":\"次日不跌回平台\",\"description\":\"避免假突破\"}]},\"risk_management\":{\"stop_loss\":{\"type\":\"percentage\",\"percentage\":0.08},\"take_profit\":{\"type\":\"trailing\",\"trailing_pullback_pct\":0.08,\"activation_profit_pct\":0.12,\"reference\":\"highest_price\"}}}"
```

### 优化讨论

- `POST /v1/trading-systems/optimize-discussion`

推荐优先使用 `--body-file`：

```bash
python docs/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /v1/trading-systems/optimize-discussion \
  --body-file docs/skills/tradingagents-cn/examples/optimize-discussion.json
```

```bash
python docs/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /v1/trading-systems/optimize-discussion \
  --body "{\"trading_plan_data\":{\"name\":\"趋势波段系统\",\"style\":\"medium_term\",\"risk_profile\":\"balanced\",\"description\":\"中线趋势跟随\"},\"evaluation_result\":{\"overall_score\":72,\"grade\":\"B\",\"suggestions\":[\"补充明确的止盈规则\",\"加强选股排除条件\"]},\"user_question\":\"先告诉我最值得优先优化的点，并给出可以直接应用的修改候选\",\"selected_suggestions\":[\"补充明确的止盈规则\"],\"conversation_history\":[{\"role\":\"user\",\"content\":\"我想把计划做得更可执行\"}]}"
```

### 创建交易计划

- `POST /v1/trading-systems`

```bash
python docs/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /v1/trading-systems \
  --body "{\"name\":\"趋势波段系统\",\"description\":\"中线趋势跟随，优先做强势行业龙头\",\"style\":\"medium_term\",\"risk_profile\":\"balanced\"}"
```

## 10. 建议的调用顺序

### 分析任务

1. 先跑 `ensure_tradingagents_token.py`
2. 调分析接口
3. 轮询任务状态
4. 读取任务结果

### 交易计划任务

1. 先跑 `ensure_tradingagents_token.py`
2. 如果是从零开始或计划还很空，优先走规则生成接口
3. 优先补 `stock_selection`、`timing`、`risk_management`
4. 再补 `position`、`holding`、`review`、`discipline`
5. 草稿基本成形后，再走 `/v1/trading-systems/evaluate-draft`
6. 需要继续改时走优化讨论接口
7. 需要保存时再创建交易计划

推荐记住这条规则：

- `generate-module-rules` / `generate-risk-rules` 用来生成计划内容
- `evaluate-draft` / `/{system_id}/evaluate` 用来评估已有计划
- `optimize-discussion` 用来基于评估结果继续优化

### 持仓和复盘任务

1. 先跑 `ensure_tradingagents_token.py`
2. 先查现状接口
3. 再决定是否发起分析或复盘任务
