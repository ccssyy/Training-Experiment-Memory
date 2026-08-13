#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EvidenceEvent：回灌闭环的训练事实入口（不可变，追加式）。

对应 schema.md §1。训练后先追加 EvidenceEvent，再关联/创建 Case、生成 candidate Claim。
"""
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class EvidenceEvent:
    event_id: str
    run_ref: str
    kind: str = "intervention"                            # intervention | diagnostic
    badcase_analysis: dict = field(default_factory=dict)   # {problem_pattern, suggested_fix}
    metrics: dict = field(default_factory=dict)            # {baseline, delta, improved, degradation}
    evaluator: dict = field(default_factory=dict)          # {valid, runtime_raw, id_ood, leakage, adapter_missing, fake}
    provenance: dict = field(default_factory=dict)         # {source_revisions, created_at}

    def to_dict(self):
        return asdict(self)


# 7 项 validated 门槛与 8 类 rejected 情形的可检索清单（供 validate.py 使用）
VALIDATED_CHECKS = [
    "target_improved",          # 目标指标改善
    "no_unexplained_degradation",  # bbox/基数/归组无未解释退化
    "protected_no_regression",  # 保护字段无回归
    "evaluator_valid",          # evaluator 有效
    "runtime_raw_complete",     # runtime raw 完整
    "id_ood_explainable",       # ID-OOD 可解释
    "human_approval",           # 人工验收
]

REJECTED_CASES = [
    "core_not_improved",        # 核心指标不改善
    "protected_regression",     # 保护字段回归
    "empty_output_increased",   # 空输出/截断增加
    "repeated_group_increased", # 重复 group 增加
    "leakage_inflation",        # 污染评估提升
    "adapter_not_loaded",       # runtime 未加载 adapter
    "cost_no_gain",             # 成本增加无收益
]

WRITE_GATES = [
    "evidence_bound",           # 必须绑定证据
    "delta_vs_prior_best",      # delta 对 prior-best
    "caliber_aligned",          # 口径一致
    "not_fake",                 # 非 simulation/fake
]
