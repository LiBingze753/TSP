#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统计分析脚本（阶段5）
输入：out/main_results.csv, out/trajectory_grid.csv, out/sensitivity_results.csv
输出：out/table1.csv ... out/table4.csv, out/tables_fmt.md, out/stats_summary.md,
      figs/fig_convergence_*.png, figs/fig_sensitivity.png
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats as st

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.size"] = 10.5

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")
FIGS = os.path.join(ROOT, "figs")
os.makedirs(FIGS, exist_ok=True)

INSTANCES = ["eil51", "berlin52", "st70"]
STRATS = ["A", "B", "C", "D"]
LABEL = {"A": "A 基础GA", "B": "B GA+2-opt", "C": "C GA+贪婪初始化", "D": "D GA+2-opt+贪婪"}
COLORS = {"A": "#888888", "B": "#1f77b4", "C": "#2ca02c", "D": "#d62728"}
MARKERS = {"A": "o", "B": "s", "C": "^", "D": "D"}
T95_29 = st.t.ppf(0.975, 29)

main = pd.read_csv(os.path.join(OUT, "main_results.csv"))
grid = pd.read_csv(os.path.join(OUT, "trajectory_grid.csv"))

log = []


def w(s=""):
    print(s)
    log.append(str(s))


# ---------------------------------------------------------------- 表1 描述统计
def table1():
    rows = []
    for inst in INSTANCES:
        for s in STRATS:
            d = main[(main.instance == inst) & (main.strategy == s)]
            dev = d.deviation_pct.values
            rows.append(dict(
                instance=inst, strategy=s, n=len(d),
                mean_length=d.final_length.mean(),
                mean_dev=dev.mean(),
                sd_dev=dev.std(ddof=1),
                min_length=int(d.final_length.min()),
                max_length=int(d.final_length.max()),
                mean_first_best=d.first_best_eval.mean(),
                mean_elapsed_ms=d.elapsed_ms.mean(),
                sr_05=(dev <= 0.5 + 1e-9).mean() * 100,
                sr_10=(dev <= 1.0 + 1e-9).mean() * 100,
                sr_20=(dev <= 2.0 + 1e-9).mean() * 100,
                sr_50=(dev <= 5.0 + 1e-9).mean() * 100,
                hit_opt=int(d.hit_opt.sum()),
                mean_distinct=d.distinct_final.mean(),
                mean_opt_moves=d.opt_moves.mean(),
                mean_opt_evals=d.opt_evals.mean(),
            ))
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(OUT, "table1.csv"), index=False, encoding="utf-8-sig")
    w("## 表1 主实验描述统计")
    w()
    w("| 实例 | 策略 | 平均路径长度 | 平均偏差率% | 偏差率SD | 最小值 | 最大值 | 平均首次最优评估次数 | 平均耗时ms | ≤0.5% | ≤1% | ≤2% | ≤5% | 命中最优(/30) |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for _, r in t.iterrows():
        w(f"| {r.instance} | {r.strategy} | {r.mean_length:.2f} | {r.mean_dev:.3f} | {r.sd_dev:.3f} | "
          f"{r.min_length} | {r.max_length} | {r.mean_first_best:.1f} | {r.mean_elapsed_ms:.1f} | "
          f"{r.sr_05:.0f}% | {r.sr_10:.0f}% | {r.sr_20:.0f}% | {r.sr_50:.0f}% | {int(r.hit_opt)} |")
    w()
    return t


# ---------------------------------------------------------------- 表3 Wilcoxon
def holm(p):
    p = np.asarray(p, dtype=float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    run = 0.0
    for i, idx in enumerate(order):
        val = (m - i) * p[idx]
        run = max(run, val)
        adj[idx] = min(1.0, run)
    return adj


PAIRS = [("A", "B", "H1"), ("A", "C", "H2"), ("B", "D", "非假设"), ("C", "D", "非假设")]


def table3():
    rows = []
    for inst in INSTANCES:
        sub = {}
        for s in STRATS:
            sub[s] = main[(main.instance == inst) & (main.strategy == s)].set_index("seed")["deviation_pct"]
        ps = []
        recs = []
        for a, b, hyp in PAIRS:
            x = sub[a].sort_index()
            y = sub[b].sort_index()
            common = x.index.intersection(y.index)
            xv, yv = x.loc[common].values, y.loc[common].values
            diff = xv - yv
            nz = int(np.sum(np.abs(diff) > 1e-12))
            n = len(common)
            if nz < 5:
                W, p, note = np.nan, np.nan, "无法检验（有效非零差<%d）" % 5
            else:
                res = st.wilcoxon(xv, yv, zero_method="wilcox", alternative="two-sided")
                W, p = float(res.statistic), float(res.pvalue)
                note = ""
            recs.append(dict(instance=inst, comparison=f"{a} vs {b}", hypothesis=hyp,
                             n_pairs=n, n_nonzero=nz, n_zero=n - nz, W=W, p_raw=p, note=note))
            ps.append(p)
        adj = holm([1.0 if np.isnan(v) else v for v in ps])
        for r, pa in zip(recs, adj):
            r["p_holm"] = pa
            if np.isnan(r["p_raw"]):
                r["significant"] = "无法检验"
            else:
                r["significant"] = "是" if pa < 0.05 else "否"
            rows.append(r)
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(OUT, "table3.csv"), index=False, encoding="utf-8-sig")
    w("## 表3 Wilcoxon 符号秩检验（配对：同实例同种子，双侧 α=0.05，Holm 校正）")
    w()
    w("| 实例 | 对比组 | 有效配对n | 零差数 | W | p_raw | p_holm | 显著 |")
    w("|---|---|---|---|---|---|---|---|")
    for _, r in t.iterrows():
        w(f"| {r.instance} | {r.comparison} | {r.n_nonzero} | {r.n_zero} | "
          f"{'' if pd.isna(r.W) else f'{r.W:.1f}'} | {'' if pd.isna(r.p_raw) else f'{r.p_raw:.3e}'} | "
          f"{'' if pd.isna(r.p_holm) else f'{r.p_holm:.3e}'} | {r.significant} |")
    w()
    return t


# ---------------------------------------------------------------- 表4 交互效应
def art_tables(df):
    """ART（对齐秩变换）：对每个效应分别对齐（移除其余全部效应）后取秩，
    再对秩次做同一二因素方差分析（区组为种子）。返回 {term: anova_table}。"""
    import statsmodels.formula.api as smf
    import statsmodels.api as sm
    specs = {
        "C(opt)": "deviation ~ C(seed) + C(greedy) + C(opt):C(greedy)",
        "C(greedy)": "deviation ~ C(seed) + C(opt) + C(opt):C(greedy)",
        "C(opt):C(greedy)": "deviation ~ C(seed) + C(opt) + C(greedy)",
    }
    out = {}
    for term, f in specs.items():
        add = smf.ols(f, data=df).fit()
        d = df.copy()
        d["aligned"] = d["deviation"] - add.fittedvalues + d["deviation"].mean()
        d["rank"] = d["aligned"].rank(method="average")
        out[term] = sm.stats.anova_lm(smf.ols("rank ~ C(opt)*C(greedy) + C(seed)", data=d).fit(), typ=3)
    return out


def table4():
    import statsmodels.formula.api as smf
    import statsmodels.api as sm
    rows = []
    for inst in INSTANCES:
        d = main[main.instance == inst].copy()
        d["opt"] = d.strategy.isin(["B", "D"]).astype(int)
        d["greedy"] = d.strategy.isin(["C", "D"]).astype(int)
        d = d.rename(columns={"deviation_pct": "deviation"})
        m = smf.ols("deviation ~ C(opt)*C(greedy) + C(seed)", data=d).fit()
        tab = sm.stats.anova_lm(m, typ=3)
        key = "C(opt):C(greedy)"
        F = float(tab.loc[key, "F"]); p = float(tab.loc[key, "PR(>F)"])
        sw_W, sw_p = st.shapiro(m.resid.values)
        method = "ANOVA"
        main_opt_p = float(tab.loc["C(opt)", "PR(>F)"])
        main_gre_p = float(tab.loc["C(greedy)", "PR(>F)"])
        if sw_p < 0.05:
            art = art_tables(d)
            F = float(art[key].loc[key, "F"]); p = float(art[key].loc[key, "PR(>F)"])
            method = "ART ANOVA"
        # 交互效应值 = mean((D-B)-(C-A))，按种子配对
        piv = d.pivot_table(index="seed", columns="strategy", values="deviation")
        eff = float(((piv["D"] - piv["B"]) - (piv["C"] - piv["A"])).mean())
        rows.append(dict(instance=inst, response="deviation_pct", method=method,
                         F_interaction=F, p_interaction=p,
                         significant=("是" if p < 0.05 else "否"),
                         effect_value=eff,
                         shapiro_p=sw_p,
                         main_opt_p=main_opt_p, main_greedy_p=main_gre_p,
                         df1=int(tab.loc[key, "df"]),
                         df2=int(tab.loc["Residual", "df"])))
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(OUT, "table4.csv"), index=False, encoding="utf-8-sig")
    w("## 表4 H3 交互效应检验")
    w()
    w("| 实例 | 响应变量 | 方法 | F | p | 显著 | 交互效应值(百分点) | Shapiro p | 主效应p(opt)* | 主效应p(greedy)* |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for _, r in t.iterrows():
        w(f"| {r.instance} | 偏差率% | {r.method} | {r.F_interaction:.3f} | {r.p_interaction:.3e} | "
          f"{r.significant} | {r.effect_value:+.3f} | {r.shapiro_p:.3e} | {r.main_opt_p:.3e} | {r.main_greedy_p:.3e} |")
    w()
    return t


def posthoc():
    """若交互显著：4 组简单效应配对 Wilcoxon + Holm。"""
    rows = []
    for inst in INSTANCES:
        sub = {s: main[(main.instance == inst) & (main.strategy == s)].set_index("seed")["deviation_pct"].sort_index()
               for s in STRATS}
        comps = [("opt=0: C vs A", "C", "A"), ("opt=1: D vs B", "D", "B"),
                 ("greedy=0: B vs A", "B", "A"), ("greedy=1: D vs C", "D", "C")]
        ps, recs = [], []
        for name, a, b in comps:
            x, y = sub[a], sub[b]
            common = x.index.intersection(y.index)
            xv, yv = x.loc[common].values, y.loc[common].values
            nz = int(np.sum(np.abs(xv - yv) > 1e-12))
            if nz < 5:
                W, p = np.nan, np.nan
            else:
                r = st.wilcoxon(xv, yv, zero_method="wilcox", alternative="two-sided")
                W, p = float(r.statistic), float(r.pvalue)
            recs.append(dict(instance=inst, contrast=name, n_nonzero=nz, W=W, p_raw=p))
            ps.append(p)
        for r, pa in zip(recs, holm([1.0 if np.isnan(v) else v for v in ps])):
            r["p_holm"] = pa
            rows.append(r)
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(OUT, "table4_posthoc.csv"), index=False, encoding="utf-8-sig")
    w("### 表4附表 简单效应事后检验（配对 Wilcoxon，Holm 校正）")
    w()
    w("| 实例 | 对比 | 有效配对 | W | p_raw | p_holm |")
    w("|---|---|---|---|---|---|")
    for _, r in t.iterrows():
        w(f"| {r.instance} | {r.contrast} | {r.n_nonzero} | "
          f"{'' if pd.isna(r.W) else f'{r.W:.1f}'} | {'' if pd.isna(r.p_raw) else f'{r.p_raw:.3e}'} | "
          f"{'' if pd.isna(r.p_holm) else f'{r.p_holm:.3e}'} |")
    w()
    return t


# ---------------------------------------------------------------- 收敛曲线
def convergence():
    w("## 收敛曲线数据核对")
    for inst in INSTANCES:
        fig, ax = plt.subplots(figsize=(6.4, 4.2), dpi=300)
        for s in STRATS:
            d = grid[(grid.instance == inst) & (grid.strategy == s)]
            g = d.groupby("eval")["deviation_pct"].agg(["mean", "std", "count"])
            x = g.index.values
            y = g["mean"].values
            se = g["std"].values / np.sqrt(g["count"].values)
            ax.plot(x, y, label=LABEL[s], color=COLORS[s], lw=1.5, marker=MARKERS[s], ms=2.2, markevery=5)
            ax.fill_between(x, y - T95_29 * se, y + T95_29 * se, color=COLORS[s], alpha=0.16, lw=0)
        ax.set_xlabel("累计完整适应度评估次数")
        ax.set_ylabel("当前最优偏差率 / %")
        ax.set_title(f"{inst} 收敛曲线（30 次运行均值，阴影为 95% 置信区间）", fontsize=10)
        ax.grid(alpha=0.3, ls="--", lw=0.6)
        ax.legend(fontsize=7.5, loc="upper right")
        ax.set_xlim(0, 100000)
        fig.tight_layout()
        fig.savefig(os.path.join(FIGS, f"fig_convergence_{inst}.png"))
        plt.close(fig)
        # 对数纵轴（附录用）
        fig, ax = plt.subplots(figsize=(6.4, 4.2), dpi=300)
        for s in STRATS:
            d = grid[(grid.instance == inst) & (grid.strategy == s)]
            g = d.groupby("eval")["deviation_pct"].mean()
            ax.plot(g.index.values, g.values, label=LABEL[s], color=COLORS[s], lw=1.5)
        ax.set_yscale("log")
        ax.set_xlabel("累计完整适应度评估次数")
        ax.set_ylabel("当前最优偏差率 / %（对数刻度）")
        ax.set_title(f"{inst} 收敛曲线（对数纵轴，30 次均值）", fontsize=10)
        ax.grid(alpha=0.3, ls="--", lw=0.6, which="both")
        ax.legend(fontsize=7.5)
        fig.tight_layout()
        fig.savefig(os.path.join(FIGS, f"fig_convergence_log_{inst}.png"))
        plt.close(fig)
        # 曲线末端数值
        last = grid[(grid.instance == inst) & (grid["eval"] == 100000)].groupby("strategy")["deviation_pct"].mean()
        w(f"- {inst} 末点(100000次)平均偏差率: " + ", ".join(f"{k}={v:.3f}%" for k, v in last.items()))
    w()


# ---------------------------------------------------------------- 表2 敏感性
def table2():
    p = os.path.join(OUT, "sensitivity_results.csv")
    if not os.path.exists(p):
        w("!! 未找到 sensitivity_results.csv，跳过表2")
        return None
    d = pd.read_csv(p)
    rows = []
    for mr, g in d.groupby("mutation_rate"):
        dev = g.deviation_pct.values
        rows.append(dict(mutation_rate=mr, n=len(g),
                         mean_length=g.final_length.mean(),
                         mean_dev=dev.mean(), sd_dev=dev.std(ddof=1),
                         hit_opt=int(g.hit_opt.sum()),
                         mean_first_best=g.first_best_eval.mean(),
                         mean_elapsed_ms=g.elapsed_ms.mean()))
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(OUT, "table2.csv"), index=False, encoding="utf-8-sig")
    w("## 表2 变异率敏感性实验汇总（berlin52，探索性）")
    w()
    w("| 变异率 | 运行次数 | 平均路径长度 | 平均偏差率% | 偏差率SD | 命中最优 | 平均首次收敛评估次数 | 平均耗时ms |")
    w("|---|---|---|---|---|---|---|---|")
    for _, r in t.iterrows():
        w(f"| {r.mutation_rate:.2f} | {int(r.n)} | {r.mean_length:.2f} | {r.mean_dev:.3f} | {r.sd_dev:.3f} | "
          f"{int(r.hit_opt)} | {r.mean_first_best:.1f} | {r.mean_elapsed_ms:.1f} |")
    w()
    # 趋势图
    fig, ax = plt.subplots(figsize=(5.6, 4.0), dpi=300)
    x = t.mutation_rate.values
    y = t.mean_dev.values
    se = t.sd_dev.values / np.sqrt(t.n.values)
    tcrit = st.t.ppf(0.975, int(t.n.iloc[0]) - 1)
    ax.errorbar(x, y, yerr=tcrit * se, fmt="o-", color="#1f77b4", capsize=4, lw=1.6, ms=6)
    for xi, yi in zip(x, y):
        ax.annotate(f"{yi:.3f}", (xi, yi), textcoords="offset points", xytext=(6, 8), fontsize=8)
    ax.set_xlabel("变异率")
    ax.set_ylabel("平均偏差率 / %")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{v:.2f}" for v in x])
    ax.set_title("变异率对平均偏差率的影响（探索性分析，误差线为 95% CI）", fontsize=9.5)
    ax.grid(alpha=0.3, ls="--", lw=0.6)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, "fig_sensitivity.png"))
    plt.close(fig)
    return t


def diagnostics():
    """附表：2-opt 预算占用与种群多样性诊断。"""
    t = main.groupby(["instance", "strategy"]).agg(
        mean_opt_moves=("opt_moves", "mean"),
        mean_opt_evals=("opt_evals", "mean"),
        mean_scan=("opt_scan_checks", "mean"),
        mean_distinct=("distinct_final", "mean"),
        mean_first_best=("first_best_eval", "mean"),
        mean_elapsed=("elapsed_ms", "mean"),
    ).reset_index()
    t["opt_eval_share_pct"] = t.mean_opt_evals / 100000 * 100
    t.to_csv(os.path.join(OUT, "diagnostics.csv"), index=False, encoding="utf-8-sig")
    w("## 附表B1 搜索行为诊断（30 次运行均值）")
    w()
    w("| 实例 | 策略 | 平均2-opt接受移动 | 平均2-opt评估数 | 2-opt评估占比 | 平均扫描检查 | 终止时平均不同个体数 | 平均首次最终最优评估数 |")
    w("|---|---|---|---|---|---|---|---|")
    for _, r in t.iterrows():
        w(f"| {r.instance} | {r.strategy} | {r.mean_opt_moves:.1f} | {r.mean_opt_evals:.1f} | "
          f"{r.opt_eval_share_pct:.2f}% | {r.mean_scan:.0f} | {r.mean_distinct:.2f} | {r.mean_first_best:.1f} |")
    w()
    return t


def main_():
    t1 = table1()
    t3 = table3()
    t4 = table4()
    posthoc()
    t2 = table2()
    diagnostics()
    convergence()
    # 汇总
    with open(os.path.join(OUT, "stats_summary.md"), "w", encoding="utf-8") as f:
        f.write("# 统计分析结果汇总\n\n```\n" + "\n".join(log) + "\n```\n")
    print("done")


if __name__ == "__main__":
    main_()
