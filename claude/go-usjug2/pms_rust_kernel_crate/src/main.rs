// PMS-Minimal-Kernel (deterministisch, fail-closed).
//
// Umfang (ehrlich definiert):
//   - Validiert Operator-Aufrufe und Chains gegen ein PMS.yaml-Modell.
//   - Fuehrt eine feste Menge DETERMINISTISCHER Operatoren aus, die den vier
//     bewiesenen Knoten-Saetzen der heroic_math_engine entsprechen
//     (K16 Transpositions-Reziprozitaet, K17 Orthogonalprojektor,
//      K19 bedingte Monotonie, K20 Banach-Fixpunkt).
//   - Schreibt einen JSONL-Audit-Trail (Input-/Result-Hash, Status).
//   - FAIL-CLOSED: jeder Validierungs-/Parse-/Rechenfehler beendet den
//     Prozess mit Exit-Code != 0 und Fehlertext auf stderr; es gibt keinen
//     "besten Versuch".
//
// Determinismus: identischer Input (Operator + Payload + Modell) erzeugt
// identisches Result-JSON. Der Audit-Zeitstempel ist Metadatum und geht
// nicht ins Result ein.
//
// Dies ist ein EIGENER Minimal-Kernel dieses Repos; das externe Projekt
// tz-dev/PMS-RUST ist damit NICHT eingebunden.

use serde::Deserialize;
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::io::Read;
use std::io::Write;
use std::process::exit;

// ---------------------------- Modell (PMS.yaml) ----------------------------

#[derive(Debug, Deserialize)]
struct Model {
    version: u32,
    model: String,
    domains: Vec<String>,
    execution_domains: Vec<String>,
    operators: BTreeMap<String, OperatorSpec>,
    #[serde(default)]
    chains: BTreeMap<String, Vec<String>>,
}

#[derive(Debug, Deserialize)]
struct OperatorSpec {
    domains: Vec<String>,
    #[serde(default)]
    params: BTreeMap<String, String>, // name -> typ ("matrix" | "vector" | "string" | "number")
}

// ------------------------------- Lin-Alg ----------------------------------

type Mat = Vec<Vec<f64>>;

fn dims(m: &Mat) -> Result<(usize, usize), String> {
    let r = m.len();
    if r == 0 {
        return Err("leere Matrix".into());
    }
    let c = m[0].len();
    if c == 0 || m.iter().any(|row| row.len() != c) {
        return Err("Matrix nicht rechteckig".into());
    }
    if m.iter().flatten().any(|v| !v.is_finite()) {
        return Err("Matrix enthaelt NaN/inf".into());
    }
    Ok((r, c))
}

fn matmul(a: &Mat, b: &Mat) -> Result<Mat, String> {
    let (ar, ac) = dims(a)?;
    let (br, bc) = dims(b)?;
    if ac != br {
        return Err(format!("Shape-Konflikt {}x{} * {}x{}", ar, ac, br, bc));
    }
    let mut out = vec![vec![0.0; bc]; ar];
    for i in 0..ar {
        for k in 0..ac {
            let aik = a[i][k];
            for j in 0..bc {
                out[i][j] += aik * b[k][j];
            }
        }
    }
    Ok(out)
}

fn transpose(a: &Mat) -> Mat {
    let r = a.len();
    let c = a[0].len();
    let mut t = vec![vec![0.0; r]; c];
    for i in 0..r {
        for j in 0..c {
            t[j][i] = a[i][j];
        }
    }
    t
}

fn frob_norm(a: &Mat) -> f64 {
    a.iter().flatten().map(|v| v * v).sum::<f64>().sqrt()
}

fn mat_sub(a: &Mat, b: &Mat) -> Mat {
    a.iter()
        .zip(b)
        .map(|(ra, rb)| ra.iter().zip(rb).map(|(x, y)| x - y).collect())
        .collect()
}

/// Spektralnorm ||A||_2 via deterministischer Potenz-Iteration auf A^T A
/// (Startvektor = Einsen, 200 Iterationen — fuer die kleinen Kernel-Inputs
/// mehr als ausreichend konvergiert).
fn spectral_norm(a: &Mat) -> Result<f64, String> {
    let at = transpose(a);
    let ata = matmul(&at, a)?;
    let n = ata.len();
    let mut v = vec![1.0f64; n];
    let mut lambda = 0.0f64;
    for _ in 0..200 {
        let mut w = vec![0.0f64; n];
        for i in 0..n {
            for j in 0..n {
                w[i] += ata[i][j] * v[j];
            }
        }
        let norm = w.iter().map(|x| x * x).sum::<f64>().sqrt();
        if norm < 1e-300 {
            return Ok(0.0);
        }
        for x in w.iter_mut() {
            *x /= norm;
        }
        lambda = norm;
        v = w;
    }
    Ok(lambda.sqrt())
}

/// Loest (I - A) x = c per Gauss-Elimination mit Partial Pivoting.
fn solve_i_minus_a(a: &Mat, c: &[f64]) -> Result<Vec<f64>, String> {
    let n = a.len();
    if c.len() != n {
        return Err("Vektor-Laenge passt nicht zur Matrix".into());
    }
    let mut m = vec![vec![0.0f64; n + 1]; n];
    for i in 0..n {
        for j in 0..n {
            m[i][j] = (if i == j { 1.0 } else { 0.0 }) - a[i][j];
        }
        m[i][n] = c[i];
    }
    for col in 0..n {
        let piv = (col..n)
            .max_by(|&x, &y| m[x][col].abs().partial_cmp(&m[y][col].abs()).unwrap())
            .unwrap();
        if m[piv][col].abs() < 1e-12 {
            return Err("(I - A) numerisch singulaer".into());
        }
        m.swap(col, piv);
        for row in (col + 1)..n {
            let f = m[row][col] / m[col][col];
            for k in col..=n {
                m[row][k] -= f * m[col][k];
            }
        }
    }
    let mut x = vec![0.0f64; n];
    for i in (0..n).rev() {
        let mut acc = m[i][n];
        for j in (i + 1)..n {
            acc -= m[i][j] * x[j];
        }
        x[i] = acc / m[i][i];
    }
    Ok(x)
}

/// Gram-Schmidt-Orthonormalisierung der Spalten (Rang-defiziente Spalten
/// werden verworfen) -> U mit orthonormalen Spalten.
fn orthonormal_columns(a: &Mat) -> Result<Mat, String> {
    let (n, k) = dims(a)?;
    let mut cols: Vec<Vec<f64>> = Vec::new();
    for j in 0..k {
        let mut v: Vec<f64> = (0..n).map(|i| a[i][j]).collect();
        for u in &cols {
            let dot: f64 = v.iter().zip(u).map(|(x, y)| x * y).sum();
            for i in 0..n {
                v[i] -= dot * u[i];
            }
        }
        let norm = v.iter().map(|x| x * x).sum::<f64>().sqrt();
        if norm > 1e-10 {
            for x in v.iter_mut() {
                *x /= norm;
            }
            cols.push(v);
        }
    }
    if cols.is_empty() {
        return Err("keine linear unabhaengigen Spalten".into());
    }
    let mut u = vec![vec![0.0; cols.len()]; n];
    for (j, col) in cols.iter().enumerate() {
        for i in 0..n {
            u[i][j] = col[i];
        }
    }
    Ok(u)
}

// ------------------------------ Operatoren --------------------------------

fn get_matrix(payload: &serde_json::Value, key: &str) -> Result<Mat, String> {
    let v = payload
        .get(key)
        .ok_or_else(|| format!("Parameter '{}' fehlt", key))?;
    serde_json::from_value::<Mat>(v.clone())
        .map_err(|e| format!("Parameter '{}' ist keine Matrix: {}", key, e))
        .and_then(|m| dims(&m).map(|_| m))
}

fn get_vector(payload: &serde_json::Value, key: &str) -> Result<Vec<f64>, String> {
    let v = payload
        .get(key)
        .ok_or_else(|| format!("Parameter '{}' fehlt", key))?;
    let vec = serde_json::from_value::<Vec<f64>>(v.clone())
        .map_err(|e| format!("Parameter '{}' ist kein Vektor: {}", key, e))?;
    if vec.is_empty() || vec.iter().any(|x| !x.is_finite()) {
        return Err(format!("Parameter '{}' leer oder NaN/inf", key));
    }
    Ok(vec)
}

fn op_transpose_reciprocity(payload: &serde_json::Value) -> Result<serde_json::Value, String> {
    let (q1, b1, q2, b2) = (
        get_matrix(payload, "q1")?,
        get_matrix(payload, "b1")?,
        get_matrix(payload, "q2")?,
        get_matrix(payload, "b2")?,
    );
    let lhs = matmul(&matmul(&matmul(&q1, &b1)?, &b2)?, &q2)?;
    let rhs_t = matmul(
        &matmul(&matmul(&transpose(&q2), &transpose(&b2))?, &transpose(&b1))?,
        &transpose(&q1),
    )?;
    let rhs = transpose(&rhs_t);
    let scale = f64::max(1.0, f64::max(frob_norm(&lhs), frob_norm(&rhs)));
    let err = frob_norm(&mat_sub(&lhs, &rhs));
    Ok(serde_json::json!({
        "theorem": "K16 Transpositions-Reziprozitaet",
        "holds": err < 1e-9 * scale,
        "abs_err": err,
        "rel_err": err / scale,
    }))
}

fn op_projector_check(payload: &serde_json::Value) -> Result<serde_json::Value, String> {
    let basis = get_matrix(payload, "basis")?;
    let u = orthonormal_columns(&basis)?;
    let p = matmul(&u, &transpose(&u))?;
    let idem_err = frob_norm(&mat_sub(&matmul(&p, &p)?, &p));
    let symm_err = frob_norm(&mat_sub(&p, &transpose(&p)));
    // Nicht-Expansivitaet am deterministischen Testvektor (Einsen):
    let n = p.len();
    let ones = vec![vec![1.0f64]; n];
    let pv = matmul(&p, &ones)?;
    let nonexpansive = frob_norm(&pv) <= (n as f64).sqrt() + 1e-9;
    Ok(serde_json::json!({
        "theorem": "K17 Orthogonalprojektor",
        "idempotent": idem_err < 1e-8,
        "symmetric": symm_err < 1e-8,
        "nonexpansive_on_ones": nonexpansive,
        // Spektrum in {0,1} folgt ANALYTISCH aus idempotent+symmetrisch (Satz K17).
        "spectrum_in_01_by_theorem": idem_err < 1e-8 && symm_err < 1e-8,
        "rank": u[0].len(),
    }))
}

fn op_banach_fixpoint(payload: &serde_json::Value) -> Result<serde_json::Value, String> {
    let a = get_matrix(payload, "a")?;
    let c = get_vector(payload, "c")?;
    let (r, cdim) = dims(&a)?;
    if r != cdim {
        return Err("a muss quadratisch sein".into());
    }
    let q = spectral_norm(&a)?;
    if q >= 1.0 {
        // FAIL-CLOSED: keine Kontraktion -> kein Ergebnis, harter Fehler.
        return Err(format!("||A||_2 = {:.6} >= 1 — keine Kontraktion (Satz K20 nicht anwendbar)", q));
    }
    let x = solve_i_minus_a(&a, &c)?;
    // Residuum ||x - (Ax + c)|| als Verifikation
    let mut ax: Vec<f64> = vec![0.0; r];
    for i in 0..r {
        for j in 0..r {
            ax[i] += a[i][j] * x[j];
        }
    }
    let resid: f64 = x
        .iter()
        .zip(ax.iter().zip(c.iter()))
        .map(|(xi, (axi, ci))| (xi - (axi + ci)).powi(2))
        .sum::<f64>()
        .sqrt();
    Ok(serde_json::json!({
        "theorem": "K20 Banach-Fixpunkt",
        "contraction_q": q,
        "fixpoint": x,
        "residual": resid,
        "verified": resid < 1e-8,
    }))
}

fn op_monotone_fusion(payload: &serde_json::Value) -> Result<serde_json::Value, String> {
    let get = |k: &str| -> Result<f64, String> {
        payload
            .get(k)
            .and_then(|v| v.as_f64())
            .filter(|x| x.is_finite())
            .ok_or_else(|| format!("Parameter '{}' fehlt oder ist keine Zahl", k))
    };
    let (a, b, c, d, lambda) = (get("a")?, get("b")?, get("c")?, get("d")?, get("lambda")?);
    if lambda < 0.0 {
        return Err("lambda < 0 verletzt Voraussetzung von K19".into());
    }
    let in_domain = a * c >= 0.0 && (b - d).abs() <= f64::min(b.abs(), d.abs()) + 1e-12;
    if !in_domain {
        return Err("(a,b),(c,d) liegt ausserhalb des bewiesenen K19-Bereichs".into());
    }
    let s = |x: f64, y: f64| x * x - lambda * y * y;
    let fused = (a + c, b - d);
    let s_fused = s(fused.0, fused.1);
    let holds = s_fused >= f64::max(s(a, b), s(c, d)) - 1e-9;
    Ok(serde_json::json!({
        "theorem": "K19 bedingte Monotonie",
        "fused": [fused.0, fused.1],
        "stability_fused": s_fused,
        "monotone": holds,
    }))
}

fn op_q_b_circ(payload: &serde_json::Value) -> Result<serde_json::Value, String> {
    let action = payload
        .get("action")
        .and_then(|v| v.as_str())
        .ok_or("Parameter 'action' fehlt")?;
    match action {
        "verify_reciprocity" => {
            // Deterministische Referenzmatrizen (Rotation pi/4 + Standard-B).
            let s = std::f64::consts::FRAC_1_SQRT_2;
            let q: Mat = vec![vec![s, -s], vec![s, s]];
            let b: Mat = vec![vec![1.0, 0.0], vec![0.0, 0.0]];
            let payload = serde_json::json!({"q1": q, "b1": b, "q2": [[0.5,0.2],[0.1,0.9]], "b2": b});
            op_transpose_reciprocity(&payload)
        }
        other => Err(format!("unbekannte q-b-Aktion '{}'", other)),
    }
}

// --------------------------------- Audit -----------------------------------

fn sha256_hex(data: &[u8]) -> String {
    let mut h = Sha256::new();
    h.update(data);
    format!("{:x}", h.finalize())
}

fn append_audit(path: &str, operator: &str, input: &str, result: &str, status: &str) {
    let ts = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    let line = serde_json::json!({
        "ts_unix": ts,
        "operator": operator,
        "input_sha256": sha256_hex(input.as_bytes()),
        "result_sha256": sha256_hex(result.as_bytes()),
        "status": status,
    });
    if let Ok(mut f) = std::fs::OpenOptions::new().create(true).append(true).open(path) {
        let _ = writeln!(f, "{}", line);
    }
}

// --------------------------------- Main ------------------------------------

fn fail(msg: &str, audit: &str, operator: &str, input: &str) -> ! {
    append_audit(audit, operator, input, "", &format!("FAIL_CLOSED: {}", msg));
    eprintln!("FAIL_CLOSED: {}", msg);
    exit(1)
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let mut operator = String::new();
    let mut model_path = "PMS.yaml".to_string();
    let mut audit_path = "pms_audit.jsonl".to_string();
    let mut chain = String::new();
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--operator" if i + 1 < args.len() => {
                operator = args[i + 1].clone();
                i += 2;
            }
            "--model" if i + 1 < args.len() => {
                model_path = args[i + 1].clone();
                i += 2;
            }
            "--audit" if i + 1 < args.len() => {
                audit_path = args[i + 1].clone();
                i += 2;
            }
            "--validate-chain" if i + 1 < args.len() => {
                chain = args[i + 1].clone();
                i += 2;
            }
            other => {
                eprintln!("FAIL_CLOSED: unbekanntes Argument '{}'", other);
                exit(1)
            }
        }
    }

    // Modell laden + validieren (fail-closed bei jedem Fehler)
    let model_raw = match std::fs::read_to_string(&model_path) {
        Ok(s) => s,
        Err(e) => fail(&format!("PMS.yaml nicht lesbar ({}): {}", model_path, e), &audit_path, "-", ""),
    };
    let model: Model = match serde_yaml::from_str(&model_raw) {
        Ok(m) => m,
        Err(e) => fail(&format!("PMS.yaml ungueltig: {}", e), &audit_path, "-", ""),
    };
    if model.version != 1 {
        fail(&format!("PMS.yaml Version {} nicht unterstuetzt", model.version), &audit_path, "-", "");
    }
    for d in &model.execution_domains {
        if !model.domains.contains(d) {
            fail(&format!("execution_domain '{}' nicht in domains", d), &audit_path, "-", "");
        }
    }
    for (op, spec) in &model.operators {
        for d in &spec.domains {
            if !model.domains.contains(d) {
                fail(&format!("Operator {}: Domaene '{}' unbekannt", op, d), &audit_path, "-", "");
            }
        }
    }

    // Chain-Validierung (nur Modell-Ebene, keine Ausfuehrung)
    if !chain.is_empty() {
        let ops = match model.chains.get(&chain) {
            Some(o) => o,
            None => fail(&format!("Chain '{}' nicht im Modell", chain), &audit_path, &chain, ""),
        };
        for op in ops {
            if !model.operators.contains_key(op) {
                fail(&format!("Chain '{}': Operator '{}' nicht im Katalog", chain, op), &audit_path, &chain, "");
            }
        }
        let out = serde_json::json!({
            "status": "VALID",
            "model": model.model,
            "chain": chain,
            "operators": ops,
        })
        .to_string();
        append_audit(&audit_path, &format!("chain:{}", chain), "", &out, "VALID");
        println!("{}", out);
        return;
    }

    if operator.is_empty() {
        fail("kein --operator angegeben", &audit_path, "-", "");
    }
    let spec = match model.operators.get(&operator) {
        Some(s) => s,
        None => fail(&format!("Operator '{}' nicht im PMS.yaml-Katalog", operator), &audit_path, &operator, ""),
    };
    // Operator muss in mindestens einer Execution-Domain zugelassen sein
    if !spec.domains.iter().any(|d| model.execution_domains.contains(d)) {
        fail(&format!("Operator '{}' ist in keiner Execution-Domain zugelassen", operator), &audit_path, &operator, "");
    }

    let mut input = String::new();
    if std::io::stdin().read_to_string(&mut input).is_err() {
        fail("stdin nicht lesbar", &audit_path, &operator, "");
    }
    let payload: serde_json::Value = match serde_json::from_str(&input) {
        Ok(v) => v,
        Err(e) => fail(&format!("Payload kein gueltiges JSON: {}", e), &audit_path, &operator, &input),
    };
    // Parameter-Schema pruefen (Anwesenheit)
    for (pname, _ptype) in &spec.params {
        if payload.get(pname).is_none() {
            fail(&format!("Pflichtparameter '{}' fehlt (Schema PMS.yaml)", pname), &audit_path, &operator, &input);
        }
    }

    let result = match operator.as_str() {
        "OP_TRANSPOSE_RECIPROCITY" => op_transpose_reciprocity(&payload),
        "OP_PROJECTOR_CHECK" => op_projector_check(&payload),
        "OP_BANACH_FIXPOINT" => op_banach_fixpoint(&payload),
        "OP_MONOTONE_FUSION" => op_monotone_fusion(&payload),
        "OP_Q_B_CIRC" => op_q_b_circ(&payload),
        other => Err(format!("Operator '{}' im Modell, aber ohne Kernel-Implementierung", other)),
    };

    match result {
        Ok(val) => {
            let out = serde_json::json!({
                "status": "SUCCESS",
                "model": model.model,
                "operator": operator,
                "result": val,
            })
            .to_string();
            append_audit(&audit_path, &operator, &input, &out, "SUCCESS");
            println!("{}", out);
        }
        Err(e) => fail(&e, &audit_path, &operator, &input),
    }
}
