#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""训练前经验推荐统一入口：JSON 输入 → 画像 → 检索 → 建议卡。

用法（二选一）：
  1. echo '{"doc_type":"packing_list","fields":[{"name":"goods_quantity","sample":"1,392 BAGS"}]}' | python3 advise.py
  2. python3 advise.py '{"doc_type":"packing_list","fields":[...]}'

可选版式视觉路：JSON 里加 image_path + embedding_server + index_path（或环境变量
EMBEDDING_SERVER / LAYOUT_INDEX），会对样例图做版式视觉确认（识别真实单据类型、纠 doc_type 标错）。
可选字段语义向量路：JSON 里加 concept_embedding_server + concept_index_path（或环境变量
CONCEPT_EMBEDDING_SERVER / CONCEPT_INDEX），别名表未命中时走 bge-m3 语义兜底。
不提供则纯字段版自包含，零外部依赖。

输出：Markdown 策略建议卡（画像摘要 + top-k 历史经验 + 失效边界 + 证据）。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from profiler import profile_fields
from retriever import retrieve_with_mechanism
from advisor import render_card


def advise_from_input(inp):
    doc_type = inp.get("doc_type")
    fields = inp.get("fields", [])
    # 版式视觉路（可选增强）：需提供样例图 + embedding 服务 + 版式索引，否则纯字段版自包含
    profile = profile_fields(
        fields,
        doc_type=doc_type,
        task_shape=inp.get("task_shape"),
        image_path=inp.get("image_path"),
        embedding_server=inp.get("embedding_server") or os.environ.get("EMBEDDING_SERVER"),
        index_path=inp.get("index_path") or os.environ.get("LAYOUT_INDEX"),
        concept_embedding_server=inp.get("concept_embedding_server") or os.environ.get("CONCEPT_EMBEDDING_SERVER"),
        concept_index_path=inp.get("concept_index_path") or os.environ.get("CONCEPT_INDEX"),
    )
    # 用 retrieve_with_mechanism：既得 top-k 实例，也保留「命中机制但无实例」的 ③b 兜底 + near-miss
    ranked, fallbacks, near_miss = retrieve_with_mechanism(profile, top_k=inp.get("top_k", 5))
    return render_card(profile, ranked, mechanism_fallbacks=fallbacks, near_miss=near_miss)


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
