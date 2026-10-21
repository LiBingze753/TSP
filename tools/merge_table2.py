# -*- coding: utf-8 -*-
"""表 2 也把均值与标准差合并为“均值±SD”，与表 1 保持一致。"""
import io
import re

p = "paper.md"
s = io.open(p, encoding="utf-8").read()

start = s.index("| 变异率 | 运行次数 | 平均路径长度 | 平均偏差率/% | 偏差率 SD |")
end = s.index("**表 3 ")
block = s[start:end]

out = []
for ln in block.splitlines():
    if not ln.startswith("|"):
        out.append(ln)
        continue
    if re.fullmatch(r"\|[\s:\-\|]+\|", ln.strip()):
        out.append("|---|---|---|---|---|---|---|")
        continue
    c = [x.strip() for x in ln.strip().strip("|").split("|")]
    if c[0] == "变异率":
        out.append("| 变异率 | 运行次数 | 平均路径长度 | 平均偏差率/%（均值±SD） | 命中最优次数 | 平均首次收敛评估次数 | 平均耗时/ms |")
    else:
        out.append("| %s |" % " | ".join([c[0], c[1], c[2], "%s±%s" % (c[3], c[4]), c[5], c[6], c[7]]))

s = s[:start] + "\n".join(out) + s[end:]
io.open(p, "w", encoding="utf-8").write(s)

i = s.index("| 变异率 |")
print(s[i:i + 400])
