# -*- coding: utf-8 -*-
"""Epistemischer Wissensgraph — Write-Gate über HERO-GUIDE Werkbank."""
from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

STATE_DIR = Path(os.getenv("FUSION_STATE_DIR", r"C:\Users\Admin\.fusion-hero-os"))
GRAPH_FILE = STATE_DIR / "knowledge_graph.json"

_ALLOWED_CATEGORIES = frozenset({"SATZ", "BEDINGT", "MODELL", "FRAGMENT"})


class KnowledgeGraph:
    """In-Memory-Graph mit persistenter Speicherung — nur gated Writes."""

    def __init__(self, path: Path = GRAPH_FILE) -> None:
        self.path = path
        self.nodes: List[dict] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.nodes = list(data.get("nodes", []))
        except Exception:
            self.nodes = []

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": "1.0",
            "updated_at": time.time(),
            "nodes": self.nodes,
        }
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def add_node(self, text: str, category: str, meta: Optional[dict] = None) -> dict:
        """Interner Write — nur von HeroGuideWorkbench nach Auflösung."""
        cat = (category or "FRAGMENT").upper()
        if cat not in _ALLOWED_CATEGORIES:
            raise ValueError(f"Kategorie nicht graph-fähig: {category}")
        node = {
            "id": str(uuid.uuid4())[:12],
            "text": text,
            "category": cat,
            "meta": meta or {},
            "ts": time.time(),
        }
        self.nodes.append(node)
        self._save()
        return node

    def write_claim(self, payload: dict) -> dict:
        """Öffentlicher Write — immer via Projektions-Auflösung."""
        from hero_guide_ide import get_workbench
        wb = get_workbench(with_graph=True)
        return wb.resolve_from_payload(payload, persist=True)

    def list_nodes(self, limit: int = 50) -> List[dict]:
        return list(reversed(self.nodes[-limit:]))

    def status(self) -> dict:
        counts: Dict[str, int] = {}
        for n in self.nodes:
            c = n.get("category", "?")
            counts[c] = counts.get(c, 0) + 1
        return {
            "nodes_total": len(self.nodes),
            "category_counts": counts,
            "path": str(self.path),
            "write_gate": "HERO-GUIDE projektions_aufloesung",
        }


_graph_singleton: Optional[KnowledgeGraph] = None


def get_knowledge_graph() -> KnowledgeGraph:
    global _graph_singleton
    if _graph_singleton is None:
        _graph_singleton = KnowledgeGraph()
    return _graph_singleton