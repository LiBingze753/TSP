package tspga;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/**
 * TSP 实例：节点坐标 + EUC_2D 距离矩阵 + 已知最优值。
 * 距离口径：d(i,j) = nint(sqrt(dx^2+dy^2))，即四舍五入到最近整数。
 */
public final class Instance {
    public final String name;
    public final int n;
    public final int[] id;        // 原始城市编号（TSPLIB 为 1..n，cities10 为 0..9）
    public final double[] x, y;
    public final int[][] d;
    public final int bestKnown;

    private Instance(String name, int[] id, double[] x, double[] y, int bestKnown) {
        this.name = name;
        this.n = id.length;
        this.id = id;
        this.x = x;
        this.y = y;
        this.bestKnown = bestKnown;
        this.d = new int[n][n];
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                if (i == j) { d[i][j] = 0; continue; }
                double dx = x[i] - x[j], dy = y[i] - y[j];
                d[i][j] = (int) Math.round(Math.sqrt(dx * dx + dy * dy));
            }
        }
        validateMatrix();
    }

    /** 校验：维度一致、对称、对角线为 0。 */
    private void validateMatrix() {
        for (int i = 0; i < n; i++) {
            if (d[i][i] != 0) throw new IllegalStateException("distance diagonal != 0 at " + i);
            for (int j = i + 1; j < n; j++) {
                if (d[i][j] != d[j][i]) throw new IllegalStateException("distance matrix not symmetric: " + i + "," + j);
                if (d[i][j] < 0) throw new IllegalStateException("negative distance");
            }
        }
    }

    /** 解析 TSPLIB 格式（EUC_2D）。 */
    public static Instance loadTsplib(String path, int bestKnown) throws IOException {
        List<String> lines = new ArrayList<>();
        try (BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream(path), StandardCharsets.UTF_8))) {
            String s;
            while ((s = br.readLine()) != null) lines.add(s.trim());
        }
        String name = null, ewt = null;
        int dim = -1;
        int idx = -1;
        List<double[]> rows = new ArrayList<>();
        for (int k = 0; k < lines.size(); k++) {
            String s = lines.get(k);
            if (s.isEmpty()) continue;
            String up = s.toUpperCase(Locale.ROOT);
            if (up.startsWith("NAME")) {
                name = s.substring(s.indexOf(':') + 1).trim();
            } else if (up.startsWith("DIMENSION")) {
                dim = Integer.parseInt(s.substring(s.indexOf(':') + 1).trim());
            } else if (up.startsWith("EDGE_WEIGHT_TYPE")) {
                ewt = s.substring(s.indexOf(':') + 1).trim();
            } else if (up.startsWith("NODE_COORD_SECTION")) {
                idx = k + 1;
                break;
            }
        }
        if (idx < 0) throw new IOException("NODE_COORD_SECTION not found in " + path);
        for (int k = idx; k < lines.size(); k++) {
            String s = lines.get(k);
            if (s.isEmpty()) continue;
            if (s.toUpperCase(Locale.ROOT).startsWith("EOF")) break;
            String[] p = s.split("\\s+");
            if (p.length < 3) break;
            rows.add(new double[]{Double.parseDouble(p[0]), Double.parseDouble(p[1]), Double.parseDouble(p[2])});
        }
        if (!"EUC_2D".equalsIgnoreCase(ewt)) throw new IOException("EDGE_WEIGHT_TYPE must be EUC_2D, got " + ewt);
        if (dim != rows.size()) throw new IOException("DIMENSION mismatch: header=" + dim + " rows=" + rows.size());
        int n = rows.size();
        int[] id = new int[n];
        double[] x = new double[n], y = new double[n];
        for (int i = 0; i < n; i++) {
            double[] r = rows.get(i);
            id[i] = (int) Math.round(r[0]);
            x[i] = r[1];
            y[i] = r[2];
        }
        if (name == null) name = path;
        return new Instance(name, id, x, y, bestKnown);
    }

    /** 解析 cities10.csv（逗号分隔：id,x,y）。 */
    public static Instance loadCsv(String path, String name, int bestKnown) throws IOException {
        List<double[]> rows = new ArrayList<>();
        try (BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream(path), StandardCharsets.UTF_8))) {
            String s = br.readLine(); // header
            if (s == null) throw new IOException("empty csv");
            while ((s = br.readLine()) != null) {
                s = s.trim();
                if (s.isEmpty()) continue;
                String[] p = s.split(",");
                rows.add(new double[]{Double.parseDouble(p[0].trim()), Double.parseDouble(p[1].trim()), Double.parseDouble(p[2].trim())});
            }
        }
        int n = rows.size();
        int[] id = new int[n];
        double[] x = new double[n], y = new double[n];
        for (int i = 0; i < n; i++) {
            id[i] = (int) rows.get(i)[0];
            x[i] = rows.get(i)[1];
            y[i] = rows.get(i)[2];
        }
        return new Instance(name, id, x, y, bestKnown);
    }

    /** 路径长度（完整适应度评估）。 */
    public int length(int[] tour) {
        int s = 0;
        for (int i = 0; i < n; i++) s += d[tour[i]][tour[(i + 1) % n]];
        return s;
    }

    public boolean isPermutation(int[] tour) {
        if (tour.length != n) return false;
        boolean[] seen = new boolean[n];
        for (int v : tour) {
            if (v < 0 || v >= n || seen[v]) return false;
            seen[v] = true;
        }
        return true;
    }

    public String tourToString(int[] tour) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < n; i++) {
            if (i > 0) sb.append('-');
            sb.append(id[tour[i]]);
        }
        return sb.toString();
    }
}
