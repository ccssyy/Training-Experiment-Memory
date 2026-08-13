# Phase 3 回灌闭环结构反馈（FINDINGS）

> 日期：2026-08-13 ｜ 用途：dry-run 后发现的 EvidenceEvent schema 缺口，作为补丁依据。
> 结论：回灌链路跑通（4 场景：validated / rejected / confirmed / blocked），但 EvidenceEvent 的 schema 定义不够细，无法承载"验证门槛"所需的全部证据字段。

## dry-run 结果

| 场景 | 证据 | 判定 | 结果 |
|---|---|---|---|
| 正例 · 金额清洗 | amount F1 0.4211→1.0000 | validated（7 项全过） | ✅ |
| 反例 · GB512 坍缩 | ckpt80 全 0 | rejected（命中 2 类） | ✅ |
| 归因 · 空输出二分 | 可避免比例 77%/71%/94% | confirmed | ✅ |
| 缺证据 | 空 event | blocked | ✅ |

## F5 EvidenceEvent.metrics 缺 degradation 矩阵（高）

**现象**：7 项 validated 的"无退化"、8 类 rejected 的"保护回归/空输出增/重复 group 增"，都依赖一个**退化矩阵**（core / protected / empty_output / repeated_group / bbox_card_group），但 schema §1 的 EvidenceEvent.metrics 只写了 `{baseline, delta, protected_fields}`，没有这个矩阵。

**影响**：回灌校验时"无退化"无法从 schema 字段判定，只能靠代码里的隐式约定（`metrics.degradation`）。

**补丁**：EvidenceEvent.metrics 增加 `degradation` 矩阵 + `improved` 布尔标记。

## F6 EvidenceEvent.evaluator 缺污染/adapter/fake 字段（高）

**现象**：8 类 rejected 里的"污染评估提升（leakage）""runtime 未加载 adapter（adapter_missing）"，以及写入门槛的"simulation/fake 不得入库"，都需要 evaluator 承载，但 schema §1 的 evaluator 只写了 `{valid, runtime_raw, id_ood}`。

**补丁**：evaluator 增加 `leakage` / `adapter_missing` / `fake` 字段。

## F7 缺 is_diagnostic 维度（中）

**现象**：confirmed（归因/诊断确认）需要显式区分"归因分析"vs"干预验证"，但 schema 没有这个维度，只能靠代码参数传 `is_diagnostic`。

**影响**：不写入 schema 的话，回灌时"这条是归因结论还是干预验证"会散落在代码里，无法追溯。

**补丁**：EvidenceEvent 增加 `kind: intervention | diagnostic` 字段（单值枚举）。

## 修正优先级

| # | 问题 | 优先级 | 动作 |
|---|---|---|---|
| F5 | metrics 缺 degradation 矩阵 | 高 | schema EvidenceEvent.metrics 补 degradation + improved |
| F6 | evaluator 缺 leakage/adapter/fake | 高 | schema EvidenceEvent.evaluator 补 3 字段 |
| F7 | 缺 is_diagnostic 维度 | 中 | schema EvidenceEvent 加 kind 枚举 |
