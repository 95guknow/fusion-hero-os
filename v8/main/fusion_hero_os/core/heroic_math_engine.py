"""
Heroic Math Engine - v8 (bewiesene Fassung)

Mathematische Kernkomponenten des Fusion-Hero-OS.
Orientiert an der Strenge von Kompendium V3.3 & V4.0.

Repariert zentrale mathematische Schwaechen (Knoten 16, 17, 19, 20) — jetzt
mit BEWEIS statt Behauptung. "Repariert" heisst hier: die urspruenglich
behauptete, aber falsche bzw. fehlende Aussage wurde durch einen KORREKTEN,
allgemein gueltigen Satz ersetzt, der (a) analytisch bewiesen (Beweis im
jeweiligen Docstring), (b) implementiert und (c) numerisch mit 0 Verletzungen
ueber grosse Zufalls-Sweeps verifiziert ist (siehe run_sandbox_verification()
und tests/test_heroic_math_engine.py).

  - Knoten 16 (Reziprozitaet): Die naive Gleichung Q1B1B2Q2 = Q2B2B1Q1 ist
    FALSCH (Gegenbeispiele existieren fuer fast alle Q1 != Q2). Der korrekte
    universelle Satz ist die Transpositions-Reziprozitaet:
        Q1B1B2Q2 = (Q2^T B2^T B1^T Q1^T)^T   fuer ALLE reellen Matrizen.
  - Knoten 17 (Projektion): Orthogonalprojektoren P = U U^T sind idempotent,
    symmetrisch, haben Spektrum in {0,1} und sind nicht-expansiv.
  - Knoten 19 (Monotonie der Fusion): S(fused) >= max(S(psi), S(phi)) gilt
    BEDINGT — bewiesen unter Realteil-Kompatibilitaet + Imaginaer-Kontraktion
    und eta = 0. Der frueher voreingestellte eta-Asymmetrieterm ZERSTOERT die
    Monotonie (numerisch ~9-15 % Verletzungen) und ist daher per Default 0.
  - Knoten 20 (Fixpunkt): Banach-Kontraktion T(x) = Ax + c mit ||A||_2 < 1
    hat einen eindeutigen Fixpunkt; die Iteration konvergiert geometrisch.
    Das ist die mathematische Grundlage des MasterSeed-Layer-0-Modells.

Teil der 02_architecture Schicht.
"""

import numpy as np


class HeroicMatrixEngine:
    def __init__(self):
        self.b_default = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=np.float64)
        phi = np.pi / 4
        self.q_default = np.array([[np.cos(phi), -np.sin(phi)], [np.sin(phi), np.cos(phi)]], dtype=np.float64)

    def compute_commutator(self, q: np.ndarray, b: np.ndarray) -> np.ndarray:
        return np.dot(q, b) - np.dot(b, q)

    @staticmethod
    def check_reciprocity_condition(q1, b1, q2, b2, tolerance=1e-9):
        """HISTORISCH (naive Form): Q1B1B2Q2 == Q2B2B1Q1.

        Diese Gleichung ist KEIN Satz — sie gilt i. A. nur im Trivialfall
        Q1=Q2, B1=B2 und wird durch Zufallsmatrizen praktisch immer verletzt.
        Bleibt als Negativ-Referenz erhalten; der bewiesene universelle Satz
        ist check_transpose_reciprocity().
        """
        lhs = np.dot(np.dot(np.dot(q1, b1), b2), q2)
        rhs = np.dot(np.dot(np.dot(q2, b2), b1), q1)
        scale = max(1.0, np.linalg.norm(lhs), np.linalg.norm(rhs))
        return bool(np.linalg.norm(lhs - rhs) < tolerance * scale)

    @staticmethod
    def check_transpose_reciprocity(q1, b1, q2, b2, tolerance=1e-9):
        """Knoten 16 — SATZ (Transpositions-Reziprozitaet, universell):

            Q1 B1 B2 Q2 = (Q2^T B2^T B1^T Q1^T)^T   fuer alle reellen n x n
            Matrizen Q1, B1, B2, Q2.

        BEWEIS: Fuer beliebige Matrizen gilt (XY)^T = Y^T X^T. Dreifach
        angewandt: (Q1B1B2Q2)^T = Q2^T B2^T B1^T Q1^T. Transponieren beider
        Seiten liefert die Behauptung. QED.

        Die Reihenfolge-Umkehr (Q2..Q1 statt Q1..Q2) ist also genau dann
        gueltig, wenn sie mit Transposition kombiniert wird — das ist der
        korrekte Kern der "Reziprozitaets"-Idee aus Knoten 16.
        """
        lhs = q1 @ b1 @ b2 @ q2
        rhs = (q2.T @ b2.T @ b1.T @ q1.T).T
        # RELATIVE Toleranz: die Rundungsdifferenz der beiden Assoziations-
        # reihenfolgen skaliert mit dem Normprodukt (~||.||^4); eine absolute
        # Schranke wuerde den exakt gueltigen Satz bei grossen Normen
        # faelschlich verwerfen (adversarial verifiziert mit Eintraegen ~1e8).
        scale = max(1.0, np.linalg.norm(lhs), np.linalg.norm(rhs))
        return bool(np.linalg.norm(lhs - rhs) < tolerance * scale)


class OrthogonalProjector:
    """Knoten 17 — SATZ (Orthogonalprojektor):

    Sei U eine n x k Matrix mit orthonormalen Spalten (U^T U = I_k) und
    P = U U^T. Dann gilt:
      (a) P^2 = P                    (idempotent)
      (b) P^T = P                    (symmetrisch)
      (c) Spektrum(P) ist Teilmenge von {0, 1}
      (d) ||P v||_2 <= ||v||_2       fuer alle v (nicht-expansiv)

    BEWEIS:
      (a) P^2 = U(U^T U)U^T = U I U^T = P.
      (b) (U U^T)^T = U U^T.
      (c) Aus (a): ist lambda Eigenwert mit Pv = lambda v, v != 0, dann
          lambda^2 v = P^2 v = P v = lambda v, also lambda^2 = lambda,
          d. h. lambda in {0, 1}.
      (d) P ist die Orthogonalprojektion auf span(U): v zerfaellt orthogonal
          in v = Pv + (I-P)v mit <Pv, (I-P)v> = 0 (da P^T P = P), also
          ||v||^2 = ||Pv||^2 + ||(I-P)v||^2 >= ||Pv||^2. QED.
    """

    def __init__(self, basis_candidates: np.ndarray):
        """Konstruiert P aus beliebigen Spaltenvektoren via QR-Orthonormalisierung."""
        A = np.atleast_2d(np.asarray(basis_candidates, dtype=np.float64))
        U, _ = np.linalg.qr(A)
        self.U = U
        self.P = U @ U.T

    def project(self, v: np.ndarray) -> np.ndarray:
        return self.P @ np.asarray(v, dtype=np.float64)

    def is_idempotent(self, tolerance=1e-8) -> bool:
        return bool(np.linalg.norm(self.P @ self.P - self.P) < tolerance)

    def is_symmetric(self, tolerance=1e-8) -> bool:
        return bool(np.linalg.norm(self.P - self.P.T) < tolerance)

    def spectrum_in_01(self, tolerance=1e-7) -> bool:
        ev = np.linalg.eigvalsh(self.P)
        return bool(np.all((np.abs(ev) < tolerance) | (np.abs(ev - 1.0) < tolerance)))

    def is_nonexpansive_for(self, v: np.ndarray, tolerance=1e-9) -> bool:
        v = np.asarray(v, dtype=np.float64)
        return bool(np.linalg.norm(self.P @ v) <= np.linalg.norm(v) + tolerance)


class StableCoreLattice:
    def __init__(self, elements, order_relations):
        self.elements = elements
        self.relations = set(order_relations)
        for e in elements:
            self.relations.add((e, e))
        self._apply_transitive_closure()

    def _apply_transitive_closure(self):
        while True:
            new_relations = set(self.relations)
            for a, b, c in [(a, b, c) for a in self.elements for b in self.elements for c in self.elements]:
                if (a, b) in self.relations and (b, c) in self.relations:
                    new_relations.add((a, c))
            if new_relations == self.relations:
                break
            self.relations = new_relations

    def is_less_or_equal(self, a, b):
        return (a, b) in self.relations

    def get_join(self, a, b):
        upper_bounds = [e for e in self.elements if self.is_less_or_equal(a, e) and self.is_less_or_equal(b, e)]
        for ub in upper_bounds:
            if all(self.is_less_or_equal(ub, other) for other in upper_bounds):
                return ub
        raise ValueError(f"Kein eindeutiger Join für {a} und {b}")


class RepairedStructureIP:
    """Knoten 19 — SATZ (bedingte Monotonie der Fusion):

    Sei S(x + iy) = x^2 - lmbda * y^2 mit lmbda >= 0 (eta = 0, s. u.) und die
    Fusion (a + ib) (+) (c + id) = (a + c) + i(b - d). Falls
      (i)  a * c >= 0                     (Realteil-Kompatibilitaet) und
      (ii) |b - d| <= min(|b|, |d|)       (Imaginaer-Kontraktion),
    dann gilt S(fused) >= max(S(psi), S(phi)).

    BEWEIS: S(fused) - S(psi) = (a+c)^2 - a^2 - lmbda[(b-d)^2 - b^2]
      = (c^2 + 2ac) + lmbda[b^2 - (b-d)^2].
    Wegen (i) ist c^2 + 2ac >= 0; wegen (ii) ist (b-d)^2 <= min(b,d)^2 <= b^2,
    also der zweite Summand >= 0 (lmbda >= 0). Beide Summanden nicht-negativ
    => S(fused) >= S(psi). Der Fall S(phi) folgt symmetrisch (a <-> c,
    b^2 >= (b-d)^2 analog via (ii) mit d). QED.

    WICHTIG (Ehrlichkeit): Mit eta != 0 (Asymmetrieterm eta*y in S) ist die
    Monotonie FALSCH — Zufalls-Sweeps zeigen ~9-15 % Verletzungen. Deshalb ist
    eta jetzt per Default 0; wer eta setzt, verlaesst den bewiesenen Bereich
    (der Konstruktor erlaubt es fuer Experimente, run_sandbox_verification
    weist die Verletzungsrate dann explizit aus).
    """

    def __init__(self, lmbda=0.5, eta=0.0):
        if lmbda < 0:
            raise ValueError("lmbda >= 0 erforderlich (Voraussetzung des Monotonie-Satzes).")
        self.lmbda = lmbda
        self.eta = eta

    def compute_stability(self, psi):
        re_part = psi.real
        im_part = psi.imag
        base_stability = (re_part ** 2) - self.lmbda * (im_part ** 2)
        asymmetry_term = self.eta * im_part
        return base_stability + asymmetry_term

    def check_compatibility(self, psi, phi):
        """Bedingung (i): Realteil-Kompatibilitaet a*c >= 0."""
        return bool((psi.real >= 0 and phi.real >= 0) or (psi.real <= 0 and phi.real <= 0))

    def check_monotone_domain(self, psi, phi):
        """Voller bewiesener Geltungsbereich: (i) UND (ii) UND eta == 0."""
        cond_i = self.check_compatibility(psi, phi)
        cond_ii = abs(psi.imag - phi.imag) <= min(abs(psi.imag), abs(phi.imag)) + 1e-12
        return bool(cond_i and cond_ii and self.eta == 0.0)

    def fusion_operator(self, psi, phi):
        if not self.check_compatibility(psi, phi):
            raise ValueError("Knoten 19 Verletzung: Strukturen außerhalb des Kompatibilitäts-Gegenraums.")
        re_new = psi.real + phi.real
        im_new = psi.imag - phi.imag
        return complex(re_new, im_new)


class BanachContractionSeed:
    """Knoten 20 — SATZ (Banachscher Fixpunktsatz, affiner Spezialfall):

    Sei T(x) = A x + c mit q := ||A||_2 < 1. Dann ist T eine q-Kontraktion
    auf (R^n, ||.||_2), besitzt genau einen Fixpunkt x* = (I - A)^{-1} c, und
    fuer jede Startnaehe x_0 gilt geometrische Konvergenz:
        ||x_k - x*||_2 <= q^k * ||x_0 - x*||_2.

    BEWEIS: ||T(x) - T(y)|| = ||A(x - y)|| <= q ||x - y||  (Kontraktion).
    (I - A) ist invertierbar, da fuer ||A|| < 1 die Neumann-Reihe
    sum A^k = (I - A)^{-1} konvergiert; x* := (I - A)^{-1} c erfuellt
    T(x*) = A x* + c = x*. Eindeutigkeit: aus T(x)=x und T(y)=y folgt
    ||x - y|| = ||A(x-y)|| <= q||x - y||, mit q < 1 also x = y. Die
    Fehlerabschaetzung folgt induktiv aus der Kontraktionseigenschaft. QED.

    Dies praezisiert das MasterSeed-Layer-0-Modell "M0 = R(M0) mit Strict
    Contraction": R uebernimmt die Rolle von T, M0 die des Fixpunkts x*.
    """

    def __init__(self, A: np.ndarray, c: np.ndarray):
        self.A = np.asarray(A, dtype=np.float64)
        self.c = np.asarray(c, dtype=np.float64)
        self.q = float(np.linalg.norm(self.A, 2))
        if self.q >= 1.0:
            raise ValueError(f"Keine Kontraktion: ||A||_2 = {self.q:.4f} >= 1.")

    def apply(self, x: np.ndarray) -> np.ndarray:
        return self.A @ np.asarray(x, dtype=np.float64) + self.c

    def fixpoint(self) -> np.ndarray:
        """Geschlossene Form x* = (I - A)^{-1} c."""
        n = self.A.shape[0]
        return np.linalg.solve(np.eye(n) - self.A, self.c)

    def iterate(self, x0: np.ndarray, tol=1e-10, max_steps=100_000):
        """Fixpunkt-Iteration; Schrittzahl folgt aus der Theorie
        (kleinstes k mit q^k * ||x0 - x*|| <= tol)."""
        x = np.asarray(x0, dtype=np.float64)
        x_star = self.fixpoint()
        d0 = float(np.linalg.norm(x - x_star))
        if d0 <= tol:
            return x, 0
        k_needed = int(np.ceil(np.log(tol / d0) / np.log(self.q))) + 1 if self.q > 0 else 1
        steps = min(max(k_needed, 1), max_steps)
        for _ in range(steps):
            x = self.apply(x)
        return x, steps

    def verify_contraction_bound(self, x0: np.ndarray, n_steps=50, tolerance=1e-9) -> bool:
        """Prueft ||x_k - x*|| <= q^k ||x_0 - x*|| fuer k = 1..n_steps."""
        x_star = self.fixpoint()
        x = np.asarray(x0, dtype=np.float64)
        d0 = float(np.linalg.norm(x - x_star))
        for k in range(1, n_steps + 1):
            x = self.apply(x)
            if np.linalg.norm(x - x_star) > (self.q ** k) * d0 + tolerance:
                return False
        return True


global_heroic_math = HeroicMatrixEngine()


def run_sandbox_verification():
    """Verifikations-Sandbox: prueft die BEWIESENEN Saetze mit echten Asserts.

    Jeder Knoten laeuft einen Zufalls-Sweep; die Saetze muessen mit 0
    Verletzungen bestehen (CI-Gate: python -m fusion_hero_os.core.heroic_math_engine).
    Kontrolllaeufe zeigen zusaetzlich, dass die Saetze nicht-trivial sind
    (die naive K16-Form und der eta-Term verletzen reihenweise).
    """
    print("=" * 65)
    print("RUNNING FUSION-HERO-OS CORE VERIFICATION SANDBOX (bewiesene Saetze)")
    print("=" * 65)
    rng = np.random.default_rng(20260703)
    engine = HeroicMatrixEngine()

    print(f"[Knoten 1] Standardkommutator [q, b] (Demonstration):\n"
          f"{engine.compute_commutator(engine.q_default, engine.b_default)}")

    # ---- Knoten 16: Transpositions-Reziprozitaet (Satz) ----
    trials = 2000
    viol = 0
    naive_holds = 0
    for _ in range(trials):
        n = int(rng.integers(2, 6))
        q1, b1, b2, q2 = (rng.normal(0, 2, (n, n)) for _ in range(4))
        if not engine.check_transpose_reciprocity(q1, b1, q2, b2):
            viol += 1
        if engine.check_reciprocity_condition(q1, b1, q2, b2):
            naive_holds += 1
    assert viol == 0, f"K16 Transpositions-Reziprozitaet verletzt: {viol}/{trials}"
    print(f"[Knoten 16] Transpositions-Reziprozitaet: {trials - viol}/{trials} bestanden "
          f"(SATZ; naive Form haelt nur {naive_holds}/{trials} -> war nie ein Satz)")

    # ---- Knoten 17: Orthogonalprojektor (Satz) ----
    viol = 0
    for _ in range(trials):
        n = int(rng.integers(2, 7))
        k = int(rng.integers(1, n + 1))
        proj = OrthogonalProjector(rng.normal(0, 1, (n, k)))
        v = rng.normal(0, 1, n)
        if not (proj.is_idempotent() and proj.is_symmetric()
                and proj.spectrum_in_01() and proj.is_nonexpansive_for(v)):
            viol += 1
    assert viol == 0, f"K17 Projektor-Eigenschaften verletzt: {viol}/{trials}"
    print(f"[Knoten 17] Orthogonalprojektor (idempotent/symmetrisch/Spektrum{{0,1}}/"
          f"nicht-expansiv): {trials - viol}/{trials} bestanden (SATZ)")

    # ---- Knoten 19: bedingte Monotonie (Satz) + eta-Kontrolle ----
    ip_system = RepairedStructureIP(lmbda=0.5)  # eta = 0: bewiesener Bereich
    psi, phi = complex(2.0, -1.0), complex(1.5, -0.5)
    assert ip_system.check_monotone_domain(psi, phi)
    s_psi, s_phi = ip_system.compute_stability(psi), ip_system.compute_stability(phi)
    s_fused = ip_system.compute_stability(ip_system.fusion_operator(psi, phi))
    print(f"[Knoten 19] Beispiel: S(psi)={s_psi:.4f}, S(phi)={s_phi:.4f}, S(fused)={s_fused:.4f}")
    assert s_fused >= max(s_psi, s_phi)

    viol = tested = 0
    for _ in range(trials * 5):
        lm = float(rng.uniform(0, 3))
        sysm = RepairedStructureIP(lmbda=lm)
        a = float(rng.uniform(-3, 3))
        c = np.sign(a) * abs(float(rng.uniform(0, 3)))
        b = float(rng.uniform(-3, 3))
        if abs(b) < 1e-6:
            continue
        d = b * float(rng.uniform(0.5, 2.0))
        p, q = complex(a, b), complex(c, d)
        if not sysm.check_monotone_domain(p, q):
            continue
        tested += 1
        sf = sysm.compute_stability(sysm.fusion_operator(p, q))
        if sf < max(sysm.compute_stability(p), sysm.compute_stability(q)) - 1e-9:
            viol += 1
    assert viol == 0, f"K19 Monotonie im bewiesenen Bereich verletzt: {viol}/{tested}"
    print(f"  -> Sweep: {tested} Paare im bewiesenen Bereich, {viol} Verletzungen (SATZ, bedingt)")

    eta_sys = RepairedStructureIP(lmbda=0.5, eta=1.5)
    ev = et = 0
    for _ in range(2000):
        a, c = float(rng.uniform(0.1, 3)), float(rng.uniform(0.1, 3))
        b = float(rng.uniform(-3, 3))
        d = b * float(rng.uniform(0.5, 2.0))
        if abs(b - d) > min(abs(b), abs(d)) + 1e-12:
            continue
        et += 1
        p, q = complex(a, b), complex(c, d)
        sf = eta_sys.compute_stability(eta_sys.fusion_operator(p, q))
        if sf < max(eta_sys.compute_stability(p), eta_sys.compute_stability(q)) - 1e-9:
            ev += 1
    print(f"  -> Kontrolle eta=1.5: {ev}/{et} Verletzungen -> eta-Term liegt AUSSERHALB des Satzes")

    # ---- Knoten 20: Banach-Fixpunkt (Satz) ----
    viol = 0
    for _ in range(trials // 2):
        n = int(rng.integers(2, 6))
        M = rng.normal(0, 1, (n, n))
        q = float(rng.uniform(0.1, 0.9))
        seed = BanachContractionSeed(M * (q / np.linalg.norm(M, 2)), rng.normal(0, 1, n))
        x0 = rng.normal(0, 5, n)
        x_end, _ = seed.iterate(x0, tol=1e-8)
        ok = seed.verify_contraction_bound(x0, n_steps=40)
        if not ok or np.linalg.norm(x_end - seed.fixpoint()) > 1e-6:
            viol += 1
    assert viol == 0, f"K20 Banach-Kontraktion verletzt: {viol}/{trials // 2}"
    print(f"[Knoten 20] Banach-Kontraktion (eindeutiger Fixpunkt, geometrische "
          f"Konvergenz): {trials // 2 - viol}/{trials // 2} bestanden (SATZ)")

    print("=" * 65)
    print("ALLE VIER KNOTEN-SAETZE MIT 0 VERLETZUNGEN VERIFIZIERT.")
    print("=" * 65)


if __name__ == "__main__":
    run_sandbox_verification()
