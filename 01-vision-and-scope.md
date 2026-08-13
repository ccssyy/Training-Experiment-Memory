# ATF 训练经验 Memory 调研与讨论稿

> 分支：`work/20260808-atf-training-experience-memory`
>
> 日期：2026-08-08
>
> 状态：调研讨论稿，不是已接受的产品合同、训练准入或实现授权
>
> 目标：评估“持久化训练经验 memory”能否提高一次训练得到好模型的成功率，并提出与 ATF v0.1.0 兼容的后续设计边界。

## 1. 先给结论

这个构想值得进入 ATF 的下一阶段，而且它补上了当前流程最重要的价值缺口：ATF 可以减少一次训练流程的人工等待和调度时间，但“完成一轮训练”不等于“更快得到可用模型”。训练经验 memory 通过训练前任务画像、历史方案检索、训练后 badcase 归因和受控经验回灌，有机会减少盲试次数，提升首轮命中率。

但 memory 不应从“经验知识库”直接做成一个会自动改参数的 RAG。最小可辩护的定义是：

```text
不可变实验事实
  -> 结构化问题/策略/结果卡片
  -> 证据等级与适用边界
  -> 训练前候选方案
  -> 受保护指标下的单变量验证
  -> 通过后才进入 validated memory
```

最重要的判断有五条：

1. **先存事实，再存经验。** 数据分布、split、Prompt/schema、训练配置、运行时和指标必须能回溯到 immutable artifact；“某参数有效”不能脱离这些上下文。
2. **经验条目必须表达失败和不适用条件。** 只存成功案例会造成策略过拟合和幸存者偏差；历史上 GB512 长训、后期 checkpoint、字段 targeted 修复都有“局部提升、整体回归”的反例。
3. **推荐必须是候选方案，不是自动执行。** 在当前 v0.1.0 的 `plan/dry_run/execute` 边界下，memory 只能生成带证据的 `Suggestion` 和方案 diff；不能自动修改数据、Prompt 或训练参数。
4. **“好模型”必须定义为 prior-best baseline 上的业务收益。** 不能用当前实验内部最佳 checkpoint 代替全局 baseline，也不能用污染或字段合同不一致的评估结果更新 memory。
5. **MVP 应先解决可追溯、可检索、可验证，不先建设向量数据库。** 结构化索引 + Markdown/JSON 证据卡足以验证价值；等检索质量和写入 Gate 稳定后再引入 embedding 或图数据库。

## 2. 对构想的完善：从知识库升级为“训练决策记忆”

### 2.1 Memory 不是一张经验表

建议把 memory 分为四层，分离事实 owner 与经验 owner：

| 层 | 保存内容 | 是否可作为事实 | 典型 owner |
| --- | --- | --- | --- |
| `Fact` | 数据集、样本、cluster、字段、Prompt、训练包、运行时、checkpoint、raw completion、metrics、badcase | 是 | Artifact Catalog / Operation Journal / Decision Ledger |
| `Profile` | 任务画像、数据版式画像、字段难度画像、输出长度与运行时画像 | 仅在引用事实后成立 | profile/query skill |
| `Experience` | 问题模式、干预策略、适用条件、收益、代价、失败边界、证据等级 | 否，是可审计的推断 | memory curator |
| `Suggestion` | 针对新任务生成的候选训练方案和保护条件 | 否，是待人工接受的建议 | strategy skill |

因此不建议把所有文本、badcase 截图和人工结论直接向量化。检索命中后必须回到 `Fact`，确认 source revision、scope、split、字段合同和评估口径一致。

### 2.2 一条可复用经验的最小结构

每个 `ExperienceCard` 至少包含：

```yaml
experience_id: EXP-KIE-0001
status: observed | candidate | validated | rejected | superseded | expired
scope:
  task_family: document_kie
  lane: goods | non_goods | mixed
  document_types: [packing_list]
  domain: [bank_a, customs]
  layout_tags: [dense_table, multi_block, repeated_rows]
problem:
  pattern_id: PL-ROW-UNDERCOUNT
  symptom: row_delta_negative
  affected_fields: [goods_quantity, item_no, product_no]
  evidence_refs: [ArtifactRef...]
intervention:
  strategy_id: STR-TARGETED-ROW-ALIGNMENT
  changes: [data_slice, field_quota, prompt_anchor, cutoff]
  frozen_variables: [base_model, eval_set, metric_policy]
outcome:
  baseline_ref: prior-best
  candidate_ref: run/checkpoint
  delta: {macro_f1: ..., recall: ..., row_under_count: ...}
  protected_metrics: {...}
  cost: {gpu_hours: ..., wall_time: ...}
  stability: {seeds: ..., ci95: ...}
applicability:
  preconditions: [...]
  contraindications: [...]
  confidence: low | medium | high
provenance:
  source_revisions: [...]
  decision_ref: ...
  reviewer_refs: [...]
  created_at: ...
  expires_at: ...
```

关键点是同时存 `change`、`outcome`、`cost` 和 `contraindications`。没有对照变量、保护指标或失败边界的文字只能是 `candidate`，不能成为自动推荐依据。

## 3. Memory 应包含的内容方向

### 3.1 任务与数据画像

这是训练前分析的入口，应由确定性统计产生，再由模型或 Agent 做解释：

- 任务目标：字段 KIE、货描/非货描 lane、是否含 group、是否要求 bbox、是否跨页。
- 文档类型与业务域：单据类别、银行/供应商/国家、语言、扫描来源、拍照/传真/电子 PDF。
- 物理数据规模：唯一图片数、JSONL 行数、每图 mode 数、正/负样本比例、空值语义、缺图和解析失败。
- 版式结构：family、cluster、页面尺寸/长宽比、版面区域数量、表格行数、跨页关系、旋转/倾斜、印章/手写/背景噪声。
- 字段分布：字段出现率、support、长尾程度、字段共现、易混字段对、值长度/数值范围/单位分布。
- 泛化风险：raw hash、decoded pixel hash、感知 hash、document/family/cluster overlap，ID/OOD 分布。
- 输出难度：Prompt 长度、字段子集数量、group 行数、bbox 数量、completion 长度、截断和 repair 历史。

画像需要保留原始统计和派生标签，不能只保存“数据较难”这样的自然语言。

### 3.2 数据处理与构造策略

- 来源快照、标签版本、清洗规则、金额/单位/日期归一化、拒绝项。
- split 策略：随机、family-safe、cluster 内 ID/OOD、整簇 OOD、时间切分。
- 去重闭包：文件 SHA、解码像素 SHA、感知 hash、document/family/cluster。
- 字段/任务采样：全字段、字段组、单字段、易混字段对照、低频字段 floor、真实空和负样本。
- 长表构造：按真实 bbox 的窗口、无标签 planner、shared-context、跨窗合并、行级守恒。
- 数据增强：版式扰动、模糊/旋转/压缩、字体和颜色、合成表格；必须记录增强来源和是否改变字段事实。
- 数据混合：跨银行/跨单据比例、每类曝光配额、是否保持 A 域训练量不变。

### 3.3 Prompt、schema 和评估合同

- Prompt 模板、字段 map、alias、mode、seed、extend、输出 schema 版本。
- 坐标空间、范围、四点顺序、page_id、group 容器、缺失字段和真实空输出。
- 训练字段面与 eval 字段面的逐字段对账，排除 `train-excluded` 字段混入主指标。
- JSON parse、repair、finish reason、prompt/completion token、max token 证据。
- 指标定义：字段 exact、单据 micro/macro/weighted F1、group/row 指标、bbox 文本联合指标、prior-best 规则。

### 3.4 模型、微调和优化器策略

- 基座模型 revision、量化格式、processor、image token/像素预算。
- LoRA/QLoRA：rank、alpha、dropout、target modules、是否训练视觉塔/projector、真实 trainable names/数量。
- optimizer、LR、scheduler、warmup、global batch、gradient accumulation、cutoff、epoch/step、early-stop。
- 训练拓扑：GPU/节点、精度、FlashAttention、ZeRO、gradient checkpointing、随机种子。
- 运行时：vLLM/SGLang/Transformers 版本、LoRA 是否加载视觉模块、merge/挂载方式、generation 参数。
- 保能力策略：OCR/grounding 回放比例、base-model KL、领域 adapter 合并/路由。

### 3.5 Badcase 与根因模式

建议把 badcase 做成可比较的多标签 taxonomy，而不是单条备注：

- `ocr_character`：字符/数字识别错误。
- `bbox_localization`：框位置、裁剪或坐标转换错误。
- `field_boundary`：值边界、单位、地址、主体角色边界错误。
- `field_confusion`：相邻列或角色字段串位。
- `row_under_count` / `row_duplicate` / `row_order`：表格行构造失败。
- `missing_field` / `false_positive` / `empty_collapse`：漏抽、误抽、空输出坍缩。
- `prompt_contract` / `schema_parse` / `truncation` / `runtime`：非模型能力问题。
- `data_leakage` / `eval_contamination` / `field_surface_drift`：评估有效性问题。

每个标签要引用样本级证据、根因置信度和是否适合进入训练集。推断不能冒充已证实因果。

### 3.6 结果、代价和负知识

经验不能只记 F1：还应记录召回/精度方向、保护字段、ID/OOD retention、bootstrap CI、输出完整性、训练时间、GPU 小时、评估成本和人工复核量。

同时记录“已验证无效”或“有副作用”的方案，例如：GB512 长训、后期 checkpoint、盲目扩大学习率、将训练窗口 suffix 直接搬到推理、只按总 F1 选点。负知识能防止系统反复重走旧路径。

## 4. 当前 Qwen2.5-VL-main 历史训练经验盘点

下面只记录可由本地归档支持的事实，不把污染历史数字包装成独立泛化结论。

| 训练/实验 | 采用策略 | 遇到的困难 | 有效改善或判断 | Memory 应沉淀 |
| --- | --- | --- | --- | --- |
| 5 单据货描 Exp4 | `GB256/LR2e-4`、LoRA `r16/a32/dropout0.01`、冻结 vision/projector、密集 checkpoint 搜索 | 训练后期字段间转移，继续训练并非整体变好 | checkpoint-1015 在同口径五单据全量 macro F1 `0.8537`，优于 ep9 的 `0.8455`；checkpoint-1295 反而降到 `0.8318` | `best_checkpoint` 必须按 prior-best、macro/weighted 与保护字段联合选择；不能取最后点 |
| 5 单据货描 Exp5 fieldfix | 新版式/字段修复、BL/CI targeted 数据、字段配额、约 2% 负样本、CR `goods_parcel` 定向上采样 | CI `product_no`、BL `goods_name/quantity`、Air `total_qty` 等长尾字段仍弱，且局部修复产生回归 | CI `goods_name`、BL `goods_weight/goods_parcel` 明显恢复；但同名 badcase 中 CI 修复 83 行/回归 106 行，BL 修复 74 行/回归 112 行 | 记录“策略命中的字段”和“牺牲的保护字段”；targeted 策略必须配单变量和回归门禁 |
| 6 单据非货描 mini/Exp4 | raw-label 重新生成、mode `[0,1,5]`、约 5% 负样本、GB/LR 矩阵、早停 | GB512 后期少输出，loss 降而 F1/recall 坍缩；机器和 vLLM 不是主因 | GB256/LR2e-4 在约 1.5 epoch 得到 macro F1 `0.7672`；GB512 最好 `0.7208`，2.0 epoch 降到 `0.2903` | 训练动态必须记录空输出、平均长度、召回；按 epoch/样本曝光选 checkpoint |
| 第一轮 10 新单据 | 直接沿用历史 split/eval 与全字段评估 | goods `310/524`、non_goods `311/595` exact-image overlap；train/eval 字段面不一致 | 结论被标为 `contaminated_historical_observation`，不能用于 baseline | 污染状态必须是硬 Gate；指标不能进入 validated memory |
| 第二轮 10 新单据 badcase | group split、固定 eval、字段级/样本级 taxonomy、raw completion 审计 | 装箱单占 goods 78%、non_goods 63% 错误；漏行、重复 group、窄列串位、size/单位/角色混淆 | 明确了 `row_under_count`、`row_duplicate`、`slot_confusion` 等根因；不是单纯 OCR 失败 | badcase taxonomy 是经验抽取的主输入；每条策略要指向具体模式 |
| 第三轮 cluster 8:2 | 同 cluster 内 8:2，保持 prompt/训练设置单变量不变 | 早期验收曾把 mode5 随机 prompt 当成 byte identity 漂移；训练包出现冻结配置回退 | 通过 canonical contract 和 directed invariant 修复 Gate，避免无意义重建 | 记录“错误 Gate 规则”本身，防止把随机性误判为数据漂移 |
| 第五轮与七单据 ID/OOD 旁路 | 训练集 487 张；cluster 内 ID、整簇 OOD-core、OOD-tail；goods/non_goods 共用物理 partition | goods 旁路长表仍低；non_goods 主要精度收益但提货单重量字段回退 | goods Base→LoRA `0.3951→0.6363`，OOD-core 仍增 `+0.2290`；non_goods `0.4314→0.4963` 但 recall 下降 | 经验要区分 ID/OOD、lane、单据和字段；micro F1 不能掩盖低支持字段回退 |
| 第五轮装箱单推理链路 | 无标签 planner、窗口/完整图混合、fallback、字段/文本/IoU 去重 | suffix 直接搬到推理对多窗样本有损；planner 失败会被误计为空 | 混合链路使 PL F1 `0.6560→0.6744`，planner 失败 4 张由 0 拉到 `0.7458` | 推理路径是策略维度；训练策略不能与 serving/切窗策略分开记录 |
| 历史运行时 | QLoRA 训练或 AWQ/vLLM 推理，部分服务未加载 `visual.*` LoRA | 参数名显示“all”但 runtime receipt 证明视觉侧模块被忽略 | 历史指标只能按“语言侧 LoRA 加载”解释 | `trainable_set` 与 `loaded_adapter_set` 必须是强制证据 |
| 2026-08 字段合同审计 | 对 8 类单据训练标签、Gold、预测字段做合同对齐 | 发现字段定义/单位/别名/训练排除面漂移 | 只能说明合同状态，不能替代业务指标 | schema revision 变化要使旧经验自动降级或失效 |

### 4.1 已确认的困难单据和困难模式

当前最稳定的困难排序不是按单据总 F1 单一排序，而是按“错误机制”：

- **装箱单货描**：长表、重复主体、相邻窄列、列角色绑定、行低估/重复，是当前最高价值难点；F1 低只是结果。
- **装箱单非货描**：`size`、重量标题单位、角色字段、双区域布局，误报和字段合同问题并存。
- **提货单非货描**：`total_net_weight`、`total_gross_weight` 的召回回退，不能只加 epoch。
- **BL 货描/非货描**：地址/角色边界、订单号、货名/数量，targeted 只恢复了部分重量/件数类字段。
- **CI 货描**：`product_no`、`goods_name` 与 item code/HS code 角色混淆；货名 targeted 有效但产品编号仍弱。
- **Air**：`total_qty` 是召回型长尾字段，继续训练会与 `goods_quantity/goods_carton` 发生字段间转移。
- **低 support 字段**：例如 CR `goods_parcel`，单次变化可能很大，只能作为观察或专项门禁。

### 4.2 历史策略的可迁移性判断

- `GB256/LR2e-4 + 早停`：在当前 Qwen3-VL/QLoRA 数据规模上有重复支持，暂可作为候选默认；不应推广到不同基座、不同 batch 或不同输出长度而不复验。
- `targeted field sampling`：对低分字段有效，但必须配保护字段和对照；不能把复制样本数量直接当收益。
- `cluster-safe split + ID/OOD`：是评估有效性策略，不是模型优化技巧；但它决定 memory 是否允许记录收益。
- `mode 0/1/5`：目前是项目内稳定的数据生成手段，mode5 的随机子字段应记录算法和 seed，不应要求跨 run 字节完全相同。
- `planner/window/fallback`：属于推理/数据流策略，不能把推理链路收益误归因到训练参数。
- `visual.*` LoRA：历史证据不足以证明启用视觉 adapter 一定更好；先补 runtime identity，再做单变量消融。

## 5. 公开资料给出的可迁移方法

### 5.1 文档模型与 KIE

| 方法 | 一手证据给出的启发 | 对 ATF memory 的可记录策略 |
| --- | --- | --- |
| Qwen2.5-VL | 动态分辨率、文档解析、结构化抽取和定位是模型能力的一部分 | 记录视觉预算、processor、坐标 schema 与任务类型；同一模型不同预算不可视为同一策略 |
| LayoutLMv3 | 统一文本/图像 masking 与 word-patch alignment 改善文本中心和图像中心 Document AI | 适合作为 OCR+layout 专家或教师；记录 layout/text 预训练和字段任务的适用边界 |
| Donut | OCR-free 端到端文档理解，提供可控的合成数据生成 | 记录 OCR-free 与 OCR-dependent 路线选择；合成数据必须保留 renderer/domain 参数 |
| DocLLM | 用文本与 bbox 的 layout-aware 生成建模不规则布局 | 对密集 KIE 可形成 `OCR/layout facts -> 语义映射` 候选线，不能直接替换图像 VLM |
| 业务文档专用预训练 | 额外的版面任务、数字数量级任务和 BIESO 解码改善 invoice/receipt/PO 信息抽取 | 对金额、数量、单位和复杂实体建立专门 task/metric，而不是只加整页 SFT |
| KIEval | 将实体抽取与结构化分组同时评估，更贴近工业 KIE | 把 group/row 正确率、行低估/重复和字段 F1 并列为业务指标 |
| SynDoc | 结构信息抽取、领域 query 合成、adaptive instruction tuning、递归推理 | 作为合成数据和迭代推理的研究候选；进入 validated memory 前必须有私有数据对照 |

### 5.2 数据中心与主动学习

公开数据中心 AI 研究把工作拆为 training data development、inference data development 和 data maintenance；这与 ATF 的数据准入、评估和归档天然对应。主动学习的可迁移策略不是“挑模型最不确定的图”这么简单，应同时考虑：

- **不确定性**：生成分布、多个 checkpoint/模型 disagreement、JSON repair 或 low-confidence OCR。
- **代表性**：避免只挑相似 badcase，按 family/cluster/字段共现覆盖。
- **多样性**：对长表行数、版式密度、旋转、噪声、语言、单位等做分层。
- **业务价值**：优先影响 prior-best 保护字段或高成本人工复核的错误。

因此 `sample_selection` 经验卡必须记录选择函数、阈值、覆盖约束和反事实对照，不能只写“选择 hard examples”。

### 5.3 PEFT、保能力与后训练

QLoRA 证明 4-bit 量化基座上训练 LoRA 可以降低显存，且高质量小数据集可以取得强效果；这支持 ATF 将“高质量、可解释、低冗余”的数据策略纳入 memory，但不支持自动推断最佳 rank/LR。LoRA 的遗忘较少但并非无遗忘，建议把 OCR/grounding 回放、较低 LR、target module 和 KL/adapter 路由作为分开的可验证策略。

DPO/GRPO/RLAIF-V、self-training 和 recursive inference 可能改善偏好或稳定性，但它们需要可审计的 reward、偏好对和模型输出质量控制。当前单据 KIE 已有明确 Gold 和字段级 badcase，第一阶段仍应优先 SFT、数据修复、候选约束和早停。

## 6. 建议的 ATF 闭环

### 6.1 训练前

```text
新任务输入
  -> 数据/任务 Profile
  -> 检索相似 ExperienceCard
  -> 生成 1 个 baseline + 至多 2 个 candidate 方案
  -> 显示证据、适用条件、风险和预计成本
  -> 人工接受/修改/拒绝
  -> 形成 immutable TrainingPlan
```

训练前分析至少要回答：

1. 新任务最可能的困难是 OCR、坐标、字段边界、表格行、跨页还是合同问题？
2. 历史上相似任务有哪些“成功”和“失败”策略？相似度来自哪些字段？
3. 当前数据缺什么支持：family/cluster、字段 support、易混字段对、长表行型、空值和噪声？
4. 方案改变哪些变量，保护哪些字段，何时停止，成功后如何写入 memory？

### 6.2 训练中

训练运行不写 memory，而是写运行事实和 telemetry：

- 每个 checkpoint 的 loss、macro/micro/weighted F1、recall、关键字段、ID/OOD、空输出、平均 completion 长度。
- trainable module set、runtime loaded adapter set、生成参数、processor/image grid、资源和 wall time。
- 训练数据曝光量、字段/任务配额、实际样本数、负样本和长输出比例。

当出现输出坍缩、字段回归或 runtime 漂移时，系统生成 `blocked` 或 `candidate` 结论，不把失败 run 直接升级为经验。

### 6.3 训练后

```text
checkpoint/eval closure
  -> prior-best compare
  -> badcase taxonomy + root-cause confidence
  -> 单变量或最小干预方案
  -> 保护字段/ID-OOD/输出完整性 Gate
  -> human accept/reject
  -> validated/rejected ExperienceCard
```

有效建议的“沉淀条件”应包括：同一冻结 eval set、同一 metric policy、可识别的 controlled variable、至少一个保护指标、raw completion 和运行时证据、业务 reviewer/QA join。只有结构或格式校验通过而业务证据未闭合时，状态应为 `pending/block`。

## 7. Memory 的检索和写入机制

### 7.1 先结构化检索，后语义检索

第一版推荐：

1. 结构化过滤：`task_family`、lane、document_type、field_set、layout_tags、split_policy、base_model、schema_revision、runtime。
2. 事实相似度：字段分布、版式密度、行数分位数、输出长度、错误 taxonomy、ID/OOD retention。
3. 文本/embedding 作为召回补充，不参与最终适用性判断。
4. 返回前三条经验和一条“无可靠历史匹配”结果；无匹配时走 baseline，不猜测。

这样可以避免把“看起来像 packing list”的旧策略错误套到不同 schema 或不同评估口径任务。

### 7.2 经验状态与证据等级

建议采用单调状态和证据等级：

| 等级 | 含义 | 允许作用 |
| --- | --- | --- |
| `E0` | 人工观察/公开资料迁移，未在私有任务验证 | 只能提示研究方向 |
| `E1` | 单次可复算对照，变量和指标完整 | 可生成候选方案，不自动采用 |
| `E2` | 同一 domain/任务在不同 split 或 seed 复现 | 可列为默认候选，仍需保护指标 |
| `E3` | 跨 domain/文档类型复现，收益和成本稳定 | 可进入策略 preset，仍不可绕过 Gate |

`rejected` 和 `superseded` 也要保留，以阻止重复试错；schema、base model、runtime 或数据分布变化时自动降级为 `expired/review_required`。

### 7.3 不应把什么写入 memory

- 原始含 PII 的图片、完整训练数据或密钥、远端 endpoint。
- 没有 prior-best 对照的单次 F1。
- 污染 eval、字段面漂移或 raw completion 缺失的结果。
- 只引用目录 mtime、最新 checkpoint 名称或人工“看起来不错”的结论。
- 将推理链路、训练策略和数据修复混成一个不可拆分的“成功配方”。

## 8. MVP 设计和验收边界

### 8.1 第一阶段只做三件事

1. **经验卡 schema + 证据索引**：从已有归档导入 10–20 条高价值经验，全部标记来源和状态。
2. **任务画像与只读检索**：输入新任务和数据 manifest，输出 profile、匹配经验、证据缺口和候选方案，不写上游。
3. **闭环回灌 fixture**：用 fake run 验证 badcase -> suggestion -> validated/rejected 的状态流，不启动真实训练。

不建议第一版做自动超参搜索、向量数据库、自动标注回灌或跨项目共享 memory；它们会扩大事实 owner 和隐私边界，且无法证明首轮成功率改善。

### 8.2 可接受的 MVP 验收

- 对一个新 `packing_list` fixture，能输出数据画像、Top-3 经验、每条经验的证据和不适用条件。
- 任何经验卡均能回溯到 immutable source revision 和 prior-best 对照。
- 污染、字段合同不一致、跨 run/mode 引用或缺 raw evidence 的条目自动 `block`。
- 相同输入多次检索结果、排序和 `plan_digest` 一致。
- `plan` 不创建 Operation；`dry_run` 只写隔离 simulation facts；`execute` 在 v0.1.0 仍拒绝。
- 反馈闭环可以明确区分“业务收益已证实”“工程证据完整但业务 pending”“策略无效/回归”。

### 8.3 成功指标

不要把“memory 条目数”当成功指标。第一阶段应该测：

- 首轮方案采纳后，达到 prior-best 保护线所需的训练尝试数/墙钟时间是否下降。
- 相似任务上，memory 推荐的候选是否比无 memory baseline 更快发现有效变量。
- 误推荐率、无匹配率、经验过期率和被人工拒绝率。
- 经验条目引用完整率、业务证据闭合率、污染/合同冲突拦截率。
- 训练成本：GPU 小时、人工复核样本数、评估请求数。

## 9. 还应补充的几个方向

1. **成本感知目标**：把“到达可用模型的时间”定义为 `训练 + 评估 + badcase 人工 + 重训`，而不是只优化单轮 wall time。
2. **反事实记录**：保留未采用的候选策略、停止原因和差异，以免成功经验被错误归因。
3. **稳定性**：对低 support 字段和 OOD-tail 使用 bootstrap/seed 区间，不能用一次尖峰写成稳定策略。
4. **隐私和脱敏**：memory 只保存 hash、统计、脱敏文本片段和结构标签，原图留在受控 Artifact Catalog。
5. **经验版本化**：schema revision、Prompt revision、base model revision、runtime 版本变化都要触发再验证，而不是静默复用。
6. **负知识和冲突处理**：同时存在“收益”和“回归”的策略必须按条件分叉；不能由最新时间戳覆盖旧结论。
7. **多模型/多 adapter 路由**：当普通页、长表、OCR 前端的最佳模型不同，memory 应推荐组合方案，而不是强迫所有任务使用一个 checkpoint。

## 10. 讨论问题

下一轮设计需要先与你确认三个产品选择：

1. memory 的第一目标是“减少达到 prior-best 的训练次数”，还是“减少总 GPU/人工成本”？两者会影响策略排序和成功指标。
2. 第一版是否只服务 Qwen2.5/3-VL 单据 KIE，还是从一开始保留模型无关的任务画像字段？建议公共事实模型保持通用，策略卡先限定在 KIE。
3. 是否接受“推荐策略必须人工确认”，还是希望在满足历史高置信度和保护指标的情况下自动填充训练计划？建议首版只自动填充草案，不自动执行。

## 11. 证据索引

### 本地训练史

- `/data/sam/Qwen2.5-VL-main/docs/performance/2026-08-04-5goods-exp5-and-6other-exp4-complete-experiment-archive.md`
- `/data/sam/Qwen2.5-VL-main/docs/performance/2026-05-12-exp4-best-checkpoint-selection.md`
- `/data/sam/Qwen2.5-VL-main/docs/performance/2026-05-16-6other-po0512-regen-formal-gb-lr-scaling.md`
- `/data/sam/Qwen2.5-VL-main/docs/performance/2026-07-14-round2-10docs-badcase-analysis.md`
- `/data/sam/Qwen2.5-VL-main/docs/performance/2026-07-30-round5-and-7docs-cluster-id-ood-results.md`
- `/data/sam/Qwen2.5-VL-main/docs/performance/2026-08-04-10docs-bypass-id-ood-complete-experiment-archive.md`
- `/data/sam/Qwen2.5-VL-main/docs/data/2026-08-05-training-preflight-lessons.md`
- `/data/sam/AgenticTrainingFlow/.worktrees/research-doc-parsing/docs/research/2026-07-24-document-kie-training-optimization.md`
- `/data/sam/AgenticTrainingFlow/.worktrees/research-doc-parsing/docs/research/2026-07-24-document-kie-actionable-optimization.md`

### 公开一手来源

- [Qwen2.5-VL Technical Report](https://arxiv.org/abs/2502.13923)
- [Qwen2.5-VL 官方代码仓库](https://github.com/QwenLM/Qwen2.5-VL)
- [LayoutLMv3](https://arxiv.org/abs/2204.08387)
- [Donut](https://arxiv.org/abs/2111.15664)
- [DocLLM](https://arxiv.org/abs/2401.00908)
- [Improving Information Extraction on Business Documents with Specific Pre-Training Tasks](https://arxiv.org/abs/2309.05429)
- [KIEval: Evaluation Metric for Document Key Information Extraction](https://arxiv.org/abs/2503.05488)
- [QLoRA](https://arxiv.org/abs/2305.14314)
- [A Survey of Deep Active Learning](https://arxiv.org/abs/2009.00236)
- [Data-centric AI: Perspectives and Challenges](https://arxiv.org/abs/2211.12542)
- [PaddleOCR-VL-1.6](https://arxiv.org/abs/2606.03264)
- [PaddleOCR-VL 官方流水线](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/pipeline_usage/PaddleOCR-VL.en.md)
- [MinerU2.5](https://arxiv.org/abs/2509.22186)
- [SynDoc](https://arxiv.org/abs/2509.23273)
- [LoRA Learns Less and Forgets Less](https://arxiv.org/abs/2405.09673)

## 12. 研究限制

- 外部检索 API 在本轮返回 404，外部证据通过可访问的 arXiv API/官方仓库 URL 交叉核验；未把无法访问的二手博客当作结论依据。
- 公开论文报告的 benchmark 增益不能直接外推到私有银行单据；所有外部方法都标记为候选策略，必须在同一私有 frozen eval 上验证。
- 本文未启动真实训练、评估、远端服务或数据写入；所有成本和收益仍是待验证目标。
