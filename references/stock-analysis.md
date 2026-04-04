# 股票分析

这份参考用于单股分析、批量分析，以及把自然语言目标翻译成 TradingAgentsCN 的真实分析参数。

## 适用接口

- 单股分析：`POST /analysis/single`
- 批量分析：`POST /analysis/batch`
- 任务状态：`GET /analysis/tasks/{task_id}/status`
- 任务结果：`GET /analysis/tasks/{task_id}/result`

## 何时优先使用 TradingAgentsCN

以下情况优先使用 TradingAgentsCN，而不是通用行情或 Tushare skill：
- 用户希望直接调用项目已有分析接口得到结果
- 用户希望复用现成分析任务队列，而不是外部自己拼提示词
- 用户希望后续继续衔接持仓分析、交易计划、复盘等系统内链路

## 真实请求结构

### 单股分析

顶层字段：
- `symbol`
- `parameters`

说明：
- `symbol` 是主字段，描述为 `6位股票代码`
- `stock_code` 仍存在，但模型中已标记为废弃字段，不要优先使用

### 批量分析

顶层字段：
- `title`
- `description`
- `symbols`
- `parameters`

说明：
- `title` 是必填
- `symbols` 最多 `10` 个
- `stock_codes` 也存在，但已废弃

## `parameters` 真实字段

`SingleAnalysisRequest` 和 `BatchAnalysisRequest` 共用同一套 `AnalysisParameters`：

- `market_type`
  默认值：`A股`
- `analysis_date`
  可选，时间格式
- `research_depth`
  默认值：`标准`
- `selected_analysts`
  字符串数组
- `custom_prompt`
  可选字符串
- `include_sentiment`
  默认值：`true`
- `include_risk`
  默认值：`true`
- `language`
  默认值：`zh-CN`
- `quick_analysis_model`
  默认值：`qwen-turbo`
- `deep_analysis_model`
  默认值：`qwen-max`
- `engine`
  可选值：`legacy`、`unified`、`v2`
  默认值：`v2`
- `workflow_id`
  可选，仅 `unified` 引擎有效

## 分析深度含义

项目模型里给了明确说明：

- `快速`
  1级，约 2 到 4 分钟
- `基础`
  2级，约 4 到 6 分钟
- `标准`
  3级，约 6 到 10 分钟，默认推荐
- `深度`
  4级，约 10 到 15 分钟
- `全面`
  5级，约 15 到 25 分钟

## 引擎选择建议

- 默认优先使用 `v2`
- 只有在明确知道实例配置时才切到 `unified`
- `legacy` 只用于兼容老链路

## 自然语言到参数的映射

不要逼用户直接说内部字段名。应把自然语言目标自动映射成参数：

- “先快速看一眼”
  `research_depth=快速`
- “做一版标准分析”
  `research_depth=标准`
- “尽量深一点”
  `research_depth=深度` 或 `全面`
- “只看技术面”
  重点放进 `custom_prompt`
- “重点看情绪和风险”
  `include_sentiment=true`、`include_risk=true`
- “我要中文结果”
  `language=zh-CN`

## 可以传入分析偏好的字段

如果用户对分析风格、关注点或输出侧重点有要求，优先把偏好落到真实请求字段里，而不是只写在说明文字里。

常用字段：

- `custom_prompt`
  适合放“重点看什么”“不要看什么”“输出更偏哪种视角”
- `selected_analysts`
  适合控制参与分析的分析师集合
- `research_depth`
  适合控制分析深度和等待时长
- `include_sentiment`
  适合控制是否纳入情绪面
- `include_risk`
  适合控制是否强调风险面

示例偏好：

- “重点看基本面质量和未来 1 到 3 个月观察位”
  放进 `custom_prompt`
- “更保守一些，风险提示多写一点”
  保留 `include_risk=true`，并在 `custom_prompt` 中强调风险优先
- “只做快速初筛”
  `research_depth=快速`

## 输出重点

### 单股分析输出应重点总结

- 核心观点
- 看多与看空理由
- 主要风险
- 建议动作或下一步检查点

### 批量分析输出应重点总结

- 排名结果
- 重点候选股
- 淘汰理由
- 后续建议

## 调用约束

- 单股分析至少要提供有效 `symbol`
- 批量分析至少要提供 `title`
- 批量分析的 `symbols` 上限是 `10`
- 如果只是试探接口是否在线，不要立刻发起重型任务，先用最小请求观察校验反馈
