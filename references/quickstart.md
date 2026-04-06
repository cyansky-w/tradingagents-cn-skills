# 最小使用手册

这份文件给第一次使用 `tradingagents-cn` skill 的模型看。

目标不是解释所有细节，而是让模型第一次就知道：

- 先确认什么
- 哪些事情由脚本自动处理
- 什么时候必须走异步任务闭环
- 遇到什么情况该停下来

## 一句话理解这个系统

TradingAgentsCN 是一个“有正式业务接口、脚本化认证入口和任务回调闭环”的交易分析系统。

不要把它当成普通行情源。
也不要把它当成可以随便猜 `/analyze` 路径的通用后端。

## 脚本实际路径

skill 目录位于 `/workspace/projects/workspace/skills/tradingagents-cn/`。
以下路径全部基于 skill 目录定位，AI 在 exec 调用时需拼接完整路径。

```text
skill 根目录：
  /workspace/projects/workspace/skills/tradingagents-cn/

脚本目录：
  /workspace/projects/workspace/skills/tradingagents-cn/scripts/

示例目录：
  /workspace/projects/workspace/skills/tradingagents-cn/examples/
```

## 第一次使用时的最短流程

1. 先确认 `TRADINGAGENTS_BASE_URL`
2. 确认脚本可用
3. 如需预检，可执行一次 `ensure_tradingagents_token.py`
4. 正式业务调用统一走 `invoke_tradingagents_api.py`
5. 对正式任务型接口，提交时优先附带 `openclaw_notify`
6. 如果返回 `task_id`，记录关联信息并立即退出当前等待链路
7. 由 webhook 或等价官方通知回传结果
8. 只在收到正式结果后，才汇报“分析完成”

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
2. 已存在的 Bearer Token 或有效缓存
3. 环境变量
4. 再向用户追问

## 推荐脚本入口

优先不要让 AI 自己手写登录逻辑。

### 预检脚本

```bash
python /workspace/projects/workspace/skills/tradingagents-cn/scripts/ensure_tradingagents_token.py
```

这个脚本会自动处理：

- 环境变量中的 Bearer Token
- 本地缓存的 Token
- 没有有效 Token 时自动登录
- 用 `/auth/me` 校验 Token 是否仍然可用

### 正式业务入口

```bash
python /workspace/projects/workspace/skills/tradingagents-cn/scripts/invoke_tradingagents_api.py --method GET --path /auth/me
```

这个脚本会自动处理：

- 先拿可用 Token
- 再发请求
- 遇到 `401` 自动清缓存
- 强制重新登录并重试一次

所以：

- 显式登录不是主业务流程
- 正式业务请求应统一通过 `invoke_tradingagents_api.py`
- `ensure_tradingagents_token.py` 更适合作为预检或诊断工具

## 异步任务最短规则

如果正式业务接口返回 `task_id`：

1. 不要让当前 AI 会话继续等待
2. 创建任务时优先附带 `openclaw_notify`
3. 至少记录：
   - `task_id`
   - `status_url`
   - `result_url`
   - `notification_mode`
   - `session_key` 或渠道投递信息
4. 对外只能汇报“任务已提交”，不能汇报“分析已完成”
5. 后续由 webhook 或等价官方通知唤醒会话

优先在创建任务时附带：

```json
{
  "openclaw_notify": {
    "session_key": "hook:trading-task:TASK_ID",
    "channel": "telegram",
    "to": "123456789",
    "deliver": true
  }
}
```

服务端需要同时配置 OpenClaw webhook：

- `OPENCLAW_HOOK_URL=http://<openclaw-host>/hooks/agent`
- `OPENCLAW_HOOK_TOKEN=<openclaw bearer token>`

如果需要完整对接步骤，再读：

- `references/openclaw-integration.md`

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

优先走正式持仓接口，不要拿查询接口冒充分析接口。

再读：

- `references/portfolio-and-review.md`
- `references/call-templates.md`

### 用户要做交易复盘

常见说法：

- “复盘这笔交易”
- “复盘这个月”
- “这笔交易有没有按计划执行”

优先走正式复盘接口，不要只返回交易记录。

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

对股票输入，优先规范成真实代码：

- `002837`
- `600519`

如果用户给的是 `002837.SZ` 这类格式，优先转成主代码并保留市场信息。
如果用户只给中文名称且无法可靠映射，询问一次代码，不要去穷举接口试探。

## 什么时候不要硬调接口

遇到这些情况先停下来：

- 还没有 `TRADINGAGENTS_BASE_URL`
- 脚本不可用
- 用户没给关键标识，而且系统也无法推断
- 接口已经明确返回参数校验错误
- 当前问题更适合直接用通用数据 skill，而不是 TradingAgentsCN
- 当前需要异步回调，但环境没有 webhook 或等价通知能力

## 最小输出原则

对用户只返回：

- 你做了什么
- 当前状态是什么
- 如果已完成，结论是什么
- 风险点是什么
- 下一步建议是什么

不要把原始接口字段、长 JSON、内部路由细节直接甩给用户。

## 首次加载建议阅读顺序

1. 先读本文件
2. 再读 `references/auth-and-session.md`
3. 再读 `references/environment-variables.md`
4. 然后按意图只读一个业务参考
5. 最后需要模板时再读 `references/call-templates.md`
