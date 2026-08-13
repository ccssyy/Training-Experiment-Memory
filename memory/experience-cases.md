# 首批 ExperienceCase（18 条）

> 日期：2026-08-13 ｜ 状态：首批（candidate，待 Phase 1 交叉验证后确认）
> 证据来源：`docs/performance/`、`~/coding-brain/04_Registries/`、`analysis_outputs/`（路径均为 A800 上 `/data/sam/Qwen2.5-VL-main` 相对路径）；CASE-0013 起来源为同事 `non_goods_round3_analysis` 包（`/data/chris/bea/repos/zito-atf-dev/tmp/non_goods_round3_analysis/`）。

---

## CASE-0001 装箱单 goods 明细行漏构造

```yaml
case_id: CASE-0001
run_ref: round2 formal eval（10 类单据，goods 501 请求）
fields: [goods_quantity, goods_name, product_no, goods_parcel, goods_carton]
layout: {document_type: packing_list, cluster: pl_mixed, page_role: dense_table}
problem:
  pattern_id: PL-ROW-UNDERCOUNT
  symptom_metric: row_delta<0 占 84/202 样本（明细行漏构造）；goods_quantity FP/FN=339/1045
intervention: 无（本 case 为失败观察）
outcome:
  baseline_ref: null
  delta: {goods F1: 0.6598, lane 错误占比 78.0%}
  protected_regression: null
evidence_refs:
  - docs/performance/2026-07-14-round2-10docs-badcase-analysis.md
  - docs/performance/2026-07-30-round5-and-7docs-cluster-id-ood-results.md
provenance: {source_revisions: [round2 frozen formal eval], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0002 装箱单重复 group

```yaml
case_id: CASE-0002
run_ref: round2 formal eval（装箱单 202 样本）
fields: [goods_name, goods_quantity]
layout: {document_type: packing_list, cluster: pl_mixed, page_role: dense_table}
problem:
  pattern_id: PL-REPEATED-GROUP
  symptom_metric: 20/202 样本出现 168 个重复 group 事件
intervention: 无（失败观察）
outcome:
  baseline_ref: null
  delta: {重复 group 事件: 168}
  protected_regression: null
evidence_refs:
  - docs/performance/2026-07-14-round2-10docs-badcase-analysis.md
provenance: {source_revisions: [round2 frozen formal eval], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0003 装箱单相邻数值列串位

```yaml
case_id: CASE-0003
run_ref: round2 formal eval（装箱单 202 样本）
fields: [goods_quantity, goods_carton, goods_parcel]
layout: {document_type: packing_list, cluster: pl_mixed, page_role: dense_table}
problem:
  pattern_id: PL-COLUMN-SLOT-SHIFT
  symptom_metric: 87/202 样本命中 386 个保守槽位串位事件（预测值命中相邻列 GT）
intervention: 无（失败观察）
outcome:
  baseline_ref: null
  delta: {槽位串位事件: 386}
  protected_regression: null
evidence_refs:
  - docs/performance/2026-07-14-round2-10docs-badcase-analysis.md
provenance: {source_revisions: [round2 frozen formal eval], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0004 装箱单 non_goods size 字段高错误

```yaml
case_id: CASE-0004
run_ref: round2 formal eval（non_goods 514 请求）
fields: [size]
layout: {document_type: packing_list, cluster: pl_mixed, page_role: dense_table}
problem:
  pattern_id: PL-SIZE-MISMATCH
  symptom_metric: size 单字段 826 个错误（FP/FN=612/214），占装箱单 non_goods 错误 30.6%
intervention: 无（失败观察）
outcome:
  baseline_ref: null
  delta: {size 错误: 826/2695}
  protected_regression: null
evidence_refs:
  - docs/performance/2026-07-14-round2-10docs-badcase-analysis.md
provenance: {source_revisions: [round2 frozen formal eval], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0005 装箱单重量标题单位错配

```yaml
case_id: CASE-0005
run_ref: round2 formal eval（non_goods）
fields: [goods_gross_weight_title_unit, goods_net_weight_title_unit]
layout: {document_type: packing_list, cluster: pl_mixed, page_role: dense_table}
problem:
  pattern_id: PL-WEIGHT-UNIT-MISMATCH
  symptom_metric: gross 标题单位 237 错误（FP/FN=106/131），net 203 错误（FP/FN=82/121）
intervention: 无（失败观察）
outcome:
  baseline_ref: null
  delta: {gross+net 标题单位错误: 440}
  protected_regression: null
evidence_refs:
  - docs/performance/2026-07-14-round2-10docs-badcase-analysis.md
provenance: {source_revisions: [round2 frozen formal eval], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0006 GB512 后期输出坍缩

```yaml
case_id: CASE-0006
run_ref: 6other_po0512 GB512 实验（ckpt80）
fields: []
layout: {document_type: mixed, cluster: null, page_role: null}
problem:
  pattern_id: PL-OUTPUT-COLLAPSE
  symptom_metric: GB512 后期 checkpoint80 输出全 0；sqrt LR 缩放无收益
intervention: 切回 GB256 + LR2e-4 主线
outcome:
  baseline_ref: GB256 主线
  delta: {坍缩消除}
  protected_regression: null
evidence_refs:
  - docs/performance/2026-05-16-6other-po0512-phase2-hg-gb512-lr-control.md
  - docs/performance/2026-05-16-6other-po0512-regen-formal-gb-lr-scaling.md
provenance: {source_revisions: [6other po0512], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0007 销售合同金额清洗（币种与 value 分离）

```yaml
case_id: CASE-0007
run_ref: 销售合同金额清洗实验
fields: [goods_amount, currency]
layout: {document_type: sales_contract, cluster: sc_mixed, page_role: labeled_value}
problem:
  pattern_id: PL-CURRENCY-IN-VALUE
  symptom_metric: value 内混币种导致 exact 判错（纯格式问题非模型进步）
intervention: value 去币种 + currency 独立 + bbox 保留；训练/测试/repair 同一清洗函数
outcome:
  baseline_ref: 清洗前
  delta: {amount F1: 0.4211 → 1.0000}
  protected_regression: null
evidence_refs:
  - docs/performance/2026-07-09-10newdocs-19docs-field-exact-indexes.md
provenance: {source_revisions: [销售合同清洗], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0008 vLLM 版本影响 bbox 定位

```yaml
case_id: CASE-0008
run_ref: exp6 awq vs bf16/bnb bbox 对比
fields: [bbox 相关字段]
layout: {document_type: mixed, cluster: null, page_role: null}
problem:
  pattern_id: PL-RUNTIME-BBOX-DRIFT
  symptom_metric: vLLM 0.16 no-tower IoU 0.747 vs 0.21 tower-enabled 0.068
intervention: 固定 vLLM 版本 + 显式 target 语言层（language-only QLoRA）
outcome:
  baseline_ref: vLLM 0.21 tower-enabled
  delta: {IoU: 0.068 → 0.747}
  protected_regression: null
evidence_refs:
  - runs/20260609_exp6_awq_vs_bf16_bnb_bbox_comparison
provenance: {source_revisions: [exp6 bbox 对比], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0009 CI product_no 严重漏抽

```yaml
case_id: CASE-0009
run_ref: 商业发票（CI）货描评测
fields: [product_no]
layout: {document_type: commercial_invoice, cluster: ci, page_role: dense_table}
problem:
  pattern_id: PL-IDENTIFIER-UNDEREXTRACT
  symptom_metric: product_no F1 0.3509（严重漏抽）
intervention: targeted 增强 + product_no 专项（待验证）
outcome:
  baseline_ref: null
  delta: {product_no F1: 0.3509}
  protected_regression: null
evidence_refs:
  - docs/performance/2026-07-22-round2-10docs-document-field-metrics.md
provenance: {source_revisions: [CI 货描评测], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0010 7docs cluster 整簇留出 ID/OOD 双评

```yaml
case_id: CASE-0010
run_ref: 7docs 旁路实验（487 训练图）
fields: []
layout: {document_type: mixed_7docs, cluster: id/ood_core/ood_tail, page_role: null}
problem:
  pattern_id: PL-RANDOM-SPLIT-OVERESTIMATE
  symptom_metric: 随机图片切分无法回答版式泛化
intervention: cluster 整簇留出 + ID/OOD-core/OOD-tail 三区评测 + family bootstrap
outcome:
  baseline_ref: Base（AWQ）
  delta: {goods micro F1: 0.3951 → 0.6363, 三区全正；non_goods 0.4314 → 0.4963}
  protected_regression: null
evidence_refs:
  - docs/performance/2026-07-30-round5-and-7docs-cluster-id-ood-results.md
provenance: {source_revisions: [7docs 旁路], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0011 round1 字段面四方不对齐 → 评估污染

```yaml
case_id: CASE-0011
run_ref: round1 10 新单据
fields: [9 个训练排除字段]
layout: {document_type: mixed, cluster: null, page_role: null}
problem:
  pattern_id: PL-FIELD-CONTRACT-MISALIGN
  symptom_metric: 9 个训练排除字段仍进入评估 → 整体判 contaminated
intervention: 字段面四方对齐（prompt/训练标签/Gold/evaluator 一致）
outcome:
  baseline_ref: null
  delta: {round1 判 contaminated，不作 baseline}
  protected_regression: null
evidence_refs:
  - docs/performance/2026-07-14-round2-10docs-badcase-analysis.md
provenance: {source_revisions: [round1], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0012 CR goods_parcel 低频字段漏抽

```yaml
case_id: CASE-0012
run_ref: 贷记通知单（CR）货描评测
fields: [goods_parcel]
layout: {document_type: credit_note, cluster: crn, page_role: dense_table}
problem:
  pattern_id: PL-LOWFREQ-FIELD-UNDEREXTRACT
  symptom_metric: goods_parcel 有值样本低频（support 15 波动大）；5x 上采样后 322→1610 有值样本
intervention: 低频字段 5x 上采样（有值样本）
outcome:
  baseline_ref: null
  delta: {有值样本占比 → 约 34%}
  protected_regression: 未验证副作用
evidence_refs:
  - ~/coding-brain/04_Registries/Issue Registry.md（ISS-20260428-cr-parcel-lowfreq）
  - ~/coding-brain/04_Registries/Metric Registry.md
provenance: {source_revisions: [CR parcel 5x], decision_ref: null, created_at: 2026-08-13}
```

---

## 以下 CASE-0013~0018 来源：同事 non_goods round3 分析包（checkpoint-342）

## CASE-0013 non_goods 多字段同值冒充（跨字段复用同值同 bbox）

```yaml
case_id: CASE-0013
run_ref: round3 non-goods checkpoint-342（vLLM 0.16 no-tower 双 LoRA）
fields: [issuing_bank, available_with, collection_bank_nan, beneficiary_bank, beneficiary_account, reference, order_number, document_no, reference_no, swb_id]
layout: {document_type: mixed_non_goods, cluster: null, page_role: multi_block}
problem:
  pattern_id: NG-SAME-VALUE-CROSS-FIELD
  symptom_metric: 多字段输出完全相同的值+bbox——aco issuing_bank=available_with=collection_bank_nan(BANK OF NINGBO)；pi beneficiary_bank=beneficiary_account(同一 IBAN)；pi reference=order_number(PO-BC-001024)；swb document_no=reference_no=swb_id(NAM7900733)
intervention: 无（失败观察）
outcome:
  baseline_ref: null
  delta: {round3 non-goods F1: 0.8044}
  protected_regression: null
evidence_refs:
  - records/round3_badcase_recheck/report.md（逐图判定：1649d108/61b23e31/9ace41a4/0144fb97 明确复现）
  - records/round3_eval/ROUND3_HANDOFF.md
provenance: {source_revisions: [20260717_cluster_8to2_v1 test], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0014 checkbox/份数字段幻觉（无值输出 0 或错误值）

```yaml
case_id: CASE-0014
run_ref: round3 non-goods checkpoint-342
fields: [certification_of_origi, original_bl, commercial_invoice, customs_invoice, insurance_policy, draft]
layout: {document_type: aco, cluster: null, page_role: multi_block}
problem:
  pattern_id: NG-CHECKBOX-HALLUCINATION
  symptom_metric: 份数/checkbox 字段错配——certification_of_origi=B/L、original_bl=125100148...；多个缺失/checkbox 字段输出 0，违背"无值不出 key"
intervention: 无（失败观察）
outcome:
  baseline_ref: null
  delta: {aco F1: 0.8565, badcase 522 行}
  protected_regression: null
evidence_refs:
  - records/round3_badcase_recheck/report.md（0885e398 部分复现）
  - records/round3_eval/ROUND3_HANDOFF.md（aco 优先级 2）
provenance: {source_revisions: [20260717_cluster_8to2_v1 test], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0015 形式发票漏 buyer/buyer_address（当事人混淆）

```yaml
case_id: CASE-0015
run_ref: round3 non-goods checkpoint-342
fields: [buyer, buyer_address, consignee, consignee_address]
layout: {document_type: proforma_invoice, cluster: pi, page_role: multi_block}
problem:
  pattern_id: NG-PARTY-OMISSION
  symptom_metric: 非货描输出无 buyer/buyer_address，只输出 consignee/consignee_address
intervention: 无（失败观察）
outcome:
  baseline_ref: null
  delta: {pi F1: 0.6320（10 单据最低）, badcase 158 行}
  protected_regression: null
evidence_refs:
  - records/round3_badcase_recheck/report.md（0b63a76d 明确复现）
  - records/round3_eval/ROUND3_HANDOFF.md（pi 优先级 4）
provenance: {source_revisions: [20260717_cluster_8to2_v1 test], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0016 销售订单 group 缺 goods_name

```yaml
case_id: CASE-0016
run_ref: round3 non-goods checkpoint-342
fields: [goods_name]
layout: {document_type: sales_order, cluster: so, page_role: dense_table}
problem:
  pattern_id: NG-GROUP-FIELD-OMISSION
  symptom_metric: 10 个 group 全部缺少 goods_name（前两行漏抽，范围更大）
intervention: 无（失败观察）
outcome:
  baseline_ref: null
  delta: {so F1: 0.8575, badcase 112 行}
  protected_regression: null
evidence_refs:
  - records/round3_badcase_recheck/report.md（3471b630 部分复现）
provenance: {source_revisions: [20260717_cluster_8to2_v1 test], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0017 多行单价漏归组

```yaml
case_id: CASE-0017
run_ref: round3 non-goods checkpoint-342
fields: [price_of_goods]
layout: {document_type: proforma_invoice, cluster: pi, page_role: dense_table}
problem:
  pattern_id: NG-PRICE-ROW-UNGROUPED
  symptom_metric: 4 条明细的 quantity/amount 已逐行抽取，但单价只输出 1 个独立 price_of_goods=USD 19.00，未逐行归组
intervention: 无（失败观察）
outcome:
  baseline_ref: null
  delta: null
  protected_regression: null
evidence_refs:
  - records/round3_badcase_recheck/report.md（33737a32 部分复现）
provenance: {source_revisions: [20260717_cluster_8to2_v1 test], decision_ref: null, created_at: 2026-08-13}
```

## CASE-0018 海运单字段幻觉（从错误区域取值）

```yaml
case_id: CASE-0018
run_ref: round3 non-goods checkpoint-342
fields: [freight_payable_at, document_no, container_no]
layout: {document_type: sea_waybill, cluster: swb, page_role: multi_block}
problem:
  pattern_id: NG-FIELD-HALLUCINATION
  symptom_metric: freight_payable_at=NAGOYA;JAPAN 从其他港口/地点区域冒出（图内 Freight Payable 区域无该值）；container_no 被 non-goods 同 bbox 复用为 document_no
intervention: 无（失败观察）
outcome:
  baseline_ref: null
  delta: {swb F1: 0.8213, badcase 301 行}
  protected_regression: null
evidence_refs:
  - records/round3_badcase_recheck/report.md（020223e3/07944f15 部分复现）
  - records/round3_eval/ROUND3_HANDOFF.md（swb 优先级 3）
provenance: {source_revisions: [20260717_cluster_8to2_v1 test], decision_ref: null, created_at: 2026-08-13}
```
