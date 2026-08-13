#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证门槛：7 项 validated + 8 类 rejected + 写入门槛（见 12-phase3-plan.md §3）。

判定顺序：写入门槛（block）→ rejected 情形（负经验）→ validated 7 项（全过/归因确认）。
"""
from evidence import VALIDATED_CHECKS, REJECTED_CASES, WRITE_GATES


def check_write_gates(event):
    """写入门槛：任何一项不过 → block（不入库，返回失败原因）。"""
    failures = []
    if not event.badcase_analysis.get("problem_pattern"):
        failures.append("evidence_bound: 缺 badcase 结论/问题模式")
    if not event.metrics.get("delta"):
        failures.append("delta_vs_prior_best: 缺 delta（须对 prior-best）")
    if event.evaluator.get("fake"):
        failures.append("not_fake: simulation/fake 结果不得入库")
    return failures


def check_rejected(event):
    """8 类 rejected 情形：命中即 rejected（作为负经验）。"""
    hits = []
    deg = event.metrics.get("degradation", {})   # {core, protected, empty_output, repeated_group}
    if deg.get("core"):
        hits.append("core_not_improved: 核心指标不改善")
    if deg.get("protected"):
        hits.append("protected_regression: 保护字段回归")
    if deg.get("empty_output"):
        hits.append("empty_output_increased: 空输出/截断增加")
    if deg.get("repeated_group"):
        hits.append("repeated_group_increased: 重复 group 增加")
    if event.evaluator.get("leakage"):
        hits.append("leakage_inflation: 污染评估提升")
    if event.evaluator.get("adapter_missing"):
        hits.append("adapter_not_loaded: runtime 未加载 adapter")
    if event.metrics.get("cost_no_gain"):
        hits.append("cost_no_gain: 成本增加无收益")
    return hits


def check_validated(event, human_approval):
    """7 项 validated 门槛：返回 (通过项, 未过项)。"""
    passed, failed = [], []
    delta = event.metrics.get("delta", {})
    improved = event.metrics.get("improved", False)   # 显式标记：目标是否改善

    def mark(cond, name, why):
        (passed if cond else failed).append(f"{name}: {why}")

    mark(improved, "target_improved", "目标指标改善")
    mark(not event.metrics.get("degradation", {}).get("bbox_card_group"),
         "no_unexplained_degradation", "bbox/基数/归组无退化")
    mark(not event.metrics.get("degradation", {}).get("protected"),
         "protected_no_regression", "保护字段无回归")
    mark(event.evaluator.get("valid", False), "evaluator_valid", "evaluator 有效")
    mark(event.evaluator.get("runtime_raw", False), "runtime_raw_complete", "runtime raw 完整")
    mark(bool(event.evaluator.get("id_ood")), "id_ood_explainable", "ID-OOD 可解释")
    mark(human_approval, "human_approval", "人工验收")
    return passed, failed


def decide(event, human_approval=False, is_diagnostic=False):
    """综合判定状态。返回 {status, gates, rejected_hits, passed, failed, reason}。"""
    gates = check_write_gates(event)
    if gates:
        return {"status": "blocked", "gates": gates, "reason": "写入门槛未过，不入库"}

    rejected_hits = check_rejected(event)
    if rejected_hits:
        return {"status": "rejected", "rejected_hits": rejected_hits, "reason": "命中 rejected 情形，作为负经验"}

    if is_diagnostic:
        return {"status": "confirmed", "reason": "归因/诊断确认（结论可信，干预未验证）"}

    passed, failed = check_validated(event, human_approval)
    if len(failed) == 0:
        return {"status": "validated", "passed": passed, "reason": "7 项全过，干预验证通过"}
    if human_approval and len(failed) == 1 and failed[0].startswith("human_approval"):
        return {"status": "validated", "passed": passed, "reason": "仅缺人工验收（已补）"}
    return {"status": "candidate", "passed": passed, "failed": failed, "reason": "待验证（未达 validated 门槛）"}
