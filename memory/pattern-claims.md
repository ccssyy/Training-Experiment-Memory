# 首批 PatternClaim（26 条）

> 日期：2026-08-13 ｜ 状态：首批（candidate / validated，依历史证据强度区分；见 schema 状态机）
> `supported_by` 指向 `experience-cases.md`；`capability_tags`/`task_shape` 见 `capability-tags.md` 与 `schema.md`。

---

## CLAIM-0001 行级归组数量字段在密集跨页表格易漏行

```yaml
claim_id: CLAIM-0001
status: candidate            # 问题已量化确认，干预在多案例上未验证
capability_tags:
  semantic: [quantity]
  value_shape: [numeric_value]
  cardinality: [grouped_value, row_aligned, cross_page_group]
  layout: [dense_table, long_table]
problem_pattern: 行级归组数量字段（goods_quantity）在密集跨页表格易漏行（row_delta<0）
intervention_strategy: 长表分段 + 行级守恒 + 连续重叠 core；推理用无标签 planner 切窗
applicability:
  preconditions: [行级归组的数量字段, 密集表格, 可能跨页]
  contraindications: [单值字段不适用, 短表（<10 行）收益有限]
  confidence: medium
  transfer_level: mechanism   # 字段不同但"行级归组数量"机制相同即可迁移
supported_by: [CASE-0001]
outcome_aggregate: {typical_delta: 装箱单 goods F1 0.6598~0.6744 仍为最低, cost_range: 未知, stability: 未知}
```

## CLAIM-0002 归组字段在长表易重复 group / 相邻列串位

```yaml
claim_id: CLAIM-0002
status: candidate
capability_tags:
  semantic: [quantity, parcel]
  value_shape: [numeric_value]
  cardinality: [grouped_value, row_aligned, multi_value]
  layout: [dense_table, long_table]
problem_pattern: 归组字段在长表易重复 group（168 事件）+ 相邻数值列串位（386 事件）
intervention_strategy: 行对齐 + 连续重叠 core + 槽位去重（字段/文本/空间位置约束）
applicability:
  preconditions: [多数值列密集表格, 行级归组]
  contraindications: [单列数值表不适用, 字段间语义距离远时串位风险低]
  confidence: medium
  transfer_level: mechanism
supported_by: [CASE-0002, CASE-0003]
outcome_aggregate: {typical_delta: 串位为保守下界 386 事件, cost_range: 未知, stability: 未知}
```

## CLAIM-0003 尺寸/重量标题单位字段易错配

```yaml
claim_id: CLAIM-0003
status: candidate
capability_tags:
  semantic: [size, weight, unit]
  value_shape: [numeric_unit]
  cardinality: [single_value, multi_value]
  layout: [dense_table, multi_block]
problem_pattern: 尺寸（size）与重量标题单位（gross/net weight title unit）字段在装箱单 non_goods 高频错配
intervention_strategy: 单位独立建模（数值与单位解耦）+ 标题单位专项样本
applicability:
  preconditions: [数值+单位字段, 标题与数值分离的版式]
  contraindications: [无单位字段不适用]
  confidence: medium
  transfer_level: structural
supported_by: [CASE-0004, CASE-0005]
outcome_aggregate: {typical_delta: size 30.6% / gross+net 单位 440 错误, cost_range: 未知, stability: 未知}
```

## CLAIM-0004 训练 batch 过大 + LR 不匹配导致输出坍缩

```yaml
claim_id: CLAIM-0004
status: validated            # 历史多轮稳定主线，坍缩可复现且切回后消除
capability_tags:
  semantic: []
  value_shape: []
  cardinality: []
  layout: []
problem_pattern: GB512 后期输出坍缩（ckpt80 全 0）；sqrt LR 缩放无收益
intervention_strategy: GB256 + LR2e-4 稳定主线；避免盲目放大 batch 与 sqrt LR 缩放
applicability:
  preconditions: [Qwen3-VL-32B-AWQ + LoRA 类训练]
  contraindications: [其他模型规模/训练栈需重新验证]
  confidence: high
  transfer_level: context
supported_by: [CASE-0006]
outcome_aggregate: {typical_delta: 坍缩消除, cost_range: 8*A800, stability: 多轮稳定}
```

## CLAIM-0005 金额字段需 value 去币种 + currency 独立

```yaml
claim_id: CLAIM-0005
status: validated            # amount F1 0.4211→1.0000，纯格式归因清晰
capability_tags:
  semantic: [monetary, unit]
  value_shape: [currency_amount]
  cardinality: [single_value]
  layout: [labeled_value]
problem_pattern: 币种混入 value 导致 exact 判错（纯格式问题非模型进步）
intervention_strategy: value 去币种 + currency 独立 + bbox 保留；训练/测试/repair 同一清洗函数
applicability:
  preconditions: [金额字段含币种符号]
  contraindications: [币种在训练目标内需单独评估]
  confidence: high
  transfer_level: direct
supported_by: [CASE-0007]
outcome_aggregate: {typical_delta: amount F1 +0.5789, cost_range: 低, stability: 高}
```

## CLAIM-0006 推理运行时版本影响 bbox 定位

```yaml
claim_id: CLAIM-0006
status: validated            # IoU 0.068→0.747，归因清晰
capability_tags:
  semantic: []
  value_shape: []
  cardinality: [per_value_bbox]
  layout: []
problem_pattern: vLLM 版本与 LoRA 模块加载直接影响 bbox（0.16 no-tower 0.747 vs 0.21 tower 0.068）
intervention_strategy: 固定 vLLM 版本 + language-only QLoRA（显式 target 语言层）；训练/评估/推理运行时同合同
applicability:
  preconditions: [需要 bbox 定位的任务]
  contraindications: [纯文本抽取无 bbox 需求时影响小]
  confidence: high
  transfer_level: context
supported_by: [CASE-0008]
outcome_aggregate: {typical_delta: IoU +0.679, cost_range: 低, stability: 高}
```

## CLAIM-0007 标识/低频字段需专项增强

```yaml
claim_id: CLAIM-0007
status: candidate
capability_tags:
  semantic: [identifier, parcel]
  value_shape: [code_value, numeric_value]
  cardinality: [single_value, multi_value]
  layout: [dense_table]
problem_pattern: 标识字段（product_no）与低频字段（goods_parcel）漏抽严重
intervention_strategy: targeted 增强 + 低频字段受控上采样（标记来源 score_note）+ 字段配额 + floor 保护
applicability:
  preconditions: [低频有值字段, 标识类字段]
  contraindications: [高频字段过度上采样会样本膨胀]
  confidence: medium
  transfer_level: structural
supported_by: [CASE-0009, CASE-0012]
outcome_aggregate: {typical_delta: product_no F1 0.3509 / parcel 有值样本→34%, cost_range: 中, stability: 未验证}
```

## CLAIM-0008 评估需 cluster 整簇留出 + ID/OOD 双评

```yaml
claim_id: CLAIM-0008
status: validated            # ID/OOD/OOD-tail 三区全正 + family bootstrap 区间为正
capability_tags:
  semantic: []
  value_shape: []
  cardinality: []
  layout: [cross_page]
problem_pattern: 随机图片切分无法回答版式泛化（内容级 train/test 重叠）
intervention_strategy: cluster 整簇留出 + ID/OOD-core/OOD-tail 三区评测 + family bootstrap + 泄漏闭包（SHA/像素 SHA/感知 hash/family/cluster）
applicability:
  preconditions: [有 cluster/family 元数据的数据集]
  contraindications: [无版式聚类元数据时需先补聚类]
  confidence: high
  transfer_level: context
supported_by: [CASE-0010]
outcome_aggregate: {typical_delta: goods micro F1 +0.2412, cost_range: 低, stability: 高}
```

## CLAIM-0009 评估字段面必须四方对齐

```yaml
claim_id: CLAIM-0009
status: validated            # round1 contaminated → round2 valid_eval，流程修复验证
capability_tags:
  semantic: []
  value_shape: []
  cardinality: []
  layout: []
problem_pattern: prompt/训练标签/Gold/evaluator 字段面不一致导致评估污染
intervention_strategy: 字段面四方对齐 + 训练排除字段不入评估 + test lock 四状态（valid_eval/contaminated/contract 失效/证据不足）
applicability:
  preconditions: [任何字段级 KIE 评估]
  contraindications: [无]
  confidence: high
  transfer_level: context
supported_by: [CASE-0011]
outcome_aggregate: {typical_delta: 污染结果只作历史追溯, cost_range: 低, stability: 高}
```

---

## 以下 CLAIM-0010~0012 来源：同事 non_goods round3 分析包

## CLAIM-0010 non_goods 多字段同值冒充

```yaml
claim_id: CLAIM-0010
status: candidate
capability_tags:
  semantic: [bank, identifier, party]
  value_shape: [code_value, short_text]
  cardinality: [single_value, multi_value]
  layout: [multi_block]
problem_pattern: non_goods 银行/编号/份数字段易复用同一值+bbox（同值跨字段冒充）
intervention_strategy: 字段级排他/互斥约束 + 值唯一性检查（同值同 bbox 只允许命中单一字段）；排他对：issuing_bank↔available_with、beneficiary_bank↔beneficiary_account、reference↔order_number、document_no↔reference_no↔swb_id
applicability:
  preconditions: [多字段同语义域密集单据（银行/编号/份数）]
  contraindications: [合法共用的共享值需人工豁免]
  confidence: medium
  transfer_level: mechanism
supported_by: [CASE-0013, CASE-0018]
outcome_aggregate: {typical_delta: 明确复现 5 张/24 张, cost_range: 低, stability: 未验证}
```

## CLAIM-0011 checkbox/份数类字段易幻觉

```yaml
claim_id: CLAIM-0011
status: candidate
capability_tags:
  semantic: [term, status]
  value_shape: [numeric_value, short_text]
  cardinality: [single_value]
  layout: [multi_block]
problem_pattern: checkbox/份数/存在性字段在无值时易输出 0 或错误值，违背"无值不出 key"
intervention_strategy: 存在性字段的"无值不出 key"约束 + 份数字段严格取文档份数词（如 B/L、COPIES）而非业务编号
applicability:
  preconditions: [checkbox/份数/存在性字段（aco 托收申请、随附单据清单）]
  contraindications: [数值型字段不适用]
  confidence: medium
  transfer_level: structural
supported_by: [CASE-0014]
outcome_aggregate: {typical_delta: aco badcase 522 行（含此类）, cost_range: 低, stability: 未验证}
```

## CLAIM-0012 当事人字段漏抽与混淆

```yaml
claim_id: CLAIM-0012
status: candidate
capability_tags:
  semantic: [party]
  value_shape: [short_text]
  cardinality: [single_value, multi_value]
  layout: [multi_block]
problem_pattern: 当事人字段（buyer/consignee）在多区块版式易漏抽或混淆；group 内锚点字段（goods_name）易整组漏抽
intervention_strategy: 当事人字段按引导词独立定位（Buyer/Consignee/Ship To）+ 互斥去重；group 锚点字段（goods_name）纳入行级完整性校验
applicability:
  preconditions: [多区块版式单据（pi/so 等），存在 buyer↔consignee 同现]
  contraindications: [单当事人单据不适用]
  confidence: medium
  transfer_level: mechanism
supported_by: [CASE-0015, CASE-0016]
outcome_aggregate: {typical_delta: pi F1 0.6320（最低）/ so 漏 goods_name, cost_range: 低, stability: 未验证}
```

---

## 以下 CLAIM-0013~0018 来源：coding-brain Registry（4-5 月早期训练）

## CLAIM-0013 空输出要二分（选错字段 vs 真实负样本）

```yaml
claim_id: CLAIM-0013
status: confirmed            # 归因正确（空输出二分），但"二分后训练改善"未验证
capability_tags:
  semantic: []
  value_shape: []
  cardinality: []
  layout: []
task_shape:
  triggers: [empty_output]
problem_pattern: 空输出混同"选错字段"与"真实无货物负样本"两种成因，处理策略相反
intervention_strategy: 二分归因——选错字段（加字段锚点，可避免）vs 真实负样本（控比例，不能清零）
applicability:
  preconditions: [存在空输出字段的抽取任务]
  contraindications: [全部真负样本的单据（如 CR）不加锚点]
  confidence: high
  transfer_level: context
supported_by: [CASE-0019]
outcome_aggregate: {typical_delta: 可避免比例 CI 77%/BL 71%/Air 94%/PO 7%/CR 0%, cost_range: 低, stability: 高}
```

## CLAIM-0014 指标下降先查标注口径，再判模型退化

```yaml
claim_id: CLAIM-0014
status: confirmed
capability_tags:
  semantic: []
  value_shape: []
  cardinality: []
  layout: []
task_shape:
  triggers: [label_caliber]
problem_pattern: 指标下降可能来自标注口径迁移（如 group 从旧合并迁移到真实多 group），而非模型退化
intervention_strategy: 先核对标注口径是否变化，再判退化；口径迁移时不回退修复，转向 targeted 增强
applicability:
  preconditions: [标注口径有过变更的字段/单据]
  contraindications: [口径未变时直接当退化分析]
  confidence: high
  transfer_level: context
supported_by: [CASE-0020]
outcome_aggregate: {typical_delta: BL F1 -0.0646 为口径迁移, cost_range: 低, stability: 高}
```

## CLAIM-0015 late checkpoint 不一定更好，需平局阈值 + 风险标记

```yaml
claim_id: CLAIM-0015
status: confirmed
capability_tags:
  semantic: []
  value_shape: []
  cardinality: []
  layout: []
task_shape:
  triggers: [checkpoint_selection]
problem_pattern: 最末 checkpoint 可能只微弱高于早停点却带风险（如 ckpt1575 只高 0.0007）
intervention_strategy: 密集保存 + 多 checkpoint 评估 + 0.003 平局阈值 + 风险标记（Total F1 降>0.02 / 关键字段降>0.05）
applicability:
  preconditions: [多 checkpoint 训练]
  contraindications: [无]
  confidence: high
  transfer_level: context
supported_by: [CASE-0021]
outcome_aggregate: {typical_delta: ckpt1015 macro 0.8537, cost_range: 低, stability: 高}
```

## CLAIM-0016 页眉/letterhead 卖方抬头是当事人字段坏例集中模式

```yaml
claim_id: CLAIM-0016
status: candidate
capability_tags:
  semantic: [party]
  value_shape: [short_text]
  cardinality: [single_value]
  layout: [multi_block, labeled_value]
problem_pattern: 当事人（seller）字段坏例集中在页眉/左上 logo/letterhead 卖方抬头
intervention_strategy: 版式/公司频次统计用于 prompt 约束或样本修复
applicability:
  preconditions: [有页眉/letterhead 版式的单据]
  contraindications: [无]
  confidence: medium
  transfer_level: structural
supported_by: [CASE-0022]
outcome_aggregate: {typical_delta: letterhead 卖方抬头 45/82, cost_range: 低, stability: 未验证}
```

## CLAIM-0017 跨硬件训练结论要分层表达（可正确训练 ≠ 等价）

```yaml
claim_id: CLAIM-0017
status: confirmed
capability_tags:
  semantic: []
  value_shape: []
  cardinality: []
  layout: []
task_shape:
  triggers: [cross_hardware]
problem_pattern: 跨硬件 fp16/多卡通信/micro batch 差异会破坏逐位可复现，不能声明等价
intervention_strategy: 结论分层——"可正确训练但不等价"，业务指标在同硬件复测
applicability:
  preconditions: [跨硬件迁移训练]
  contraindications: [无]
  confidence: high
  transfer_level: context
supported_by: [CASE-0023]
outcome_aggregate: {typical_delta: BW1000 约 A800 80% 吞吐, cost_range: 低, stability: 高}
```

## CLAIM-0018 样本贡献比失衡导致低占比单据被淹没

```yaml
claim_id: CLAIM-0018
status: candidate
capability_tags:
  semantic: []
  value_shape: []
  cardinality: []
  layout: []
task_shape:
  triggers: [sample_balance]
problem_pattern: 多单据联合训练时样本贡献比失衡（14.3:1）导致低占比单据被淹没
intervention_strategy: 平衡贡献比（→2.3:1）+ warmup/effective batch 调整
applicability:
  preconditions: [多单据联合训练]
  contraindications: [单单据不适用]
  confidence: medium
  transfer_level: context
supported_by: [CASE-0024]
outcome_aggregate: {typical_delta: 贡献比 14.3:1 → 2.3:1, cost_range: 低, stability: 未验证模型指标}
```

---

## 以下 CLAIM-0019~0022 来源：session-digests（数据工程/训练前置方法论）

## CLAIM-0019 badcase 分类法（7 类错误 + 训练侧三分）

```yaml
claim_id: CLAIM-0019
status: confirmed
capability_tags:
  semantic: []
  value_shape: []
  cardinality: []
  layout: []
task_shape:
  triggers: [badcase_taxonomy]
problem_pattern: 仅看 badcase CSV 无法区分漏抽/误抽/字段混淆/边界/OCR/标签问题，难以定位根因
intervention_strategy: 固定 7 类错误枚举 + 图片/GT/Predict/bbox 联合复核 + 训练侧三分（train yes/review/no）
applicability:
  preconditions: [字段级 badcase 分析]
  contraindications: [无图片/bbox 证据时只能粗判]
  confidence: high
  transfer_level: context
supported_by: [CASE-0025]
outcome_aggregate: {typical_delta: 漏抽占 61% 主导, cost_range: 中, stability: 高}
```

## CLAIM-0020 测试 badcase 去测试化后才能入训

```yaml
claim_id: CLAIM-0020
status: validated            # 泄漏闭包决策，与 CLAIM-0008 cluster 留出一致
capability_tags:
  semantic: []
  value_shape: []
  cardinality: []
  layout: []
task_shape:
  triggers: [badcase_decontaminate]
problem_pattern: 测试集 badcase 直接入训会造成泄漏，但全丢弃浪费诊断价值
intervention_strategy: 只诊断/归纳规则，转成去测试化的版式/字段模式入训，不回灌测试图片
applicability:
  preconditions: [标准测试集 badcase 处理]
  contraindications: [无]
  confidence: high
  transfer_level: context
supported_by: [CASE-0026]
outcome_aggregate: {typical_delta: 入训原则为去测试化模式, cost_range: 低, stability: 高}
```

## CLAIM-0021 JSONL 行数不等于唯一图片数

```yaml
claim_id: CLAIM-0021
status: confirmed
capability_tags:
  semantic: []
  value_shape: []
  cardinality: []
  layout: []
task_shape:
  triggers: [data_admission]
problem_pattern: mode 扩展/负样本/上采样让 JSONL 行数膨胀，误当图片数导致 admission 误判
intervention_strategy: 区分 row count 与 unique image count，manifest 以实际图片数为准
applicability:
  preconditions: [数据生成/admission 环节]
  contraindications: [无]
  confidence: high
  transfer_level: context
supported_by: [CASE-0027]
outcome_aggregate: {typical_delta: null, cost_range: 低, stability: 高}
```

## CLAIM-0022 训练前置门禁链（8 门禁 + 顺序）

```yaml
claim_id: CLAIM-0022
status: confirmed
capability_tags:
  semantic: []
  value_shape: []
  cardinality: []
  layout: []
task_shape:
  triggers: [preflight_gates]
problem_pattern: 数据/生成/运行/训练问题事后无法分离，误归因模型训练
intervention_strategy: 8 门禁顺序执行——SourceSnapshot/SplitPlanner/FieldContractGate/DistributionAudit/DataAdmissionGate/TestLock/RuntimeReceipt/CheckpointGate
applicability:
  preconditions: [正式训练前置筛查]
  contraindications: [快速 smoke 可跳过部分门禁]
  confidence: high
  transfer_level: context
supported_by: [CASE-0028]
outcome_aggregate: {typical_delta: 8 个 ATF 需求候选, cost_range: 中, stability: 高}
```

---

## 以下 CLAIM-0023~0026 来源：round5 完整归档 + round3 训练包 digest

## CLAIM-0023 非货描 ID/OOD 迁移弱于货描

```yaml
claim_id: CLAIM-0023
status: confirmed
capability_tags:
  semantic: []
  value_shape: []
  cardinality: []
  layout: []
task_shape:
  triggers: [lane_migration]
problem_pattern: 货描与非货描的 ID/OOD 迁移能力不对称——货描强迁移，非货描弱迁移（精确率升、召回降）
intervention_strategy: 按 lane 分开设预期与回退保护；非货描迁移需重点盯召回和重量/提货单字段回归
applicability:
  preconditions: [ID/OOD 迁移评测]
  contraindications: [无]
  confidence: high
  transfer_level: context
supported_by: [CASE-0029]
outcome_aggregate: {typical_delta: 货描 +0.2412 / 非货描 +0.0649, cost_range: 低, stability: 高}
```

## CLAIM-0024 content-level 重叠使历史指标只能标 as-run

```yaml
claim_id: CLAIM-0024
status: validated            # 泄漏闭包，与 CLAIM-0008 一致
capability_tags:
  semantic: []
  value_shape: []
  cardinality: []
  layout: []
task_shape:
  triggers: [leakage_caliber]
problem_pattern: 同图片内容、不同文件名/标签序列化的 content-level 重叠，使历史指标带泄漏
intervention_strategy: 泄漏检测用 content hash（image_sha256），历史指标标注 as-run 口径，不当严格泛化指标
applicability:
  preconditions: [历史指标口径判定]
  contraindications: [无]
  confidence: high
  transfer_level: context
supported_by: [CASE-0030]
outcome_aggregate: {typical_delta: 货描 75/482、非货描 65/485 重叠, cost_range: 低, stability: 高}
```

## CLAIM-0025 训练配置冻结用 package-level 残差比较（非单点断言）

```yaml
claim_id: CLAIM-0025
status: validated            # RED/GREEN 负例证明
capability_tags:
  semantic: []
  value_shape: []
  cardinality: []
  layout: []
task_shape:
  triggers: [config_freeze]
problem_pattern: 跨轮单变量训练实验的配置冻结，单点断言防不住相邻配置漂移（fail-open）
intervention_strategy: 从冻结基线出发做 package-level 白名单残差比较 + 负例矩阵证明拒绝路径
applicability:
  preconditions: [跨轮训练包配置冻结]
  contraindications: [无]
  confidence: high
  transfer_level: context
supported_by: [CASE-0031]
outcome_aggregate: {typical_delta: 17 项负例矩阵、20 passed, cost_range: 低, stability: 高}
```

## CLAIM-0026 多机启动合同要传播到每个 remote rank + 单一身份 resolver

```yaml
claim_id: CLAIM-0026
status: validated            # 168→181 测试通过
capability_tags:
  semantic: []
  value_shape: []
  cardinality: []
  layout: []
task_shape:
  triggers: [multinode_contract]
problem_pattern: 多机 smoke 只在 coordinator 限参数、launcher/child 各自派生身份，导致合同传播遗漏与 dry/实际 preflight 分叉
intervention_strategy: RUN_MODE 状态机 + remote rank 合同全字段传播 + launcher/child 单一 resolver + collision guard（output/log/PID）
applicability:
  preconditions: [多机训练启动]
  contraindications: [单机不适用]
  confidence: high
  transfer_level: context
supported_by: [CASE-0032]
outcome_aggregate: {typical_delta: 181 测试通过, cost_range: 低, stability: 高}
```
