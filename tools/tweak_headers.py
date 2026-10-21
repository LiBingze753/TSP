import io

p = "paper.md"
s = io.open(p, encoding="utf-8").read()
n0 = s.count("（均值±SD）")
s = s.replace("平均偏差率/%（均值±SD）", "平均偏差率/%（±SD）")
s = s.replace("| 实例 | 策略 | 平均路径长度 | 平均偏差率/%（±SD） | 最小值 | 最大值 | 命中最优(/30) |",
              "| 实例 | 策略 | 平均路径长度 | 平均偏差率/%（±SD） | 最小值 | 最大值 | 命中最优（次） |")
io.open(p, "w", encoding="utf-8").write(s)
print("replaced", n0, "->", s.count("（均值±SD）"))
