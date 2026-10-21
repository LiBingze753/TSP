package tspga;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.*;

/**
 * 实验驱动：
 *   main   : 主实验 4 策略 × 3 实例 × 30 种子(42..71) = 360 次
 *   warmup : 计时前的 JIT 预热（不记录结果）
 *   sens   : 变异率敏感性 3 个变异率 × 20 种子(72..91) = 60 次
 *   ten    : 10 城市实例穷举 + 四策略验证
 *   one    : 单次运行并打印一行结果
 *
 * 可通过系统属性指定输入/输出目录（默认 data/ 与 out/），便于复跑时不影响已交付数据：
 *   java -Dout.dir=repro -Ddata.dir=data -cp out/classes tspga.Main main
 */
public final class Main {

    private static final String[] INSTANCES = {"eil51", "berlin52", "st70"};
    private static final int[] BEST = {426, 7542, 675};
    private static final String[] STRATEGIES = {"A", "B", "C", "D"};

    private static final String DATA_DIR = System.getProperty("data.dir", "data");
    private static final String OUT_DIR = System.getProperty("out.dir", "out");

    private static final String EV_HEADER = "instance,strategy,seed,eval,best_length,deviation_pct";

    public static void main(String[] args) throws Exception {
        String mode = args.length > 0 ? args[0] : "one";
        switch (mode) {
            case "warmup": warmup(); break;
            case "main": runMain(); break;
            case "sens": runSensitivity(args.length > 1 ? args[1] : "B"); break;
            case "ten": runTen(); break;
            case "one": runOne(args); break;
            default:
                System.err.println("用法: java -Dout.dir=out -cp out/classes tspga.Main "
                        + "{main|sens <A|B|C|D>|ten|warmup|one <实例> <策略> <种子> [变异率]}");
                throw new IllegalArgumentException("unknown mode " + mode);
        }
    }

    private static Instance load(String name) throws IOException {
        for (int i = 0; i < INSTANCES.length; i++) {
            if (INSTANCES[i].equals(name)) return Instance.loadTsplib(DATA_DIR + "/" + name + ".tsp", BEST[i]);
        }
        throw new IllegalArgumentException("unknown instance " + name);
    }

    // ------------------------------------------------------------------ 预热

    private static void warmup() throws Exception {
        System.err.println("[warmup] JIT 预热开始（结果不记录）");
        for (int rep = 0; rep < 3; rep++) {
            for (String inst : INSTANCES) {
                Instance in = load(inst);
                for (String s : STRATEGIES) {
                    new GA(in, s, 1L + rep).run();
                }
            }
        }
        System.err.println("[warmup] 完成");
    }

    // ------------------------------------------------------------------ 主实验

    private static void runMain() throws Exception {
        warmup();
        try (BufferedWriter wRes = writer(path("main_results.csv"));
             BufferedWriter wEv = writer(path("trajectory_events.csv"));
             BufferedWriter wGrid = writer(path("trajectory_grid.csv"))) {

            wRes.write("run_id,instance,strategy,seed,params_version,final_length,best_known,deviation_pct,"
                    + "hit_opt,first_best_eval,total_evals,elapsed_ms,optimal_path,opt_moves,opt_evals,"
                    + "opt_scan_checks,distinct_final,status,notes");
            wRes.newLine();
            wEv.write(EV_HEADER); wEv.newLine();
            wGrid.write(EV_HEADER); wGrid.newLine();

            int runId = 0;
            for (String inst : INSTANCES) {
                Instance in = load(inst);
                for (String s : STRATEGIES) {
                    for (int seed = 42; seed <= 71; seed++) {
                        runId++;
                        GA.Result r = new GA(in, s, seed).run();
                        wRes.write(row(runId, in, s, seed, r)); wRes.newLine();
                        writeTraj(wEv, in, s, seed, r.events);
                        writeTraj(wGrid, in, s, seed, r.grid);
                        System.err.printf(Locale.ROOT, "[main] %3d %s %s seed=%d len=%d dev=%.3f%% evals=%d %.0fms%n",
                                runId, inst, s, seed, r.finalLength, r.deviationPct, r.totalEvals, (double) r.elapsedMs);
                    }
                }
            }
        }
    }

    private static void writeTraj(BufferedWriter w, Instance in, String s, int seed, List<int[]> pts) throws IOException {
        for (int[] p : pts) {
            double dev = (p[1] - in.bestKnown) * 100.0 / in.bestKnown;
            w.write(in.name + "," + s + "," + seed + "," + p[0] + "," + p[1] + "," + fmt(dev));
            w.newLine();
        }
    }

    private static String row(int runId, Instance in, String s, int seed, GA.Result r) {
        return runId + "," + in.name + "," + s + "," + seed + "," + GA.PARAMS_VERSION + ","
                + r.finalLength + "," + r.bestKnown + "," + fmt(r.deviationPct) + "," + r.hitOpt + ","
                + r.firstBestEval + "," + r.totalEvals + "," + r.elapsedMs + ","
                + r.optimalPath + "," + r.optMoves + "," + r.optEvals + "," + r.optScanChecks + ","
                + r.distinctFinal + "," + r.status + ","
                + (r.notes == null ? "" : r.notes.replace(",", ";"));
    }

    // ------------------------------------------------------------------ 敏感性实验

    private static void runSensitivity(String strategy) throws Exception {
        double[] rates = {0.01, 0.05, 0.10};
        Instance in = load("berlin52");
        try (BufferedWriter w = writer(path("sensitivity_results.csv"))) {
            w.write("run_id,instance,strategy,seed,params_version,mutation_rate,final_length,best_known,"
                    + "deviation_pct,hit_opt,first_best_eval,total_evals,elapsed_ms,optimal_path,"
                    + "opt_moves,opt_evals,opt_scan_checks,distinct_final,status,notes");
            w.newLine();
            int id = 0;
            for (double mr : rates) {
                for (int seed = 72; seed <= 91; seed++) {
                    id++;
                    GA.Result r = new GA(in, strategy, seed).withMutationRate(mr).run();
                    w.write(id + "," + in.name + "," + strategy + "," + seed + "," + GA.PARAMS_VERSION + ","
                            + mr + "," + r.finalLength + "," + r.bestKnown + "," + fmt(r.deviationPct) + ","
                            + r.hitOpt + "," + r.firstBestEval + "," + r.totalEvals + "," + r.elapsedMs + ","
                            + r.optimalPath + "," + r.optMoves + "," + r.optEvals + "," + r.optScanChecks + ","
                            + r.distinctFinal + "," + r.status + "," + (r.notes == null ? "" : r.notes));
                    w.newLine();
                    System.err.printf(Locale.ROOT, "[sens] %2d mr=%.2f seed=%d len=%d dev=%.3f%%%n",
                            id, mr, seed, r.finalLength, r.deviationPct);
                }
            }
        }
    }

    // ------------------------------------------------------------------ 10 城市

    private static void runTen() throws Exception {
        Instance in = Instance.loadCsv(DATA_DIR + "/cities10.csv", "cities10", 0);
        int[] bestTour = new int[in.n];
        int opt = Exhaustive.best(in, bestTour);
        System.out.println("[ten] exhaustive optimum = " + opt);
        System.out.println("[ten] optimal tour (0-based) = " + Arrays.toString(bestTour));
        System.out.println("[ten] optimal path = " + in.tourToString(bestTour));

        Instance withOpt = Instance.loadCsv(DATA_DIR + "/cities10.csv", "cities10", opt);
        try (BufferedWriter w = writer(path("cities10_check.csv"))) {
            w.write("strategy,seed,final_length,exact_optimum,deviation_pct,legal,path,opt_moves,"
                    + "opt_evals,opt_scan_checks,total_evals,elapsed_ms,status,notes");
            w.newLine();
            for (String s : STRATEGIES) {
                for (int seed = 42; seed <= 46; seed++) {
                    GA.Result r = new GA(withOpt, s, seed).run();
                    boolean legal = in.isPermutation(parsePath(r.optimalPath, in));
                    w.write(s + "," + seed + "," + r.finalLength + "," + opt + "," + fmt(r.deviationPct) + ","
                            + (legal ? 1 : 0) + "," + r.optimalPath + "," + r.optMoves + "," + r.optEvals + ","
                            + r.optScanChecks + "," + r.totalEvals + "," + r.elapsedMs + "," + r.status
                            + "," + (r.notes == null ? "" : r.notes));
                    w.newLine();
                    System.out.printf(Locale.ROOT, "[ten] %s seed=%d len=%d opt=%d dev=%.3f%% legal=%b%n",
                            s, seed, r.finalLength, opt, r.deviationPct, legal);
                }
            }
        }
        System.out.println("[ten] exhaustive check done");
    }

    private static int[] parsePath(String path, Instance in) {
        String[] p = path.split("-");
        int[] t = new int[p.length];
        for (int i = 0; i < p.length; i++) {
            int id = Integer.parseInt(p[i]);
            int idx = -1;
            for (int k = 0; k < in.n; k++) if (in.id[k] == id) { idx = k; break; }
            t[i] = idx;
        }
        return t;
    }

    // ------------------------------------------------------------------ 单次

    private static void runOne(String[] args) throws Exception {
        String inst = args.length > 1 ? args[1] : "eil51";
        String strat = args.length > 2 ? args[2] : "A";
        int seed = args.length > 3 ? Integer.parseInt(args[3]) : 42;
        Instance in = load(inst);
        GA ga = new GA(in, strat, seed);
        if (args.length > 4) ga = ga.withMutationRate(Double.parseDouble(args[4]));
        GA.Result r = ga.run();
        System.out.println(row(1, in, strat, seed, r));
    }

    // ------------------------------------------------------------------ 工具

    private static String path(String name) {
        return OUT_DIR + "/" + name;
    }

    private static BufferedWriter writer(String path) throws IOException {
        File f = new File(path);
        File dir = f.getParentFile();
        if (dir != null && !dir.exists()) Files.createDirectories(Paths.get(dir.getPath()));
        return new BufferedWriter(new OutputStreamWriter(new FileOutputStream(f), StandardCharsets.UTF_8));
    }

    static String fmt(double v) {
        return String.format(Locale.ROOT, "%.6f", v);
    }
}
