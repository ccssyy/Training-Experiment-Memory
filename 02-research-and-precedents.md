# 训练经验 Memory 深度调研与设计讨论稿（v2）

> 分支：`work/20260810-training-experience-memory-research`（基于 C02 golden 基线 14a8e8f 新建）
>
> 日期：2026-08-10
>
> 状态：深度调研讨论稿，不是已接受的产品合同、训练准入或实现授权
>
> 前置阅读：`docs/research/2026-08-08-atf-training-experience-memory.md`（v1 构想与四层模型）

## 0. 一句话结论

构想可行且有直接先例（XAutoLM 的 experience store 是最接近的系统），关键不在"能不能做"，而在：**经验条目必须绑定证据、表达失败边界、作为候选方案而非自动执行注入训练流程**。本次深度调研补充了互联网先例、Qwen 历史可沉淀经验清单、以及与 ATF 五模块/Gate/事实 owner 的集成设计。

## 1. 互联网调研：业界先例与可行度

### 1.1 最接近的先例

| 系统/工作 | 核心思想 | 对本构想的启示 |
|---|---|---|
| **XAutoLM**（EMNLP 2025, arXiv:2508.00924） | experience store 每条经验 = 四元组（配置, 指标, 任务元特征, 系统资源），分正/负经验；新任务按相似度检索、指数核加权生成"经验先验"热启动 AutoML；评估耗时最高降 4.5x、错误率降 7 倍 | **负经验用于回避"昂贵死胡同"**；任务元特征是检索键；结果写回形成闭环 |
| **APT: Weakness Case Acquisition and Iterative Preference Training**（arXiv:2506.03483） | badcase → 偏好训练闭环，只用出错样本迭代，Llama2-7b 通用能力不降反升 | 验证"只学错题"的 badcase 驱动迭代有效 |
| **DataFlywheel 数据飞轮** | 采集 → 坏样本识别（评分阈值自动触发）→ 改进注入 → 导出重标注 → LoRA 重训练 → 部署 | 阈值自动触发，无需人工盯仪表盘 |
| **Grab Vision LLM 工程实录** | LoRA 在非拉丁文字/密集小字版面失败 → 根因诊断（vision encoder 未见字形）→ 转向两阶段全量微调 → 自建 1B 模型 | **失败经验如何改写训练策略**的教科书案例 |
| **Case-Driven Multi-Agent 框架** | 用户/标注/优化三智能体，坏 case 驱动微调，可复用"先例"写入全局记忆 | 经验库 + 规则演进的"双写"模式 |

### 1.2 单据 KIE 微调公开最佳实践（可沉淀为经验条目）

- **数据集与评估**：PaddleOCR KIE 全流程（SER/RE 标注、四点 bbox、hmean 字段级指标）；VDInstruct 证明高分辨率下每页 500 token 可 SOTA（F1 超 DocOwl1.5 +5.5）。
- **防泄漏**：MinHash/n-gram 去重；**按文档/主体 family/group split 而非随机切分**；分层 eval。
- **负样本**：合成负样本 + 硬负样本是 KIE 鲁棒性关键；合成数据比例 ≤50%，保留真实锚点。
- **过拟合**：SFT 7B 级 epoch 2-3 即可；Label Mask 错误是"训练无效"头号原因。
- **LoRA 参数共识**：rank 16 起步（复杂 32-64）、alpha≈2r、all-linear、lr 2e-4 + cosine + 3% warmup、bf16；先跑几百样本 pilot 抓格式/lr bug。
- **评估污染防控**：固定 eval 集 + 与 base model（最优 prompt）和 RAG 基线对比；遗忘检测 MMLU 跌 >2 点即过拟合。

### 1.3 知识库设计模式

- **混合检索**（2026 主流）：向量语义 + BM25 + metadata 过滤 + rerank；KIE 建议加规则维度（字段集合匹配：同样缺"税额/银行账号"字段的失败经验优先命中）。
- **Agent 集成两时点**：训练前生成任务画像 → 检索 top-k → LLM 汇总策略建议卡；训练后 badcase 结论经验证（二次训练/人工确认）才写库。
- **防过期**：时间戳加权、新策略优先 + 冲突检测；每条经验绑定证据（数据集版本、run 记录、badcase 样本）。

## 2. Qwen2.5-VL-main 历史训练可沉淀经验清单

（来源：docs/performance/ 20+ 份报告 + session-digests + 8/5 预检经验 + 7/24 调研）

### 2.1 已验证有效的训练策略（带出处）

1. **GB256/LR2e-4 稳定主线**：GB512 后期输出坍缩（ckpt80 全 0），sqrt LR 缩放无收益 → 参数域经验条目。
2. **密集保存 + 多 checkpoint 评估 + 早停**：最优非最后 checkpoint（macro F1 最高 ckpt1575 但带风险标记，选 ckpt1015）；0.003 平局阈值 + 风险标记（Total F1 降>0.02、关键字段降>0.05）。
3. **2% 负样本防"无条件输出非空 JSON"**。
4. **targeted 增强 + 字段配额 + floor 保护**：压缩低分字段权重避免样本膨胀；低频字段受控重复必须标记来源（score_note）。
5. **mode0/1/5 数据生成**：全字段/分组/随机子字段三模式；mode5 需字段锚点与存在性约束，仅作受控增强不掩盖覆盖不足。
6. **长表分段训练**：≥10 行表生成连续重叠 core/宽范围随机 core；训练标签切窗、推理 planner 且不读测试标签。
7. **金额清洗**：value 去币种、currency 独立、bbox 保留；训练/测试/repair 同一清洗函数（销售合同去 USD 后 amount F1 0.4211→1.0000，纯格式问题）。
8. **QLoRA（BNB4+Bf16）language-only**：显式 target 7 个线性层；**vLLM 版本与 LoRA 模块加载直接影响 bbox**（0.16 no-tower IoU 0.747 vs 0.21 tower-enabled 0.068）→ 运行时同合同。
9. **cluster 整簇留出 + ID/OOD 双层评测**：随机图片切分无法回答版式泛化（7docs 487 训练图按 cluster 划分后 ID/OOD 均有增益）。

### 2.2 困难单据与困难字段（problem pattern 库素材）

- **装箱单（最难点）**：占 goods lane 78%、non_goods 63.2% 错误；机制量化：明细行漏构造（row_delta<0 占 84/202）、重复 group（20/202 共 168 次）、相邻数值列串位（87/202 共 386 次）、列角色绑定失败。
- **CI**：product_no 严重漏抽（F1 0.3509）、item_no、goods_name 长文本。
- **Air**：total_qty 高精度低召回；**CR**：goods_parcel 低频 support 15 波动大。
- **金额类**：币种混入 value 导致 exact 判错（纯格式问题非模型进步）。
- **bbox 定位**：受 vLLM 版本和 tower LoRA 加载影响巨大。

### 2.3 数据构建与质量经验（必做门禁）

- **泄漏闭包**：文件 SHA、解码像素 SHA、感知 hash、document/family/cluster 全参与；stem-only 不够（旧 6/5 单据实验存在内容级 train/test 重叠，stem 校验抓不住改名副本）。
- **train/test 字段级分布对账**：字段支持数、值数、长度、单位、币种、容差、明细行数分布。
- **字段面四方对齐**：prompt/训练标签/Gold/evaluator 必须一致（round1 9 个训练排除字段仍入评估 → 整体判 contaminated）。
- **真实空样本 vs mode5 假空样本区分**；无效空标签图（135 张）从训练/测试剔除。
- **label rebuild 严格只读源**、版本号解析取最大、不可覆盖原子发布、冲突 hard fail。

### 2.4 评估与口径经验

- **test lock + 四状态**（valid_eval/contaminated/contract 失效/证据不足）；污染结果只作历史追溯。
- **固定测试集 + manifest + SHA256**；同 checkpoint rerun 波动（+0.0077 macro）只记运行时非确定性。
- **分层指标**：micro/macro/P/R/F1/Acc/support、按 lane/单据/字段/cluster/ID-OOD；低 support 只观察。

## 3. 知识库构建方案（结合 ATF 架构）

### 3.1 与 ATF 四层模型对齐（继承 8/8 v1 稿）

沿用 v1 的 Fact / Profile / Experience / Suggestion 四层，但补充与 ATF 现有概念的双向映射：

| ATF 现有概念 | memory 中的角色 |
|---|---|
| Artifact Catalog（事实 owner） | Fact 层的事实源：ArtifactRef 必须可回溯 |
| Operation Journal | 训练/评估 operation 记录即经验 provenance |
| Decision Ledger | 人工决策是经验 validate/rejected 的裁判记录 |
| Approval Ledger | 经验入库前的受控批准 |
| `Suggestion`（envelope） | 训练前策略推荐的载体——**复用现有 envelope，不新造** |
| GateResult（G1-G7） | 经验写入/检索的 Gate：缺证据 block |
| Skill Registry | 新增 memory-curator / strategy-advisor Skill 的注册位 |

### 3.2 经验条目 Schema（在 v1 ExperienceCard 基础上增补）

```yaml
experience_id: EXP-KIE-0001
status: observed | candidate | validated | rejected | superseded | expired
task_profile:            # 任务画像 = 检索键
  document_types: [packing_list]
  field_fingerprint: [goods_name, goods_quantity, ...]  # 字段集合指纹
  layout_tags: [dense_table, repeated_rows]
  lane: goods
problem:
  pattern_id: PL-ROW-UNDERCOUNT
  symptom_metric: {row_delta_negative: 84/202, repeated_group: 20/202}
  evidence_refs: [ArtifactRef]
intervention:
  strategy_id: STR-TARGETED-ROW-ALIGNMENT
  changes: [data_slice, field_quota, prompt_anchor]
  frozen_variables: [base_model, eval_set, metric_policy]
outcome:
  baseline_ref: prior-best        # 必须对 prior-best，不许对实验内部最佳
  delta: {macro_f1: +0.0112, recall: ...}
  cost: {gpu_hours, wall_time}
  stability: {seeds, ci95}
applicability:
  preconditions: [...]            # 适用条件
  contraindications: [...]        # 失败边界/不适用条件（GB512、late ckpt 反例）
  confidence: low|medium|high
provenance:
  source_revisions: [...]         # 数据/代码版本
  decision_ref: ...
  created_at / expires_at
```

**关键增补**：`contraindications`（失败/不适用条件）与 `stability`（多 seed 稳定性）必须非空才允许 validated；只有 `status=validated` 的经验可进入训练前推荐。

### 3.3 训练前推荐流程（写进 Workflow）

```text
新任务原始素材
  -> profile skill：生成任务画像（确定性统计，不猜测）
  -> strategy-advisor：按字段指纹 + 版式标签 + 单据类型检索 top-k 经验
  -> 生成 Suggestion（候选方案 diff + 证据 + 保护条件）
  -> 人工/Operator 接受后才进入 plan -> dry_run -> execute
```

约束（与 v0.1.0 plan/dry_run/execute 边界一致）：memory 只能产出 Suggestion，不能自动改参数。

### 3.4 训练后经验回灌流程

```text
badcase 分析结论（evaluation-diagnosis 模块）
  -> 候选经验卡（status=candidate）
  -> 受保护指标下的单变量验证（新训练或复用历史证据）
  -> 人工 Decision（Decision Ledger 记录 validate/rejected）
  -> validated 经验入库；contraindications 同步更新
```

### 3.5 防污染与防过期的 5 条规则

1. 经验必须绑定 ArtifactRef 证据，缺证据 block。
2. 检索命中后必须回到 Fact 确认 source revision/scope/split/字段合同/评估口径一致。
3. 同一问题领域的新经验优先；冲突经验进入人工裁决（Approval Ledger）。
4. 每个经验带 expires_at，过期自动降级为 observed。
5. 不把 simulation/fake 结果写入 validated 经验（simulation 事实不得推进 canonical 知识）。

## 4. 分阶段实施路线（建议）

| 阶段 | 内容 | 验收 |
|---|---|---|
| **P0 事实索引** | 把现有 runs/ 归档的 manifest、指标、badcase 报告结构化索引（JSONL/SQLite），建立可检索的 Fact 层 | 现有 8 单据/10 单据历史可被按字段指纹检索 |
| **P1 经验卡 MVP** | 从 Qwen 历史经验清单（本文 2.x）人工沉淀 20-30 张 ExperienceCard（含失败反例）；实现检索（字段指纹规则 + 关键词，先不上向量库） | fresh Agent 可对给定任务画像返回带证据的候选策略 |
| **P2 训练前集成** | strategy-advisor Skill + 复用 Suggestion envelope；训练前生成策略建议卡 | 新任务训练前必出建议卡，人工可接受/拒绝 |
| **P3 回灌闭环** | badcase → candidate → 验证 → validated 的 workflow；写入 Gate 与污染审计 | 至少 3 条经验走完"建议→应用→验证→回灌"闭环 |
| **P4 扩展** | embedding 检索、跨项目经验迁移、经验画像可视化 | 检索质量评估（命中率/收益） |

## 5. 开放问题（待讨论）

1. **经验 owner 归属**：memory curator 是新 Skill/模块，还是挂在现有 evaluation-diagnosis / iteration 模块下？是否引入第六个事实 owner（目前架构明确定"四个 owner"）？
2. **验证成本**：candidate 经验必须"二次训练验证"才转 validated——在 GPU 未授权阶段，能否先用历史证据 + 规则推理完成初步验证（降低验证成本）？
3. **任务画像的自动生成**：画像需要确定性统计（cluster/字段分布/泄漏），哪些可以在 ATF 内自动算，哪些需要引用 Qwen 侧脚本？
4. **与 CodingBrain / session-digests 的关系**：现有 coding-brain 已是经验库，是替代、迁移还是并存？
5. **经验粒度**：字段级（product_no 难抽）vs 单据级（装箱单难）vs 策略级（长表分段）——检索和推荐粒度如何取舍？
6. **冷启动**：知识库初期只有 20-30 条经验，检索命中率低，如何设计"无经验可循"的降级路径（回退到默认 SOP）？
## 6. 讨论结论（2026-08-10 用户已定方向）

### 6.1 问题 #1：经验 owner 归属 —— 建议 MVP 不引入新 owner，P3 后再评估

**引入经验 owner（Experience Ledger）的优劣**

优点：
1. 符合 ATF "fact owner 单写" 原则，经验有明确归属、写入权限和审计路径；`audit-run` 可审计经验生命周期。
2. 经验可版本化（observed → candidate → validated → superseded），append-only + CAS，与四 owner 对称。
3. 训练前推荐/训练后回灌的可信基础：经验可绑定证据、可回滚、可追溯。
4. 架构上自然延伸："发生了什么（Artifact）/执行了什么（Operation）/批准了什么（Approval）/决定了什么（Decision）/学到了什么（Experience）" 五维事实完备。

缺点：
1. **违反现有架构不变量**（AGENTS.md 明确定义"运行事实只有四个 owner"），需要新增 ADR 变更，架构侵入大。
2. 实现成本高：新增 facts owner、状态机、投影、audit 集成、Skill 注册，且当前 C02 build 正在进行，此刻引入会打断验证节奏。
3. **与 Decision Ledger 职责重叠风险**：经验本质是"已验证的决策结论"，Decision 已记录 validate/rejected；双写会造成口径不一致。
4. 检索/推荐在 P0-P1 阶段只是查询能力，不需要独立 owner 支撑。

**不引入（经验作为 Artifact 类型 + Decision 标记）的优劣**

优点：
1. **零架构侵入**：经验卡作为 Artifact Catalog 下的 `experience-card/v1` 类型，用现有 ArtifactRef 引用，生命周期由现有 owner 管理。
2. 复用现有 Approval/Decision：经验 validate/rejected 就是一次 Decision，无新状态机。
3. 符合"Query/Skill 无副作用"原则，快速 MVP（P0-P1 不动架构）。
4. 与当前 C02 build 并行，不阻塞主线。

缺点：
1. 经验无独立事实身份，审计/恢复时依赖 Artifact + Decision 联合投影，不如独立 owner 清晰。
2. "经验是否有效"的状态没有专门 owner，易散落，需约定经验卡 schema 承载。
3. 若未来经验库规模大、检索/推荐逻辑复杂，与事实层耦合会限制扩展。

**结论（建议）**：MVP 阶段（P0-P2）不引入新 owner —— 经验卡作为 Artifact 类型（`experience-card/v1`），validate/rejected 状态由 Decision Ledger 记录并回链；待 P3 回灌闭环验证价值、检索质量稳定后，再评估是否升级为第五事实 owner（需新 ADR）。这符合"最短可辩护路径 + 先验证价值再固化架构"原则，也不打断当前 C02 节奏。

### 6.2 问题 #4：与 CodingBrain 关系 —— 完全替代，不双轨

用户反馈：CodingBrain 做得不好，现在不怎么用了。

CodingBrain 失效原因分析：
1. 人工/半自动 ingest（llm-wiki-ingest 技能），与训练流程脱节，维护不及时就过期。
2. 检索靠 rg 关键词，无任务画像/字段指纹匹配，命中率低。
3. 无自动回灌：训练结果、badcase 结论不会自动沉淀，需人工整理。
4. 经验无证据绑定和生命周期管理，无法判断经验是否仍有效。

新 memory 定位：**替代 CodingBrain，作为 ATF 内置模块**，与训练 workflow 深度集成（训练前推荐/训练后回灌），不是独立知识 wiki。关键差异：
1. **自动沉淀**：badcase 分析结论 → candidate 经验卡 → 验证 → validated，流程驱动而非人工 ingest。
2. **证据绑定**：每条经验绑定 ArtifactRef，可回溯、可审计、可过期。
3. **任务画像检索**：字段指纹 + 版式标签 + 单据类型，替代 rg 关键词。
4. **生命周期**：observed/candidate/validated/superseded/expired 状态机。

迁移策略：
1. 盘点 ~/coding-brain 的 04_Registries（Issue/Experiment/Training Run/Metric/Dataset/Code Pattern Registry）和 03_Domains 中仍有效的条目，人工筛选后转换为经验卡（P1 阶段首批 20-30 张的来源之一）。
2. coding-brain 只读保留为历史证据源（类似 Qwen 仓库的 source pin 角色），不再维护、不再 ingest。
3. 项目 AGENTS.md 中的 CODINGBRAIN 区块移除，替换为新 memory 的说明。
4. session-digests（.codex/session-digests/）继续作为"会话级临时沉淀"，经验卡是"跨会话验证级沉淀"，两者并存但层级不同。
