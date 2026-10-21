# -*- coding: utf-8 -*-
"""由 PDF 书签生成目录页码表（正文页码 = 物理页 - 正文起始物理页 + 1）。"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pdf_bookmarks as pb

pdf = sys.argv[1]
out = sys.argv[2]

data = open(pdf, "rb").read()
objs = pb.parse_objects(data)
pidx = pb.page_index(objs)
items = pb.outline_items(objs, data)

# 正文起始页：第一个标题 "…绪论" 的物理页
flat = [(t.strip(), pidx.get(d, 0)) for depth, t, d, num in items]
body_start = None
for t, p in flat:
    if t.endswith("绪论"):
        body_start = p
        break
print("body starts at physical page", body_start)

pages = {}
for t, p in flat:
    if t in ("摘　要", "Abstract", "目　录"):
        continue
    pages[t] = p - body_start + 1

io.open(out, "w", encoding="utf-8").write(json.dumps(pages, ensure_ascii=False, indent=1))
print("entries:", len(pages))
for k, v in pages.items():
    print("  %-40s %s" % (k, v))
