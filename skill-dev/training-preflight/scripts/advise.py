#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""训练前经验推荐统一入口：JSON 输入 → 画像 → 检索 → 建议卡。

用法（二选一）：
  1. echo '{"doc_type":"packing_list","fields":[{"name":"goods_quantity","sample":"1,392 BAGS"}]}' | python3 advise.py
  2. python3 advise.py '{"doc_type":"packing_list","fields":[...]}'

输出：Markdown 策略建议卡（画像摘要 + top-k 历史经验 + 失效边界 + 证据）。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from profiler import profile_fields
from retriever import retrieve
from advisor import render_card


def advise_from_input(inp):
    doc_type = inp.get("doc_type")
    fields = inp.get("fields", [])
    profile = profile_fields(fields, doc_type=doc_type, task_shape=inp.get("task_shape"))
    ranked = retrieve(profile, top_k=inp.get("top_k", 5))
    return render_card(profile, ranked)


def main():
    if not sys.stdin.isatty():
        raw = sys.stdin.read()
    elif len(sys.argv) > 1:
        raw = sys.argv[1]
    else:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    inp = json.loads(raw)
    print(advise_from_input(inp))


if __name__ == "__main__":
    main()
