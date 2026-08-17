# -*- coding: utf-8 -*-
"""advise 入口回归测试：端到端建议卡、③b 兜底、索引未覆盖提示、未知字段降级。

运行：python3 -m unittest discover -s tests -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import advise


class TestAdvise(unittest.TestCase):
    def test_normal_card(self):
        card = advise.advise_from_input({
            "doc_type": "packing_list",
            "fields": [{"name": "goods_quantity", "sample": "1,392 BAGS"}],
        })
        self.assertIn("# 策略建议卡", card)
        self.assertIn("CLAIM-", card)
        self.assertIn("候选策略", card)

    def test_mechanism_fallback_in_card(self):
        """主入口输出 ③b 兜底（2026-08-17 修复点：此前 advise.py 丢兜底段落）。"""
        card = advise.advise_from_input({
            "doc_type": "aco",
            "task_shape": {"lane": "goods"},
            "fields": [{"name": "beneficiary_bank", "sample": "HSBC HK"}],
        })
        self.assertIn("命中机制", card)
        self.assertIn("字段互斥排他", card)

    def test_near_miss_in_card(self):
        card = advise.advise_from_input({
            "doc_type": "aco",
            "task_shape": {"lane": "goods"},
            "fields": [{"name": "beneficiary_bank", "sample": "HSBC HK"}],
        })
        self.assertIn("相近但未命中", card)
        self.assertIn("lane 不符", card)

    def test_uncovered_hint(self):
        """发票（ci）索引未覆盖 → 显式提示而非静默。"""
        card = advise.advise_from_input({
            "doc_type": "commercial_invoice",
            "fields": [{"name": "invoice_no", "sample": "INV-2026-001"}],
        })
        self.assertIn("版式索引未覆盖", card)

    def test_unknown_fallback(self):
        """完全陌生任务 → 诚实降级「无匹配经验」。"""
        card = advise.advise_from_input({
            "doc_type": "xyz_unknown",
            "fields": [{"name": "totally_unknown_field_xyz", "sample": "zzz"}],
        })
        self.assertIn("无匹配经验", card)


if __name__ == "__main__":
    unittest.main()
