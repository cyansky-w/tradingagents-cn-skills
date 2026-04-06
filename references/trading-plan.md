# 交易计划

这份参考用于 TradingAgentsCN 里最长的一条业务链路。

不要把交易计划理解成“一次让 AI 在外部直接写完一整套正文”。
更稳定的做法是严格走系统已有的正式接口链路：

1. 生成
2. 评估
3. 优化

## 先看真实接口

- 创建计划：`POST /v1/trading-systems`
- 更新计划：`PUT /v1/trading-systems/{system_id}`
- 查询激活计划：`GET /v1/trading-systems/active`
- 评估已保存计划：`POST /v1/trading-systems/{system_id}/evaluate`
- 评估草稿计划：`POST /v1/trading-systems/evaluate-draft`
- 生成风控规则：`POST /v1/trading-systems/generate-risk-rules`
- 生成模块规则：`POST /v1/trading-systems/generate-module-rules`
- 优化讨论：`POST /v1/trading-systems/optimize-discussion`
- 发布计划：`POST /v1/trading-systems/{system_id}/publish`
- 激活计划：`POST /v1/trading-systems/{system_id}/activate`

## 核心规则

- 交易计划优先走“正式生成接口 -> 补齐草稿 -> 正式评估接口 -> 正式优化接口”的链路
- 不要在计划还很空的时候直接调用 `evaluate-draft`
- 不要默认一次性手写完整计划，优先调用系统已有生成接口
- 如果用户只想补某一部分，优先只生成对应模块，不要改整套计划
- `evaluate-draft` 是评估接口，不是生成接口
- `optimize-discussion` 也不是从零生成接口，它更适合在已有计划和评估结果基础上输出可应用 patch
- 如果某个正式计划接口返回 `task_id`，按异步任务闭环处理
- 如果某个正式计划接口直接返回最终结构化结果，则该步骤可以视为同步完成
- 不得因为想省事，就猜测未确认的 `/plan/analyze`、`/plan/generate` 替代路径

## 先理解真实计划结构

`TradingSystemCreate` 顶层字段：

- `name`
- `description`
- `style`
- `risk_profile`
- `stock_selection`
- `timing`
- `position`
- `holding`
- `risk_management`
- `review`
- `discipline`

`style` 可选值：

- `short_term`
- `medium_term`
- `long_term`

`risk_profile` 可选值：

- `conservative`
- `balanced`
- `aggressive`

## 推荐总流程

### 场景一：从零开始制定交易计划

推荐顺序：

1. 先收集或推断 `name`、`description`、`style`、`risk_profile`
2. 优先生成 `stock_selection`
3. 再生成 `timing`
4. 再生成 `risk_management`
5. 再补 `position`、`holding`、`review`、`discipline`
6. 组装成完整 `TradingSystemCreate`
7. 用正式评估接口评估
8. 如需继续改，再走 `optimize-discussion`
9. 需要保存时，再调用创建接口
10. 需要正式启用时，再发布和激活

### 场景二：用户只想补计划中的某个模块

推荐顺序：

1. 保留现有计划其余部分
2. 调用正式模块生成接口，只生成目标模块
3. 把生成结果合并回草稿
4. 视需要重新评估整个计划

### 场景三：用户已经有一份较完整的计划草稿

推荐顺序：

1. 先检查 7 个模块是否基本齐全
2. 若缺 `stock_selection`、`timing`、`risk_management`，优先调用生成接口补齐
3. 若缺 `position`、`holding`、`review`、`discipline`，先补草稿结构
4. 再调用正式评估接口
5. 如需讨论修改，再调用 `optimize-discussion`

## 生成阶段怎么做

适用于：

- “帮我从零定一套交易计划”
- “先把规则框架搭起来”
- “帮我补全选股 / 择时 / 风控规则”

### 模块生成优先级

优先调用系统已有生成接口：

1. `stock_selection`
2. `timing`
3. `risk_management`

### 风控专用生成

接口：`POST /v1/trading-systems/generate-risk-rules`

真实字段：

- `style`
- `risk_profile`
- `risk_style`
- `description`
- `current_rules`

### 通用模块生成

接口：`POST /v1/trading-systems/generate-module-rules`

真实字段：

- `module`
- `style`
- `risk_profile`
- `description`
- `current_rules`

当前确认支持的 `module`：

- `stock_selection`
- `timing`
- `risk_management`

不要写成 `risk`。

## 评估阶段怎么做

适用于：

- “这套计划合理吗”
- “哪里最薄弱”
- “哪些规则不够可执行”

### 两种评估入口

- 已保存计划：
  `POST /v1/trading-systems/{system_id}/evaluate`
- 未保存草稿：
  `POST /v1/trading-systems/evaluate-draft`

### 评估前最低检查

调用评估接口前，至少确认：

- 顶层的 `name`、`style`、`risk_profile` 已给出
- `stock_selection`、`timing`、`risk_management` 不要长期留空
- `position`、`holding`、`review`、`discipline` 至少有基础规则骨架

如果计划过于单薄，先补结构，再评估。

## 优化阶段怎么做

适用于：

- “基于评估结果继续改”
- “帮我把建议落成可以直接应用的 patch”

推荐做法：

1. 先拿到评估结果
2. 把当前计划和评估结果一起送进 `optimize-discussion`
3. 从返回的结构化 `updates` 里挑选要应用的 patch
4. 再更新草稿或正式计划

## 同步与异步判定

交易计划类接口不要预设“全部同步”或“全部异步”。
以正式返回为准：

- 如果返回最终结构化结果，本次调用可视为完成
- 如果返回 `task_id` 或等价任务标识，本次调用只算“任务创建成功”，必须等待正式结果回传

无论哪种情况，都不得为了追求省事而发明替代路径。
