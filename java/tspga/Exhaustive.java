package tspga;

/** 10 城市实例穷举：固定起点为节点 0，枚举其余 9! 个排列。 */
public final class Exhaustive {

    private static int n;
    private static int[][] d;
    private static boolean[] used;
    private static int[] cur, best;
    private static int bestLen = Integer.MAX_VALUE;

    public static int best(Instance in, int[] outBest) {
        n = in.n;
        d = in.d;
        used = new boolean[n];
        cur = new int[n];
        best = new int[n];
        bestLen = Integer.MAX_VALUE;
        cur[0] = 0;
        used[0] = true;
        dfs(1, 0, 0);
        System.arraycopy(best, 0, outBest, 0, n);
        return bestLen;
    }

    private static void dfs(int depth, int curCity, int len) {
        if (depth == n) {
            int total = len + d[curCity][0];
            if (total < bestLen) {
                bestLen = total;
                System.arraycopy(cur, 0, best, 0, n);
            }
            return;
        }
        // 剪枝：当前部分路径已不短于已知最优
        if (len >= bestLen) return;
        for (int v = 1; v < n; v++) {
            if (used[v]) continue;
            used[v] = true;
            cur[depth] = v;
            dfs(depth + 1, v, len + d[curCity][v]);
            used[v] = false;
        }
    }
}
