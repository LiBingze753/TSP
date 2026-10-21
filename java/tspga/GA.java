package tspga;

import java.util.*;

/**
 * 遗传算法求解 TSP（四种策略 A/B/C/D）。
 *
 * 固定参数（params_v1）：
 *   POP=100, 锦标赛规模=2, 交叉概率=0.90（每对父母，未交叉则复制父母各1个）,
 *   变异率=0.05（每个子代，交换变异一次）, 精英保留=2,
 *   终止：累计完整适应度评估次数达到 100000（硬截断）。
 *
 * 2-opt（策略 B/D）：每代对排序后前 2 个精英执行；first-improvement；
 *   单次最多 3 轮、每轮最多接受 20 次改进、累计最多 60 次接受移动；
 *   每次接受移动后对完整路径长度计 1 次完整评估并计入总预算；
 *   候选边对增量检查不计入总评估，仅计入 opt_scan_checks。
 *
 * 贪婪初始化（策略 C/D）：初始种群前 50% 用最近邻构造（随机起点、并列取小编号）。
 */
public final class GA {

    public static final String PARAMS_VERSION = "params_v1";
    public static final int POP = 100;
    public static final int ELITE = 2;
    public static final int TOURNAMENT = 2;
    public static final int BUDGET = 100000;
    public static final double PROB_CROSS = 0.90;
    public static final double PROB_MUT = 0.05;
    public static final int OPT_ROUNDS = 3;
    public static final int OPT_PER_ROUND = 20;
    public static final int OPT_TOTAL = 60;
    public static final int GRID_STEP = 1000;

    /** 一次运行的完整结果。 */
    public static final class Result {
        public int finalLength;
        public int bestKnown;
        public double deviationPct;
        public int hitOpt;
        public int firstBestEval;      // 首次达到本次运行最终最优时的累计完整评估次数
        public int totalEvals;
        public long elapsedMs;
        public String optimalPath;
        public int optMoves, optEvals, optScanChecks;
        public int distinctFinal;      // 终止时种群中不同个体的数目（多样性诊断）
        public String status = "ok";
        public String notes = "";
        public List<int[]> events = new ArrayList<>();  // {eval, best_length}
        public List<int[]> grid = new ArrayList<>();    // {eval, best_length}，每 1000 次评估
    }

    private static final class Ind {
        int[] t;
        int len;
        Ind(int[] t) { this.t = t; }
        Ind copy() { Ind c = new Ind(t.clone()); c.len = len; return c; }
    }

    private static final Comparator<Ind> BY_LEN = Comparator.comparingInt((Ind a) -> a.len);

    private final Instance in;
    private final String strategy;   // "A"|"B"|"C"|"D"
    private final long seed;
    private final Random rnd;
    private final boolean useOpt, useGreedy;
    private double probMut = PROB_MUT;

    private int evals = 0;
    private int[] gBest;
    private int gBestLen = Integer.MAX_VALUE;
    private int firstBestEval = -1;
    private int lastGridEval = -1;
    private final ArrayList<int[]> events = new ArrayList<>();
    private final ArrayList<int[]> grid = new ArrayList<>();
    private int optMoves = 0, optEvals = 0, optScanChecks = 0;

    public GA(Instance in, String strategy, long seed) {        this.in = in;
        this.strategy = strategy.toUpperCase(Locale.ROOT);
        this.seed = seed;
        this.rnd = new Random(seed);
        switch (this.strategy) {
            case "A": useOpt = false; useGreedy = false; break;
            case "B": useOpt = true;  useGreedy = false; break;
            case "C": useOpt = false; useGreedy = true;  break;
            case "D": useOpt = true;  useGreedy = true;  break;
            default: throw new IllegalArgumentException("unknown strategy " + strategy);
        }
    }

    /** 仅用于敏感性实验：覆盖变异率（默认 0.05）。 */
    public GA withMutationRate(double mr) {
        this.probMut = mr;
        return this;
    }

    // ------------------------------------------------------------------ 运行主循环

    public Result run() {
        final long t0 = System.nanoTime();
        final int n = in.n;

        Ind[] pop = new Ind[POP];
        for (int i = 0; i < POP; i++) {
            int[] t = (useGreedy && i < POP / 2) ? greedyTour() : randomTour();
            pop[i] = new Ind(t);
        }
        // 评估初始种群
        for (Ind p : pop) {
            p.len = in.length(p.t);
            evals++;
            noteSolution(p.len, p.t);
        }

        int gen = 0;
        final boolean dbg = System.getProperty("ga.debug") != null;
        while (evals < BUDGET) {
            Arrays.sort(pop, BY_LEN);

            if (useOpt) {
                boolean stop = false;
                for (int k = 0; k < ELITE; k++) {
                    if (twoOpt(pop[k].t)) { stop = true; break; }
                    pop[k].len = in.length(pop[k].t);   // 仅更新缓存，不计评估
                }
                if (stop) break;
                Arrays.sort(pop, BY_LEN);
            }

            // 生成子代
            Ind[] q = new Ind[POP];
            int qs = 0;
            while (qs < POP) {
                int i1 = tournament(pop);
                int i2 = tournament(pop);
                Ind c1, c2;
                if (rnd.nextDouble() < PROB_CROSS) {
                    int[][] ch = pmx(pop[i1].t, pop[i2].t);
                    c1 = new Ind(ch[0]);
                    c2 = new Ind(ch[1]);
                } else {
                    c1 = pop[i1].copy();
                    c2 = pop[i2].copy();
                }
                mutate(c1);
                mutate(c2);
                q[qs++] = c1;
                if (qs < POP) q[qs++] = c2;
            }

            // 逐个评估子代（评估前检查预算）
            boolean full = true;
            for (int i = 0; i < POP; i++) {
                if (evals >= BUDGET) { full = false; break; }
                q[i].len = in.length(q[i].t);
                evals++;
                noteSolution(q[i].len, q[i].t);
            }
            if (!full) break;

            // 精英保留：子代中最差 2 个用父代前 2 个精英替换
            Arrays.sort(q, BY_LEN);
            q[POP - 1] = pop[0].copy();
            q[POP - 2] = pop[1].copy();
            pop = q;
            gen++;
            if (dbg && (gen <= 5 || gen % 100 == 0)) {
                double sum = 0;
                for (Ind x : pop) sum += x.len;
                int distinct = 0, invalid = 0;
                for (int i = 0; i < POP; i++) {
                    boolean dup = false;
                    for (int j = 0; j < i; j++) if (Arrays.equals(pop[i].t, pop[j].t)) { dup = true; break; }
                    if (!dup) distinct++;
                    if (!in.isPermutation(pop[i].t)) invalid++;
                }
                System.err.printf(Locale.ROOT, "gen=%d evals=%d best=%d avg=%.1f distinct=%d invalid=%d%n",
                        gen, evals, pop[0].len, sum / POP, distinct, invalid);
            }
        }

        Result r = new Result();
        r.finalLength = gBestLen;
        r.bestKnown = in.bestKnown;
        r.deviationPct = (gBestLen - in.bestKnown) * 100.0 / in.bestKnown;
        r.hitOpt = (gBestLen == in.bestKnown) ? 1 : 0;
        r.firstBestEval = firstBestEval;
        r.totalEvals = evals;
        r.elapsedMs = (System.nanoTime() - t0) / 1_000_000L;
        r.optimalPath = in.tourToString(gBest);
        r.optMoves = optMoves;
        r.optEvals = optEvals;
        r.optScanChecks = optScanChecks;
        java.util.HashSet<String> uniq = new java.util.HashSet<>();
        for (Ind x : pop) uniq.add(Arrays.toString(x.t));
        r.distinctFinal = uniq.size();
        r.events = events;
        r.grid = grid;
        if (gBestLen < in.bestKnown) { r.status = "illegal"; r.notes = "final_length < best_known"; }
        if (!in.isPermutation(gBest)) { r.status = "illegal"; r.notes = "invalid permutation"; }
        if (evals != BUDGET) { r.notes = (r.notes.isEmpty() ? "" : r.notes + "; ") + "total_evals=" + evals; }
        return r;
    }

    /** 记录严格改进事件与 1000 次评估网格点。须在 evals 递增之后调用。 */
    private void noteSolution(int len, int[] tour) {
        if (len < gBestLen) {
            gBestLen = len;
            gBest = tour.clone();
            firstBestEval = evals;
            events.add(new int[]{evals, len});
        }
        if (evals % GRID_STEP == 0 && evals != lastGridEval) {
            lastGridEval = evals;
            grid.add(new int[]{evals, gBestLen});
        }
    }

    // ------------------------------------------------------------------ 初始化

    private int[] randomTour() {
        int n = in.n;
        int[] t = new int[n];
        for (int i = 0; i < n; i++) t[i] = i;
        for (int i = n - 1; i > 0; i--) {
            int j = rnd.nextInt(i + 1);
            int tmp = t[i]; t[i] = t[j]; t[j] = tmp;
        }
        return t;
    }

    /** 最近邻构造：随机起点，每次选最近的未访问城市；距离并列取编号小者。 */
    private int[] greedyTour() {
        int n = in.n;
        int[] t = new int[n];
        boolean[] used = new boolean[n];
        int cur = rnd.nextInt(n);
        t[0] = cur;
        used[cur] = true;
        for (int k = 1; k < n; k++) {
            int best = -1, bestD = Integer.MAX_VALUE;
            for (int v = 0; v < n; v++) {
                if (used[v]) continue;
                int dd = in.d[cur][v];
                if (dd < bestD) { bestD = dd; best = v; }
            }
            t[k] = best;
            used[best] = true;
            cur = best;
        }
        return t;
    }

    // ------------------------------------------------------------------ 遗传算子

    private int tournament(Ind[] pop) {
        int a = rnd.nextInt(pop.length);
        int b = rnd.nextInt(pop.length);
        return pop[a].len <= pop[b].len ? a : b;
    }

    private void mutate(Ind c) {
        if (rnd.nextDouble() < probMut) {
            int n = in.n;
            int i = rnd.nextInt(n);
            int j = rnd.nextInt(n);
            while (j == i) j = rnd.nextInt(n);
            int tmp = c.t[i]; c.t[i] = c.t[j]; c.t[j] = tmp;
        }
    }

    /** PMX（部分匹配交叉）：返回两个合法子代。 */
    private int[][] pmx(int[] p1, int[] p2) {
        int n = p1.length;
        int a = rnd.nextInt(n);
        int b = rnd.nextInt(n);
        if (a > b) { int t = a; a = b; b = t; }
        if (a == b) { b = (a + 1) % n; if (b < a) { int t = a; a = b; b = t; } }
        int[] c1 = new int[n];
        int[] c2 = new int[n];
        Arrays.fill(c1, -1);
        Arrays.fill(c2, -1);
        for (int i = a; i <= b; i++) { c1[i] = p1[i]; c2[i] = p2[i]; }
        fillPmx(c1, p1, p2, a, b);
        fillPmx(c2, p2, p1, a, b);
        return new int[][]{c1, c2};
    }

    /** child 已在 [a,b] 填入 base，其余位置按 other 的顺序填充，冲突用 PMX 映射消解。 */
    private void fillPmx(int[] child, int[] base, int[] other, int a, int b) {
        int n = child.length;
        for (int i = 0; i < n; i++) {
            if (i >= a && i <= b) continue;
            int val = other[i];
            // 若 val 已被占用（在区间内），沿映射 base[j]==val -> other[j] 继续替换
            while (inSegment(child, val, a, b)) {
                int j = indexInSegment(base, val, a, b);
                val = other[j];
            }
            child[i] = val;
        }
    }

    private static boolean inSegment(int[] arr, int val, int a, int b) {
        for (int i = a; i <= b; i++) if (arr[i] == val) return true;
        return false;
    }

    private static int indexInSegment(int[] arr, int val, int a, int b) {
        for (int i = a; i <= b; i++) if (arr[i] == val) return i;
        return -1;
    }

    // ------------------------------------------------------------------ 2-opt

    /** 对单条路径执行 first-improvement 2-opt；返回是否因预算耗尽而要求整体停止。 */
    private boolean twoOpt(int[] t) {
        int total = 0;
        for (int round = 0; round < OPT_ROUNDS; round++) {
            int acc = 0;
            while (acc < OPT_PER_ROUND && total < OPT_TOTAL) {
                if (evals >= BUDGET) return true;
                int[] mv = firstImprovement(t);
                if (mv == null) break;                 // 完整扫描无改进
                if (evals >= BUDGET) return true;
                reverse(t, mv[0] + 1, mv[1]);
                int len = in.length(t);                // 接受移动后的完整评估
                evals++;
                optEvals++;
                optMoves++;
                total++;
                acc++;
                noteSolution(len, t);
                if (evals >= BUDGET) return true;
            }
        }
        return evals >= BUDGET;
    }

    /**
     * 扫描所有边对 (i,i+1) 与 (j,j+1)，返回第一个可降低路径长度的 2-opt 移动 {i,j}。
     * 反转区间为 i+1..j；i=0 且 j=n-1 的移动等价于原路径，跳过。
     * 每次候选检查计入 opt_scan_checks。
     */
    private int[] firstImprovement(int[] t) {
        int n = t.length;
        for (int i = 0; i < n - 1; i++) {
            int i1 = (i + 1) % n;
            for (int j = i + 2; j < n; j++) {
                if (i == 0 && j == n - 1) continue;
                int j1 = (j + 1) % n;
                optScanChecks++;
                int delta = in.d[t[i]][t[j]] + in.d[t[i1]][t[j1]] - in.d[t[i]][t[i1]] - in.d[t[j]][t[j1]];
                if (delta < -1e-9) return new int[]{i, j};
            }
        }
        return null;
    }

    private static void reverse(int[] a, int from, int to) {
        while (from < to) {
            int tmp = a[from]; a[from] = a[to]; a[to] = tmp;
            from++; to--;
        }
    }
}
