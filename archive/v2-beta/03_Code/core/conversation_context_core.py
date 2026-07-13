# conversation_context_core.py — ConversationContextCoreModule
# Adaptives Kontextfenster für Subagenten mit logisch-natürlicher Rückkopplung
# zum Start-Kontextfenster (Root/Session-Anker).

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple

_LAMBDA = float(os.getenv("FUSION_BANACH_LAMBDA", "0.74"))
_BASE_TOKENS = int(os.getenv("FUSION_CONTEXT_BASE_TOKENS", "4096"))
_MAX_ROOT_TOKENS = int(os.getenv("FUSION_CONTEXT_ROOT_MAX_TOKENS", "12000"))
_STORE = Path(__file__).resolve().parent.parent / "internal_llm" / "output" / "conversation_context.json"

_TASK_WEIGHTS = {"light": 0.65, "medium": 1.0, "heavy": 1.45}


def _approx_tokens(text: str) -> int:
    return max(1, len((text or "").split()))


def _clip(text: str, max_tokens: int) -> str:
    words = (text or "").split()
    if len(words) <= max_tokens:
        return text or ""
    return " ".join(words[:max_tokens]) + " …"


def _resource_scale() -> Tuple[float, str]:
    try:
        from resource_workflow import recommend_workers

        rec = recommend_workers("medium")
        mode = rec.get("mode", "parallel")
        workers = rec.get("recommended_workers", 2)
        if mode == "serial":
            return 0.55, "serial — minimales Subagent-Fenster"
        if mode == "conservative":
            return 0.75, "conservative — RAM/llama aktiv"
        if workers >= 3:
            return 1.15, "parallel — Ressourcen frei"
        return 1.0, "balanced"
    except Exception:
        return 1.0, "fallback"


def _banach_merge(target: str, current: str, lam: float = _LAMBDA) -> str:
    """s_{n+1} = s* + λ(s_n − s*) — textuelle Kontraktion zum Ziel-Fixpunkt."""
    if not current.strip():
        return target
    if not target.strip():
        return _clip(current, _approx_tokens(current))
    t_words = target.split()
    c_words = current.split()
    out: List[str] = []
    for i in range(max(len(t_words), len(c_words))):
        tw = t_words[i] if i < len(t_words) else ""
        cw = c_words[i] if i < len(c_words) else ""
        if tw and cw:
            out.append(tw if lam < 0.5 else cw if lam > 0.85 else cw)
        elif cw:
            out.append(cw)
        elif tw:
            out.append(tw)
    merged = " ".join(out)
    return _clip(merged, max(_approx_tokens(target), int(len(merged.split()) * lam)))


def _delta_compress(text: str, max_tokens: int = 120) -> str:
    """Executive-Summary + Delta-Compression für Rückkopplung."""
    raw = (text or "").strip()
    if not raw:
        return ""
    lines = [ln.strip() for ln in re.split(r"[\n\r]+", raw) if ln.strip()]
    scored: List[Tuple[float, str]] = []
    for ln in lines:
        score = 0.0
        if ln.endswith((".", "!", "?")):
            score += 0.2
        if any(k in ln.lower() for k in ("ok", "fehler", "error", "result", "erkenntnis", "fazit", "delta")):
            score += 0.35
        if len(ln) < 160:
            score += 0.15
        scored.append((score, ln))
    scored.sort(key=lambda x: x[0], reverse=True)
    picked: List[str] = []
    used = 0
    for _, ln in scored:
        w = len(ln.split())
        if used + w > max_tokens:
            break
        picked.append(ln)
        used += w
    if not picked and lines:
        picked = [lines[0]]
    bridge = "Rückkopplung zum Start-Kontext: "
    body = " | ".join(picked[:6])
    return _clip(bridge + body, max_tokens)


@dataclass
class ContextWindow:
    window_id: str
    role: str  # root | subagent
    token_budget: int
    seed_text: str = ""
    executive_summary: str = ""
    deltas: List[str] = field(default_factory=list)
    parent_id: Optional[str] = None
    subagent_name: Optional[str] = None
    task_weight: str = "medium"
    revision: int = 0
    created_ts: float = field(default_factory=time.time)
    updated_ts: float = field(default_factory=time.time)
    feedback_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "window_id": self.window_id,
            "role": self.role,
            "token_budget": self.token_budget,
            "seed_tokens": _approx_tokens(self.seed_text),
            "executive_summary": self.executive_summary,
            "delta_count": len(self.deltas),
            "latest_delta": self.deltas[-1] if self.deltas else None,
            "parent_id": self.parent_id,
            "subagent_name": self.subagent_name,
            "task_weight": self.task_weight,
            "revision": self.revision,
            "feedback_count": self.feedback_count,
            "updated_ts": self.updated_ts,
        }


class ConversationContextCore:
    """Adaptives Kontextfenster mit Root-Anker und Subagent-Rückkopplung."""

    def __init__(self) -> None:
        self.root_id: Optional[str] = None
        self.windows: Dict[str, ContextWindow] = {}
        self.feedback_log: Deque[Dict[str, Any]] = deque(maxlen=100)
        self._load()

    def _load(self) -> None:
        if not _STORE.exists():
            return
        try:
            data = json.loads(_STORE.read_text(encoding="utf-8"))
            self.root_id = data.get("root_id")
            for wid, w in (data.get("windows") or {}).items():
                self.windows[wid] = ContextWindow(
                    window_id=wid,
                    role=w.get("role", "subagent"),
                    token_budget=int(w.get("token_budget", _BASE_TOKENS)),
                    seed_text=w.get("seed_text", ""),
                    executive_summary=w.get("executive_summary", ""),
                    deltas=list(w.get("deltas") or []),
                    parent_id=w.get("parent_id"),
                    subagent_name=w.get("subagent_name"),
                    task_weight=w.get("task_weight", "medium"),
                    revision=int(w.get("revision", 0)),
                    created_ts=float(w.get("created_ts", time.time())),
                    updated_ts=float(w.get("updated_ts", time.time())),
                    feedback_count=int(w.get("feedback_count", 0)),
                )
        except Exception:
            pass
        self._prune_duplicates()

    def _prune_duplicates(self) -> None:
        """Entfernt veraltete Root-Fenster und doppelte Subagent-Einträge."""
        roots = [w for w in self.windows.values() if w.role == "root"]
        if len(roots) > 1:
            keep = max(roots, key=lambda w: w.updated_ts)
            self.root_id = keep.window_id
            for w in roots:
                if w.window_id != keep.window_id:
                    del self.windows[w.window_id]

        if self.root_id and self.root_id not in self.windows:
            if roots:
                self.root_id = max(roots, key=lambda w: w.updated_ts).window_id
            else:
                self.root_id = None

        seen_sub: Dict[str, str] = {}
        stale: List[str] = []
        for wid, w in self.windows.items():
            if w.role != "subagent" or not w.subagent_name:
                continue
            prev = seen_sub.get(w.subagent_name)
            if prev is None or self.windows[prev].updated_ts < w.updated_ts:
                if prev:
                    stale.append(prev)
                seen_sub[w.subagent_name] = wid
            else:
                stale.append(wid)
        for wid in stale:
            self.windows.pop(wid, None)

        root = self.windows.get(self.root_id) if self.root_id else None
        if root and root.executive_summary:
            parts = [
                p.strip()
                for p in re.split(r"\s*\|\s*", root.executive_summary.replace("Rückkopplung zum Start-Kontext: ", ""))
                if p.strip()
            ]
            deduped: List[str] = []
            for p in parts:
                if p not in deduped:
                    deduped.append(p)
            if deduped:
                root.executive_summary = _clip(
                    "Rückkopplung zum Start-Kontext: " + " | ".join(deduped[:8]),
                    150,
                )

    def _persist(self) -> None:
        try:
            _STORE.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "root_id": self.root_id,
                "windows": {
                    wid: {
                        **w.to_dict(),
                        "seed_text": w.seed_text,
                        "deltas": w.deltas[-20:],
                    }
                    for wid, w in self.windows.items()
                },
                "ts": time.time(),
            }
            _STORE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def adaptive_token_budget(
        self,
        task_weight: str = "medium",
        subagent_name: Optional[str] = None,
        priority: float = 1.0,
    ) -> Dict[str, Any]:
        scale, reason = _resource_scale()
        weight_mul = _TASK_WEIGHTS.get(task_weight, 1.0)
        budget = int(_BASE_TOKENS * scale * weight_mul * priority)
        budget = max(512, min(budget, _MAX_ROOT_TOKENS))

        try:
            import sys

            code_root = Path(__file__).resolve().parent.parent
            if str(code_root) not in sys.path:
                sys.path.insert(0, str(code_root))
            from TokenManagementSystem import ResourceState, TokenManagementSystem, TransformationType

            tms = TokenManagementSystem(base_tokens=_BASE_TOKENS)
            state = ResourceState(
                stability=0.7 if scale >= 1.0 else 0.45,
                latent_tension=0.2 if task_weight != "heavy" else 0.5,
                depth=1 if task_weight == "light" else 2 if task_weight == "medium" else 3,
                fluctuation_severity=0.1 if scale >= 1.0 else 0.35,
                bottleneck_risk=0.15 if scale >= 1.0 else 0.55,
            )
            key = subagent_name or "subagent_context"
            alloc = tms.allocate_tokens({key: state}, {key: priority})
            tms_budget = alloc.get(key, budget)
            budget = int((budget + tms_budget) / 2)
        except Exception:
            pass

        return {
            "token_budget": budget,
            "scale": round(scale, 3),
            "task_weight": task_weight,
            "reason": reason,
            "lambda": _LAMBDA,
        }

    def init_root(
        self,
        seed_text: str,
        task_meta: Optional[Dict[str, Any]] = None,
        force_new: bool = False,
    ) -> Dict[str, Any]:
        """Start-Kontextfenster (Session-Anker)."""
        if self.root_id and not force_new and self.root_id in self.windows:
            root = self.windows[self.root_id]
            if seed_text.strip():
                extra = _clip(seed_text, 200)
                root.seed_text = _clip(root.seed_text + "\n" + extra, _MAX_ROOT_TOKENS // 4)
                root.executive_summary = _delta_compress(root.seed_text, 80)
                root.revision += 1
                root.updated_ts = time.time()
                self._persist()
            return {"ok": True, "reused": True, "root": root.to_dict()}

        meta = task_meta or {}
        weight = meta.get("task_weight", "medium")
        alloc = self.adaptive_token_budget(weight, "root_context", priority=1.5)
        wid = f"root-{uuid.uuid4().hex[:12]}"
        summary_seed = seed_text.strip() or meta.get("query") or meta.get("original") or ""
        root = ContextWindow(
            window_id=wid,
            role="root",
            token_budget=min(alloc["token_budget"] * 2, _MAX_ROOT_TOKENS),
            seed_text=_clip(summary_seed, alloc["token_budget"]),
            executive_summary=_delta_compress(summary_seed, 100),
            task_weight=weight,
        )
        self.windows[wid] = root
        self.root_id = wid
        self._persist()
        return {
            "ok": True,
            "reused": False,
            "root": root.to_dict(),
            "allocation": alloc,
        }

    def allocate_subagent(
        self,
        subagent_name: str,
        task_weight: str = "medium",
        seed_fragment: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Adaptives Subagent-Kontextfenster, verankert am Root."""
        parent = parent_id or self.root_id
        if not parent or parent not in self.windows:
            init = self.init_root(seed_fragment or f"Subagent {subagent_name}", {"task_weight": task_weight})
            parent = init["root"]["window_id"]

        root = self.windows[parent]
        alloc = self.adaptive_token_budget(task_weight, subagent_name)
        wid = f"sub-{hashlib.md5(subagent_name.encode()).hexdigest()[:10]}-{int(time.time()) % 100000}"
        bridge = (
            f"[Subagent {subagent_name}] Ausgangspunkt — Start-Kontext: "
            f"{_clip(root.executive_summary or root.seed_text, 60)}"
        )
        seed = seed_fragment.strip() if seed_fragment else bridge
        win = ContextWindow(
            window_id=wid,
            role="subagent",
            token_budget=alloc["token_budget"],
            seed_text=_clip(seed, alloc["token_budget"] // 2),
            executive_summary=_clip(bridge, 80),
            parent_id=parent,
            subagent_name=subagent_name,
            task_weight=task_weight,
        )
        self.windows[wid] = win
        self._persist()
        return {
            "ok": True,
            "subagent_window": win.to_dict(),
            "parent_window": root.to_dict(),
            "allocation": alloc,
            "prompt_block": self.build_prompt_context(wid),
        }

    def build_prompt_context(self, window_id: str) -> str:
        """Kontextblock für LLM/Subagent-Injektion."""
        win = self.windows.get(window_id)
        if not win:
            return ""
        parts: List[str] = []
        if win.role == "subagent" and win.parent_id:
            root = self.windows.get(win.parent_id)
            if root:
                parts.append(f"## Start-Kontext (Anker)\n{_clip(root.executive_summary or root.seed_text, 120)}")
        parts.append(f"## {'Subagent' if win.role == 'subagent' else 'Root'}-Fenster [{win.window_id[:16]}]")
        parts.append(_clip(win.seed_text, win.token_budget // 3))
        if win.deltas:
            parts.append(f"## Letzte Delta-Rückkopplung\n{win.deltas[-1]}")
        return "\n\n".join(parts)

    def feedback(
        self,
        subagent_id: str,
        result_text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Logisch-natürliche Rückkopplung: Subagent-Ergebnis → Delta → Root-Fenster.
        Banach-Kontraktion auf Executive-Summary des Start-Kontexts.
        """
        sub = self.windows.get(subagent_id)
        if not sub or sub.role != "subagent":
            return {"ok": False, "error": f"unknown subagent window {subagent_id}"}

        meta = metadata or {}
        delta = _delta_compress(result_text, max(60, sub.token_budget // 20))
        if meta.get("summary"):
            delta = _clip(str(meta["summary"]), sub.token_budget // 15)

        natural = (
            f"Subagent '{sub.subagent_name}' meldet: {delta} "
            f"(Gewicht={sub.task_weight}, Rev={sub.revision + 1})"
        )
        sub.deltas.append(natural)
        sub.executive_summary = _banach_merge(sub.executive_summary, natural)
        sub.feedback_count += 1
        sub.revision += 1
        sub.updated_ts = time.time()

        root_id = sub.parent_id or self.root_id
        root_update: Optional[Dict[str, Any]] = None
        if root_id and root_id in self.windows:
            root = self.windows[root_id]
            contracted = _banach_merge(root.executive_summary, natural, _LAMBDA)
            root.executive_summary = _clip(contracted, 150)
            root.deltas.append(f"← {natural}")
            root.feedback_count += 1
            root.revision += 1
            root.updated_ts = time.time()
            root_update = root.to_dict()

        entry = {
            "ts": time.time(),
            "subagent_id": subagent_id,
            "subagent_name": sub.subagent_name,
            "delta": natural,
            "lambda": _LAMBDA,
            "root_id": root_id,
            "metadata": {k: v for k, v in meta.items() if k != "raw"},
        }
        self.feedback_log.append(entry)
        self._persist()

        return {
            "ok": True,
            "feedback": entry,
            "subagent_window": sub.to_dict(),
            "root_window": root_update,
            "banach_formula": "s_{n+1} = s* + λ(s_n − s*)",
            "lambda": _LAMBDA,
        }

    def feedback_from_task_result(
        self,
        task: Dict[str, Any],
        result: Any = None,
    ) -> Optional[Dict[str, Any]]:
        """Convenience: Rückkopplung aus Task/Subagent-Ergebnis."""
        sub_name = (
            task.get("assigned_agent")
            or task.get("subagent")
            or task.get("subagent_action")
            or "worker"
        )
        text = ""
        if isinstance(result, dict):
            text = str(
                result.get("response")
                or result.get("synthesised_response")
                or result.get("result")
                or result
            )
        elif isinstance(result, str):
            text = result
        elif task.get("llama_subagent_result"):
            tracks = task["llama_subagent_result"].get("tracks") or []
            parts = [
                f"{t.get('subagent')}: {'OK' if t.get('ok') else 'FAIL'}"
                for t in tracks[:8]
            ]
            text = "; ".join(parts)
        if not text.strip():
            return None

        existing = [
            w for w in self.windows.values()
            if w.role == "subagent" and w.subagent_name == str(sub_name)
        ]
        if existing:
            wid = sorted(existing, key=lambda w: w.updated_ts)[-1].window_id
        else:
            alloc = self.allocate_subagent(str(sub_name), task.get("task_weight", "medium"))
            wid = alloc["subagent_window"]["window_id"]

        return self.feedback(wid, text, {"task_id": task.get("id"), "dom": task.get("dom")})

    def status(self) -> Dict[str, Any]:
        root = self.windows.get(self.root_id) if self.root_id else None
        subagents = [w.to_dict() for w in self.windows.values() if w.role == "subagent"]
        scale, reason = _resource_scale()
        return {
            "module": "conversation_context_core",
            "enabled": os.getenv("FUSION_CONTEXT_WINDOW", "1") == "1",
            "root_id": self.root_id,
            "root_window": root.to_dict() if root else None,
            "subagent_windows": subagents[-12:],
            "subagent_count": len(subagents),
            "feedback_log_len": len(self.feedback_log),
            "recent_feedback": list(self.feedback_log)[-3:],
            "lambda": _LAMBDA,
            "base_tokens": _BASE_TOKENS,
            "resource_scale": scale,
            "resource_reason": reason,
            "store_path": str(_STORE),
            "store_exists": _STORE.exists(),
        }


_CTX: Optional[ConversationContextCore] = None


def get_context() -> ConversationContextCore:
    global _CTX
    if _CTX is None:
        _CTX = ConversationContextCore()
    return _CTX


def is_enabled() -> bool:
    return os.getenv("FUSION_CONTEXT_WINDOW", "1") == "1"


def init_root(seed_text: str, task_meta: Optional[Dict[str, Any]] = None, force_new: bool = False) -> Dict[str, Any]:
    if not is_enabled():
        return {"ok": False, "disabled": True}
    return get_context().init_root(seed_text, task_meta, force_new)


def allocate_subagent(
    subagent_name: str,
    task_weight: str = "medium",
    seed_fragment: Optional[str] = None,
) -> Dict[str, Any]:
    if not is_enabled():
        return {"ok": False, "disabled": True}
    return get_context().allocate_subagent(subagent_name, task_weight, seed_fragment)


def build_prompt_context(window_id: str) -> str:
    return get_context().build_prompt_context(window_id)


def feedback(subagent_id: str, result_text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not is_enabled():
        return {"ok": False, "disabled": True}
    return get_context().feedback(subagent_id, result_text, metadata)


def feedback_from_task(task: Dict[str, Any], result: Any = None) -> Optional[Dict[str, Any]]:
    if not is_enabled():
        return None
    return get_context().feedback_from_task_result(task, result)


def status() -> Dict[str, Any]:
    return get_context().status()