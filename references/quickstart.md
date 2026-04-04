# 最小使用手册

这份文件给第一次使用 `tradingagents-cn` skill 的模型看。

目标不是解释所有细节，而是让模型第一次就知道：
- 先做什么
- 什么时候调用哪个接口
- 遇到什么情况该停下来

## 一句话理解这个系统

TradingAgentsCN 是一个“先登录，再走业务接口”的交易分析系统。

不要把它当成普通行情源。
它更像一个已经封装好了分析、持仓、复盘、交易计划流程的后端服务。

## 第一次使用时的最短流程

1. 先读环境变量
2. 先执行一次 `scripts/ensure_tradingagents_token.py`
3. 再用 `scripts/invoke_tradingagents_api.py` 发业务请求
4. 根据用户意图选择业务模块
5. 如果返回 `task_id`，优先用 `scripts/wait_for_task.py`
6. 只把用户需要的结论返回给用户

## 默认配置

如果用户没有另行说明，优先按下面的默认配置尝试：

- `TRADINGAGENTS_BASE_URL=http://124.222.83.243/api`
- `TRADINGAGENTS_USERNAME=admin`
- `TRADINGAGENTS_PASSWORD=admin123`

如果环境变量里已经有值，用环境变量覆盖这些默认值。

## 必须先检查的环境变量

- `TRADINGAGENTS_BASE_URL`
- `TRADINGAGENTS_USERNAME`
- `TRADINGAGENTS_PASSWORD`
- `TRADINGAGENTS_BEARER_TOKEN`

优先级：
1. 当前请求显式给出的值
2. 已存在的 Bearer Token
3. 环境变量
4. 再向用户追问

## 推荐脚本入口

优先不要让 AI 自己每次都手写登录逻辑。

先执行：

```bash
python docs/skills/tradingagents-cn/scripts/ensure_tradingagents_token.py
```

这个脚本会自动处理：
- 环境变量中的 Bearer Token
- 本地缓存的 Token
- 没有有效 Token 时自动登录
- 用 `/auth/me` 校验 Token 是否仍然可用

然后业务请求统一走：

```bash
python docs/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py --method GET --path /auth/me
```

这个脚本会自动处理：
- 先拿可用 Token
- 再发请求
- 遇到 `401` 自动重新登录并重试一次

如果接口返回 `task_id`，优先再用：

```bash
python docs/skills/tradingagents-cn/scripts/wait_for_task.py \
  --task-id TASK_ID \
  --depth 标准
```

这个脚本会自动处理：
- 按 skill 约定的低频轮询节奏等待
- `completed` 时自动再取结果
- `failed` 时立刻停止
- 超时后返回“仍在后台运行”的提示

推荐记忆方式很简单：
- 登录：`ensure_tradingagents_token.py`
- 发请求：`invoke_tradingagents_api.py`
- 等结果：`wait_for_task.py`

如果请求体比较长，优先不要在命令行里直接写 `--body`，而是改用：

```bash
python docs/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py \
  --method POST \
  --path /v1/trading-systems/evaluate-draft \
  --body-file docs/skills/tradingagents-cn/examples/evaluate-draft.json
```

## 意图到模块的最短路由

### 用户要分析股票

常见说法：
- “分析一下 600519”
- “比较这几只股票”
- “给我排个优先级”

优先走：
- 单股：`POST /analysis/single`
- 批量：`POST /analysis/batch`

再读：
- `references/stock-analysis.md`
- `references/call-templates.md`

### 用户要做交易计划

常见说法：
- “帮我定一套交易计划”
- “这套计划合理吗”
- “帮我优化现有计划”

优先判断是哪一段：
- 生成
- 评估
- 优化

再读：
- `references/trading-plan.md`
- `references/call-templates.md`

### 用户要做持仓分析

常见说法：
- “我的仓位合理吗”
- “这只持仓股怎么办”
- “我能不能加仓”

优先走：
- 组合级：`POST /portfolio/analysis`
- 单票汇总持仓：`POST /portfolio/positions/analyze-by-code`

再读：
- `references/portfolio-and-review.md`
- `references/call-templates.md`

### 用户要做交易复盘

常见说法：
- “复盘这笔交易”
- “复盘这个月”
- “这笔交易有没有按计划执行”

优先走：
- 单笔或整笔：`POST /review/trade`
- 周期复盘：`POST /review/periodic`

再读：
- `references/portfolio-and-review.md`
- `references/call-templates.md`

### 用户要管理自选股

常见说法：
- “建一个自选组”
- “把这几只票加入观察”
- “把股票从 A 组移到 B 组”

优先走：
- `GET/POST /watchlist-groups`
- `GET/POST/DELETE /watchlist-groups/{group_id}/stocks`

再读：
- `references/watchlist.md`
- `references/api-map.md`

## 参数处理原则

不要要求用户先学内部字段名。

应该先把用户自然语言转成系统参数，再发请求。

例如：
- “先快速看一眼”
  优先映射成较浅的 `research_depth`
- “偏保守”
  优先映射成更稳健的风控或风险参数
- “按我的交易计划复盘”
  复盘时优先补 `trading_system_id`

## 轮询等待规则

对会返回 `task_id` 的异步任务，不要高频轮询。

默认规则：
- 提交任务后不要立刻查状态
- 第一次状态检查放在 `30` 秒后
- 后续默认每 `30` 到 `60` 秒轮询一次
- 不要低于每 `30` 秒一次

按分析深度可进一步调整：
- `快速`、`基础`
  首次检查 `30` 秒后，后续每 `30` 秒一次
- `标准`
  首次检查 `30` 秒后，后续每 `30` 到 `45` 秒一次
- `深度`、`全面`
  首次检查 `45` 秒后，后续每 `45` 到 `60` 秒一次

停止条件：
- 如果状态变成 `completed`，立刻取结果
- 如果状态变成 `failed` 或 `error`，立刻停止，不再继续轮询
- 如果超过预期上限仍未完成，告诉用户“任务仍在后台运行”，并保留 `task_id`

建议的最长等待：
- `快速`、`基础`：最多约 `6` 分钟
- `标准`：最多约 `12` 分钟
- `深度`：最多约 `18` 分钟
- `全面`：最多约 `30` 分钟

## 什么时候不要硬调接口

遇到这些情况先停下来：

- 还没有有效登录态
- 用户没给关键标识，而且系统也无法推断
  例如完全没给股票代码、交易 ID、计划 ID
- 接口已经明确返回参数校验错误
- 当前问题更适合直接用通用数据 skill，而不是 TradingAgentsCN

## 最小输出原则

对用户只返回：
- 你做了什么
- 结论是什么
- 风险点是什么
- 下一步建议是什么

不要把原始接口字段、长 JSON、内部路由细节直接甩给用户。

## 给 AI 的实际执行原则

- 每次开始使用这个 skill 时，先跑一次 `ensure_tradingagents_token.py`
- 之后所有接口调用都优先走 `invoke_tradingagents_api.py`
- 如果业务接口返回 `task_id`，优先走 `wait_for_task.py`
- AI 只需要关心：
  - 该选哪个业务接口
  - 该传什么业务参数
  - 结果该怎么解释给用户
- AI 不需要重复手写登录流程、拼 Token 头、处理 401 续登
- 复杂 JSON 优先放到 `examples/*.json` 或临时 JSON 文件里，再用 `--body-file`

## 首次加载建议阅读顺序

1. 先读本文件
2. 再读 `references/environment-variables.md`
3. 再读 `references/auth-and-session.md`
4. 然后按意图只读一个业务参考
5. 最后需要模板时再读 `references/call-templates.md`
