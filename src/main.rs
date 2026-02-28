use std::io::{self, BufRead, Write};
use std::collections::BinaryHeap;
use std::cmp::Reverse;

const N: usize = 30;
const N_H: usize = N * (N - 1); // horizontal edges: 30*29 = 870
const N_V: usize = (N - 1) * N; // vertical edges: 29*30 = 870
const N_EDGES: usize = N_H + N_V;
const N_PARAMS: usize = N * 2; // 30 row_h + 30 col_v
const INIT_W: f64 = 5000.0;
const SIGMA_PRIOR: f64 = 3000.0;   // prior std dev on parameters
const SIGMA_NOISE: f64 = 500.0;    // observation noise std dev (10% of ~5000)
const LAMBDA: f64 = (SIGMA_NOISE * SIGMA_NOISE) / (SIGMA_PRIOR * SIGMA_PRIOR);
const UCB_C: f64 = 3.0;            // Bayesian UCB coefficient (mean - C * sigma)
const UCB_STOP: usize = 200;       // stop exploration after this many queries

// Edge index helpers
// h_{i,j}: horizontal edge between (i,j)-(i,j+1), i in 0..30, j in 0..29
fn h_idx(i: usize, j: usize) -> usize {
    i * (N - 1) + j
}
// v_{i,j}: vertical edge between (i,j)-(i+1,j), i in 0..29, j in 0..30
fn v_idx(i: usize, j: usize) -> usize {
    N_H + i * N + j
}

// Parameter index: row_h[i] -> param i, col_v[j] -> param 30+j
fn edge_to_param(edge: usize) -> usize {
    if edge < N_H {
        edge / (N - 1) // row index
    } else {
        N + (edge - N_H) % N // N + col index
    }
}

struct Solver {
    edge_est: Vec<f64>,
    param_var: Vec<f64>,  // posterior variance per parameter
    query_count: usize,
    // Posterior precision matrix (AtA/σ² + Σ_prior⁻¹) and right-hand side
    ata: Vec<f64>,  // 60x60, row-major
    aty: Vec<f64>,  // 60
}

impl Solver {
    fn new() -> Self {
        let mut ata = vec![0.0f64; N_PARAMS * N_PARAMS];
        let mut aty = vec![0.0f64; N_PARAMS];
        // Add regularization: lambda * I, and lambda * 5000 to aty
        for i in 0..N_PARAMS {
            ata[i * N_PARAMS + i] += LAMBDA;
            aty[i] += LAMBDA * INIT_W;
        }
        Solver {
            edge_est: vec![INIT_W; N_EDGES],
            param_var: vec![SIGMA_PRIOR * SIGMA_PRIOR; N_PARAMS],
            query_count: 0,
            ata,
            aty,
        }
    }

    fn add_observation(&mut self, path_edges: &[usize], b_obs: f64) {
        self.query_count += 1;
        // Compute row/col counts for this path
        let mut a = vec![0.0f64; N_PARAMS];
        for &e in path_edges {
            a[edge_to_param(e)] += 1.0;
        }
        // Update AtA and Aty
        for i in 0..N_PARAMS {
            if a[i] == 0.0 { continue; }
            self.aty[i] += a[i] * b_obs;
            for j in 0..N_PARAMS {
                if a[j] == 0.0 { continue; }
                self.ata[i * N_PARAMS + j] += a[i] * a[j];
            }
        }
    }

    fn solve(&mut self) {
        // Solve (AtA + lambda*I) x = Aty via Gaussian elimination
        let n = N_PARAMS;
        let mut mat = self.ata.clone();
        let mut rhs = self.aty.clone();

        for col in 0..n {
            // Find pivot
            let mut pivot = col;
            for row in col + 1..n {
                if mat[row * n + col].abs() > mat[pivot * n + col].abs() {
                    pivot = row;
                }
            }
            for k in 0..n {
                mat.swap(col * n + k, pivot * n + k);
            }
            rhs.swap(col, pivot);

            let diag = mat[col * n + col];
            if diag.abs() < 1e-12 { continue; }
            for row in col + 1..n {
                let factor = mat[row * n + col] / diag;
                for k in col..n {
                    let v = mat[col * n + k] * factor;
                    mat[row * n + k] -= v;
                }
                rhs[row] -= rhs[col] * factor;
            }
        }
        // Back substitution for mean
        let mut x = vec![0.0f64; n];
        for i in (0..n).rev() {
            let mut s = rhs[i];
            for j in i + 1..n {
                s -= mat[i * n + j] * x[j];
            }
            x[i] = s / mat[i * n + i];
        }

        // Compute posterior variance (diagonal of (AtA + λI)^{-1} * σ²)
        // Solve for each unit vector e_i to get column i of the inverse
        let mut var = vec![0.0f64; n];
        for col_idx in 0..n {
            let mut ei = vec![0.0f64; n];
            ei[col_idx] = 1.0;
            // Forward substitution using already-eliminated mat
            // (apply same row ops that were done during elimination — but we lost them)
            // Instead: solve mat * v = ei by back substitution since mat is upper triangular
            let mut v = ei;
            // Forward: nothing to do (mat is upper triangular after elimination)
            // Back substitution
            for i in (0..n).rev() {
                let mut s = v[i];
                for j in i + 1..n {
                    s -= mat[i * n + j] * v[j];
                }
                v[i] = s / mat[i * n + i];
            }
            var[col_idx] = v[col_idx] * (SIGMA_NOISE * SIGMA_NOISE);
        }
        for i in 0..n {
            self.param_var[i] = var[i].max(1.0);
        }

        // Update edge estimates
        for i in 0..N {
            for j in 0..N - 1 {
                let w = x[i].max(1.0); // row_h[i]
                self.edge_est[h_idx(i, j)] = w;
            }
        }
        for i in 0..N - 1 {
            for j in 0..N {
                let w = x[N + j].max(1.0); // col_v[j]
                self.edge_est[v_idx(i, j)] = w;
            }
        }
    }

    fn ucb_weight(&self, e: usize) -> f64 {
        if self.query_count >= UCB_STOP {
            return self.edge_est[e];
        }
        let p = edge_to_param(e);
        let sigma = self.param_var[p].sqrt();
        (self.edge_est[e] - UCB_C * sigma).max(1.0)
    }

    fn dijkstra(&self, si: usize, sj: usize, ti: usize, tj: usize) -> Vec<usize> {
        let src = si * N + sj;
        let dst = ti * N + tj;
        let mut dist = vec![f64::INFINITY; N * N];
        let mut prev_edge = vec![usize::MAX; N * N];
        let mut prev_node = vec![usize::MAX; N * N];
        dist[src] = 0.0;

        // Min-heap: (cost * 1e6 as u64, node)
        let mut heap: BinaryHeap<Reverse<(u64, usize)>> = BinaryHeap::new();
        heap.push(Reverse((0, src)));

        while let Some(Reverse((d, u))) = heap.pop() {
            let df = d as f64 / 1e6;
            if df > dist[u] + 1e-9 { continue; }
            if u == dst { break; }

            let ui = u / N;
            let uj = u % N;

            // Up: (ui-1, uj)
            if ui > 0 {
                let e = v_idx(ui - 1, uj);
                let nd = dist[u] + self.ucb_weight(e);
                let v = (ui - 1) * N + uj;
                if nd < dist[v] {
                    dist[v] = nd;
                    prev_edge[v] = e;
                    prev_node[v] = u;
                    heap.push(Reverse(((nd * 1e6) as u64, v)));
                }
            }
            // Down: (ui+1, uj)
            if ui < N - 1 {
                let e = v_idx(ui, uj);
                let nd = dist[u] + self.ucb_weight(e);
                let v = (ui + 1) * N + uj;
                if nd < dist[v] {
                    dist[v] = nd;
                    prev_edge[v] = e;
                    prev_node[v] = u;
                    heap.push(Reverse(((nd * 1e6) as u64, v)));
                }
            }
            // Left: (ui, uj-1)
            if uj > 0 {
                let e = h_idx(ui, uj - 1);
                let nd = dist[u] + self.ucb_weight(e);
                let v = ui * N + uj - 1;
                if nd < dist[v] {
                    dist[v] = nd;
                    prev_edge[v] = e;
                    prev_node[v] = u;
                    heap.push(Reverse(((nd * 1e6) as u64, v)));
                }
            }
            // Right: (ui, uj+1)
            if uj < N - 1 {
                let e = h_idx(ui, uj);
                let nd = dist[u] + self.ucb_weight(e);
                let v = ui * N + uj + 1;
                if nd < dist[v] {
                    dist[v] = nd;
                    prev_edge[v] = e;
                    prev_node[v] = u;
                    heap.push(Reverse(((nd * 1e6) as u64, v)));
                }
            }
        }

        // Trace back path edges
        let mut edges = Vec::new();
        let mut cur = dst;
        while cur != src {
            edges.push(prev_edge[cur]);
            cur = prev_node[cur];
        }
        edges.reverse();
        edges
    }

    fn path_to_str(&self, si: usize, sj: usize, path_edges: &[usize]) -> String {
        let mut s = String::new();
        let mut ci = si;
        let mut cj = sj;
        for &e in path_edges {
            if e < N_H {
                let ei = e / (N - 1);
                let ej = e % (N - 1);
                if ei == ci && ej == cj {
                    s.push('R');
                    cj += 1;
                } else {
                    s.push('L');
                    cj -= 1;
                }
            } else {
                let ve = e - N_H;
                let ei = ve / N;
                let ej = ve % N;
                if ei == ci && ej == cj {
                    s.push('D');
                    ci += 1;
                } else {
                    s.push('U');
                    ci -= 1;
                }
            }
        }
        s
    }
}

fn main() {
    let stdin = io::stdin();
    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());

    let mut solver = Solver::new();
    let mut lines = stdin.lock().lines();

    for _ in 0..1000 {
        let line = lines.next().unwrap().unwrap();
        let mut iter = line.split_whitespace();
        let si: usize = iter.next().unwrap().parse().unwrap();
        let sj: usize = iter.next().unwrap().parse().unwrap();
        let ti: usize = iter.next().unwrap().parse().unwrap();
        let tj: usize = iter.next().unwrap().parse().unwrap();

        let path_edges = solver.dijkstra(si, sj, ti, tj);
        let path_str = solver.path_to_str(si, sj, &path_edges);

        writeln!(out, "{}", path_str).unwrap();
        out.flush().unwrap();

        let line2 = lines.next().unwrap().unwrap();
        let b_obs: f64 = line2.trim().parse().unwrap();

        solver.add_observation(&path_edges, b_obs);
        solver.solve();
    }
}
