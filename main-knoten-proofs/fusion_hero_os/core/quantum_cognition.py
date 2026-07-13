"""
Quantum Cognition Engine - v8 (Busemeyer-QPT-Primitives, bewiesene Fassung)

Setzt die GitHub-Updates vom 2026-07-05 um:
  docs/v8/GROK_DEEP_RESEARCH_EXPORT_Empirical_Mathematical_Anchors_v8.md  (Abschnitt 2)
  docs/v8/architecture/FULL_OS_Themenfelder_Integration_April_Mai_Juni_v8.md  (Roadmap Punkt 3)

Quantum Probability Theory (QPT) nach Busemeyer & Bruza ("Quantum Models of
Cognition and Decision") als mathematisches Fundament fuer das
Quantenkognition-Modul: Glaubenszustaende als Einheitsvektoren im Hilbertraum,
Urteile als projektive Messungen, Ordnungseffekte via Nicht-Kommutativitaet,
Interferenz als Verletzung der klassischen totalen Wahrscheinlichkeit.

EHRLICHKEITS-RAHMEN (High-Intellect Protocol):
  * Die Saetze in diesem Modul sind reine Mathematik — analytisch bewiesen
    (Beweis im Docstring) und numerisch mit 0 Verletzungen ueber
    Zufalls-Sweeps verifiziert (tests/test_quantum_cognition.py, Registry-IDs
    QPT-*).
  * Es wird KEIN physischer Quantenprozess im Gehirn behauptet (das behauptet
    auch Busemeyer nicht) — QPT ist ein Wahrscheinlichkeitsformalismus.
  * Ob dieser Formalismus Sisyphos-Oszillationen / Psycholyse-Uebergaenge
    EMPIRISCH besser beschreibt als klassische Modelle, ist eine OFFENE
    Hypothese (Registry: QPT-SISYPHOS-FIT, status OFFEN) — hier steht nur die
    Modell-Maschinerie, nicht ihr empirischer Nachweis.

Teil der 02_architecture Schicht; Schwester-Modul zu heroic_math_engine.py.
"""

from __future__ import annotations

import numpy as np


def _as_state(psi: np.ndarray) -> np.ndarray:
    """Normiert einen Vektor zum Zustand ||psi|| = 1 (komplex erlaubt)."""
    psi = np.asarray(psi, dtype=np.complex128).ravel()
    n = np.linalg.norm(psi)
    if n == 0:
        raise ValueError("Nullvektor ist kein Zustand.")
    return psi / n


def _check_projector(P: np.ndarray, tol: float = 1e-9) -> np.ndarray:
    """Validiert P als Orthogonalprojektor (hermitesch + idempotent)."""
    P = np.asarray(P, dtype=np.complex128)
    if np.linalg.norm(P - P.conj().T) > tol:
        raise ValueError("Projektor nicht hermitesch.")
    if np.linalg.norm(P @ P - P) > tol:
        raise ValueError("Projektor nicht idempotent.")
    return P


def projector_from_vectors(vectors: np.ndarray) -> np.ndarray:
    """Orthogonalprojektor auf span(vectors) via QR (analog OrthogonalProjector,
    aber komplexfaehig)."""
    A = np.atleast_2d(np.asarray(vectors, dtype=np.complex128))
    if A.shape[0] < A.shape[1]:
        A = A.T
    U, _ = np.linalg.qr(A)
    return U @ U.conj().T


class BeliefState:
    """QPT-SATZ (Bornsche Regel + Vollstaendigkeit):

    Sei psi ein Einheitsvektor und {P_1,...,P_m} eine vollstaendige Familie
    paarweise orthogonaler Projektoren (sum P_i = I, P_i P_j = 0 fuer i != j).
    Dann sind p_i := ||P_i psi||^2 eine Wahrscheinlichkeitsverteilung:
    p_i >= 0 und sum p_i = 1.

    BEWEIS: p_i = ||P_i psi||^2 >= 0 trivial. psi = I psi = sum P_i psi ist
    eine ORTHOGONALE Zerlegung: fuer i != j gilt
    <P_i psi, P_j psi> = psi^dagger P_i P_j psi = 0. Pythagoras liefert
    1 = ||psi||^2 = sum ||P_i psi||^2 = sum p_i. QED.
    """

    def __init__(self, amplitudes: np.ndarray):
        self.psi = _as_state(amplitudes)

    def prob(self, P: np.ndarray) -> float:
        """Bornsche Regel: p = ||P psi||^2."""
        P = _check_projector(P)
        return float(np.linalg.norm(P @ self.psi) ** 2)

    def collapse(self, P: np.ndarray) -> "BeliefState":
        """Lueders-Kollaps: psi -> P psi / ||P psi|| (Kontext-Update nach Urteil)."""
        P = _check_projector(P)
        v = P @ self.psi
        if np.linalg.norm(v) < 1e-15:
            raise ValueError("Kollaps auf Ereignis mit Wahrscheinlichkeit 0.")
        return BeliefState(v)

    def prob_sequence(self, *projectors: np.ndarray) -> float:
        """Sequenzielle Urteile: p(A dann B dann ...) = ||... P_B P_A psi||^2."""
        v = self.psi
        for P in projectors:
            v = _check_projector(P) @ v
        return float(np.linalg.norm(v) ** 2)


def order_effect(psi: np.ndarray, P_A: np.ndarray, P_B: np.ndarray) -> float:
    """Ordnungseffekt-Mass: p(A dann B) - p(B dann A).

    QPT-SATZ (Ordnungs-Invarianz bei Kommutativitaet): Kommutieren die
    Projektoren, [P_A, P_B] = 0, dann ist der Ordnungseffekt exakt 0 fuer
    JEDEN Zustand.

    BEWEIS: p(A dann B) = ||P_B P_A psi||^2. Mit P_B P_A = P_A P_B folgt
    ||P_B P_A psi||^2 = ||P_A P_B psi||^2 = p(B dann A). QED.

    Die Umkehrung gilt punktweise NICHT (einzelne Zustaende koennen auch bei
    Nicht-Kommutativitaet ordnungs-invariant sein) — Nicht-Kommutativitaet
    macht Ordnungseffekte moeglich, nicht zwingend.
    """
    s = BeliefState(psi)
    return s.prob_sequence(P_A, P_B) - s.prob_sequence(P_B, P_A)


def qq_equality_residual(psi: np.ndarray, P_A: np.ndarray, P_B: np.ndarray) -> float:
    """QPT-SATZ (QQ-Equality, Wang & Busemeyer 2013 / Wang et al. PNAS 2014):

    Fuer JEDEN Zustand psi und JEDES Paar Orthogonalprojektoren A, B gilt
    (mit Q_A = I - A, Q_B = I - B):

        [p(Ay dann By) + p(An dann Bn)] - [p(By dann Ay) + p(Bn dann An)] = 0.

    Einzelne Ordnungseffekte duerfen beliebig gross sein — ihre "Ja-Ja plus
    Nein-Nein"-Summe ist ordnungsinvariant. Das ist DIE parameterfreie,
    empirisch getestete Signatur von QPT (PNAS 2014: 72 Surveys).

    BEWEIS: p(Ay dann By) = ||B A psi||^2 = psi^dagger A B A psi (A, B
    hermitesch-idempotent). Analog die anderen drei Terme. Algebra mit
    A^2 = A, B^2 = B:
        Q_A Q_B Q_A = (I-A)(I-B)(I-A) = I - A - B + AB + BA - ABA
        Q_B Q_A Q_B = (I-B)(I-A)(I-B) = I - A - B + AB + BA - BAB
    Also  ABA + Q_A Q_B Q_A = I - A - B + AB + BA = BAB + Q_B Q_A Q_B.
    Sandwiching mit psi^dagger ... psi liefert Residuum 0. QED.

    Rueckgabe: das Residuum (analytisch 0; numerisch ~Maschinengenauigkeit).
    """
    P_A = _check_projector(P_A)
    P_B = _check_projector(P_B)
    I = np.eye(P_A.shape[0], dtype=np.complex128)
    s = BeliefState(psi)
    lhs = s.prob_sequence(P_A, P_B) + s.prob_sequence(I - P_A, I - P_B)
    rhs = s.prob_sequence(P_B, P_A) + s.prob_sequence(I - P_B, I - P_A)
    return float(lhs - rhs)


def interference_term(psi: np.ndarray, P_final: np.ndarray,
                      partition: list[np.ndarray]) -> float:
    """QPT-SATZ (exakte Interferenz-Zerlegung / Verletzung der totalen
    Wahrscheinlichkeit):

    Sei {P_1,...,P_m} eine vollstaendige orthogonale Projektor-Familie
    (Zwischen-"Messung"/Kontexte) und F ein Projektor (Ziel-Urteil). Mit
    x_i := F P_i psi gilt EXAKT:

        p_direkt := ||F psi||^2
                  = sum_i ||x_i||^2  +  2 sum_{i<j} Re<x_i, x_j>
                  = p_klassisch      +  delta.

    delta ist der Interferenzterm; die klassische totale Wahrscheinlichkeit
    (p_direkt = p_klassisch) gilt genau dann, wenn delta = 0.

    BEWEIS: psi = sum P_i psi (Vollstaendigkeit), also F psi = sum x_i und
    ||sum x_i||^2 = sum ||x_i||^2 + 2 sum_{i<j} Re<x_i,x_j> (Parallelogramm-
    Expansion des Skalarprodukts). QED.

    ZUSATZ-SATZ (klassischer Grenzfall): Kommutiert F mit allen P_i, dann
    delta = 0. BEWEIS: <x_i,x_j> = psi^dagger P_i F F P_j psi
    = psi^dagger P_i F P_j psi = psi^dagger F P_i P_j psi = 0 fuer i != j
    (Orthogonalitaet P_i P_j = 0). QED.

    Rueckgabe: delta = p_direkt - p_klassisch.
    """
    psi = _as_state(psi)
    F = _check_projector(P_final)
    p_direct = float(np.linalg.norm(F @ psi) ** 2)
    p_classical = sum(float(np.linalg.norm(F @ _check_projector(P) @ psi) ** 2)
                      for P in partition)
    return p_direct - p_classical


class TwoLevelOscillator:
    """QPT-SATZ (unitaere 2-Level-Oszillation, geschlossene Form):

    Hamiltonian H = omega * X mit X = [[0,1],[1,0]]. Wegen X^2 = I gilt

        U(t) = exp(-i H t) = cos(omega t) I - i sin(omega t) X,

    U(t) ist unitaer (Normerhaltung), und die Uebergangswahrscheinlichkeit
    aus dem Basiszustand e_0 ist exakt

        p_01(t) = sin^2(omega t).

    BEWEIS: Potenzreihe exp(-iHt) = sum ((-i omega t)^k / k!) X^k. Mit
    X^{2k} = I, X^{2k+1} = X zerfaellt die Reihe in cos-Reihe * I und
    -i sin-Reihe * X. Unitaritaet: U U^dagger = (cos^2 + sin^2) I = I.
    Amplitude <e_1| U(t) |e_0> = -i sin(omega t), Betragsquadrat sin^2. QED.

    VERWENDUNGS-HINWEIS (ehrlich): Dies ist der formale Baustein, mit dem die
    Docs "Sisyphos-Oszillation" modellieren wollen (kontrollierte Oszillation
    zwischen zwei Zustaenden). Der Satz betrifft NUR die Mathematik; ob das
    Modell reale Sisyphos-Zyklen beschreibt, ist offen (QPT-SISYPHOS-FIT).
    """

    X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)

    def __init__(self, omega: float):
        self.omega = float(omega)

    def unitary(self, t: float) -> np.ndarray:
        """Geschlossene Form U(t) = cos(wt) I - i sin(wt) X."""
        wt = self.omega * t
        return np.cos(wt) * np.eye(2, dtype=np.complex128) - 1j * np.sin(wt) * self.X

    def unitary_via_spectral(self, t: float) -> np.ndarray:
        """Kontrollrechnung: U(t) = V exp(-i diag(lambda) t) V^dagger ueber
        Eigenzerlegung von H (unabhaengiger Rechenweg fuer die Tests)."""
        H = self.omega * self.X
        lam, V = np.linalg.eigh(H)
        return V @ np.diag(np.exp(-1j * lam * t)) @ V.conj().T

    def transition_probability(self, t: float) -> float:
        """p_01(t) = sin^2(omega t) (geschlossene Form aus dem Satz)."""
        return float(np.sin(self.omega * t) ** 2)

    def evolve(self, psi: np.ndarray, t: float) -> BeliefState:
        return BeliefState(self.unitary(t) @ _as_state(psi))


if __name__ == "__main__":
    # Mini-Demonstration (die eigentliche Verifikation liegt in
    # tests/test_quantum_cognition.py und wird vom Registry-Gate erzwungen).
    rng = np.random.default_rng(0)
    psi = rng.normal(size=4) + 1j * rng.normal(size=4)
    P_A = projector_from_vectors(rng.normal(size=(4, 2)))
    P_B = projector_from_vectors(rng.normal(size=(4, 1)))
    print(f"Ordnungseffekt p(AB)-p(BA):   {order_effect(psi, P_A, P_B):+.6f}  (i.A. != 0)")
    print(f"QQ-Equality-Residuum:         {qq_equality_residual(psi, P_A, P_B):+.2e} (Satz: 0)")
    osc = TwoLevelOscillator(omega=1.3)
    print(f"2-Level p01(t=0.7):           {osc.transition_probability(0.7):.6f} "
          f"= sin^2(0.91) = {np.sin(0.91)**2:.6f}")
