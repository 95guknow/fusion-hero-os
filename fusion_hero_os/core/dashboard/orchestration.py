"""
Dashboard Orchestration Layer - v8

Verantwortlich für die Koordination von Agenten und Aufgaben innerhalb des Dashboards.

Teil der 04_execution Schicht.
"""



class DashboardOrchestrator:
    def __init__(self):
        self.agents: dict[str, dict] = {}

    def register_agent(self, name: str, capabilities: list[str]):
        self.agents[name] = {"capabilities": capabilities, "active": True}

    def assign_best_agent(self, task: dict) -> str:
        dom = task.get("dom", "General")
        # Einfache Heuristik (später durch echten QUBO-Energy ersetzen)
        if dom == "Math":
            return "qb-qubo"
        elif dom == "Phil":
            return "grok-intern"
        else:
            return "fusion-hero"

    def get_active_agents(self) -> list[str]:
        return [name for name, data in self.agents.items() if data["active"]]


global_orchestrator = DashboardOrchestrator()