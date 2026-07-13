# ... (bestehender Code)

class QuadCoreBridge:
    def __init__(self, spine: PMSEvidenceSpine, seed: MasterSeed = None, mode: str = "heroic"):
        self.spine = spine
        self.seed = seed or MasterSeed()
        self.mode = mode.upper()
        self.volatile_history: list = []
        self.volatile_cache: Dict[str, Any] = {}

        # Heroic Track
        self.heroic = get_heroic_core(quad_core=self)
        self.llm = self.heroic.llm if self.heroic else None

        # Ascension Track (jetzt mit substantiellem AscensionCore v9.2)
        self.ascension: Optional[AscensionCore] = None
        if get_ascension_core:
            try:
                self.ascension = get_ascension_core()
                if seed:
                    self.ascension.register_masterseed(seed)
            except Exception:
                self.ascension = None

    def ask_llm(self, prompt: str, system_prompt: Optional[str] = None, force_provider: Optional[str] = None) -> LLMResult:
        if self.mode == "ASCENSION" and self.ascension:
            print("[ASCENSION v9.2] Using enhanced AscensionCore")
            return self.ascension.ask(prompt) or self.llm.ask(prompt, system_prompt, force_provider, context="ascension") if self.llm else LLMResult("no-llm", "AscensionCore nicht verfügbar")

        # Default Heroic Path
        ...

    def run_ascension_generation(self, generations: int = 5):
        if self.ascension:
            return self.ascension.run_generation(generations=generations)
        return {"status": "AscensionCore nicht verfügbar"}

# ... (Rest bleibt)
