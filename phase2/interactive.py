#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""交互式体验：输入新单据字段定义，实时看画像 + 检索命中 + 建议卡。

用法：python3 interactive.py
提示符下逐行输入「字段名 = 样例值」，直接回车结束，然后看完整建议卡。
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from profiler import profile_fields
from advisor import advise


def main():
    print("=" * 62)
    print("训练经验 Memory · 交互式体验")
    print("=" * 62)
    print("输入字段定义（格式：字段名 = 样例值，例如 goods_quantity = 1,392 BAGS）")
    print("直接回车结束输入，然后看画像 + 建议卡。\n")

    fields = []
    doc_type = input("单据类型（如 packing_list / 回车用 unknown）：").strip() or None

    while True:
        line = input(f"字段 {len(fields)+1}：").strip()
        if not line:
            break
        if "=" in line:
            name, sample = line.split("=", 1)
            fields.append({"name": name.strip(), "sample": sample.strip()})
        else:
            fields.append({"name": line, "sample": ""})

    if not fields:
        print("未输入字段，退出。")
        return

    profile = profile_fields(fields, doc_type=doc_type)
    print("\n" + advise(profile, top_k=5))


if __name__ == "__main__":
    main()
