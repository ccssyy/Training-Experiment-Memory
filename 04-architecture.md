# 训练经验 Memory 模块级详细设计（v5）

> 分支：`work/20260810-training-experience-memory-research` ｜ 日期：2026-08-10 ｜ 状态：设计讨论稿
> 前置：v4（整体架构 + 调研）。本文给出**每个模块的详细设计**（输入/输出/核心逻辑/与现有组件接线）。

## 1. 模块清单与职责

| 模块 | 类型 | 职责 | 挂载点 |
|---|---|---|---|
| `profile-task` | 新 Skill + 画像引擎 | 生成任务画像（8 方向确定性统计） | 数据准入后、prepare-training 前 |
| `strategy-advisor` | 新 Skill + 检索引擎 | 检索经验 → 生成 Suggestion 策略建议卡 | prepare-training 内部 |
| `experience-curator` | 新 Skill + 回灌引擎 | badcase 结论 → 候选卡 → 验证触发 → 入库/拒绝 | 迭代决策后 |
| `experience store` | 存储层 | 经验卡/画像/索引的持久化与状态机 | 全局 |
| 复用：Suggestion envelope、Artifact Catalog、Decision Ledger、analyze-badcases | | | |

## 2. profile-task（任务画像引擎）详细设计

**输入**：新任务原始素材引用（source refs：数据集目录/样本/manifest）+ 新单据定性问卷（首次）。
**输出**：`task-profile/v1` Artifact（不可变 JSON）。

```yaml
task_profile:
  schema_version: 1
  task: {lane, bbox_required, cross_page, document_types[], field_count}
  data_scale: {unique_images, jsonl_rows, pos_neg_ratio, empty_ratio, missing_images, parse_errors, duplicate_rate}
  layout: {families, clusters, dense_table_ratio, avg_table_rows, cross_page_ratio, noisy_ratio}
  fields: {fingerprint, support[], long_text[], currency[], ambiguous_pairs[][]}
  difficulty: {badcase_density{by_doc_type}, row_delta_negative_ratio, repeated_group_ratio}
  leakage: {raw_sha_overlap, pixel_sha_overlap, family_overlap, ood_clusters}
  output: {prompt_len, field_subset_count, max_group_rows, max_completion_len, truncation_history}
  resources: {gpu, gpu_count, vram_gb, budget_hours}
  provenance: {source_refs[], computed_by, computed_at, human_confirmed[]}
```

**核心逻辑**：
1. 复用 Qwen 侧已验证的统计逻辑（split_manifests 的 cluster 分配、hash 闭包、字段分布统计）抽为独立脚本，source-backed 只读。
2. 新单据定性项（业务域/语言/扫描来源）在首次出现时向用户提 3-5 个确认问题，答案写入 `human_confirmed`，后续同单据类型复用。
3. 画像不可变：任何输入变化产生新画像版本，旧画像保留。

## 3. strategy-advisor（策略检索与推荐）详细设计

**输入**：task-profile/v1 + 现有 validated 经验卡。
**输出**：`Suggestion`（复用 envelope）+ 策略建议卡 Markdown（含证据/反证/置信度）。

**检索算法**：
```
score(exp, profile) = 0.5 * jaccard(field_fingerprint)      # 字段重叠
                   + 0.3 * layout_tag_overlap                # 版式标签重合
                   + 0.2 * (doc_type_match + lane_match)     # 单据/lane
score *= time_decay(created_at)                              # 新经验略优先
只检 status=validated 且 confidence >= medium
```
**建议卡生成**（LLM 汇总 top-k）：
```markdown
## 策略建议卡
- 任务画像摘要（3-5 行）
- 候选策略 1：STR-X（来自 EXP-KIE-xxxx，provenance=project）
  - changes: [...]  frozen: [...]
  - 证据: [ArtifactRef]  反证/不适用: [...]
  - 预期影响: {参考 delta}
- 候选策略 2：...
- 无匹配经验时的回退：默认 SOP（Qwen SOP 固化版）
- 保护条件（frozen variables）与回归保护建议
```
**约束**：永不自动改参数；输出仅为建议，人工接受后进入 plan。

## 4. experience-curator（经验回灌）详细设计

**输入**：badcase 分析结论（analyze-badcases 产出）+ 下一轮迭代验证结果（指标对 prior-best）。
**输出**：经验卡（status=validated/rejected）+ Decision 记录。

**流程**：
```
badcase 分析结论（problem pattern + 建议修复）
  → 生成候选卡 status=candidate（绑定 ArtifactRef：数据集版本/评估证据/badcase 样本）
  → 下一轮迭代应用该修复
  → 受保护指标验证（对 prior-best，含字段回归保护）
  → 提升且无回归：candidate → validated（Decision 记录 validate）
  → 未提升/回归：candidate → rejected（记录 contraindication，防重复尝试）
```
**写入门禁**（违反即 block）：
1. 必须绑定 ArtifactRef 证据（缺证据不入库）。
2. delta 必须对 prior-best，不得对实验内部最佳 checkpoint。
3. 口径一致（字段面四方对齐、测试集锁定）。
4. simulation/fake 结果不得产生 validated 卡。
5. 与已有经验冲突时进入人工裁决（Approval Ledger）。

## 5. experience store（存储层）详细设计

**存储**：SQLite（`experience.db`：experiences/profile_cache/decision_refs 表）或 JSONL 目录，P4 加 embedding 列。

**经验卡 schema**（`experience-card/v1`，必填项加 *）：
```yaml
experience_id* / status* / provenance*(project|public) / source_url?
task_profile*: {field_fingerprint*, document_types, layout_tags, lane}
problem*: {pattern_id, symptom_metric, evidence_refs*}
intervention*: {strategy_id, changes, frozen_variables}
outcome*: {baseline_ref, delta, cost?, stability?}
applicability*: {preconditions, contraindications*, confidence*}
provenance: {source_revisions, decision_ref, created_at, expires_at?}
```

**状态机**（每个转换 = 一条 Decision 记录）：
```
observed → candidate → validated ──→ superseded
                 └──────→ rejected ──→ expired
```
- observed：公开资料提炼/初步观察，不参与推荐
- candidate：badcase 回灌待验证
- validated：验证通过，参与检索
- rejected：验证失败，作为负经验（contraindication 素材）
- superseded：被新策略取代（保留历史，可追溯）
- expired：过期自动降级

**索引**：字段指纹哈希表（primary）+ 版式标签倒排 + 创建时间。P1 先用 SQLite FTS/JSON 查询，不上向量。

## 6. 与现有 ATF 组件接线表

| 现有组件 | 接线方式 |
|---|---|
| `Suggestion` envelope | strategy-advisor 输出直接复用，不新造 |
| Artifact Catalog | 画像/经验卡均作为 Artifact 类型注册（task-profile/v1、experience-card/v1） |
| Decision Ledger | 经验状态每次转换 = 一条 Decision（validate/rejected/supersede） |
| Approval Ledger | 冲突经验裁决、人工接受建议卡 |
| analyze-badcases Skill | experience-curator 消费其产出 |
| Gate 体系 | 经验写入前过"证据绑定/口径一致"Gate；无 Gate 变更 |
| 四 owner 不变量 | **不引入第五 owner**：经验卡是 Artifact 类型，状态由 Decision 裁判 |

## 7. 模块依赖与开发顺序

```
P0: experience-card/v1 schema 冻结 + 首批经验卡（普适 10-15 + 自有 20-30）
P1: profile-task 画像引擎（复用 Qwen 统计脚本）+ strategy-advisor 规则检索
P2: 训练前集成（prepare-training 内调用，出建议卡）
P3: experience-curator 回灌闭环（badcase → 验证 → 入库）
P4: 向量检索 + 画像可视化 + 跨项目迁移
```
依赖：P1 依赖 P0（检索需要经验卡）；P3 依赖 GPU 授权（验证需要真实迭代）；P0/P1/P2 不依赖 GPU。
