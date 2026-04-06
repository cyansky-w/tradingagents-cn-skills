# 股票分析

这份参考用于单股分析、批量分析，以及把自然语言目标翻译成 TradingAgentsCN 的真实分析参数。

核心规则：

- 正式入口只有文档确认的股票分析接口
- 单股和批量分析默认按任务型接口处理
- 一旦返回 `task_id`，AI 只记录并退出等待，不持续轮询

## 适用接口

- 单股分析：`POST /analysis/single`
- 批量分析：`POST /analysis/batch`
- 任务状态：`GET /analysis/tasks/{task_id}/status`
- 任务结果：`GET /analysis/tasks/{task_id}/result`

## 禁止事项

- 不要猜测同步 `/analyze`、`/analysis/run`、`/stock/analyze` 之类路径
- 不要把轻量探测、参数校验响应或 `200` 状态码表述为“分析完成”
- 不要在当前 AI 会话中持续等待任务结果
- 不要因为暂时拿不到回调，就自动改走未确认的同步替代路径

## 何时优先使用 TradingAgentsCN

以下情况优先使用 TradingAgentsCN，而不是通用行情或 Tushare skill：

- 用户希望直接调用项目已有分析接口得到结果
- 用户希望复用现成分析任务队列，而不是外部自己拼提示词
- 用户希望后续继续衔接持仓分析、交易计划、复盘等系统内链路

## 输入规范

### 单股分析

顶层字段：

- `symbol`
- `parameters`
- `openclaw_notify`

说明：

- `symbol` 是主字段，描述为 `6位股票代码`
- `stock_code` 仍存在，但模型中已标记为废弃字段，不要优先使用

用户输入规范化规则：

- `000001` -> 直接作为 `symbol`
- `002837.SZ` -> 规范成 `002837`，并把市场提示保留到 `market_type`
- 中文股票名 -> 若上下文不能可靠映射成唯一代码，只询问一次真实代码

### 批量分析

顶层字段：

- `title`
- `description`
- `symbols`
- `parameters`
- `openclaw_notify`

说明：

- `title` 是必填
- `symbols` 最多 `10` 个
- `stock_codes` 也存在，但已废弃

## `parameters` 真实字段

`SingleAnalysisRequest` 和 `BatchAnalysisRequest` 共用同一套 `AnalysisParameters`：

- `market_type`
  默认值：`A股`
- `analysis_date`
  可选
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

## `selected_analysts` 已确认可用枚举值

- `market`
- `fundamentals`
- `news`
- `sector_analyst`
- `index_analyst`
- `social`

常见映射方式：

- “看大盘环境” -> `market`
- “看基本面” -> `fundamentals`
- “看新闻催化” -> `news`
- “看行业视角” -> `sector_analyst`
- “看指数和市场位置” -> `index_analyst`
- “看社交舆情” -> `social`

## 分析深度含义

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

## 单股分析标准流程

1. 确认正式入口是 `POST /analysis/single`
2. 规范化 `symbol`
3. 组装 `parameters`
4. 提交请求时附带 `openclaw_notify`
5. 记录：
   - `task_id`
   - `status_url`
   - `result_url`
   - `notification_mode`
6. 当前会话只汇报“任务已提交”
7. 等待 webhook 或等价官方结果通知
8. 收到正式结果后再输出：
   - 核心观点
   - 看多与看空理由
   - 主要风险
   - 建议动作或下一步检查点

完成判定：

- 必须拿到 `task_id`
- 必须拿到正式结果
- 仅提交成功不算完成

## 批量分析标准流程

1. 确认正式入口是 `POST /analysis/batch`
2. 规范化 `title`、`symbols` 和 `parameters`
3. 附带 `openclaw_notify`
4. 记录任务关联信息
5. 当前会话不等待
6. 收到正式结果后再输出：
   - 排名结果
   - 重点候选股
   - 淘汰理由
   - 后续建议

## 调用约束

- 单股分析至少要提供有效 `symbol`
- 批量分析至少要提供 `title`
- 批量分析的 `symbols` 上限是 `10`
- 异步任务优先使用 `openclaw_notify`
- 如果只是试探接口是否在线，不要立刻发起重型任务，先用最小正式请求观察校验反馈
