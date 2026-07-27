# -*- coding: utf-8 -*-
"""Konnektor-Vollautomat — alle Konnektoren in einem Lauf.

Direktive (verbindlich, in genau dieser Reihenfolge):

1. **Laden der Erinnerungen — immer bottom-up** (``L0_state`` -> ``L4_remotes``).
   Keine Schicht wird angefasst, bevor die darunterliegende geladen ist.
2. **Verarbeiten — immer top-down** (``L6omega`` -> ``L0``) nach
   ``Gott_Layering_v11_TopDown_Herleitung.md``, inklusive der vier Axiome.
3. **Ausgabe — immer Geister manifestiert.** Jede Luecke wird als Geist
   sichtbar gemacht; ``manifest=False`` kommt im Output nicht vor.

Konnektor-Quellen sind ``mesh_connectors.yaml``, ``graph_api_connectors.yaml``,
``llm_frameworks.yaml`` und ``control_instances.yaml`` — konfiguriert in
``konnektor_vollautomat.yaml``.

Policy (folgt ``fusion_hero_os/connectors/graph_api.py``): Dry-Run ist Default.
Live nur wenn ``FUSION_KONNEKTOR_LIVE=1`` **und** das jeweilige Token gesetzt
ist. Token-*Werte* verlassen dieses Modul nie — ausschliesslich
``token_present: bool``.

Geltung: Registry-/Pfad-Ergebnisse = Satz · fehlende optionale Quelle =
Bedingt skip · Live-Ausfuehrung = Spezifikation solange would_execute=false
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "konnektor_vollautomat.yaml"
DOCS_JSON = ROOT / "docs" / "ops" / "KONNEKTOR_VOLLAUTOMAT.latest.json"
DOCS_MD = ROOT / "docs" / "ops" / "KONNEKTOR_VOLLAUTOMAT.md"
PIN = Path.home() / ".fusion" / "ops" / "konnektor_vollautomat.latest.json"

PLATFORM = "13.0.0"
LIVE_ENV = "FUSION_KONNEKTOR_LIVE"

#: Ladereihenfolge — bottom-up, verbindlich.
LADEN_ORDER: Tuple[str, ...] = (
    "L0_state",
    "L1_registries",
    "L2_connectors",
    "L3_links",
    "L4_remotes",
)

#: Verarbeitungsreihenfolge — top-down, verbindlich (Gott-Layering v11).
LAYER_ORDER: Tuple[str, ...] = (
    "L6_masterseed",
    "L5_projektion",
    "L4_intent",
    "L3_internalisierung",
    "L2_bindung",
    "L1_verkoerperung",
    "L0_fundament",
)

__all__ = [
    "LADEN_ORDER",
    "LAYER_ORDER",
    "load_config",
    "load_bottom_up",
    "process_top_down",
    "manifest_ghosts",
    "automatisiere",
    "run_vollautomat",
    "status",
]


# ---------------------------------------------------------------------------
# Helfer
# ---------------------------------------------------------------------------


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_yaml(path: Path) -> Dict[str, Any]:
    """YAML defensiv laden — fehlendes ``yaml`` oder Parse-Fehler -> ``{}``."""
    try:
        import yaml  # type: ignore
    except ImportError:
        return {}
    try:
        if path.is_file():
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except Exception:
        pass
    return {}


def load_config() -> Dict[str, Any]:
    return _load_yaml(CONFIG)


def _expand(raw: str) -> Path:
    return Path(os.path.expanduser(str(raw).replace("\\", "/")))


def _env_present(names: Sequence[str]) -> bool:
    """True, wenn mindestens eine der Env-Variablen einen Wert hat.

    Gibt bewusst nur einen bool zurueck — der Wert wird nirgends gelesen,
    gespeichert oder ausgegeben.
    """
    for name in names:
        if name and (os.environ.get(str(name)) or "").strip():
            return True
    return False


def _live_enabled(force: bool = False) -> bool:
    if force:
        return True
    return (os.environ.get(LIVE_ENV) or "").strip().lower() in ("1", "true", "yes", "on")


def _strip_private(obj: Any) -> Any:
    """Entfernt ``_``-Schluessel rekursiv (Rohdaten gehoeren nicht in den Report)."""
    if isinstance(obj, dict):
        return {k: _strip_private(v) for k, v in obj.items() if not str(k).startswith("_")}
    if isinstance(obj, list):
        return [_strip_private(v) for v in obj]
    return obj


def _ghost_id(klasse: str, subjekt: str) -> str:
    """Deterministische Geist-ID.

    Bewusst ein Hash statt ``uuid4`` wie in ``geisterjagd_banach_viz.py``:
    der Report laeuft geplant in CI und soll bei unveraendertem Befund
    byte-identisch bleiben, sonst rauscht jeder Lauf einen Diff.
    """
    return hashlib.sha1(f"{klasse}:{subjekt}".encode("utf-8")).hexdigest()[:6]


# ---------------------------------------------------------------------------
# PHASE 1 — LADEN (bottom-up, L0 -> L4)
# ---------------------------------------------------------------------------


def _load_L0_state(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Erinnerung des letzten Laufs. Fehlt sie, ist das kein Fehler."""
    spec = ((cfg.get("laden_bottom_up") or {}).get("L0_state") or {})
    entries: List[Dict[str, Any]] = []
    for raw in spec.get("paths") or []:
        p = _expand(str(raw))
        rec: Dict[str, Any] = {"path": str(p), "exists": p.exists()}
        if not p.exists():
            rec["skipped"] = True
            rec["reason"] = "path_missing"
        elif p.is_file():
            try:
                prev = json.loads(p.read_text(encoding="utf-8"))
                counts = prev.get("counts") or {}
                rec["erinnerung"] = {
                    "generated_at": prev.get("generated_at"),
                    "konnektoren_gesamt": counts.get("konnektoren_gesamt"),
                    "geister": counts.get("geister"),
                    "l0_fundament": counts.get("l0_fundament"),
                }
            except Exception as exc:  # noqa: BLE001
                rec["error"] = str(exc)[:120]
        else:
            try:
                rec["file_count"] = sum(1 for f in p.rglob("*") if f.is_file())
            except OSError:
                rec["file_count"] = -1
        entries.append(rec)
    return {
        "layer": "L0_state",
        "kind": "state",
        "ok": True,
        "optional": bool(spec.get("optional", True)),
        "entries": entries,
        "erinnerung_vorhanden": any("erinnerung" in e for e in entries),
    }


def _load_L1_registries(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Die Konnektor-Registries des Repos einlesen."""
    spec = ((cfg.get("laden_bottom_up") or {}).get("L1_registries") or {})
    sources: List[Dict[str, Any]] = []
    data: Dict[str, Dict[str, Any]] = {}
    for src in spec.get("sources") or []:
        sid = str(src.get("id") or "")
        path = ROOT / str(src.get("path") or "")
        raw = _load_yaml(path)
        data[sid] = raw
        sources.append(
            {
                "id": sid,
                "path": str(src.get("path") or ""),
                "present": path.is_file(),
                "parsed": bool(raw),
                "top_level_keys": sorted(str(k) for k in raw.keys())[:12],
            }
        )
    return {
        "layer": "L1_registries",
        "kind": "registry",
        "ok": all(s["parsed"] for s in sources) if sources else False,
        "sources": sources,
        "_data": data,
    }


def _connector_record(
    *,
    familie: str,
    basis_id: str,
    kind: str,
    base_url: str = "",
    skill_module: str = "",
    api_key_envs: Optional[Sequence[str]] = None,
    health_path: str = "",
    actions: Optional[Sequence[str]] = None,
    mesh_id: str = "",
    provider: str = "",
    beschreibung: str = "",
) -> Dict[str, Any]:
    envs = [str(e) for e in (api_key_envs or []) if e]
    return {
        "id": f"{familie}:{basis_id}",
        "basis_id": basis_id,
        "familie": familie,
        "kind": kind,
        "base_url": base_url or "",
        "skill_module": skill_module or "",
        "credential_envs": envs,
        "token_present": _env_present(envs),
        "health_path": health_path or "",
        "actions": list(actions or []),
        "mesh_id": mesh_id or "",
        "provider": provider or "",
        "beschreibung": beschreibung or "",
    }


def _load_L2_connectors(registries: Dict[str, Any]) -> Dict[str, Any]:
    """Einzelne Konnektoren aus allen vier Familien extrahieren."""
    data = registries.get("_data") or {}
    mesh = data.get("mesh") or {}
    graph = data.get("graph_api") or {}
    llm = data.get("llm_frameworks") or {}
    ctrl = data.get("control_instances") or {}
    frameworks = llm.get("frameworks") or {}

    records: List[Dict[str, Any]] = []

    # -- mesh: MCP-Konnektoren am Knoten -----------------------------------
    for cid, raw in (mesh.get("connectors") or {}).items():
        raw = raw if isinstance(raw, dict) else {}
        records.append(
            _connector_record(
                familie="mesh",
                basis_id=str(cid),
                kind=str(raw.get("type") or "mcp"),
                health_path=str(raw.get("health_path") or ""),
                mesh_id=str(raw.get("mesh_id") or ""),
                beschreibung=str(raw.get("description") or ""),
            )
        )

    # -- graph_api: Graph-/REST-Konnektoren mit eigenem Token --------------
    for cid, raw in (graph.get("connectors") or {}).items():
        raw = raw if isinstance(raw, dict) else {}
        envs = [raw.get("env_token"), raw.get("alt_token")]
        records.append(
            _connector_record(
                familie="graph_api",
                basis_id=str(cid),
                kind=str(raw.get("kind") or "rest"),
                base_url=str(raw.get("base_url") or ""),
                skill_module=str(raw.get("skill_module") or ""),
                api_key_envs=[e for e in envs if e],
                actions=raw.get("actions") or [],
                beschreibung=str(raw.get("note") or ""),
            )
        )

    # -- llm_frameworks: je LLM ein eigenes Framework ----------------------
    llm_health_tpl = str(llm.get("per_provider") or "")
    for fid, raw in frameworks.items():
        raw = raw if isinstance(raw, dict) else {}
        envs = raw.get("api_key_env") or []
        if isinstance(envs, str):
            envs = [envs]
        health = llm_health_tpl.replace("{provider}", str(fid)) if llm_health_tpl else ""
        records.append(
            _connector_record(
                familie="llm_frameworks",
                basis_id=str(fid),
                kind="llm_framework",
                base_url=str(raw.get("base_url") or ""),
                skill_module=str(raw.get("module") or ""),
                api_key_envs=envs,
                health_path=health,
                actions=["status", "chat"],
                mesh_id=str(raw.get("mesh_id") or ""),
                provider=str(fid),
                beschreibung=str(raw.get("display_name") or ""),
            )
        )

    # -- control_instances: Credential ueber den Provider -------------------
    for raw in ctrl.get("instances") or []:
        if not isinstance(raw, dict):
            continue
        provider = str(raw.get("provider") or "")
        fw = frameworks.get(provider) or {}
        envs = fw.get("api_key_env") or []
        if isinstance(envs, str):
            envs = [envs]
        records.append(
            _connector_record(
                familie="control_instances",
                basis_id=str(raw.get("id") or ""),
                kind="control_instance",
                base_url=str(fw.get("base_url") or ""),
                skill_module=str(fw.get("module") or ""),
                api_key_envs=envs,
                actions=["verify"],
                provider=provider,
                beschreibung=str(raw.get("label") or ""),
            )
        )

    per_familie: Dict[str, int] = {}
    for r in records:
        per_familie[r["familie"]] = per_familie.get(r["familie"], 0) + 1

    return {
        "layer": "L2_connectors",
        "kind": "connectors",
        "ok": bool(records),
        "gesamt": len(records),
        "per_familie": per_familie,
        "_records": records,
    }


def _load_L3_links(registries: Dict[str, Any], connectors: Dict[str, Any]) -> Dict[str, Any]:
    """Verdrahtung Konnektor <-> Framework bzw. Instanz <-> Provider aufloesen."""
    data = registries.get("_data") or {}
    llm = data.get("llm_frameworks") or {}
    frameworks = llm.get("frameworks") or {}

    links: List[Dict[str, Any]] = []
    for cid, fw in (llm.get("connector_links") or {}).items():
        links.append(
            {
                "quelle": "connector_links",
                "von": str(cid),
                "nach": str(fw),
                "aufgeloest": str(fw) in frameworks,
            }
        )

    gesehen: Set[str] = set()
    for rec in connectors.get("_records") or []:
        if rec["familie"] != "control_instances":
            continue
        prov = rec.get("provider") or ""
        if not prov or prov in gesehen:
            continue
        gesehen.add(prov)
        links.append(
            {
                "quelle": "control_instances.provider",
                "von": prov,
                "nach": prov,
                "aufgeloest": prov in frameworks,
            }
        )

    offen = [ln for ln in links if not ln["aufgeloest"]]
    return {
        "layer": "L3_links",
        "kind": "links",
        # ok = die Schicht liess sich laden und aufloesen, soweit die Daten es
        # hergeben. Ein offener Link ist ein Befund (-> Geist), kein Ladefehler:
        # sonst faerbt eine Registry-Luecke den geplanten Lauf dauerhaft rot.
        "ok": True,
        "gesamt": len(links),
        "aufgeloest": len(links) - len(offen),
        "offen": len(offen),
        "links": links,
    }


def _load_L4_remotes(registries: Dict[str, Any], connectors: Dict[str, Any]) -> Dict[str, Any]:
    """Deklarierte Health-/Routing-Endpunkte einsammeln. Kein Netzwerk-Probe."""
    data = registries.get("_data") or {}
    mesh = data.get("mesh") or {}
    routing = mesh.get("routing") or {}

    eintraege: List[Dict[str, Any]] = []
    for rec in connectors.get("_records") or []:
        if rec["health_path"]:
            eintraege.append(
                {
                    "id": rec["id"],
                    "health_path": rec["health_path"],
                    "quelle": "registry",
                }
            )

    return {
        "layer": "L4_remotes",
        "kind": "remotes",
        "ok": True,
        "probe_durchgefuehrt": False,
        "hinweis": "Nur Deklaration — dieser Automat fuehrt keine Health-Probes aus.",
        "base_url": str(routing.get("base_url") or ""),
        "per_connector_template": str(routing.get("per_connector") or ""),
        "mit_health_path": len(eintraege),
        "eintraege": eintraege,
    }


def load_bottom_up(cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Phase 1 — Erinnerungen bottom-up laden (L0 -> L4).

    ``reihenfolge`` wird waehrend der Ausfuehrung mitgeschrieben, nicht aus
    einer Konstanten kopiert: der Test prueft damit die tatsaechliche
    Ladereihenfolge, nicht eine Behauptung.
    """
    cfg = cfg if cfg is not None else load_config()
    reihenfolge: List[str] = []
    mem: Dict[str, Any] = {}

    mem["L0_state"] = _load_L0_state(cfg)
    reihenfolge.append("L0_state")

    mem["L1_registries"] = _load_L1_registries(cfg)
    reihenfolge.append("L1_registries")

    mem["L2_connectors"] = _load_L2_connectors(mem["L1_registries"])
    reihenfolge.append("L2_connectors")

    mem["L3_links"] = _load_L3_links(mem["L1_registries"], mem["L2_connectors"])
    reihenfolge.append("L3_links")

    mem["L4_remotes"] = _load_L4_remotes(mem["L1_registries"], mem["L2_connectors"])
    reihenfolge.append("L4_remotes")

    return {
        "ok": all(mem[name].get("ok") for name in reihenfolge),
        "richtung": "bottom_up",
        "reihenfolge": reihenfolge,
        "schichten": mem,
    }


# ---------------------------------------------------------------------------
# PHASE 2 — VERARBEITEN (top-down, L6omega -> L0)
# ---------------------------------------------------------------------------


def _widerspruch(a: Dict[str, Any], b: Dict[str, Any]) -> Optional[str]:
    """Axiom 4: unvereinbare Doppelprojektion derselben Basis-Identitaet."""
    for feld in ("base_url", "credential_envs"):
        va, vb = a.get(feld), b.get(feld)
        if va and vb and va != vb:
            return feld
    return None


def _distanzen(
    sets: Dict[str, Set[str]], gesamt: int, lam: float, eps: float
) -> Dict[str, float]:
    """Distanz zum MasterSeed je Layer.

    ``d(L6) = 0`` — L6omega *ist* der MasterSeed. Nach unten waechst die
    Distanz um ein Inkrement, das mit ``lam ** k`` schrumpft; das ist die
    Banach-Kontraktion, von L0 aufwaerts zum Fixpunkt gelesen.

    Strikte Monotonie ist durch ``eps > 0`` konstruktiv garantiert. Die
    Pruefung in :func:`process_top_down` ist deshalb ein Regressionswaechter
    gegen kaputte Konfiguration — kein Beweis des Axioms.
    """
    dist: Dict[str, float] = {LAYER_ORDER[0]: 0.0}
    laufend = 0.0
    for k, name in enumerate(LAYER_ORDER[1:], start=1):
        w = len(sets[name]) / max(1, gesamt)
        laufend += (lam ** k) * (eps + w)
        dist[name] = round(laufend, 6)
    return dist


def process_top_down(
    memories: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Phase 2 — strikt top-down verarbeiten (L6omega -> L0).

    Jede Schicht filtert ausschliesslich die darueberliegende; damit gilt
    ``L_n subset L_{n+1}`` per Konstruktion (Axiom 1).
    """
    cfg = cfg if cfg is not None else load_config()
    defaults = cfg.get("defaults") or {}
    lam = max(0.15, min(0.95, float(defaults.get("lambda_contract") or 0.78)))
    eps = float(defaults.get("increment_epsilon") or 0.01)

    schichten = memories.get("schichten") or {}
    records: List[Dict[str, Any]] = list(schichten.get("L2_connectors", {}).get("_records") or [])
    nach_id = {r["id"]: r for r in records}
    links = schichten.get("L3_links", {}).get("links") or []

    verarbeitet: List[str] = []
    sets: Dict[str, Set[str]] = {}

    # -- L6omega: alle erwaehnten Identitaeten -----------------------------
    erwaehnt: Set[str] = set(nach_id)
    nur_erwaehnt: Dict[str, str] = {}
    for ln in links:
        if not ln.get("aufgeloest"):
            ziel = f"erwaehnt:{ln.get('nach')}"
            erwaehnt.add(ziel)
            nur_erwaehnt[ziel] = str(ln.get("quelle") or "")
    sets["L6_masterseed"] = set(erwaehnt)
    verarbeitet.append("L6_masterseed")

    # -- L5: Projektion pi — nur mit echtem Registry-Eintrag ---------------
    sets["L5_projektion"] = {cid for cid in sets["L6_masterseed"] if cid in nach_id}
    verarbeitet.append("L5_projektion")

    # -- L4: eindeutige, widerspruchsfreie Basis-Identitaet ----------------
    nach_basis: Dict[str, List[Dict[str, Any]]] = {}
    for cid in sorted(sets["L5_projektion"]):
        rec = nach_id[cid]
        nach_basis.setdefault(rec["basis_id"], []).append(rec)

    invarianz_brueche: List[Dict[str, Any]] = []
    raus_l4: Set[str] = set()
    for basis, gruppe in sorted(nach_basis.items()):
        if len(gruppe) < 2:
            continue
        for i in range(len(gruppe)):
            for j in range(i + 1, len(gruppe)):
                feld = _widerspruch(gruppe[i], gruppe[j])
                if feld:
                    invarianz_brueche.append(
                        {
                            "basis_id": basis,
                            "feld": feld,
                            "beteiligte": sorted([gruppe[i]["id"], gruppe[j]["id"]]),
                        }
                    )
                    raus_l4.update({gruppe[i]["id"], gruppe[j]["id"]})
    sets["L4_intent"] = sets["L5_projektion"] - raus_l4
    verarbeitet.append("L4_intent")

    # -- L3: Internalisierung (Operator C) — ausfuehrbare Spezifikation ----
    def _hat_spec(rec: Dict[str, Any]) -> bool:
        return bool(rec["base_url"] or rec["skill_module"] or rec["health_path"])

    sets["L3_internalisierung"] = {
        cid for cid in sets["L4_intent"] if _hat_spec(nach_id[cid])
    }
    verarbeitet.append("L3_internalisierung")

    # -- L2: deklarierte Credential-Quelle ---------------------------------
    sets["L2_bindung"] = {
        cid for cid in sets["L3_internalisierung"] if nach_id[cid]["credential_envs"]
    }
    verarbeitet.append("L2_bindung")

    # -- L1: Credential tatsaechlich vorhanden -----------------------------
    sets["L1_verkoerperung"] = {
        cid for cid in sets["L2_bindung"] if nach_id[cid]["token_present"]
    }
    verarbeitet.append("L1_verkoerperung")

    # -- L0: versiegelt, Eintritt nur ueber Operator C (Axiom 3) -----------
    sets["L0_fundament"] = {
        cid for cid in sets["L1_verkoerperung"] if cid in sets["L3_internalisierung"]
    }
    verarbeitet.append("L0_fundament")

    # -- Axiome pruefen -----------------------------------------------------
    gesamt = len(sets["L6_masterseed"])
    dist = _distanzen(sets, gesamt, lam, eps)

    teilmengen_ok = all(
        sets[LAYER_ORDER[i + 1]] <= sets[LAYER_ORDER[i]] for i in range(len(LAYER_ORDER) - 1)
    )
    folge = [dist[name] for name in LAYER_ORDER]
    kontraktion_ok = all(folge[i] < folge[i + 1] for i in range(len(folge) - 1))
    integration_ok = sets["L0_fundament"] <= sets["L3_internalisierung"]

    return {
        "ok": teilmengen_ok and kontraktion_ok and integration_ok and not invarianz_brueche,
        "richtung": "top_down",
        "reihenfolge": verarbeitet,
        "lambda_contract": lam,
        "epsilon": eps,
        "masterseed": {
            "platform_version": PLATFORM,
            "policy": str(cfg.get("policy") or "dry_run_default"),
            "bounds": cfg.get("bounds") or {},
        },
        "mengen": {name: sorted(sets[name]) for name in LAYER_ORDER},
        "groessen": {name: len(sets[name]) for name in LAYER_ORDER},
        "distanz_zum_masterseed": dist,
        "axiome": {
            "1_top_down_teilmengen": teilmengen_ok,
            "2_kontraktion_strikt_monoton": kontraktion_ok,
            "3_integration_ueber_operator_c": integration_ok,
            "4_invarianz": not invarianz_brueche,
        },
        "invarianz_brueche": invarianz_brueche,
        "_sets": sets,
        "_nach_id": nach_id,
        "_nur_erwaehnt": nur_erwaehnt,
    }


# ---------------------------------------------------------------------------
# PHASE 3 — AUSGABE (Geister manifestiert)
# ---------------------------------------------------------------------------


def manifest_ghosts(
    memories: Dict[str, Any],
    layering: Dict[str, Any],
    cfg: Optional[Dict[str, Any]] = None,
    *,
    live: bool = False,
) -> List[Dict[str, Any]]:
    """Phase 3 — jede Luecke als manifestierten Geist ausgeben.

    ``manifest`` ist ausnahmslos ``True``: nichts bleibt latent. ``activation``
    dient nur der Sortierung, nicht der Sichtbarkeit. ``by_design=True``
    markiert Befunde, die bauartbedingt sind (siehe ``familien:`` in der
    Konfiguration) — sie werden gedaempft, aber nicht verschwiegen.
    """
    cfg = cfg if cfg is not None else load_config()
    klassen = ((cfg.get("geister") or {}).get("klassen") or {})
    familien = cfg.get("familien") or {}
    waisen_familien = set(
        (cfg.get("waisen_pruefung") or {}).get("familien") or []
    )
    credential_ausnahmen = {str(x) for x in (cfg.get("credential_ausnahmen") or [])}

    sets: Dict[str, Set[str]] = layering["_sets"]
    nach_id: Dict[str, Dict[str, Any]] = layering["_nach_id"]
    nur_erwaehnt: Dict[str, str] = layering.get("_nur_erwaehnt") or {}

    geister: List[Dict[str, Any]] = []

    def _add(
        klasse: str,
        subjekt: str,
        *,
        latent_layer: str,
        detail: Optional[Dict[str, Any]] = None,
        by_design: bool = False,
    ) -> None:
        spec = klassen.get(klasse) or {}
        akt = float(spec.get("activation") or 0.5)
        if by_design:
            akt = round(akt * 0.25, 4)
        geister.append(
            {
                "id": _ghost_id(klasse, subjekt),
                "klasse": klasse,
                "label": subjekt,
                "activation": akt,
                "manifest": True,  # Direktive: Ausgabe immer Geister manifestiert
                "latent_layer": latent_layer,
                "manifest_layer": "ausgabe",
                "by_design": by_design,
                "bedeutung": str(spec.get("bedeutung") or ""),
                "detail": detail or {},
            }
        )

    # -- Abstiegs-Geister: wer faellt zwischen welchen Schichten heraus? ----
    for cid in sorted(sets["L6_masterseed"] - sets["L5_projektion"]):
        _add(
            "link_ins_leere",
            cid.replace("erwaehnt:", ""),
            latent_layer="L5_projektion",
            detail={"quelle": nur_erwaehnt.get(cid, "")},
        )

    for cid in sorted(sets["L5_projektion"] - sets["L4_intent"]):
        _add("invarianz_bruch", cid, latent_layer="L4_intent")

    for cid in sorted(sets["L4_intent"] - sets["L3_internalisierung"]):
        _add("keine_internalisierung", cid, latent_layer="L3_internalisierung")

    for cid in sorted(sets["L3_internalisierung"] - sets["L2_bindung"]):
        rec = nach_id[cid]
        fam = familien.get(rec["familie"]) or {}
        lokal = bool(
            {rec["basis_id"], rec["provider"]} & credential_ausnahmen
        )
        _add(
            "keine_credential_bindung",
            cid,
            latent_layer="L2_bindung",
            by_design=not bool(fam.get("erwartet_credential", True)) or lokal,
            detail={
                "familie": rec["familie"],
                "grund": "lokal/self-hosted" if lokal else "keine env-Quelle deklariert",
            },
        )

    for cid in sorted(sets["L2_bindung"] - sets["L1_verkoerperung"]):
        rec = nach_id[cid]
        _add(
            "credential_fehlt",
            cid,
            latent_layer="L1_verkoerperung",
            detail={"envs": rec["credential_envs"]},
        )

    # -- Bewusst im Dry-Run gehalten (kein Defekt) --------------------------
    if not live:
        for cid in sorted(sets["L0_fundament"]):
            _add("dry_run_gehalten", cid, latent_layer="L0_fundament")

    # -- Querschnitt: Waisen zwischen den ueberlappenden Familien -----------
    basis_zu_familien: Dict[str, Set[str]] = {}
    for cid in sorted(sets["L5_projektion"]):
        rec = nach_id[cid]
        if rec["familie"] in waisen_familien:
            basis_zu_familien.setdefault(rec["basis_id"], set()).add(rec["familie"])
    for basis, fams in sorted(basis_zu_familien.items()):
        fehlend = waisen_familien - fams
        if fehlend:
            _add(
                "registry_waise",
                basis,
                latent_layer="L5_projektion",
                detail={"bekannt_in": sorted(fams), "fehlt_in": sorted(fehlend)},
            )

    # -- Querschnitt: kein Health-Probe, wo die Familie einen erwartet ------
    for cid in sorted(sets["L5_projektion"]):
        rec = nach_id[cid]
        fam = familien.get(rec["familie"]) or {}
        if fam.get("erwartet_health") and not rec["health_path"]:
            _add("kein_health_probe", cid, latent_layer="L4_remotes")

    # -- Axiom-Verletzungen -------------------------------------------------
    if not layering["axiome"]["2_kontraktion_strikt_monoton"]:
        _add(
            "kontraktions_bruch",
            "layer_distanzen",
            latent_layer="L6_masterseed",
            detail=layering["distanz_zum_masterseed"],
        )

    geister.sort(key=lambda g: (-g["activation"], g["klasse"], g["label"]))
    return geister


# ---------------------------------------------------------------------------
# PHASE 4 — VOLLAUTOMATISIERUNG
# ---------------------------------------------------------------------------


def automatisiere(
    layering: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None, *, force_live: bool = False
) -> Dict[str, Any]:
    """Je L0-Konnektor die konfigurierte Aktion ausfuehren.

    Ausgefuehrt wird ueber den bestehenden :class:`GraphAPIHub` — der kennt
    nur die ``graph_api``-Familie. Fuer alle anderen Familien gibt es keinen
    Ausfuehrungspfad; das wird als solches gemeldet statt als Erfolg.
    """
    cfg = cfg if cfg is not None else load_config()
    aktion = str((cfg.get("automatisierung") or {}).get("aktion_je_konnektor") or "status")
    live = _live_enabled(force_live)

    hub = None
    hub_fehler = ""
    try:
        from fusion_hero_os.connectors.graph_api import build_default_hub

        hub = build_default_hub()
    except Exception as exc:  # noqa: BLE001
        hub_fehler = str(exc)[:160]

    nach_id: Dict[str, Dict[str, Any]] = layering["_nach_id"]
    ergebnisse: List[Dict[str, Any]] = []
    for cid in sorted(layering["_sets"]["L0_fundament"]):
        rec = nach_id[cid]
        eintrag: Dict[str, Any] = {
            "id": cid,
            "familie": rec["familie"],
            "aktion": aktion,
            # Nur die Env-*Namen* — sie stehen ohnehin offen in den Registries
            # und sagen dem Operator, welche Variable diesen Konnektor speist.
            "credential_envs": list(rec["credential_envs"]),
            "token_present": rec["token_present"],
            "live_enabled": live,
        }
        if rec["familie"] != "graph_api":
            eintrag.update(
                {
                    "ok": True,
                    "would_execute": False,
                    "reason": "kein Ausfuehrungspfad ausserhalb des Graph-Hubs",
                }
            )
        elif hub is None:
            eintrag.update({"ok": False, "would_execute": False, "reason": hub_fehler})
        else:
            try:
                res = hub.dispatch(rec["basis_id"], aktion)
                eintrag.update(
                    {
                        "ok": bool(res.get("ok")),
                        "would_execute": bool(res.get("would_execute", False)),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                eintrag.update(
                    {"ok": False, "would_execute": False, "reason": str(exc)[:160]}
                )
        ergebnisse.append(eintrag)

    return {
        "ok": all(e.get("ok") for e in ergebnisse) if ergebnisse else True,
        "live_enabled": live,
        "modus": "LIVE" if live else "DRY-RUN",
        "aktion": aktion,
        "hub_verfuegbar": hub is not None,
        "ausgefuehrt": sum(1 for e in ergebnisse if e.get("would_execute")),
        "ergebnisse": ergebnisse,
    }


def _render_markdown(report: Dict[str, Any]) -> str:
    lay = report["verarbeiten"]
    geister = report["geister"]
    counts = report["counts"]

    zeilen: List[str] = []
    zeilen.append("# Konnektor-Vollautomat")
    zeilen.append("")
    zeilen.append(
        f"Platform {report['platform_version']} · "
        "`python -m fusion_hero_os.core.konnektor_vollautomat`"
    )
    zeilen.append("")
    zeilen.append(f"**UTC:** {report['generated_at']}  ")
    zeilen.append(f"**Modus:** {report['automatisierung']['modus']}  ")
    zeilen.append(f"**Status:** {'ok' if report['ok'] else 'Befunde offen'}")
    zeilen.append("")
    zeilen.append("## Direktive")
    zeilen.append("")
    zeilen.append("| Phase | Richtung | Nachweis |")
    zeilen.append("|---|---|---|")
    zeilen.append(
        f"| Laden der Erinnerungen | bottom-up | `{' -> '.join(report['laden']['reihenfolge'])}` |"
    )
    zeilen.append(
        f"| Verarbeiten | top-down | `{' -> '.join(lay['reihenfolge'])}` |"
    )
    zeilen.append(
        f"| Ausgabe | Geister manifestiert | {counts['geister']} Geister, "
        f"{counts['geister_latent']} latent |"
    )
    zeilen.append("")
    zeilen.append("## Gott-Layering — Abstieg L6omega -> L0")
    zeilen.append("")
    zeilen.append("| Layer | Konnektoren | d(Layer, MasterSeed) |")
    zeilen.append("|---|---:|---:|")
    for name in LAYER_ORDER:
        zeilen.append(
            f"| {name} | {lay['groessen'][name]} | {lay['distanz_zum_masterseed'][name]} |"
        )
    zeilen.append("")
    zeilen.append("## Axiome")
    zeilen.append("")
    zeilen.append("| Axiom | Ergebnis |")
    zeilen.append("|---|---|")
    for k, v in lay["axiome"].items():
        zeilen.append(f"| {k} | {'PASS' if v else 'FAIL'} |")
    zeilen.append("")
    zeilen.append("## Geister (manifestiert)")
    zeilen.append("")
    if not geister:
        zeilen.append("Keine Geister — jeder erwaehnte Konnektor erreicht L0.")
    else:
        zeilen.append("| Aktivierung | Klasse | Subjekt | faellt bei | by design |")
        zeilen.append("|---:|---|---|---|---|")
        for g in geister:
            zeilen.append(
                f"| {g['activation']:.2f} | {g['klasse']} | `{g['label']}` | "
                f"{g['latent_layer']} | {'ja' if g['by_design'] else 'nein'} |"
            )
    zeilen.append("")
    zeilen.append("## Bounds")
    zeilen.append("")
    zeilen.append(
        "Offense **FORBIDDEN** · sandbox_only · keine Token-Werte im Report · "
        "Vault nicht in Git"
    )
    zeilen.append("")
    zeilen.append(f"**Geltung:** {report['geltung']}")
    zeilen.append("")
    return "\n".join(zeilen)


def run_vollautomat(*, force_live: bool = False, schreiben: bool = True) -> Dict[str, Any]:
    """Phase 1-4 in einem Lauf. Dry-Run, solange kein Live-Flag gesetzt ist."""
    t0 = datetime.now(timezone.utc)
    cfg = load_config()
    live = _live_enabled(force_live)

    laden = load_bottom_up(cfg)
    verarbeiten = process_top_down(laden, cfg)
    geister = manifest_ghosts(laden, verarbeiten, cfg, live=live)
    auto = automatisiere(verarbeiten, cfg, force_live=force_live)

    echte_befunde = [g for g in geister if not g["by_design"] and g["klasse"] != "dry_run_gehalten"]
    counts = {
        "konnektoren_gesamt": verarbeiten["groessen"]["L6_masterseed"],
        "l0_fundament": verarbeiten["groessen"]["L0_fundament"],
        "geister": len(geister),
        "geister_latent": sum(1 for g in geister if not g["manifest"]),
        "geister_echte_befunde": len(echte_befunde),
        "per_familie": laden["schichten"]["L2_connectors"]["per_familie"],
    }

    report: Dict[str, Any] = {
        "kind": "KONNEKTOR_VOLLAUTOMAT",
        "generated_at": _now(),
        "platform_version": PLATFORM,
        # ok = der Automat selbst lief korrekt (Registries lesbar, Axiome halten).
        # Gefundene Luecken stehen in befunde_offen — sie sind das Produkt des
        # Laufs, nicht sein Scheitern.
        "ok": bool(laden["ok"] and verarbeiten["ok"] and auto["ok"]),
        "befunde_offen": bool(echte_befunde),
        "duration_sec": round((datetime.now(timezone.utc) - t0).total_seconds(), 3),
        "direktiven": {
            "laden": "bottom_up",
            "verarbeiten": "top_down",
            "ausgabe": "geister_manifestiert",
        },
        "laden": _strip_private(laden),
        "verarbeiten": _strip_private(verarbeiten),
        "geister": geister,
        "automatisierung": auto,
        "counts": counts,
        "geltung": str(cfg.get("geltung") or "").strip()
        or "Registry-/Pfad-Ergebnisse = Satz",
    }

    if schreiben:
        DOCS_JSON.parent.mkdir(parents=True, exist_ok=True)
        DOCS_JSON.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        DOCS_MD.write_text(_render_markdown(report), encoding="utf-8")
        try:
            PIN.parent.mkdir(parents=True, exist_ok=True)
            PIN.write_text(
                json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            report["pin"] = str(PIN)
        except OSError as exc:
            report["pin_error"] = str(exc)[:120]
        report["docs"] = str(DOCS_JSON.relative_to(ROOT))
        report["markdown"] = str(DOCS_MD.relative_to(ROOT))

    return report


def status() -> Dict[str, Any]:
    cfg = load_config()
    return {
        "ok": True,
        "module": "konnektor_vollautomat",
        "platform_version": PLATFORM,
        "config": str(CONFIG.relative_to(ROOT)),
        "config_ok": bool(cfg),
        "policy": str(cfg.get("policy") or "dry_run_default"),
        "live_env": LIVE_ENV,
        "live_enabled": _live_enabled(),
        "laden_reihenfolge": list(LADEN_ORDER),
        "verarbeiten_reihenfolge": list(LAYER_ORDER),
        "report": str(DOCS_JSON.relative_to(ROOT)) if DOCS_JSON.exists() else None,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Konnektor-Vollautomat — bottom-up laden, top-down verarbeiten, "
        "Geister manifestiert ausgeben"
    )
    ap.add_argument("--status", action="store_true", help="nur Modul-Status")
    ap.add_argument("--json", action="store_true", help="vollen Report als JSON")
    ap.add_argument(
        "--force-live",
        action="store_true",
        help=f"Live erzwingen (sonst ueber {LIVE_ENV}=1); Token bleibt Pflicht",
    )
    ap.add_argument("--no-write", action="store_true", help="keine Report-Dateien schreiben")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="auch bei offenen Befunden mit 1 enden (Gate-Betrieb statt Report-Betrieb)",
    )
    args = ap.parse_args(argv)

    if args.status:
        print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0

    r = run_vollautomat(force_live=args.force_live, schreiben=not args.no_write)
    rc = 0 if r["ok"] and not (args.strict and r["befunde_offen"]) else 1

    if args.json:
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return rc

    lay = r["verarbeiten"]
    print(json.dumps({
        "ok": r["ok"],
        "befunde_offen": r["befunde_offen"],
        "modus": r["automatisierung"]["modus"],
        "counts": r["counts"],
        "axiome": lay["axiome"],
        "duration_sec": r["duration_sec"],
        "docs": r.get("docs"),
    }, indent=2, ensure_ascii=False))

    print("\n  Laden (bottom-up):      " + " -> ".join(r["laden"]["reihenfolge"]))
    print("  Verarbeiten (top-down): " + " -> ".join(lay["reihenfolge"]))
    print("\n  Layer            Konnektoren   d(MasterSeed)")
    for name in LAYER_ORDER:
        print(
            f"  {name:<18}{lay['groessen'][name]:>6}"
            f"{lay['distanz_zum_masterseed'][name]:>16.6f}"
        )
    print(f"\n  Geister manifestiert: {r['counts']['geister']} "
          f"(davon echte Befunde: {r['counts']['geister_echte_befunde']})")
    for g in r["geister"][:15]:
        marke = " [by design]" if g["by_design"] else ""
        print(f"    {g['activation']:.2f}  {g['klasse']:<26} {g['label']}{marke}")
    if len(r["geister"]) > 15:
        print(f"    … {len(r['geister']) - 15} weitere im Report")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
