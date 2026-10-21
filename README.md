# 交付包说明（README）

> 代码与数据仓库：<https://github.com/LiBingze753/TSP>


**论文题目**：遗传算法求解 TSP 及其 2-opt 局部搜索改进——基于 TSPLIB 小规模实例的复现实验
**参数版本**：params_v1　｜　**数据生成日期**：2026-10-20

## 1. 交付物清单（对应阶段 7.5）

| # | 交付物 | 位置 |
|---|---|---|
| 1 | 课程论文全文（按西南财经大学规范排版：封面、声明、中英文摘要、目录、正文、参考文献、附录、致谢） | `paper.docx`（39 页；另有 `paper.md` 源文与 `paper.pdf`） |
| 2 | 四种策略 Java 源代码（含注释与编译运行说明） | `java/tspga/`（`Instance`、`GA`、`Exhaustive`、`Main`、`BaselineHill`） |
| 3 | 主实验原始数据（360 行） | `out/main_results.csv` |
| 4 | 敏感性实验原始数据（60 行） | `out/sensitivity_results.csv` |
| 5 | 收敛轨迹数据 | `out/trajectory_events.csv`、`out/trajectory_grid.csv` |
| 6 | 表 1—表 4 数据文件 | `out/table1.csv`—`out/table4.csv`、`out/table4_posthoc.csv` |
| 7 | 图表源文件 | `figs/fig_flowchart.png`、`figs/fig_convergence_{eil51,berlin52,st70}.png`、`figs/fig_sensitivity.png`（另附对数纵轴图 3 张）；绘图脚本 `tools/draw_flowchart.py`、`stats/analyze.py` |
| 8 | 统计与绘图脚本 | `stats/analyze.py`、`stats/verify.py` |
| 9 | 种子表 | `out/seeds_main.csv`、`out/seeds_sensitivity.csv` |
| 10 | 环境记录与运行日志 | `environment.md`、`run_log.md`、`out/verification.md` |
| 11 | 参考文献核对（12 条，含 7 条新增经典/方法学文献） | `refs/references_check.csv`、`refs/Djordjevic_2012_thesis.pdf` |
| 12 | 10 城市实例与穷举验证 | `data/cities10.csv`、`out/cities10_check.csv`、`java/tspga/Exhaustive.java` |
| 13 | 诊断附表（附表 F1）与同预算爬山基线 | `out/diagnostics.csv`、`java/tspga/BaselineHill.java` |
| 14 | 完整复跑校验结果（与 `out/` 除耗时外逐字段一致） | `repro/`（360 + 60 + 20 行） |

## 2. 目录结构

```
paper/
├─ paper.docx / paper.md / paper.pdf    论文（SWUFE 格式，41 页）
├─ environment.md                      环境记录（JDK、机器、Python、计时口径、参数版本）
├─ run_log.md                          运行日志（含重跑说明与诊断记录）
├─ data/                               TSPLIB 实例（eil51/berlin52/st70）与 10 城市实例
├─ java/tspga/                         Java 源码
├─ out/                                全部实验数据、表格数据、文档检查结果
├─ figs/                               图 1—图 4（300 dpi PNG）
├─ refs/                               参考文献核对表
├─ stats/                              统计与绘图脚本
└─ tools/                              论文排版脚本（Markdown → DOCX）
```

## 3. 复现步骤

```bash
# 1) 编译
javac -encoding UTF-8 -d out/classes java/tspga/*.java

# 2) 10 城市穷举与四策略验证（可选，约 5 秒）
java -cp out/classes tspga.Main ten

# 3) 主实验：4 策略 × 3 实例 × 30 种子 = 360 次（约 1 分钟）
java -cp out/classes tspga.Main main

# 4) 敏感性实验：3 个变异率 × 20 种子 = 60 次
java -cp out/classes tspga.Main sens D

# 5) 统计与绘图
python stats/analyze.py

# 6) 数据可追溯抽查
python stats/verify.py
```

依赖：JDK 17、Python 3.12（numpy、pandas、scipy、statsmodels、matplotlib）。版本详见 `environment.md`。

## 4. 关键结论速览

| 实例 | 策略 A | 策略 B | 策略 C | 策略 D |
|---|---|---|---|---|
| eil51（最优 426） | 40.10% | 4.22% | 9.30% | **1.28%** |
| berlin52（最优 7542） | 41.30% | 6.89% | 8.15% | **1.49%** |
| st70（最优 675） | 85.41% | **4.65%** | 14.34% | 6.95% |

（表中数字为 30 次运行的平均偏差率；框内加粗为该实例最优策略。）

- H1（2-opt 有效）：三实例均成立（p_holm < 1e-8）。
- H2（贪婪初始化有效）：三实例均成立（p_holm < 1e-8），收敛加速亦得到支持。
- H3（交互效应）：三实例交互项均显著（F=216.54/237.63/1060.92，p<0.001），交互效应值为正，说明两项改进收益部分重叠；st70 上含 2-opt 时贪婪初始化反而显著变差（6.95% 对 4.65%）。
- 探索性敏感性实验：变异率 0.01/0.05/0.10 无可分辨差异（2.573%/2.573%/2.570%）。

## 5. 说明

- 全部 420 次正式运行的 `total_evals` 均为 100000，`status` 均为 `ok`，无非法解。
- 表格数值全部由 `stats/analyze.py` 从原始 CSV 生成，未手工录入；8 个抽查点的独立重算见 `out/verification.md`。
- 数据渠道（GitHub 镜像、TSPLIB）按要求只写入附录，不列入正式参考文献。

## 6. 排版说明（西南财经大学本科生毕业论文规范）

- 纸张 A4，**上下左右页边距均为 3 cm**；正文小四号宋体、1.5 倍行距、首行缩进 2 字符、两端对齐。
- 一级标题二号华文中宋加粗居中（段前 3 行、段后 2 行）；二级标题小三号黑体；三级标题小四号黑体。
- 中文摘要、英文摘要（Abstract）、正文**各自从第 1 页起编**，页码居中、小五号；封面、声明、目录不编页码。
- 表题在表上方、图题在图下方，均为黑体加粗居中、段前段后 0.5 行；表内文字五号、单倍行距。
- 参考文献 12 条，先中文后外文，序号左顶格，格式符合规范示例（期刊 [J] / 学位论文 [D]）。
- 目录由 `tools/build_swufe.py` 两遍生成：先排版、再由 `tools/pdf_bookmarks.py` 读取 PDF 书签得到各标题物理页码，回填正文页码后重新生成，页码与实际排版一致。
- 封面**直接取自规范文件提供的封面**（含“西南财经大学”题字与校徽图片，按原样复制），仅填入论文题目与日期；学院、专业、姓名、学号、年级、指导教师留空待填。
- 题目较长，封面处按 14 pt 排为两行；正文标题仍为规范字号。
- 致谢为通用文字，**建议按实际情况修改**。
