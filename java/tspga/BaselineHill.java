package tspga;

import java.util.Locale;
import java.util.Random;

/**
 * 诊断用基线：随机 1-交换爬山。
 *
 * 用途仅作对照——在同一评估预算（100000 次完整路径长度计算）下，
 * 反复随机交换两个城市，若路径变长则回退。它不使用种群、交叉与精英机制，
 * 每次评估都针对一个"新"个体，因此可用于衡量策略 A 是否把预算浪费在了重复个体上。
 * 该程序不参与主实验、敏感性实验与论文表格的任何数值。
 */
public final class BaselineHill {

    public static void main(String[] args) throws Exception {
        String[] names = {"eil51", "berlin52", "st70"};
        int[] best = {426, 7542, 675};
        int budget = 100000;
        for (int k = 0; k < names.length; k++) {
            Instance in = Instance.loadTsplib("data/" + names[k] + ".tsp", best[k]);
            Random rnd = new Random(42);
            int[] t = new int[in.n];
            for (int i = 0; i < in.n; i++) t[i] = i;
            for (int i = in.n - 1; i > 0; i--) {
                int j = rnd.nextInt(i + 1);
                int tmp = t[i]; t[i] = t[j]; t[j] = tmp;
            }
            int cur = in.length(t);
            int bestLen = cur;
            for (int e = 0; e < budget; e++) {
                int i = rnd.nextInt(in.n), j = rnd.nextInt(in.n);
                while (j == i) j = rnd.nextInt(in.n);
                int tmp = t[i]; t[i] = t[j]; t[j] = tmp;
                int len = in.length(t);
                if (len <= cur) {
                    cur = len;
                    if (len < bestLen) bestLen = len;
                } else {
                    tmp = t[i]; t[i] = t[j]; t[j] = tmp;
                }
            }
            double dev = (bestLen - best[k]) * 100.0 / best[k];
            System.out.printf(Locale.ROOT, "%s  best=%d  dev=%.2f%%%n", names[k], bestLen, dev);
        }
    }
}
