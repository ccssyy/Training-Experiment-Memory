# -*- coding: utf-8 -*-
"""retriever 回归测试：机制两级检索、③b 兜底、near-miss、值形态过滤、向后兼容。

覆盖 2026-08-15 机制层（MECH-0001~0005）与 2026-08-17 near-miss 新增。
运行：python3 -m unittest discover -s tests -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from profiler import profile_fields
import retriever


class TestMechanismLayer(unittest.TestCase):
    def test_mechanism_fallback_3b(self):
        """bank 字段 + lane=goods：MECH-0004 命中但实例(non_goods)被过滤 → ③b 兜底。"""
        profile = profile_fields([{"name": "beneficiary_bank", "sample": "HSBC HK"}],
                                 doc_type="aco", task_shape={"lane": "goods"})
        ranked, fallbacks, near_miss = retriever.retrieve_with_mechanism(profile, top_k=5)
        self.assertEqual([m["mechanism_id"] for m in fallbacks], ["MECH-0004"])

    def test_near_miss_lane(self):
        """near-miss：CLAIM-0010 标签命中但 lane 不符，带可读原因。"""
        profile = profile_fields([{"name": "beneficiary_bank", "sample": "HSBC HK"}],
                                 doc_type="aco", task_shape={"lane": "goods"})
        _, _, near_miss = retriever.retrieve_with_mechanism(profile, top_k=5)
        hit = [n for n in near_miss if n["claim_id"] == "CLAIM-0010"]
        self.assertEqual(len(hit), 1)
        self.assertIn("lane", hit[0]["reason"])

    def test_mechanism_attach(self):
        """装箱单数量字段：CLAIM-0001/0002 挂 MECH-0001（行级归组字段分段守恒）。"""
        profile = profile_fields([{"name": "goods_quantity", "sample": "1,392 BAGS"},
                                  {"name": "goods_amount", "sample": "USD 535.00"}],
                                 doc_type="packing_list")
        results = retriever.retrieve(profile, top_k=10)
        for r in results:
            if r["claim_id"] in ("CLAIM-0001", "CLAIM-0002"):
                self.assertEqual(r["mechanism_id"], "MECH-0001", r["claim_id"])


class TestRetrieveCompat(unittest.TestCase):
    def test_retrieve_returns_list(self):
        """retrieve() 向后兼容：返回 top-k list，含 claim_id/score。"""
        profile = profile_fields([{"name": "goods_quantity", "sample": "1,392 BAGS"}],
                                 doc_type="packing_list")
        results = retriever.retrieve(profile)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        for key in ("claim_id", "score", "problem_pattern", "intervention_strategy", "supported_by"):
            self.assertIn(key, results[0], key)

    def test_value_shape_filter(self):
        """单值字段不推荐行级归组经验（grouped_value 经验被过滤）。"""
        profile = profile_fields([{"name": "buyer", "sample": "Acme Corp"}], doc_type="packing_list")
        results = retriever.retrieve(profile)
        self.assertTrue(all(r["claim_id"] != "CLAIM-0001" for r in results))


if __name__ == "__main__":
    unittest.main()
