# OpenClaw 对接指南

这份文档描述 TradingAgentsCN 与 OpenClaw 的推荐对接方式。

目标很明确：

- 创建异步任务后立刻返回
- AI 记录任务关联信息但不等待
- 任务进入终态后由 TradingAgentsCN 主动回调 OpenClaw
- 只有收到正式结果后，才把任务表述为“完成”

## 1. 推荐架构

推荐链路：

1. AI skill 调用正式任务创建接口，例如 `POST /analysis/single` 或 `POST /analysis/batch`
2. 请求体里附带 `openclaw_notify`
3. TradingAgentsCN 立即返回 `task_id`
4. AI 记录关联信息并结束当前等待链路
5. 任务进入 `completed` 或 `failed` 后，TradingAgentsCN 主动 `POST /hooks/agent`
6. OpenClaw 根据 `sessionKey` 或默认会话配置唤醒对应会话
7. AI 在收到正式结果后，再整理最终回复

不要再让 AI 助手进程自己长轮询。

## 2. AI 侧必须记录的关联信息

一旦任务创建成功，AI 必须至少记录：

- `task_id`
- `status_url`
- `result_url`
- `notification_mode`
- `openclaw_notify.session_key`
- 或 `channel` / `to`

如果后端没有透传 `session_key`，也要明确记住：

- 当前回调会落到哪个默认会话
- 后续该如何把回调和原任务关联起来

如果这些关联信息不完整，不能声称异步闭环已经准备好。

## 3. 服务端配置

TradingAgentsCN 后端需要配置：

- `OPENCLAW_HOOK_MODE`
- `OPENCLAW_USE_REQUEST_SESSION_KEY`
- `OPENCLAW_HOOK_URL`
- `OPENCLAW_HOOK_TOKEN`

示例：

```env
OPENCLAW_HOOK_MODE=openclaw_webhook
OPENCLAW_USE_REQUEST_SESSION_KEY=false
OPENCLAW_HOOK_URL=http://openclaw.local/hooks/agent
OPENCLAW_HOOK_TOKEN=replace-with-openclaw-bearer-token
```

说明：

- `OPENCLAW_HOOK_MODE=openclaw_webhook` 时才会发送 OpenClaw webhook
- 如果 mode 不是 `openclaw_webhook`，后端会把通知视为关闭
- `OPENCLAW_USE_REQUEST_SESSION_KEY=false` 时，后端不会向 OpenClaw 透传 `sessionKey`
- 只有在 `OPENCLAW_USE_REQUEST_SESSION_KEY=true` 时，后端才会把请求里的 `session_key` 发给 OpenClaw

## 4. 请求体写法

### 单股分析

```json
{
  "symbol": "000001",
  "parameters": {
    "market_type": "A股",
    "research_depth": "标准",
    "selected_analysts": ["fundamentals", "news", "market"],
    "include_sentiment": true,
    "include_risk": true,
    "language": "zh-CN",
    "engine": "v2"
  },
  "openclaw_notify": {
    "channel": "telegram",
    "to": "123456789",
    "deliver": true
  }
}
```

### 批量分析

```json
{
  "title": "核心候选股对比",
  "symbols": ["000001", "600519", "000858"],
  "parameters": {
    "market_type": "A股",
    "research_depth": "标准",
    "selected_analysts": ["fundamentals", "sector_analyst", "market"],
    "include_sentiment": true,
    "include_risk": true,
    "language": "zh-CN",
    "engine": "v2"
  },
  "openclaw_notify": {
    "session_key": "hook:trading-task:batch-core",
    "deliver": true
  }
}
```

## 5. `openclaw_notify` 字段说明

当前支持字段：

- `provider`
  - 固定建议填 `openclaw`
- `session_key`
  - 可选
  - 只有在后端开启 `OPENCLAW_USE_REQUEST_SESSION_KEY=true` 时才会透传给 OpenClaw
- `channel`
  - 可选
- `to`
  - 可选
- `agent_id`
  - 可选，默认 `main`
- `wake_mode`
  - 可选，默认 `now`
- `deliver`
  - 可选，默认 `true`
- `timeout_seconds`
  - 可选，默认 `60`
- `name`
  - 可选，默认 `TradingAgentsCN`

## 6. 创建任务接口的返回

`POST /analysis/single` 现在会直接返回这些字段：

- `task_id`
- `status`
- `created_at`
- `status_url`
- `result_url`
- `notification_mode`

真实响应示例：

```json
{
  "success": true,
  "data": {
    "task_id": "b95dcd2e-da51-4e7c-93ad-ba6f3fa1d735",
    "status": "pending",
    "created_at": "2026-04-06T11:06:30.377529+08:00",
    "status_url": "/api/analysis/tasks/b95dcd2e-da51-4e7c-93ad-ba6f3fa1d735/status",
    "result_url": "/api/analysis/tasks/b95dcd2e-da51-4e7c-93ad-ba6f3fa1d735/result",
    "notification_mode": "openclaw_webhook"
  },
  "message": "分析任务已提交到队列，等待 Worker 处理 (引擎: v2)"
}
```

说明：

- `notification_mode=openclaw_webhook` 代表当前任务已经记录了 OpenClaw 回调配置
- `status_url` 和 `result_url` 是官方兜底读取路径，不代表推荐轮询

## 7. 回调请求格式

任务进入终态后，TradingAgentsCN 会调用：

- `POST /hooks/agent`

请求头：

```http
Authorization: Bearer <OPENCLAW_HOOK_TOKEN>
Content-Type: application/json
```

请求体示例：

```json
{
  "message": "TradingAgents 任务失败。task_id=b95dcd2e-da51-4e7c-93ad-ba6f3fa1d735。执行失败: ... 结果地址：/api/analysis/tasks/b95dcd2e-da51-4e7c-93ad-ba6f3fa1d735/result",
  "name": "TradingAgentsCN",
  "agentId": "main",
  "wakeMode": "now",
  "deliver": true,
  "timeoutSeconds": 60
}
```

如果创建任务时提供了 `channel` 和 `to`，回调体里也会带上这两个字段。

## 8. OpenClaw 侧最少要求

OpenClaw 侧至少要保证：

1. 提供可被 TradingAgentsCN 访问到的 `POST /hooks/agent`
2. 校验 `Authorization: Bearer <token>`
3. 能把回调路由到默认会话或请求透传的 `sessionKey`
4. 能消费 `message`、`name`、`agentId`、`wakeMode`、`deliver`

如果 OpenClaw 还需要渠道转发：

- 读取 `channel`
- 读取 `to`

## 9. 成功判定

成功判定分两层：

### A. 任务创建成功

创建接口返回：

- `task_id`
- `status_url`
- `result_url`
- `notification_mode=openclaw_webhook` 或等价回调标识

### B. 回调发送成功

任务进入终态后，至少应看到以下任一证据：

- mock webhook 收到实际请求
- OpenClaw 成功接收并路由回调
- 数据库中写入 `openclaw_notify_sent_at`
- 数据库中写入 `openclaw_notify_status`

只有 A + B 都成立，并且能拿到正式结果时，才算完整闭环。

## 10. 缺少 webhook 能力时怎么办

如果当前环境没有可用的 webhook 接收能力，AI 应：

1. 明确说明“当前无法完成标准异步闭环”
2. 报告缺失项
3. 请求用户提供可用回调方式，或允许使用官方兜底结果获取接口
4. 不得自动改走未确认的同步分析接口

允许的兜底动作只有：

- 官方单次状态查询
- 官方单次结果读取

不允许：

- 持续轮询
- 自行发明同步替代路径

## 11. 最短结论

如果你只记一条：

- 创建任务时带 `openclaw_notify`
- TradingAgentsCN 立即返回 `task_id`
- AI 记录关联信息但不等待
- OpenClaw 等 webhook
- 只有正式结果回到会话后，才叫“完成”
