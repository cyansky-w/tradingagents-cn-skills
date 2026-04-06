# 持仓与复盘

这份参考回答两个关键问题：

1. 持仓分析和交易复盘能不能让 AI 真正分析
2. 这些能力分别该怎么调用，何时算真正完成

结论先说：

- 不是只有查记录
- 这两个模块都确实接了 AI 分析逻辑
- 查询接口和分析接口必须分开看

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

核心规则：

- 如果用户只是想看现状，走查询接口
- 如果用户要“分析怎么办”“复盘哪里错了”，必须走正式分析/复盘接口
- 不要拿查询结果冒充分析完成

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

输入规范：

- `code` 优先使用真实股票代码
- 用户给 `002837.SZ` 时，先规范成主代码，再映射市场
- 用户只给中文名且无法可靠映射时，询问一次代码

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
- `review_type`
- `code`
- `source`
- `trading_system_id`
- `use_workflow`

### 周期复盘

接口：

- `POST /review/periodic`

真实字段：

- `period_type`
- `start_date`
- `end_date`
- `source`

## 标准流程

### 持仓分析

1. 先判断用户要查询还是要分析
2. 查询类需求先走查询接口
3. 分析类需求走正式分析接口
4. 如果返回最终结构化结果，直接按结果解释
5. 如果返回 `task_id`、`analysis_id` 或需要后续读取详情的正式标识：
   - 当前只汇报“任务已创建”
   - 记录正式标识
   - 按部署支持的官方通知或单次兜底读取拿终态结果

### 交易复盘

1. 确认是单笔/整笔复盘还是周期复盘
2. 规范化关键输入，如 `trade_ids`、日期区间、`trading_system_id`
3. 调用正式复盘接口
4. 如果直接返回复盘结果，则可直接总结
5. 如果返回任务标识或需要后续读取结果，则按任务闭环处理，不等待

## 完成判定

对持仓分析和交易复盘：

- 查询接口成功 != 分析完成
- 正式分析请求成功 != 分析完成
- 只有拿到正式分析/复盘结果后，才算真正完成

## 输出重点

### 持仓分析输出应重点覆盖

- 当前仓位状态
- 集中度与相关风险
- 最该减仓、继续持有、观察或加仓的标的
- 关键阈值

### 交易复盘输出应重点覆盖

- 发生了什么
- 进出场是否合理
- 仓位控制是否合理
- 情绪和纪律问题
- 如果有交易计划，是否偏离了计划
- 下一次如何改
