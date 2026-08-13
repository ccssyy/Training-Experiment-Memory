# Phase 2 实现切片（MVP：画像引擎 + 规则检索）

> 日期：2026-08-13 ｜ 状态：执行计划（首个可运行切片）
> 前置：Phase 1 记忆数据已就绪（18 Case + 12 Claim + 85 概念 + 标签体系）。

## 0. 目标与边界

**目标**：跑通"新单据字段定义 → 分层画像 → 规则检索 → 建议卡"的端到端链路，验证 schema/标签/词典结构是否够用。

**边界（MVP 刻意收窄）**：
- **纯规则检索**，不上向量（bge-m3 / CLIP 是 P4）。
- **零 GPU、零 ATF 依赖**，Mac 本地纯 Python 可跑。
- 检索对象是现有 18 Case + 12 Claim，验证冷启动链路，不追求高命中率。
- 只做"训练前推荐"路径，回灌（Postflight）留到 Phase 3。

## 1. 模块划分

```
phase2/
  data/            # 机器可读记忆数据（从 memory/*.md 提炼）
    cases.json     # 18 条 ExperienceCase
    claims.json    # 12 条 PatternClaim
    concepts.json  # 85 字段语义概念（概念→别名→标签→值形态）
    tags.json      # 能力标签 4 类
  profiler.py      # task-profilers：字段 → 概念 → 语义标签（三路匹配）
  retriever.py     # experience-retriever：标签命中 → top-k Claim（含 transfer_level）
  advisor.py       # strategy-advisor：top-k Claim → 建议卡
  demo.py          # 端到端 demo
```

## 2. 检索链路（规则版）

```
新单据字段定义（字段名 + 样例值）
  → profiler：三路匹配（别名表命中 / 值形态启发 / 能力标签直接命中）
      字段 → canonical 概念 → 语义标签集合
  → retriever：语义标签集合 vs Claim.capability_tags 求交集 → 排序 top-k
      值形态不匹配的 Claim 直接过滤（grouped_value 经验不推荐给 single_value）
  → advisor：top-k Claim → 建议卡（problem_pattern + intervention_strategy + 证据 + 反证）
```

## 3. 端到端验证目标（对齐 Phase 1 验收）

1. schema 可承载真实经验：Case/Claim JSON 能无损落盘，检索能读回。
2. 字段语义匹配走通：一个含 `invoice_no`/`buyer`/`goods_quantity`/`goods_amount` 的新单据，能命中对应概念的标签。
3. 规则检索排序合理：装箱单密集表格字段 → 命中 CLAIM-0001/0002（漏行/串位），而非无关 Claim。
4. 值形态过滤生效：single_value 字段不推荐 grouped_value 经验。
5. 建议卡含证据与反证，可人工审核。

## 4. 结构反馈回灌

MVP 跑通后，把"schema/标签/词典哪里不好用"的反馈记录回 `memory/schema.md` 或本计划，作为 Phase 1 全量整理前的结构修正依据——这正是"先验证结构、再堆量"的闭环。

## 5. 不在本切片

- 向量检索（bge-m3 / CLIP/DINOv2）→ P4。
- 回灌闭环（Postflight）→ Phase 3。
- 训练前集成（ATF 接入）→ Phase 2 后续切片。
- 全量素材整理 → 本切片验证结构后再做。
