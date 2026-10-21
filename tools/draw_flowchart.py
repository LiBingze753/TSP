# -*- coding: utf-8 -*-
"""绘制四种策略共用的遗传算法主流程图（图 1）。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, FancyArrowPatch

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(6.6, 8.2), dpi=300)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

BOX_FC = "#F2F6FB"
BOX_EC = "#2E5C8A"
DEC_FC = "#FFF4E0"
CX = 0.32          # 主干中心
BW = 0.58          # 主干框宽


def box(y, text, h=0.06, w=BW, x=CX - BW / 2, fc=BOX_FC, fs=9.6, weight="normal"):
    ax.add_patch(FancyBboxPatch((x, y - h / 2), w, h,
                                boxstyle="round,pad=0.004,rounding_size=0.012",
                                linewidth=1.0, edgecolor=BOX_EC, facecolor=fc))
    ax.text(x + w / 2, y, text, ha="center", va="center", fontsize=fs, weight=weight,
            linespacing=1.5)


def arrow(x1, y1, x2, y2, label=None, lx=0, ly=0):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=10, linewidth=0.9, color="#333333"))
    if label:
        ax.text((x1 + x2) / 2 + lx, (y1 + y2) / 2 + ly, label, fontsize=8.5,
                ha="center", va="center", color="#333333")


def diamond(cy, text, w=0.46, h=0.095):
    pts = [(CX, cy + h / 2), (CX + w / 2, cy), (CX, cy - h / 2), (CX - w / 2, cy)]
    ax.add_patch(Polygon(pts, closed=True, linewidth=1.0, edgecolor=BOX_EC, facecolor=DEC_FC))
    ax.text(CX, cy, text, ha="center", va="center", fontsize=9.6)


box(0.955, "开始", h=0.048, w=0.24, fs=10)
box(0.870, "初始化种群：策略 C、D 的前 50 个\n为最近邻回路，其余随机生成", h=0.078)
box(0.778, "评估全部个体，累计评估数 e ← 100", h=0.058)
diamond(0.648, "e < 100000 ？")
box(0.545, "按路径长度升序排序 P", h=0.056)
box(0.437, "【仅 B、D】对前 2 个精英执行 2-opt\nfirst-improvement，≤3 轮，每轮 ≤20 次接受", h=0.078)
box(0.322, "生成 100 个子代：锦标赛 2 选择\n→ PMX(0.90) → 交换变异(0.05)", h=0.078)
box(0.218, "逐个评估子代（评估前检查预算，e 递增）", h=0.056)
box(0.118, "精英保留：P 的前 2 名替换 Q 中最差 2 个\nP ← Q", h=0.072)

# 输出框
ax.add_patch(FancyBboxPatch((0.665, 0.585), 0.325, 0.125,
                            boxstyle="round,pad=0.004,rounding_size=0.012",
                            linewidth=1.0, edgecolor=BOX_EC, facecolor="#E8F0F8"))
ax.text(0.8275, 0.6475, "输出：最优路径、首次\n最优评估次数、总评估\n次数、耗时", ha="center",
        va="center", fontsize=8.6, linespacing=1.5)

# 主干箭头
arrow(CX, 0.931, CX, 0.909)
arrow(CX, 0.831, CX, 0.807)
arrow(CX, 0.749, CX, 0.6955)
arrow(CX, 0.6005, CX, 0.573)
ax.text(CX + 0.022, 0.586, "是", fontsize=8.5, va="center")
arrow(CX, 0.517, CX, 0.476)
arrow(CX, 0.398, CX, 0.361)
arrow(CX, 0.283, CX, 0.246)
arrow(CX, 0.190, CX, 0.154)

# 否：菱形右顶点 -> 输出
arrow(0.55, 0.648, 0.663, 0.648)
ax.text(0.605, 0.665, "否", fontsize=8.5, ha="center")

# 循环回边
ax.plot([0.03, 0.008, 0.008, 0.085], [0.118, 0.118, 0.648, 0.648],
        color="#333333", linewidth=0.9)
ax.add_patch(FancyArrowPatch((0.085, 0.648), (0.099, 0.648), arrowstyle="-|>",
                             mutation_scale=10, linewidth=0.9, color="#333333"))

fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
fig.savefig("figs/fig_flowchart.png", dpi=300, facecolor="white")
print("saved")
