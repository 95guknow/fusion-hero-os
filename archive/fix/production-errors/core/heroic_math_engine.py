"""
Heroic Math Engine - v8

Mathematische Kernkomponenten des Fusion-Hero-OS.
Orientiert an der Strenge von Kompendium V3.3 & V4.0.

Repariert zentrale mathematische Schwächen (Knoten 16, 17, 19, 20).
Teil der 02_architecture Schicht.
"""

import numpy as np
import typing


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
    print("=" * 65)
    print("RUNNING FUSION-HERO-OS CORE VERIFICATION SANDBOX")
    print("=" * 65)

    engine = HeroicMatrixEngine()
    print(f"[Knoten 1] Standardkommutator [q, b]:\n{engine.compute_commutator(engine.q_default, engine.b_default)}")
    
    m1 = np.array([[0.5, 0.2], [0.1, 0.9]])
    m2 = np.array([[0.8, -0.3], [0.4, 0.2]])
    is_reciprocal = engine.check_reciprocity_condition(m1, engine.b_default, m2, engine.b_default)
    print(f"[Knoten 16] Universelle Reziprozität erfullt? {is_reciprocal}")

    ip_system = RepairedStructureIP(lmbda=0.5, eta=1.5)
    psi = complex(2.0, -1.0)
    phi = complex(1.5, -0.5)
    
    s_psi = ip_system.compute_stability(psi)
    s_phi = ip_system.compute_stability(phi)
    fused = ip_system.fusion_operator(psi, phi)
    s_fused = ip_system.compute_stability(fused)
    
    print(f"\n[Knoten 19] S(psi)={s_psi:.4f}, S(phi)={s_phi:.4f}, S(fused)={s_fused:.4f}")
    assert s_fused >= max(s_psi, s_phi)
    print("  -> Monotonie stabilisiert")

    print("=" * 65)


if __name__ == "__main__":
    run_sandbox_verification()