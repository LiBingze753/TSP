# -*- coding: utf-8 -*-
"""论文内容与格式自检。"""
import io
import re

s = io.open("paper.md", encoding="utf-8").read()
lines = s.splitlines()

# 1) 正文范围：从 "## 1 绪论" 到 "## 参考文献"
i0 = next(i for i, l in enumerate(lines) if l.strip().startswith("## 1 "))
i1 = next(i for i, l in enumerate(lines) if l.strip() == "## 参考文献")
body = "\n".join(lines[i0:i1])
cn = len(re.findall(r"[\u4e00-\u9fff]", body))
print("正文汉字数：", cn)
print("正文总字符：", len(body))

# 2) 标题清单
print("\n== 标题 ==")
for l in lines:
    t = l.strip()
    if t.startswith("## "):
        print("  L1:", t[3:])
    elif t.startswith("### "):
        print("      L2:", t[4:])

# 3) 图表引用
print("\n== 图表 ==")
caps = [l.strip() for l in lines if l.strip().startswith("**表") or l.strip().startswith("**附表")]
figs = re.findall(r"!\[(.*?)\]", s)
for c in caps:
    print("  表题:", c.replace("**", ""))
for f in figs:
    print("  图题:", f)
for k in ("图 1", "图 2", "图 3", "图 4", "表 1", "表 2", "表 3", "表 4", "表 A", "附表 F1"):
    print("  正文提及 %-6s 次数：%d" % (k, body.count(k)))

# 4) 引用与文献
cites = sorted(set(int(x) for x in re.findall(r"\^\[(\d+)\]\^", body)))
refs = [int(x) for x in re.findall(r"^\[(\d+)\]", s, flags=re.M)]
print("\n正文引用编号:", cites)
print("文献表编号:", refs)

# 5) 关键词
for l in lines:
    if l.strip().startswith("**关键词**") or l.strip().startswith("**Keywords**"):
        print("\n", l.strip())
