# 记忆数据目录（memory/）

> 训练经验 Memory 的正式记忆数据。Phase 1 首批产出，依 `schema.md` 冻结的 v1 schema 组织。

## 文件

| 文件 | 内容 | 状态 |
|---|---|---|
| `schema.md` | 冻结 schema：ExperienceCase / PatternClaim / 能力标签 / 状态机 | 冻结 v1 |
| `capability-tags.md` | 通用能力标签初版（4 类约 40 标签） | candidate |
| `experience-cases.md` | 首批 ExperienceCase（12 条，绑证据） | candidate |
| `pattern-claims.md` | 首批 PatternClaim（9 条，聚合 + 失效边界） | candidate/validated |

## 关系

```
通用能力标签（检索键，与字段名解耦）
        ▲ 标注
PatternClaim（通用模式，跨单据迁移，有状态机）
        ▲ supported_by 引用
ExperienceCase（单次观察，绑证据，不可变）
        ▲ evidence_refs 落回
历史素材（runs / docs/performance / registry / analysis_outputs，只读）
```

## 检索/推荐 vs 追溯

- **给新任务推荐策略** → 用能力标签命中 PatternClaim（跨单据通用）。
- **要证据** → 沿 Claim.supported_by → Case → evidence_refs 落回具体 run/report。

## 首轮覆盖摘要

- 装箱单四大失败机制（漏行/重复 group/串位/size·重量单位错配）已固化为 Case + Claim，且通过能力标签（grouped_value/row_aligned/dense_table/numeric_unit）而非"装箱单"字段名表达，可迁移到任何同类密集跨页表格单据。
- 训练稳定性（GB256 主线）、金额清洗、运行时 bbox、评估口径（字段面对齐/泄漏闭包/cluster ID-OOD）已固化为 validated Claim。
- 负知识显式建模：`unresolved`/`candidate` 状态标记"问题确认但未解决"的难例，防止反复试错。
