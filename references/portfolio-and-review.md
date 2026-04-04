# 持仓与复盘

这份参考回答两个关键问题：

1. 持仓分析和交易复盘能不能让 AI 真正分析
2. 这些能力分别该怎么调用

结论先说：
- 不是只有查记录
- 这两个模块都确实接了 AI 分析逻辑

## 为什么能确认它不是纯查询

从 `TradingAgentsCN` 的服务层和工作流模板可以确认：

### 持仓分析

`PortfolioService` 里存在这些方法：
- `_call_ai_analysis`
- `_call_position_ai_analysis`
- `_call_position_ai_analysis_v2`
- `_call_position_ai_analysis_workflow`
- `_build_position_analysis_prompt_v2`

同时项目里还有：
- `core.workflow.templates.position_analysis_workflow`
- `core.workflow.templates.position_analysis_workflow_v2`
- `core.agents.adapters.position.*`

这说明持仓模块不是简单返回持仓列表，而是会把持仓快照、风险参数、缓存过的单股分析结果等信息送进专门的分析链路。

### 交易复盘

`TradeReviewService` 里存在这些方法：
- `_call_ai_trade_review`
- `_call_ai_periodic_review`
- `_call_workflow_trade_review`
- `_build_trade_review_prompt`
- `_format_trading_plan_for_workflow`

同时项目里还有：
- `core.workflow.templates.trade_review_workflow`
- `core.workflow.templates.trade_review_workflow_v2`
- `core.agents.adapters.review.*`

这说明交易复盘也不是只查成交记录，而是会结合交易信息、市场快照、可能的交易计划规则，生成 AI 复盘结果。

## 哪些接口是“查数据”，哪些接口是“做分析”

### 主要是查询类

- `GET /portfolio/positions`
- `GET /portfolio/statistics`
- `GET /review/statistics`
- `GET /review/reviewable-trades`
- `GET /review/trade/history`
- `GET /review/periodic/history`

### 会触发分析或复盘类

- `POST /portfolio/analysis`
- `POST /portfolio/positions/{position_id}/analysis`
- `POST /portfolio/positions/analyze-by-code`
- `POST /review/trade`
- `POST /review/periodic`

## 持仓分析

适用于：
- “我的持仓结构怎么样”
- “这只持仓股现在该怎么处理”
- “我能不能加仓”
- “整个组合的风险和集中度如何”

### 组合级分析

接口：
- `POST /portfolio/analysis`

真实请求模型可确认字段：
- `include_paper`
  默认 `true`
- `research_depth`
  默认 `标准`

### 按股票代码做汇总持仓分析

接口：
- `POST /portfolio/positions/analyze-by-code`

真实字段：
- `code`
  必填
- `market`
  默认 `CN`
- `research_depth`
  默认 `标准`
- `include_add_position`
  默认 `true`
- `target_profit_pct`
  默认 `20.0`
- `total_capital`
- `max_position_pct`
  默认 `30.0`
- `max_loss_pct`
  默认 `10.0`
- `risk_tolerance`
  默认 `medium`
- `investment_horizon`
  默认 `medium`
- `analysis_focus`
  默认 `comprehensive`
- `position_type`
  默认 `real`
- `use_stock_analysis`
  默认 `true`

这个接口的服务逻辑会：
1. 查询该股票的全部持仓记录
2. 汇总成一个持仓快照
3. 优先查缓存的单股分析报告
4. 再进入持仓专用 AI 分析

所以它很适合给 AI 做“这只票我现在怎么操作”的判断。

## 交易复盘

适用于：
- “帮我复盘这笔交易”
- “这次为什么做错了”
- “帮我做周复盘/月复盘”
- “这笔交易有没有遵守我的交易计划”

### 单笔或整笔交易复盘

接口：
- `POST /review/trade`

真实字段：
- `trade_ids`
  必填
- `review_type`
  默认 `complete_trade`
- `code`
- `source`
  默认 `paper`
- `trading_system_id`
- `use_workflow`

从服务代码可以看到：
- 会先拉交易记录
- 会构造 `trade_info`
- 会拉市场快照
- 如果传了 `trading_system_id`，还会把交易计划拿进复盘链路里
- 最终调用 `_call_ai_trade_review` 或 `_call_workflow_trade_review`

这意味着它可以做“交易是否遵守计划”的分析，而不只是事后描述。

### 周期复盘

接口：
- `POST /review/periodic`

真实字段：
- `period_type`
  默认 `month`
- `start_date`
  必填
- `end_date`
  必填
- `source`
  默认 `paper`

服务代码还能确认：
- 它支持从 `paper` 或 `position` 两类数据源取数据
- 会先统计周期表现
- 再调用 `_call_ai_periodic_review`

## 输出重点

### 持仓分析输出应重点覆盖

- 当前仓位状态
- 集中度与相关风险
- 最该减仓、继续持有、观察或加仓的标的
- 关键阈值
  比如止盈、止损、最大仓位

### 交易复盘输出应重点覆盖

- 发生了什么
- 进出场是否合理
- 仓位控制是否合理
- 情绪和纪律问题
- 如果有交易计划，是否偏离了计划
- 下一次如何改

## 给模型的使用建议

- 如果用户只是问“我现在持有哪些仓位”，先查数据
- 如果用户问“这些仓位怎么办”，再走分析接口
- 如果用户问“这笔交易错在哪”，直接走复盘接口，不要只返回成交记录
- 如果用户提到“按我的交易计划来看”，优先把 `trading_system_id` 带进复盘请求
