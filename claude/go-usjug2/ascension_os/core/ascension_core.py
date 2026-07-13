# ... (bestehender Code)

try:
    from .persistent_sisyphos import PersistentSisyphosCycle
except Exception:
    PersistentSisyphosCycle = None


class AscensionCore:
    def __init__(self):
        ...
        # Persistent Sisyphos
        self.persistent_sisyphos: Optional[PersistentSisyphosCycle] = None
        if PersistentSisyphosCycle:
            self.persistent_sisyphos = PersistentSisyphosCycle()

    def step_sisyphos(self, load: float, notes: str = ""):
        if self.persistent_sisyphos:
            return self.persistent_sisyphos.step(load, notes)
        return None

    def get_sisyphos_history(self, last_n: int = 10):
        if self.persistent_sisyphos:
            return self.persistent_sisyphos.get_history(last_n)
        return []
