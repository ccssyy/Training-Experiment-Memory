# -*- coding: utf-8 -*-
"""profiler 回归测试：值形态启发、doc_type 归一化、三路字段匹配、索引未覆盖标志。

覆盖 2026-08-13~15 修复过的 F2/F4 类问题 + 2026-08-17 新增的中文值形态与 doc_type 归一化。
运行：python3 -m unittest discover -s tests -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import profiler


class TestValueShapeHeuristic(unittest.TestCase):
    """值形态启发：中英文全场景（F4 修复点：CTN/PCS 归计数、KG/LB 归重量）。"""

    def test_currency_amount(self):
        for s in ["USD 535.00", "¥1,200.50", "￥800", "535.00元", "人民币 12,000.00", "$535", "EUR 100"]:
            self.assertEqual(profiler.value_shape_heuristic(s)[0], "currency_amount", s)

    def test_date_value(self):
        for s in ["2026-03-25", "25 MAR 2026", "2026年3月25日", "2026/08/17"]:
            self.assertEqual(profiler.value_shape_heuristic(s)[0], "date_value", s)

    def test_numeric_unit_weight_size(self):
        for s in ["24,897 KGS", "1.5 MT", "50公斤", "1.2吨", "30厘米", "5立方米", "10 CBM"]:
            self.assertEqual(profiler.value_shape_heuristic(s)[0], "numeric_unit", s)

    def test_numeric_value_count(self):
        for s in ["1,392 BAGS", "10 CTN", "10箱", "5件", "3袋", "12套", "100个", "1,392", "8 PCS"]:
            self.assertEqual(profiler.value_shape_heuristic(s)[0], "numeric_value", s)

    def test_code_value(self):
        for s in ["INV-2026-001", "AWB/12345", "SKU-88231", "BL123"]:
            self.assertEqual(profiler.value_shape_heuristic(s)[0], "code_value", s)

    def test_short_long_text(self):
        self.assertEqual(profiler.value_shape_heuristic("GPU A100 Module")[0], "short_text")
        self.assertEqual(profiler.value_shape_heuristic("x" * 45)[0], "long_text")
        self.assertIsNone(profiler.value_shape_heuristic(None)[0])
        self.assertIsNone(profiler.value_shape_heuristic("")[0])


class TestDocTypeNormalize(unittest.TestCase):
    """doc_type 归一化（2026-08-17）：提单 BL ≠ 海运单 SWB，发票/提单索引未覆盖。"""

    def test_alias_mapping(self):
        cases = {
            "packing_list": "pl", "装箱单": "pl",
            "sea_waybill": "swb", "海运单": "swb",
            "提单": "bl", "bill_of_lading": "bl",
            "commercial_invoice": "ci", "发票": "ci",
            "sales_order": "so", "air_waybill": "air",
            "托收": "aco", "贷记通知": "crn", "借记通知": "dbn",
            "提货单": "do", "发货单": "sdn", "proforma_invoice": "pi",
            "sales_contract": "sc", "purchase_order": "po",
        }
        for raw, expect in cases.items():
            self.assertEqual(profiler._normalize_doc_type(raw), expect, raw)

    def test_unknown_and_empty(self):
        self.assertEqual(profiler._normalize_doc_type("unknown"), "unknown")
        self.assertEqual(profiler._normalize_doc_type(""), "")
        self.assertEqual(profiler._normalize_doc_type(None), None)

    def test_resolve_index_covered(self):
        keys = list(profiler._DOC_TYPE_TO_INDEX.values())
        self.assertEqual(profiler._resolve_index_doc("装箱单", keys), "pl_mixed")
        self.assertEqual(profiler._resolve_index_doc("sea_waybill", keys), "swb_mixed")
        self.assertEqual(profiler._resolve_index_doc("托收", keys), "aco_non_goods")
        # 2026-08-17 新增覆盖：提单/发票等已建索引
        self.assertEqual(profiler._resolve_index_doc("提单", keys), "bl")
        self.assertEqual(profiler._resolve_index_doc("发票", keys), "ci")
        self.assertEqual(profiler._resolve_index_doc("形式发票", keys), "pi")
        self.assertEqual(profiler._resolve_index_doc("销售合同", keys), "sc")

    def test_resolve_index_uncovered(self):
        """索引未覆盖的单据（loan 等）→ None。"""
        keys = list(profiler._DOC_TYPE_TO_INDEX.values())
        self.assertIsNone(profiler._resolve_index_doc("loan", keys))
        self.assertIsNone(profiler._resolve_index_doc("报关单", keys))


class TestProfileFields(unittest.TestCase):
    def test_layout_doc_uncovered_flag(self):
        p = profiler.profile_fields([{"name": "goods_amount", "sample": "USD 535"}], doc_type="loan")
        self.assertTrue(p["layout_doc_uncovered"])
        self.assertEqual(p["doc_type_norm"], "loan")
        p2 = profiler.profile_fields([{"name": "goods_amount", "sample": "USD 535"}], doc_type="packing_list")
        self.assertFalse(p2["layout_doc_uncovered"])
        # 2026-08-17：发票/提单已建索引，不再标未覆盖
        p3 = profiler.profile_fields([{"name": "goods_amount", "sample": "USD 535"}], doc_type="commercial_invoice")
        self.assertFalse(p3["layout_doc_uncovered"])
        p4 = profiler.profile_fields([{"name": "goods_amount", "sample": "USD 535"}], doc_type="unknown")
        self.assertFalse(p4["layout_doc_uncovered"])

    def test_alias_match(self):
        p = profiler.profile_fields([{"name": "goods_quantity", "sample": "1,392 BAGS"}])
        self.assertEqual(p["fields"][0]["matched_by"], "alias")
        self.assertIn("quantity", p["semantic_tags"])

    def test_value_shape_fallback_semantic(self):
        """未知字段名靠值形态给语义（F4 修复点：金额样例 → monetary/currency_amount）。"""
        p = profiler.profile_fields([{"name": "weird_field", "sample": "USD 100"}])
        self.assertIn("monetary", p["semantic_tags"])
        self.assertIn("currency_amount", p["value_shapes"])

    def test_unmatched_fields(self):
        p = profiler.profile_fields([{"name": "totally_unknown_xyz", "sample": "abc"}])
        self.assertIn("totally_unknown_xyz", p["unmatched_fields"])


class TestNearConcepts(unittest.TestCase):
    """未匹配字段的最接近概念候选（2026-08-17 产品优化）。"""

    def test_bank_near(self):
        near = profiler._near_concepts("bank", profiler.load_concepts())
        self.assertEqual(near[0]["concept"], "bank.issuing")
        self.assertGreaterEqual(near[0]["score"], 0.85)

    def test_qty_variant(self):
        near = profiler._near_concepts("qty_of_goods", profiler.load_concepts())
        self.assertEqual(near[0]["concept"], "quantity")

    def test_shipment_date_variant(self):
        near = profiler._near_concepts("shipment_date_x", profiler.load_concepts())
        self.assertEqual(near[0]["concept"], "date.shipment")

    def test_completely_unknown(self):
        self.assertEqual(profiler._near_concepts("zzzz_unknown", profiler.load_concepts()), [])

    def test_profile_carries_near_concepts(self):
        p = profiler.profile_fields([{"name": "bank", "sample": "HSBC"}])
        f = p["fields"][0]
        self.assertEqual(f["matched_by"], "none")
        self.assertTrue(f["near_concepts"])
        self.assertEqual(f["near_concepts"][0]["concept"], "bank.issuing")


if __name__ == "__main__":
    unittest.main()
