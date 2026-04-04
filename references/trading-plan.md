# 交易计划

这份参考用于 TradingAgentsCN 里最长的一条业务链路。

不要把交易计划理解成“一次让 AI 直接写完一大段计划正文”。
更稳定的做法是把它拆成 3 个阶段：

1. 生成
2. 评估
3. 优化

其中“生成”本身也应优先走模块化生成，而不是一开始就手写整套规则。

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

这 7 个业务模块里，当前系统已经提供专门生成接口的是：

- `stock_selection`
- `timing`
- `risk_management`

其中 `risk_management` 有两种走法：

- 通用模块生成：`generate-module-rules`，`module="risk_management"`
- 专门风控生成：`generate-risk-rules`

## 给模型的核心规则

- 交易计划优先走“模块生成 -> 补齐草稿 -> 评估 -> 优化 -> 保存”的链路。
- 不要在计划还很空的时候直接调用 `evaluate-draft`。
- 不要默认一次性手写完整计划，优先调用系统已有生成接口。
- 如果用户只想补某一部分，优先只生成对应模块，不要改整套计划。
- 评估接口不是生成接口，`evaluate-draft` 输入的是计划草稿，不会替你自动补计划结构。
- `optimize-discussion` 也不是从零生成，它更适合在已有计划和评估结果的基础上产出可应用 patch。
- 如果用户对计划风格、限制条件、偏好重点有要求，优先写进对应接口字段再调用。

## 推荐总流程

### 场景一：从零开始制定交易计划

推荐顺序：

1. 先收集或推断 `name`、`description`、`style`、`risk_profile`
2. 优先生成 `stock_selection`
3. 再生成 `timing`
4. 再生成 `risk_management`
5. 再补 `position`、`holding`、`review`、`discipline`
6. 组装成完整 `TradingSystemCreate`
7. 用 `evaluate-draft` 评估
8. 如需继续改，再走 `optimize-discussion`
9. 需要保存时，再调用创建接口
10. 需要正式启用时，再发布和激活

### 场景二：用户只想补计划中的某个模块

推荐顺序：

1. 保留现有计划其余部分
2. 调用模块生成接口，只生成目标模块
3. 把生成结果合并回草稿
4. 视需要重新评估整个计划

### 场景三：用户已经有一份较完整的计划草稿

推荐顺序：

1. 先检查 7 个模块是否基本齐全
2. 若缺 `stock_selection`、`timing`、`risk_management`，优先调用生成接口补齐
3. 若缺 `position`、`holding`、`review`、`discipline`，先补草稿结构
4. 再调用 `evaluate-draft`
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

原因：

- 这是项目已经提供的正式生成入口
- 比在接口外重新拼整套内容更省 token
- 生成结果天然更贴近系统自己的数据结构

### 风控专用生成

接口：`POST /v1/trading-systems/generate-risk-rules`

真实字段：

- `style`
- `risk_profile`
- `risk_style`
- `description`
- `current_rules`

这些字段里，最适合承载生成偏好的是：

- `description`
  放交易风格、约束、侧重点、偏好目标
- `current_rules`
  放已有规则，要求在原基础上补强或改写
- `risk_style`
  放更细的风险倾向

适用场景：

- 用户只想单独打磨风控
- 已有风控规则，但想让 AI 在现有基础上重写或补强
- 需要专门生成止损、止盈、时间止损、逻辑止损

### 通用模块生成

接口：`POST /v1/trading-systems/generate-module-rules`

真实字段：

- `module`
- `style`
- `risk_profile`
- `description`
- `current_rules`

这些字段里，最适合承载生成偏好的是：

- `module`
  明确这次只生成哪个模块
- `description`
  放本轮模块生成的目标、风格、禁忌和关注点
- `current_rules`
  放已有版本，要求接口在其基础上优化，而不是完全重写

当前确认支持的 `module`：

- `stock_selection`
- `timing`
- `risk_management`

不要写成 `risk`。
服务层实际识别的是 `risk_management`。

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

`evaluate-draft` 的请求体就是一份计划草稿，不要求先保存。
但它评估的是你送进去的计划内容，不会替你补结构。

### 评估前最低检查

调用 `evaluate-draft` 前，至少确认：

- 顶层的 `name`、`style`、`risk_profile` 已给出
- `stock_selection`、`timing`、`risk_management` 不要长期留空
- `position`、`holding`、`review`、`discipline` 至少有基础规则骨架

如果计划过于单薄，先补结构，再评估。

## 优化阶段怎么做

适用于：

- “基于评估结果继续改”
- “帮我把建议落成可以直接应用的 patch”
- “我已经知道薄弱点了，继续收敛成更可执行的版本”

推荐做法：

1. 先拿到评估结果
2. 把当前计划和评估结果一起送进 `optimize-discussion`
3. 从返回的结构化 `updates` 里挑选要应用的 patch
4. 再更新草稿或正式计划

## 优化讨论接口结构

`POST /v1/trading-systems/optimize-discussion` 请求体字段：

- `trading_plan_data`
- `evaluation_result`
- `user_question`
- `selected_suggestions`
- `conversation_history`

`conversation_history` 每项字段：

- `role`
- `content`

这条接口里最适合承载优化偏好的是：

- `user_question`
  放本轮最关心的问题，例如“先优先补可执行性，不要大改风格”
- `selected_suggestions`
  放已经确认要沿用的建议方向
- `conversation_history`
  放多轮收敛过程，帮助接口延续上下文

## 各模块内部结构

### `stock_selection`

应包含：

- `must_have`
- `exclude`
- `bonus`

### `timing`

应包含：

- `market_condition`
- `entry_signals`
- `confirmation`

### `position`

常见字段：

- `total_position`
- `max_per_stock`
- `max_holdings`
- `min_holdings`
- `scaling`

### `holding`

常见字段：

- `review_frequency`
- `add_conditions`
- `reduce_conditions`
- `switch_conditions`

### `risk_management`

常见字段：

- `stop_loss`
- `take_profit`
- `time_stop`
- `logical_stop`

### `review`

常见字段：

- `frequency`
- `checklist`
- `case_save`

### `discipline`

常见字段：

- `must_not`
- `must_do`
- `violation_actions`

## 模型执行时的判断规则

如果用户说“从零开始做一套计划”：

- 不要直接先评估
- 先生成模块，再补齐草稿

如果用户说“帮我补选股/择时/风控规则”：

- 优先调生成接口
- 不要直接重写整套计划

如果用户说“评估一下这套计划”：

- 先判断计划是否已经足够成形
- 不够成形就先补模块，再评估

如果用户说“按评估结果继续改”：

- 优先走 `optimize-discussion`
- 目标是拿结构化优化项，而不是只输出空泛建议
