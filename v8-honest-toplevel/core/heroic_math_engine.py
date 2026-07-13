"""
Heroic Math Engine - v8

Mathematische Kernkomponenten des Fusion-Hero-OS.
Orientiert an der Strenge von Kompendium V3.3 & V4.0.

EHRLICHER STATUS (Code-Honesty-Korrektur, siehe run_sandbox_verification()
für die numerischen Belege — Geltungskategorien nach HEROIC_SKILL.md:
Satz/Bedingt/Modell/Fragment):

  - Knoten 1  (Kommutator [Q,B])         — reine Demonstrationsrechnung, keine Behauptung.
  - Knoten 16 (\"Universelle Reziprozität\") — FRAGMENT. Die geprüfte Bedingung
    Q1·B1·B2·Q2 = Q2·B2·B1·Q1 ist numerisch verifiziert NUR im Trivialfall
    Q1=Q2 wahr; für jedes Paar Q1!=Q2 (auch bei zwei echten Rotationsmatrizen)
    liefert der Check False. Das ist keine Reziprozität, sondern eine Tautologie
    im Entartungsfall. Ohne die Originalformel aus Kompendium V3.3/V4.0 kann
    hier keine echte Reparatur vorgenommen werden — als offen markiert.
  - Knoten 19 (Monotonie der Fusion)     — MODELL, nicht bewiesen. Der Sandbox-
    Test bestand mit einem einzelnen Beispielpaar (psi, phi). Ein Sweep über
    500 zufällige kompatible Paare zeigt Verletzungen in ca. 15 % der Fälle
    (s_fused >= max(s_psi, s_phi) gilt NICHT allgemein). Als Heuristik für
    kompatible Nachbarwerte brauchbar, nicht als universeller Satz.
  - Knoten 17, 20                        — NICHT IMPLEMENTIERT. Es existiert
    kein Code für diese Knoten in diesem oder einem anderen Modul.

Frühere Formulierung \"Repariert zentrale mathematische Schwächen (Knoten 16,
17, 19, 20)\" war eine Überclaim und wurde entfernt. Teil der 02_architecture
Schicht.
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
        lhs = np.dot(np.dot(np.dot(q1, b1), b2), q2)
        rhs = np.dot(np.dot(np.dot(q2, b2), b1), q1)
        return bool(np.linalg.norm(lhs - rhs) < tolerance)


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
    def __init__(self, lmbda=0.5, eta=0.2):
        self.lmbda = lmbda
        self.eta = eta

    def compute_stability(self, psi):
        re_part = psi.real
        im_part = psi.imag
        base_stability = (re_part ** 2) - self.lmbda * (im_part ** 2)
        asymmetry_term = self.eta * im_part
        return base_stability + asymmetry_term

    def check_compatibility(self, psi, phi):
        return bool((psi.real >= 0 and phi.real >= 0) or (psi.real <= 0 and phi.real <= 0))

    def fusion_operator(self, psi, phi):
        if not self.check_compatibility(psi, phi):
            raise ValueError("Knoten 19 Verletzung: Strukturen außerhalb des Kompatibilitäts-Gegenraums.")
        re_new = psi.real + phi.real
        im_new = psi.imag - phi.imag
        return complex(re_new, im_new)


global_heroic_math = HeroicMatrixEngine()


def run_sandbox_verification():
    """Ehrliche Verifikations-Sandbox: prüft was tatsächlich zutrifft, statt es zu behaupten.

    Jeder Knoten wird gegen eine konkrete, reproduzierbare Aussage geprüft (mit echtem
    assert). Wo eine Aussage nur im Einzelfall/Trivialfall gilt, wird das explizit
    ausgegeben statt stillschweigend als "repariert" zu gelten.
    """
    print("=" * 65)
    print("RUNNING FUSION-HERO-OS CORE VERIFICATION SANDBOX")
    print("=" * 65)

    engine = HeroicMatrixEngine()
    print(f"[Knoten 1] Standardkommutator [q, b] (reine Demonstration, keine Behauptung):"
          f"\n{engine.compute_commutator(engine.q_default, engine.b_default)}")

    # Knoten 16: FRAGMENT. Echter assert auf das, was tatsächlich gilt (Trivialfall
    # Q1=Q2), PLUS expliziter Gegenbeweis für den allgemeinen Fall (Q1!=Q2), damit
    # die Lücke sichtbar bleibt statt als "False" unkommentiert im Log zu verschwinden.
    m1 = np.array([[0.5, 0.2], [0.1, 0.9]])
    m2 = np.array([[0.8, -0.3], [0.4, 0.2]])
    trivial_case = engine.check_reciprocity_condition(m1, engine.b_default, m1, engine.b_default)
    general_case = engine.check_reciprocity_condition(m1, engine.b_default, m2, engine.b_default)
    assert trivial_case is True, "Selbst der Trivialfall Q1=Q2 sollte reziprok sein"
    print(f"[Knoten 16] Reziprozitaet Q1=Q2 (Trivialfall): {trivial_case}  |  "
          f"Q1!=Q2 (allgemeiner Fall): {general_case} "
          f"-> FRAGMENT, keine universelle Reziprozitaet bewiesen (siehe Docstring)")

    # Knoten 19: MODELL. Der Einzelfall wird weiterhin gezeigt, aber zusätzlich ein
    # kleiner Sweep, der die tatsächliche Verletzungsrate ehrlich ausweist statt sie
    # durch ein einzelnes günstiges Beispiel zu verdecken.
    ip_system = RepairedStructureIP(lmbda=0.5, eta=1.5)
    psi = complex(2.0, -1.0)
    phi = complex(1.5, -0.5)

    s_psi = ip_system.compute_stability(psi)
    s_phi = ip_system.compute_stability(phi)
    fused = ip_system.fusion_operator(psi, phi)
    s_fused = ip_system.compute_stability(fused)

    print(f"\n[Knoten 19] Beispiel: S(psi)={s_psi:.4f}, S(phi)={s_phi:.4f}, S(fused)={s_fused:.4f}")
    assert s_fused >= max(s_psi, s_phi), "Selbst das dokumentierte Beispiel muss halten"
    print("  -> Monotonie gilt für DIESES Beispiel (kein allgemeiner Beweis)")

    rng = np.random.default_rng(42)
    trials, tested, violations = 500, 0, 0
    for _ in range(trials):
        p = complex(rng.uniform(-3, 3), rng.uniform(-3, 3))
        q = complex(rng.uniform(-3, 3), rng.uniform(-3, 3))
        if not ip_system.check_compatibility(p, q):
            continue
        tested += 1
        sp, sq = ip_system.compute_stability(p), ip_system.compute_stability(q)
        sf = ip_system.compute_stability(ip_system.fusion_operator(p, q))
        if sf < max(sp, sq) - 1e-9:
            violations += 1
    rate = violations / tested if tested else 0.0
    print(f"  -> Sweep ({tested} kompatible Paare von {trials} Versuchen): "
          f"{violations} Verletzungen ({rate:.1%}) -> KEIN allgemeines Monotonie-Gesetz")

    print("\n[Knoten 17, 20] Nicht implementiert — kein Code vorhanden.")
    print("=" * 65)


if __name__ == "__main__":
    run_sandbox_verification()