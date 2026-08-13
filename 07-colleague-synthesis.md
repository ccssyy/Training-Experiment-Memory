# 同事方案综合与统一设计（v7：与 zito-atf-dev Preflight 设计合并）

> 日期：2026-08-10 ｜ 状态：综合讨论稿
> 来源：`/data/chris/bea/repos/zito-atf-dev/docs/`
> - `training-capability-preflight.md`（设计理念，15KB）
> - `training-capability-preflight-execution.md`（执行计划，660 行）

## 0. 总体判断

同事的两份文档构成了一个**比我们 v1-v6 更完整、更贴近 Qwen 真实经验**的"训练能力 Preflight"设计。核心思想与我们完全同向（字段语义>版式>单据类型、memory 存通用能力模式、经验保存有效+无效、人工确认升级知识、Postflight 回灌），但在**对象模型、状态机、能力矩阵、迁移层级、负知识管理**上比我们工程化得多。**建议以同事的 Preflight 框架为主体，融入我们的向量分析、独立化架构和 ATF 接入设计**，形成统一方案。

## 1. 同事设计要点摘要

### 1.1 核心概念模型（比我们多两个抽象层）

```text
具体历史事实（run/checkpoint/badcase）
  -> ExperienceCase（案例：可追溯）
  -> 多案例聚合
  -> PatternClaim（能力模式声明：跨单据复用）
```

- **ExperienceCase**：具体案例（对应我们经验卡的事实侧），绑定证据。
- **PatternClaim**：多案例聚合出的通用能力模式（对应我们经验卡的模式侧），是长期 memory 保存的对象。
- 我们 v1-v6 只设计了"经验卡"一层，同事拆成 Case + Claim 两层——**这个拆法更正确**：具体证据与通用模式分离，避免把单次实验结果误当通用规律。

### 1.2 通用能力标签体系（开放演化，分 4 类）

| 类别 | 标签示例 |
|---|---|
| 语义 | temporal/party/monetary/quantity/weight/identifier/address/item/status |
| 值形态 | date_value/currency_amount/numeric_value/numeric_unit/code_value/short_text/long_text/mixed_value |
| 基数粒度关系 | single_value/multi_value/grouped_value/repeated_value/document/page/region/row/cell_level/row_aligned/unit_bound/currency_bound/one_to_many/cross_page_group/per_value_bbox |
| 版式视觉 | labeled_value/dense_table/long_table/multi_block/... |

- **开放演化**：标签 validated 后进正式索引；新标签为 candidate，人工确认后升级。
- 这正是我们"字段语义匹配"要匹配的目标空间——**检索键从"字段名"升级为"通用能力标签"**，比我们的 field_fingerprint 更本质（字段名千变万化，语义/值形态/基数标签稳定）。

### 1.3 检索顺序与迁移层级（比我们的评分公式更工程化）

检索顺序：字段语义 → 值形态 → 基数 → 粒度 → 字段关系 → bbox → 页面版式 → 单据类型 → 模型/prompt/evaluator。

迁移层级（匹配结果的定性标签）：
- `direct_transfer`：字段结构/bbox/版式/评估合同基本一致
- `structural_transfer`：字段结构一致，版式有差异
- `mechanism_transfer`：字段不同，问题机制相同（如"行级归组数量字段在密集跨页表格漏行"）
- `context_reference`：只有业务/单据上下文相似（**不直接生成训练动作**）

→ 我们 v6 的评分公式可以保留，但**输出应附带 transfer_level 定性标签**，比纯分数更可解释、更好做人工审核。

### 1.4 数据支持四维（我们只有一维"数据规模"）

- `support`：字段/组有多少真实实例
- `coverage`：值形态/版式/来源/cluster/字段组合覆盖多少
- `exposure`：字段实际被训练目标看到多少次（唯一物理图/JSONL/mode/窗口/重复/上采样）
- `diversity`：曝光是否带来新的值/版式/来源/视觉变化
- **`overexposed_without_diversity`**：曝光增加但物理图片/cluster/值形态没增——防"重复样本撑指标"。

### 1.5 字段能力矩阵（结论结构化）

每字段/字段组 11 维 × {high/medium/low/unknown} + 证据/反向证据：
semantic_transfer / text_value_learning / bbox_learning / cardinality_learning / grouping_learning / layout_transfer / distribution_support / effective_exposure / strategy_evidence / generalization_support / business_threshold_support

字段状态：`historically_supported / conditionally_supported / historically_unresolved / insufficient_evidence`

### 1.6 Preflight 状态机 + 14 Step

```
initialized → profiled → history_matched → provisional_ready → human_reviewed → formal_ready → handed_off
```

14 个 Step：建上下文 → 读 anno → 提炼字段标签 → 提炼版式标签 → 声明字段优先级（core/important/optional × target/protected/diagnostic/excluded）→ 读 memory → 检索 → **冲突处理（6 类）** → 分布/曝光 → 匹配难例 → 能力矩阵 → provisional plan → 人工确认 → formal plan → 旁车报告。

- provisional vs formal 两级计划：新标签/无先例/机制迁移/版式差异/证据不足/冲突 → provisional；全部闭合 → formal。
- **冲突处理**：validated vs rejected 同时命中、同策略不同模型方向不同、ID 提升 OOD 回归、目标提升保护回归、归档与 digest 不一致、evaluator/runtime 不可比。

### 1.7 难例匹配清单（直接用 Qwen 踩过的坑）

长表漏行 / 重复 group / 行对齐错误 / item-product 混淆 / 标题主体混淆 / 币种单位错配 / 数量包装错配 / gross-net-weight 混淆 / 空输出 / 截断 / bbox 偏移 / runtime-evaluator 假失败。

命中 unresolved 且无新干预 → `historically_unresolved`。

### 1.8 训练方案生成（单变量 + 分级）

- Baseline：选最接近的历史最佳有效 baseline（比较 7 维）。
- 首选方案：**只改变一个主要因素**（数据增强/字段采样/prompt/adapter/参数/推理链路），每条含问题模式/历史依据/适用字段版式/冻结变量/保护字段/失败条件/评估/停止条件。
- 条件备选：新标签确认/补样/核心字段专项/首选触发回归/结构迁移证据不足时启用。
- 历史增强候选：每项含迁移层级/来源/family/cluster/纳入排除理由/泄漏风险/可能改善/可能回归。
- **多单据联合训练决策**：兼容则联合；语义接近版式差异大→条件联合（独立采样/prompt 约束/字段保护/独立 lane）；同名不同义/单值归组冲突/evaluator 面不同/命中 unresolved/保护字段回归→拆分。

### 1.9 Postflight 回灌（比我们 experience-curator 更完整）

```text
读训练事实 → 追加 EvidenceEvent → 关联/创建 ExperienceCase → 生成 candidate → 人工验收 → validated/rejected/unresolved → 多案例后生成 PatternClaim
```

- 策略状态：validated 需 7 项全过（目标改善/bbox 基数归组无未解释退化/保护字段无回归/evaluator 有效/runtime raw 完整/ID-OOD 可解释/人工验收）；rejected 含 8 类情形（核心不改善/保护回归/空输出截断增/重复 group/污染评估提升/runtime 未加载 adapter/成本增无收益）；`unresolved`=问题确认但无解决路径。
- **unresolved 状态是我们没有的**——对"长期未解决的难例"显式建模，防止反复试错。

### 1.10 实施阶段 + 验收标准

Phase 1 历史 memory 初始整理 → 2 Preflight 分析器 → 3 历史 Golden 验证（覆盖 12 类难例）→ 4 Skill 封装（含"无 Skill 压力场景"测试）→ 5 Postflight → 6 验收迁移。验收标准 14 条（长期 memory 存通用模式/新标签需人工确认/按能力模式迁移/四维分开/高曝光低多样不误判/rejected unresolved 阻断重复/污染不升级/方案关联证据/历史只读/不启动训练）。

## 2. 两边设计对照

| 维度 | 同事方案（zito-atf-dev） | 我们 v1-v6 | 综合建议 |
|---|---|---|---|
| 抽象层 | ExperienceCase + PatternClaim 两层 | 经验卡一层 | **采用两层**：Case（证据）+ Claim（模式） |
| 检索键 | 通用能力标签（语义/值形态/基数/版式） | 字段指纹+版式标签 | **标签体系为主体**，字段指纹作辅助键 |
| 检索匹配 | 迁移层级 4 级（定性） | 评分公式（定量） | **两者都要**：分数排序 + 定性层级标注 |
| 向量分析 | 无 | 字段语义向量 + 版式视觉向量 | **保留我们的向量**，补强标签匹配 |
| 数据支持 | support/coverage/exposure/diversity 四维 | 数据规模一维 | **采用四维** |
| 结论表达 | 11 维能力矩阵 high/low | 8 方向画像 | **能力矩阵为主体**，画像字段并入 |
| 状态机 | 7 态 Preflight 状态机 | 无显式状态机（只有经验卡状态） | **采用 Preflight 状态机** |
| 冲突处理 | 6 类冲突显式处理 | 只提"冲突进裁决" | **采用 6 类冲突清单** |
| 负知识 | rejected + unresolved 显式索引 | rejected 卡 | **补 unresolved** |
| 回灌 | EvidenceEvent→Case→Claim 聚合 | candidate→validated/rejected | **采用同事链路** |
| 独立化 | 未提（zito-atf-dev 是独立仓库雏形） | 独立系统 + 接入层 | **保持我们的独立化原则** |
| ATF 接入 | 未提 | 适配层设计 | **保持我们的接入设计** |
| 向量/可视化 | 无 | 向量 + 图 | 保留 |
| 联合训练决策 | 联合/条件联合/拆分三级 | 未提 | **采用** |

## 3. 统一设计建议（合并后的概念模型）

```text
具体历史事实（run/checkpoint/badcase/anno）
  -> ExperienceCase（案例，绑定证据，可追溯）        ← 同事
      支持四维：support/coverage/exposure/diversity  ← 同事
  -> PatternClaim（能力模式，跨单据复用，状态机）     ← 同事
      通用能力标签（语义/值形态/基数/版式）           ← 同事
      + 向量增强匹配（bge-m3 / CLIP）                ← 我们
  -> 字段能力矩阵（11 维 × high/medium/low/unknown） ← 同事
  -> provisional / formal plan（单变量 + 迁移层级）   ← 同事
  -> 训练/评估 → EvidenceEvent → 人工验收            ← 同事
  -> validated / rejected / unresolved              ← 同事
  -> 聚合新 PatternClaim（回灌闭环）                  ← 同事
```

检索链：新单据 anno → 通用能力标签（自动提炼 + 向量辅助）→ 历史检索（标签命中 + transfer_level + 分数）→ 冲突处理 → 能力矩阵 → plan。

## 4. 需要你定夺的合并决策

1. **框架主体**：以同事 Preflight（Case/Claim/标签/矩阵/状态机）为主体 + 我们的向量/独立化/ATF 接入，认同吗？
2. **对象模型**：经验卡拆为 ExperienceCase + PatternClaim 两层——我们之前 schema 的 experience-card 如何映射？（建议：experience-card = PatternClaim 实例 + Case 引用集合）
3. **与 ATF 关系**：同事的 zito-atf-dev 是独立仓库，与我们的"memory 独立于 ATF"方向一致——是否考虑 memory 直接落在 zito-atf-dev 演进，ATF 只接入？
4. **下一步**：按同事 Phase 1（历史 memory 初始整理）还是先冻结我们的 schema ？

## 5. 附：同事文档与我们的研究集对应关系

| 同事文档 | 我们的研究集文档 |
|---|---|
| training-capability-preflight.md | 03-task-profiling（画像分层）+ 04-architecture（模块） |
| training-capability-preflight-execution.md | 04-architecture（模块级）+ 未来 05-consume-integration |
| （无） | 02-research-and-precedents（先例/向量） |
