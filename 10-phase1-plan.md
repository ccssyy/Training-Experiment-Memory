# Phase 1 执行切片（整理历史 → ExperienceCase / PatternClaim / 能力标签）

> 日期：2026-08-13 ｜ 状态：执行计划（本仓库首个可执行切片）
> 前置：`09-hosting-and-source-correction.md` 已确认素材主体为 Qwen2.5-VL-main，同事 non_goods round3 为补充。

## 0. 目标

把 Qwen2.5-VL-main 的历史训练归档，系统整理为首批 **ExperienceCase（证据）+ PatternClaim（通用模式）+ 通用能力标签（检索键）**，为 Phase 2 的画像引擎/检索引擎提供可检索、可追溯的冷启动记忆。

**产出一旦进入 `memory/` 即视为正式记忆数据**，遵循"历史只读、新事实不回改旧事实"原则：素材（runs/docs/registries）只读，产出（case/claim/tag）追加式演进。

## 1. 素材清单与优先级

| 优先级 | 素材 | 数量 | 用途 |
|---|---|---|---|
| P0 | `[知识库]/04_Registries/` 11 个 Registry | 692 行 | 已结构化的 Issue/Decision/Metric/Run 索引，**Case 的直接来源** |
| P0 | `docs/performance/` 实验报告 | 21 份 | 策略与指标结论，**Claim 的直接来源** |
| P1 | `analysis_outputs/` 分析输出 | 50 个 | badcase 分析、字段合同审计、泄漏闭包（装箱单机制量化） |
| P1 | `.codex/session-digests/` 会话摘要 | 69 个 | 失败机制、踩坑、迭代决策（补 Case 的"为什么"） |
| P2 | `runs/` 训练运行目录 | 104 个 | manifest/指标/checkpoint，Case 的 `run_ref`/`outcome` 证据锚点 |
| P3 | 同事 `non_goods_round3_analysis` | 1 包 | non-goods 字段合同 + checkpoint-342 + provenance，补充 non_goods Case |

## 2. 处理顺序（三条流水线）

```
流水线 A（Claim 优先）：docs/performance 报告 → 策略/指标结论 → PatternClaim（含能力标签）
流水线 B（Case 优先）：coding-brain Registry + analysis_outputs → 单次观察 → ExperienceCase（绑证据）
流水线 C（交叉验证）：Case 聚合 → 校验/升级 Claim 的 supported_by 与失效边界
```

首轮执行 A + B 并行，C 在 B 产出后做一轮交叉校验，形成"Claim 引用 Case、Case 落回 run/report"的双向可追溯。

## 3. 首批范围（本切片交付）

- **通用能力标签**：4 类 taxonomy（语义/值形态/基数关系/版式视觉）初版，约 40 个标签。
- **ExperienceCase**：12 条，覆盖（1）装箱单四大失败机制（漏行/重复 group/串位/size 错配）；（2）训练稳定性（GB512 坍缩）；（3）数据清洗（金额）；（4）推理运行时（vLLM bbox）；（5）评估口径（字段面对齐、泄漏闭包、cluster ID/OOD）；（6）低频字段（CI product_no、CR goods_parcel）。
- **PatternClaim**：9 条，由上述 Case 聚合，含 capability_tags、失效边界（contraindications）、supported_by、迁移层级。

## 4. 验收标准（对齐同事 14 条验收中的相关项）

1. 每条 Claim 都能 `supported_by` 至少 1 条 Case；每条 Case 都能 `evidence_refs` 落回具体 run/report/registry。
2. 每条 Claim 的 `contraindications`（失效边界）非空；无失效边界的不得标 `validated`。
3. 负知识显式建模：`rejected`/`unresolved` 状态被用于"已知失败/未解决难例"，防止反复试错。
4. 能力标签只作为检索键，不与字段名耦合；装箱单的"行级归组数量字段"经验通过标签（grouped_value + row_aligned + dense_table）而非"装箱单"字段名迁移。
5. 历史素材只读：产出阶段不修改 runs/docs/registries 任何文件。

## 5. 产出结构

```
memory/
  README.md                # 记忆数据索引（Case/Claim/Tag 关系 + 阅读路径）
  schema.md                # 冻结 schema（Case/Claim/能力标签/状态机）
  capability-tags.md       # 通用能力标签初版 v1
  experience-cases.md      # 首批 ExperienceCase（12 条）
  pattern-claims.md        # 首批 PatternClaim（9 条）
```

## 6. 下一阶段（Phase 2 预告）

Phase 2 前需：① 依据本切片验证 schema 可承载真实经验；② 补齐字段语义词典初版（别名表 + 值形态规则，来自装箱单字段合同审计）；③ 再定画像引擎/检索引擎的实现切片。
