# -*- coding: utf-8 -*-
"""advise 入口回归测试：端到端建议卡、③b 兜底、索引未覆盖提示、未知字段降级、输入容错。

运行：python3 -m unittest discover -s tests -v
"""
import os
import subprocess
import sys
import unittest

SCRIPT_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, SCRIPT_DIR)

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
        """索引未覆盖的单据（loan）→ 显式提示而非静默。"""
        card = advise.advise_from_input({
            "doc_type": "loan",
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

    def test_card_has_summary_and_score(self):
        """核心建议段 + 匹配分数可解释（2026-08-17 产品优化）。"""
        card = advise.advise_from_input({
            "doc_type": "packing_list",
            "fields": [{"name": "goods_quantity", "sample": "1,392 BAGS"},
                       {"name": "bank", "sample": "HSBC"}],
        })
        self.assertIn("核心建议", card)
        self.assertIn("匹配分数", card)
        self.assertIn("语义命中率", card)
        # 未匹配字段带最接近概念候选
        self.assertIn("最接近", card)

    def test_bad_json_exit2(self):
        """非法 JSON 输入 → 友好报错 + 退出码 2（2026-08-17 容错）。"""
        r = subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "advise.py")],
                           input="not json", capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("不是合法 JSON", r.stderr)

    def test_empty_fields_exit2(self):
        """空 fields → 友好报错 + 退出码 2。"""
        r = subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "advise.py")],
                           input='{"doc_type":"packing_list","fields":[]}', capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("fields 不能为空", r.stderr)


if __name__ == "__main__":
    unittest.main()
