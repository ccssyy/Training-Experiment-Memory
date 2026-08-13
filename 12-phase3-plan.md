# Phase 3 实现切片（回灌闭环框架：Postflight curator）

> 日期：2026-08-13 ｜ 状态：执行计划（首个回灌切片）
> 前置：Phase 2-MVP 已验证训练前推荐路径；本切片补训练后回灌路径，形成完整闭环。

## 0. 目标与边界

**目标**：实现回灌闭环的**框架**——训练事实（EvidenceEvent）→ candidate Case/Claim → 验证门槛 → 状态机转换。用历史证据做 dry-run 验证结构。

**边界（刻意收窄）**：
- **零 GPU**：真正回灌需真实训练迭代验证，当前 GPU 未授权。本切片交付**框架 + 历史证据 dry-run**，不跑真实训练。
- **不做 ATF 接入**：回灌引擎是独立模块，ATF 的 Decision Ledger 映射留到接入切片。
- **不做自动写库**：回灌永远停在"人工验收"闸前，不自动 promote 到 validated。

## 1. 完整闭环（承接 Phase 2）

```
训练前（Preflight，Phase 2 已做）：画像 → 检索 → 建议卡
训练中：施加建议 + 评估
训练后（Postflight，本切片）：badcase 分析 → EvidenceEvent → candidate → 人工验收 → validated/rejected/unresolved
        → 多案例聚合升级 Claim → 下次训练前再命中（闭环）
```

## 2. 回灌链路（doc 07 §1.9 落地）

```
1. 读训练事实（badcase 结论 + 指标对 prior-best）
2. 追加 EvidenceEvent（不可变，绑定 run/指标/badcase）
3. 关联/创建 ExperienceCase（若为新观察）
4. 生成 candidate Claim（status=candidate）
5. 验证门槛校验（7 项 validated / 8 类 rejected / 写入门槛）
6. 人工验收 → 状态机转换
7. 多案例聚合 → 升级 PatternClaim
```

## 3. 验证门槛（核心）

### 3.1 validated 7 项（全过才 validated，doc 07 §1.9）

1. 目标改善（target metric 提升）
2. bbox/基数/归组无未解释退化
3. 保护字段无回归
4. evaluator 有效
5. runtime raw 完整
6. ID-OOD 可解释
7. 人工验收

### 3.2 rejected 情形（doc 07 §1.9，命中即 rejected，作为负经验）

1. 核心指标不改善
2. 保护字段回归
3. 空输出/截断增加
4. 重复 group 增加
5. 污染评估提升（泄漏）
6. runtime 未加载 adapter
7. 成本增加无收益

### 3.3 写入门槛（doc 04 §4 + doc 02 §3.5）

1. 必须绑定证据（缺证据 block）
2. delta 必须对 prior-best（不对实验内部最佳 checkpoint）
3. 口径一致（字段面四方对齐、测试集锁定）
4. simulation/fake 不得产生 validated
5. 与已有经验冲突 → 人工裁决

## 4. 模块划分

```
phase3/
  evidence.py    # EvidenceEvent 结构 + 追加
  validate.py    # 7 项 validated + 8 类 rejected + 写入门槛校验
  curator.py     # candidate 生成 + 状态机转换（候选→验收→定状态）
  dry_run.py     # 用历史证据（CASE-0007 金额清洗等）走全流程
  FINDINGS.md    # 结构反馈（写回 schema 的依据）
```

## 5. dry-run 验证目标

用已有历史证据跑 3 条典型链路，验证结构：
1. **正例**：CASE-0007 金额清洗（amount F1 0.4211→1.0000）→ 应能走通 candidate→validated（7 项全过）。
2. **反例**：CASE-0006 GB512 坍缩 → 应命中 rejected 情形（输出坍缩/成本）。
3. **归因例**：CASE-0019 空输出二分 → 应走 candidate→confirmed（归因确认，非干预验证）。

## 6. 结构反馈回灌

dry-run 后把"回灌需要哪些证据字段但 schema 还没有"的缺口记录回 `phase3/FINDINGS.md`，作为 schema 补丁依据。

## 7. 不在本切片

- 真实训练验证（需 GPU）。
- ATF Decision Ledger 映射（接入切片）。
- 自动写库（永远停人工验收闸）。
- 经验过期降级（expires_at → observed，后续）。
