// QUBO Simulated-Annealing-Kernel in Rust (PyO3-Extension).
//
// Algorithmisch äquivalent zum Numba-Kernel in engine/mainframe.py:
//   - x in {0,1}^n, Energie E(x) = x^T Q x
//   - Single-Bit-Flip mit analytischem Delta, O(n)-Update von Qx
//   - Temperatur T = T0 * (1 - t/steps) + 1e-3
//   - Akzeptanz, wenn dE < 0 oder rand() < exp(-dE/T)
// Parallelisierung über `rayon`: jeder Restart läuft echt nebenläufig auf einem
// eigenen Thread (kein GIL) → volle Mehrkern-/Hyperthreading-Nutzung.
//
// HINWEIS: statistisch äquivalent zum NUMBA/PCG64-Pfad, aber NICHT bit-identisch
// (anderer PRNG: SplitMix64; Akzeptanz-Float wird lazy gezogen). Vergleiche zwischen
// den Backends über Energie-Qualität/Verteilung, nicht über exakte Werte.

use numpy::PyReadonlyArray2;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use rayon::prelude::*;

/// SplitMix64 — schneller, deterministischer PRNG (pro Restart eigener Seed).
struct Rng(u64);

impl Rng {
    #[inline]
    fn new(seed: u64) -> Self {
        Rng(seed ^ 0x9E37_79B9_7F4A_7C15)
    }
    #[inline]
    fn next_u64(&mut self) -> u64 {
        self.0 = self.0.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = self.0;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^ (z >> 31)
    }
    #[inline]
    fn next_f64(&mut self) -> f64 {
        // 53 Zufallsbits -> [0,1)
        (self.next_u64() >> 11) as f64 / (1u64 << 53) as f64
    }
    #[inline]
    fn next_index(&mut self, n: usize) -> usize {
        // unverzerrte Auswahl in [0,n) per Rejection-Sampling (n >= 1 garantiert).
        let nn = n as u64;
        let zone = u64::MAX - (u64::MAX % nn);
        loop {
            let r = self.next_u64();
            if r < zone {
                return (r % nn) as usize;
            }
        }
    }
}

/// Ein einzelner SA-Restart auf flacher row-major Matrix `q` (n×n).
/// Liefert (best_x, best_e, trace[n_samples]).
fn anneal_one(
    q: &[f64],
    n: usize,
    steps: usize,
    t0: f64,
    seed: u64,
    n_samples: usize,
) -> (Vec<i64>, f64, Vec<f64>) {
    let mut rng = Rng::new(seed);

    let mut x = vec![0i64; n];
    for v in x.iter_mut() {
        *v = (rng.next_u64() & 1) as i64;
    }

    // Qx[i] = sum_j Q[i,j]*x[j]  und  e = x^T Q x  in einem Durchlauf
    let mut qx = vec![0.0f64; n];
    let mut e = 0.0f64;
    for i in 0..n {
        let row = &q[i * n..i * n + n];
        let mut acc = 0.0f64;
        for j in 0..n {
            acc += row[j] * x[j] as f64;
        }
        qx[i] = acc;
        e += acc * x[i] as f64;
    }

    let mut best_x = x.clone();
    let mut best_e = e;

    // Sample-Schritte wie np.linspace(0, steps-1, n_samples).astype(int64) → TRUNKIERT.
    let last = if steps > 0 { steps - 1 } else { 0 };
    let targets: Vec<usize> = (0..n_samples)
        .map(|k| {
            if n_samples > 1 {
                ((k as f64) * (last as f64) / ((n_samples - 1) as f64)) as usize
            } else {
                0
            }
        })
        .collect();
    let mut trace = vec![0.0f64; n_samples];
    let mut sidx = 0usize;

    for t in 0..steps {
        let temp = t0 * (1.0 - t as f64 / steps as f64) + 1e-3;
        let i = rng.next_index(n);
        let dx = 1 - 2 * x[i]; // {+1, -1}
        let de = 2.0 * dx as f64 * qx[i] + q[i * n + i] * (dx * dx) as f64;

        if de < 0.0 || rng.next_f64() < (-de / temp).exp() {
            x[i] ^= 1;
            e += de;
            let dxf = dx as f64;
            for j in 0..n {
                qx[j] += q[j * n + i] * dxf;
            }
            if e < best_e {
                best_e = e;
                best_x.copy_from_slice(&x);
            }
        }

        while sidx < n_samples && targets[sidx] == t {
            trace[sidx] = best_e;
            sidx += 1;
        }
    }
    while sidx < n_samples {
        trace[sidx] = best_e;
        sidx += 1;
    }

    (best_x, best_e, trace)
}

/// Multi-Start SA über alle Kerne (rayon). `q` wird als numpy-Array (n×n, float64)
/// über das Buffer-Protokoll übergeben — KEINE Python-Listen-Konvertierung (das wäre
/// für große n der Flaschenhals: jedes Element einzeln als PyObject zu entpacken ist
/// O(n²) mit hohem Konstantfaktor; ein Buffer-Memcpy ist um Größenordnungen schneller).
/// Rückgabe entspricht dem Python-Dict-Vertrag: (best_x, best_e, energies, best_restart, traces).
#[pyfunction]
#[pyo3(signature = (q, n, steps, t0, n_restarts, n_samples, base_seed=0))]
fn parallel_anneal(
    py: Python<'_>,
    q: PyReadonlyArray2<'_, f64>,
    n: usize,
    steps: usize,
    t0: f64,
    n_restarts: usize,
    n_samples: usize,
    base_seed: u64,
) -> PyResult<(Vec<i64>, f64, Vec<f64>, usize, Vec<Vec<f64>>)> {
    // --- Eingabevalidierung: saubere ValueError statt Panic über die rayon-Grenze ---
    if n == 0 {
        return Err(PyValueError::new_err("n must be >= 1"));
    }
    if n_restarts == 0 {
        return Err(PyValueError::new_err("n_restarts must be >= 1"));
    }
    n.checked_mul(n)
        .ok_or_else(|| PyValueError::new_err("n too large (n*n overflows usize)"))?;
    let q_view = q.as_array();
    if q_view.shape() != [n, n] {
        return Err(PyValueError::new_err(format!(
            "q has shape {:?}, expected ({n}, {n})",
            q_view.shape()
        )));
    }
    // Bulk-Kopie via ndarray (memcpy-artig, falls C-contiguous; sonst Fallback-Iteration).
    // Läuft noch unter dem GIL, bevor py.allow_threads() startet.
    let q: Vec<f64> = match q_view.as_slice() {
        Some(s) => s.to_vec(),
        None => q_view.iter().copied().collect(),
    };
    if q.iter().any(|v| !v.is_finite()) {
        return Err(PyValueError::new_err("q contains non-finite values (NaN/inf)"));
    }

    // GIL während der Rechenarbeit freigeben → echte Mehrkern-Last.
    let results: Vec<(Vec<i64>, f64, Vec<f64>)> = py.allow_threads(|| {
        (0..n_restarts)
            .into_par_iter()
            .map(|k| {
                let seed = base_seed.wrapping_add(k as u64);
                anneal_one(&q, n, steps, t0, seed, n_samples)
            })
            .collect()
    });

    let energies: Vec<f64> = results.iter().map(|r| r.1).collect();
    let best_restart = energies
        .iter()
        .enumerate()
        .min_by(|a, b| a.1.partial_cmp(b.1).unwrap_or(std::cmp::Ordering::Equal))
        .map(|(i, _)| i)
        .unwrap_or(0);
    let best_x = results[best_restart].0.clone();
    let best_e = results[best_restart].1;
    let traces: Vec<Vec<f64>> = results.into_iter().map(|r| r.2).collect();

    Ok((best_x, best_e, energies, best_restart, traces))
}

#[pymodule]
fn rust_engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parallel_anneal, m)?)?;
    m.add(
        "__doc__",
        "QUBO Simulated-Annealing-Kernel (Rust/rayon) für Fusion Hero OS",
    )?;
    Ok(())
}
