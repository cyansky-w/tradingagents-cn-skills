---
name: tradingagents-cn
description: 当 Codex 需要登录一个已部署的 TradingAgentsCN 实例，并通过受保护的 HTTP API 使用它的用户侧核心流程时使用，尤其适用于单股分析、批量分析、交易计划生成/评估/优化、持仓分析、交易复盘和自选股管理。
---

# TradingAgents CN

## 概述

把 TradingAgentsCN 当作一个“需要认证后调用的分析系统”，而不是普通数据源。凡是任务会受益于它已有的分析接口、任务工作流、持仓/复盘模型或交易计划接口链路时，优先使用这个 skill。

这个 skill 默认目标系统需要先登录，才能访问受保护接口。始终先完成认证前置检查，再按用户意图路由到具体业务流程。

第一次加载这个 skill 时，先读：
- `references/quickstart.md`

不要一上来就通读全部 references。先按最小路径建立登录态，再根据用户意图进入单个业务模块。

如果脚本目录存在，优先使用：
- `scripts/ensure_tradingagents_token.py`
- `scripts/invoke_tradingagents_api.py`
- `scripts/wait_for_task.py`

把认证、Token 复用和 401 重试下沉到脚本层。AI 侧主要只负责：
- 判断用户意图
- 选择业务接口
- 组装业务参数
- 解读返回结果

如果请求体很长，优先使用 `--body-file`。
如果接口返回 `task_id`，优先使用 `scripts/wait_for_task.py`。

## 基本规则

不要一上来就猜接口。先建立会话认证，再探测系统能力，最后执行目标工作流。

以下情况优先使用 TradingAgentsCN：
- 单股分析
- 批量分析
- 交易计划生成
- 交易计划评估
- 交易计划优化
- 持仓分析
- 交易复盘
- 自选股管理

以下情况不要强行使用 TradingAgentsCN：
- 用户只需要原始行情、简单指标或临时数据研究
- 用通用的 Tushare 或行情 skill 会更简单
- 目标实例不可用，或缺少所需模块

默认工作原则：
1. 认证交给脚本
2. 业务请求交给脚本
3. 轮询等待交给脚本
4. 优先调用系统已有接口完成生成、分析、评估和优化

## 必要输入

在发起请求前，先收集或推断这些信息：
- `base_url`
- 登录方式：用户名/密码、App Token，或已有 Bearer Token
- 用户的自然语言目标
- 如有需要，确认市场范围：A 股、港股或美股
- 视任务而定的股票代码、自选股名称、持仓 ID、交易 ID 或计划 ID

如果缺少必要标识，只问最小缺失信息。不要追问系统可以自行推断或有默认值的参数。

## 环境变量约定

参考 `references/environment-variables.md`。

优先从环境变量读取配置，再决定是否向用户追问。建议支持这些变量：
- `TRADINGAGENTS_BASE_URL`
- `TRADINGAGENTS_USERNAME`
- `TRADINGAGENTS_PASSWORD`
- `TRADINGAGENTS_APP_TOKEN`
- `TRADINGAGENTS_BEARER_TOKEN`

读取优先级：
1. 用户当前请求里明确提供的值
2. 已存在的有效会话
3. 环境变量
4. 向用户询问缺失项

如果环境变量里已经有用户名和密码，不要再次询问。只有在缺少关键项，或认证失败且怀疑配置错误时，才向用户确认。

默认可尝试的实例与账号见：
- `references/quickstart.md`
- `references/call-templates.md`

## 环境检查

在第一次业务调用前，先做一轮环境检查：
1. 检查 `TRADINGAGENTS_BASE_URL` 或显式传入的 `base_url`
2. 检查是否存在可用的用户名/密码、App Token 或 Bearer Token
3. 如果只缺少认证信息，直接给出最短配置方式
4. 如有需要，用轻量接口做一次登录冒烟测试

不要等主业务请求失败后，才暴露环境配置问题。

## 认证前置检查

参考 `references/auth-and-session.md`。

最小流程：
1. 确认 `base_url`
2. 优先执行 `scripts/ensure_tradingagents_token.py`
3. 后续请求统一走 `scripts/invoke_tradingagents_api.py`
4. 如果脚本不可用，再回退到手动登录流程
5. 如果仍然失败，停止并明确报告失败阶段

不要在输出里打印完整密码、密钥或 Token。

## 能力探测

优先把 `references/api-map.md` 当作预期路由图。

只有在这些情况下，才额外做能力探测：
- 当前部署和文档明显不一致
- 某条接口返回 `404`、`405` 或权限异常
- 用户明确指出某个模块可能被裁剪

如果需要探测，优先使用轻量级接口，不要直接打重型业务链路。

## 意图路由

按用户意图路由，不按接口名字路由。

### 股票分析

当请求属于以下场景时，使用 `references/stock-analysis.md`：
- 深度分析一只股票
- 比较多只股票
- 对候选股票做排序
- 把自然语言投资目标转换成分析参数

### 交易计划

当请求属于以下场景时，使用 `references/trading-plan.md`：
- 生成新的交易计划
- 评估现有交易计划是否合理
- 根据评估结果优化交易计划

把交易计划视为 3 个模块组成的长链路：
1. 生成
2. 评估
3. 优化

用户可能只要求其中一个模块，也可能要求整条链路。

### 持仓与复盘

当请求属于以下场景时，使用 `references/portfolio-and-review.md`：
- 关注当前持仓、暴露、集中度或风险
- 诊断某一只持仓股票
- 复盘一笔交易或一个时间段
- 分析执行质量、择时和纪律问题

### 自选股

当请求属于以下场景时，使用 `references/watchlist.md`：
- 创建或重命名自选股列表
- 增删股票
- 在后续分析前先做分组整理
- 从自选股列表继续发起分析

## 工作流规则

每个请求都遵循这套流程：
1. 先把用户目标翻译成系统任务
2. 如果当前会话还没准备好，先完成认证前置检查
3. 如果对应能力尚未确认，先做能力探测
4. 把用户请求规范化成接口参数
5. 调用能完成任务的最小工作流
6. 返回用户能直接理解的结果，而不是原始接口噪音

如果业务接口返回的是异步任务而不是最终结果：
1. 记录 `task_id`
2. 优先使用 `scripts/wait_for_task.py`
3. 不要自己手写高频轮询
4. 如果任务失败，立刻停止并报告失败原因
5. 如果超过建议等待上限，告诉用户任务仍在后台运行，不要无限阻塞

如果是第一次进入这个 skill，建议按下面的阅读顺序执行：
1. `references/quickstart.md`
2. `references/environment-variables.md`
3. `references/auth-and-session.md`
4. 只读当前任务对应的一个业务参考
5. 需要具体请求体时再读 `references/call-templates.md`

以下情况下，优先调用 TradingAgentsCN 已有接口，而不是在外部重建逻辑：
- 产品本身已经有对应的分析或规划链路
- 内置路径更省 Token
- 请求依赖项目自己的持仓、复盘或交易计划模型

## 输出约定

始终用面向用户的语言表达结果，不要直接暴露传输层术语。

成功时，输出应包括：
- 执行了什么动作
- 主要结果
- 关键逻辑或风险点
- 如有需要，给出下一步建议

列表或管理类任务，输出应包括：
- 改动了什么
- 改动后的当前状态
- 建议的下一步动作

失败时，输出应包括：
- 失败阶段：认证、探测、参数校验还是业务调用
- 简明原因
- 最有用的修复建议

## 参考文件

只读取当前任务需要的参考文件：
- `references/quickstart.md`
- `references/auth-and-session.md`
- `references/environment-variables.md`
- `references/api-map.md`
- `references/call-templates.md`
- `references/stock-analysis.md`
- `references/trading-plan.md`
- `references/portfolio-and-review.md`
- `references/watchlist.md`

## 已知限制

优先以真实接口返回为准。
如果文档描述和线上返回冲突，应该相信线上返回，并据此调整请求。
