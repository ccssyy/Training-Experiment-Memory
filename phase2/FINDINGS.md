# Phase 2-MVP 结构验证反馈（FINDINGS）

> 日期：2026-08-13 ｜ 用途：端到端跑通后发现的结构问题，作为"先验证结构再堆量"的回灌输入。
> 结论：链路跑通（画像 → 检索 → 建议卡），但暴露 4 个结构问题，需在 Phase 1 全量整理前修正。

## 验证结果（对照 11-phase2-plan.md §3）

| 验收项 | 结果 |
|---|---|
| schema 机器可读 | ✅ Case/Claim JSON 落盘读回，检索可用 |
| 字段语义匹配走通 | ✅ 装箱单字段→quantity/parcel 标签→命中 CLAIM-0001/0002 |
| 检索排序合理 | ✅ 装箱单命中漏行/串位排第 1/2；aco 命中同值冒充排第 1 |
| 值形态过滤生效 | ⚠️ 未触发（见 F2） |
| 建议卡含证据反证 | ✅ 每条含 supported_by 证据 + contraindications |

## F1 版式标签 `multi_block` 太泛，版式兜底导致无关推荐（已修正）

**现象**：未知字段 `custom_field_x` 靠 `multi_block` 版式兜底，返回了 CLAIM-0010/0011/0012（无语义命中）。

**根因**：`_infer_layout` 对 unknown doc_type 返回 `["multi_block"]` 作兜底，而 multi_block 几乎什么单据都能套。

**修正**：有语义标签的 claim，零语义命中时版式不兜底（score=0）。修正后场景 C 正确走"回退默认 SOP"。

**结构含义**：`multi_block` 标签区分度太低，Phase 1 全量整理时版式标签需更精细（或把 multi_block 拆成更具体的子类）。

## F2 值形态过滤规则未真正生效（已修 2026-08-15）

**现象**：`_value_shape_filter` 只做"grouped_value 经验不推荐给 single_value"一条，但 demo 里所有 claim 的 cardinality 都含 grouped_value 或场景都是 grouped，未触发过滤。

**结构含义**：需要把"值形态不匹配直接过滤"扩展为更完整的规则矩阵：
- grouped_value 经验 ↔ single_value 字段（已有）
- currency_amount 经验 ↔ 非金额字段
- numeric_unit 经验 ↔ 纯数值字段
- 以及反向：single_value 字段不要推荐 multi_value/grouped_value 的干预

## F3 "上下文类" Claim 的 capability_tags 全空，字段语义检索无法命中

**现象**：CLAIM-0004（GB256 主线）、CLAIM-0006（运行时 bbox）、CLAIM-0008（cluster ID/OOD）、CLAIM-0009（字段面对齐）的 semantic 为空，字段语义检索永远命中不了它们。

**根因**：这些是"任务形态/训练配置类"经验（靠 lane、bbox 需求、跨页、训练参数、评估口径触发），不是"字段语义类"经验。schema 的 capability_tags 只设计了字段语义维度，缺一个"任务形态/检索维度"字段。

**结构含义（重要）**：schema 需要给 PatternClaim 增加一个**任务形态维度**（如 `task_shape: {lane, bbox_required, cross_page, training_config, eval_contract}`），让上下文类经验也能被检索。否则这 4 条 validated Claim 是"死数据"。

## F4 值形态启发规则粗糙（CTN 误判为重量/尺寸，已修 2026-08-15）

**现象**：`10 CTN` 的值形态启发误判为 numeric_unit + weight/size，但 CTN 是"箱数"单位，应归 quantity/parcel。

**根因**：值形态启发正则把 CTN 和 KG/LB/MT 混在同一组单位里。

**结构含义**：值形态启发需要区分"重量/尺寸单位"（KG/LB/MT/CBM/CM）与"计数/包装单位"（CTN/PCS/BAGS/PACKAGES）两类。这是 field-semantics.md §7 待补的"值形态启发正则"要解决的。

## 修正优先级建议

| # | 问题 | 优先级 | 动作 |
|---|---|---|---|
| F3 | 上下文类 Claim 缺任务形态维度 | **高** | schema 给 PatternClaim 加 `task_shape`，重写 4 条 validated Claim |
| F2 | 值形态过滤规则不全 | 高 | 扩展过滤规则矩阵 |
| F4 | 值形态启发粗糙 | 中 | 区分重量/计数单位（field-semantics 待补） |
| F1 | multi_block 太泛 | 中 | 版式标签细化（Phase 1 全量整理时） |
