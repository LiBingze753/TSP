# -*- coding: utf-8 -*-
"""按评审意见微调：① 3.4 补 2-opt 写回说明；② 表 1 的均值与标准差合并为“均值±SD”。"""
import io
import re

p = "paper.md"
s = io.open(p, encoding="utf-8").read()

# ---------- ① 3.4 增加“写回种群”说明
old4 = "4. 单次调用最多 3 轮；每轮最多接受 20 次改进移动，或当一轮完整扫描找不到改进时结束该轮；单次调用累计接受移动不超过 60 次。该上限避免局部搜索在早期反复优化同一精英而耗尽全部预算。\n5. 四种策略在**相同完整评估预算**下比较；"
new4 = ("4. 单次调用最多 3 轮；每轮最多接受 20 次改进移动，或当一轮完整扫描找不到改进时结束该轮；单次调用累计接受移动不超过 60 次。该上限避免局部搜索在早期反复优化同一精英而耗尽全部预算。\n"
        "5. 改进后的路径**写回 P 中该精英原来的位置**（P[0] 或 P[1]），随后重新排序 P，改进结果因而进入下一代的精英复制与子代生成，而不是只用于当次评估。\n"
        "6. 四种策略在**相同完整评估预算**下比较；")
assert old4 in s
s = s.replace(old4, new4)

# ---------- ② 表 1 合并均值与标准差
start = s.index("| 实例 | 策略 | 平均路径长度 | 平均偏差率/% | 偏差率 SD | 最小值 | 最大值 | 命中最优(/30) |")
end = s.index("**表 1（续）")
block = s[start:end]
lines = block.splitlines()
out = []
for ln in lines:
    if not ln.startswith("|"):
        out.append(ln)
        continue
    if re.fullmatch(r"\|[\s:\-\|]+\|", ln.strip()):
        out.append("|---|---|---|---|---|---|---|")
        continue
    cells = [c.strip() for c in ln.strip().strip("|").split("|")]
    if cells[0] == "实例":
        out.append("| 实例 | 策略 | 平均路径长度 | 平均偏差率/%（均值±SD） | 最小值 | 最大值 | 命中最优(/30) |")
    else:
        out.append("| %s |" % " | ".join([cells[0], cells[1], cells[2], "%s±%s" % (cells[3], cells[4]), cells[5], cells[6], cells[7]]))
s = s[:start] + "\n".join(out) + s[end:]

io.open(p, "w", encoding="utf-8").write(s)

# 自检
s2 = io.open(p, encoding="utf-8").read()
i = s2.index("| 实例 | 策略 | 平均路径长度 |")
print(s2[i:i+520])
