"""
Dashboard Workspace - v8

Verantwortlich für Workspace-Management und State-Handling im Dashboard.

Teil der 04_execution Schicht.
"""

class Workspace:
    def __init__(self):
        self.state = {}

    def set(self, key: str, value):
        self.state[key] = value

    def get(self, key: str):
        return self.state.get(key)

    def clear(self):
        self.state.clear()


global_workspace = Workspace()