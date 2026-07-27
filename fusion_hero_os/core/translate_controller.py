# -*- coding: utf-8 -*-
"""Translate-Controller — je Modul die optimale Sprache, Ist gegen Soll.

Der Controller **uebersetzt nichts**. Er liest das Repo, ordnet jedem Modul
nach den Regeln aus ``sprachbindung.yaml`` eine Zielsprache zu, benennt die
noetige Sprachbindung und weist die Luecke aus. Portiert wird danach von
Hand, Modul fuer Modul, mit Messung — nicht per Automat.

Warum so: eine Sprachumstellung ohne Messung ist eine Behauptung. Der
Controller macht die Behauptung pruefbar, indem er sagt, *welche* Module
betroffen waeren und *warum* — das Signal steht bei jeder Regel.

Ist-Sprache kommt aus zwei Quellen:

* ``dependency_atlas`` kennt Python-Module, Rust-Crates und JS-Pakete samt
  Layer. Das ist die Mehrheit und wird wiederverwendet statt neu gescannt.
* Der Atlas erfasst ``kernel/`` nicht (weder ``.s`` noch ``.c``). Diese Ebene
  wird hier ergaenzt — sonst fehlte ausgerechnet der Kern.

Geltung: Ist = Satz (abgelesen) · Soll = Spezifikation (Regel) ·
Luecke = Bedingt, solange die Zielsprache nicht gebaut und gebunden ist
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "sprachbindung.yaml"

__all__ = [
    "Modul",
    "load_config",
    "inventar",
    "zielsprache",
    "report",
    "status",
]


# ---------------------------------------------------------------------------
# Helfer
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError:
        return {}
    try:
        if path.is_file():
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        # Kaputte Konfiguration darf den Lauf nicht abbrechen; sie faellt in
        # status()/report() als config_ok=False auf.
        return {}
    return {}


def load_config() -> Dict[str, Any]:
    return _load_yaml(CONFIG)


@dataclass
class Modul:
    """Ein Modul mit Ist- und Soll-Sprache."""

    name: str
    pfad: str
    layer: str
    ist: str
    soll: str = ""
    regel: str = ""
    signal: str = ""
    bindung: str = ""
    hinweis: str = ""
    gebunden: bool = False

    @property
    def abweichung(self) -> bool:
        """Ist- und Soll-Sprache fallen auseinander."""
        return bool(self.soll) and self.ist != self.soll

    @property
    def luecke(self) -> bool:
        """Abweichung, die noch Arbeit bedeutet.

        Ein Modul, das die Zielsprache bereits ueber die vorgesehene Bindung
        aufruft, ist *nicht* offen — es muss nicht portiert werden. Ohne diese
        Unterscheidung wuerde der Controller Arbeit ausweisen, die es nicht
        gibt: ``fusion_hero_os/engine/mainframe.py`` etwa laedt laengst
        ``rust_backend`` mit Fallback auf numba.
        """
        return self.abweichung and not self.gebunden

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "name": self.name,
            "pfad": self.pfad,
            "layer": self.layer,
            "ist": self.ist,
            "soll": self.soll,
            "regel": self.regel,
            "signal": self.signal,
            "bindung": self.bindung,
            "gebunden": self.gebunden,
            "abweichung": self.abweichung,
            "luecke": self.luecke,
        }
        if self.hinweis:
            d["hinweis"] = self.hinweis
        return d


# ---------------------------------------------------------------------------
# Inventar — Ist-Sprache je Modul
# ---------------------------------------------------------------------------

#: Atlas-``kind`` -> Sprache dieser Registry
_KIND_ZU_SPRACHE = {
    "python": "python",
    "rust-crate": "rust",
    "js-package": "js",
}

#: Dateiendung -> Sprache, fuer die Ebenen, die der Atlas nicht scannt
_ENDUNG_ZU_SPRACHE = {".s": "asm", ".c": "c", ".h": "c"}


def _kernel_dateien() -> List[Tuple[str, str]]:
    """(repo-relativer Pfad, Ist-Sprache) fuer die Kernel-Ebene.

    Der Dependency-Atlas kennt nur Python, Rust-Crates und JS-Pakete — die
    Assembly- und C-Ebene faellt bei ihm durch. Ohne diese Ergaenzung haette
    der Controller ausgerechnet ueber den Kern nichts zu sagen.
    """
    treffer: List[Tuple[str, str]] = []
    for basis in ("kernel", "src/normal_os/kernel"):
        wurzel = ROOT / basis
        if not wurzel.is_dir():
            continue
        for p in sorted(wurzel.rglob("*")):
            if not p.is_file():
                continue
            sprache = _ENDUNG_ZU_SPRACHE.get(p.suffix)
            if sprache:
                treffer.append((str(p.relative_to(ROOT)), sprache))
    return treffer


def _atlas_knoten() -> Tuple[List[Any], str]:
    """Knoten aus dem Dependency-Atlas holen. Fehlt er, ist das ein Befund."""
    try:
        from fusion_hero_os.core.dependency_atlas import build_atlas_cached

        atlas = build_atlas_cached()
        return list(atlas.nodes.values()), ""
    except Exception as exc:  # noqa: BLE001
        return [], f"{type(exc).__name__}: {str(exc)[:160]}"


def inventar() -> Dict[str, Any]:
    """Alle Module mit ihrer Ist-Sprache."""
    knoten, atlas_fehler = _atlas_knoten()
    module: List[Modul] = []

    for n in knoten:
        sprache = _KIND_ZU_SPRACHE.get(getattr(n, "kind", ""), getattr(n, "kind", "?"))
        module.append(
            Modul(
                name=getattr(n, "name", ""),
                pfad=getattr(n, "path", ""),
                layer=getattr(n, "layer", "unassigned"),
                ist=sprache,
            )
        )

    for pfad, sprache in _kernel_dateien():
        module.append(
            Modul(name=pfad, pfad=pfad, layer="kernel", ist=sprache)
        )

    return {
        "ok": not atlas_fehler,
        "atlas_fehler": atlas_fehler,
        "module": module,
    }


# ---------------------------------------------------------------------------
# Zuordnung — Soll-Sprache nach Regel
# ---------------------------------------------------------------------------


def _datei_text(pfad: str) -> Optional[str]:
    p = ROOT / pfad
    if not p.is_file():
        return None
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _datei_enthaelt(pfad: str, muster: Sequence[str]) -> bool:
    """Teilstring-Suche — fuer Referenzen, wo eine Erwaehnung genuegt."""
    text = _datei_text(pfad)
    return text is not None and any(m in text for m in muster)


def _datei_matcht(pfad: str, regexe: Sequence[str]) -> bool:
    """Zeilenverankerte Regex-Suche — fuer Code-Signale.

    Teilstrings taugen hier nicht: ein "@jit" in einer Beschriftung oder
    einem Kommentar ist kein heisser Pfad. Genau daran ist die Regel
    heisser_pfad schon einmal falsch angeschlagen.
    """
    text = _datei_text(pfad)
    if text is None:
        return False
    return any(re.search(rx, text, re.MULTILINE) for rx in regexe)


def zielsprache(m: Modul, regeln: Sequence[Dict[str, Any]]) -> Tuple[str, str, str, str]:
    """Erste passende Regel gewinnt. Liefert (soll, regel_id, signal, hinweis)."""
    for regel in regeln:
        prefixe = regel.get("pfad_prefix") or []
        if prefixe and not any(m.pfad.startswith(p) for p in prefixe):
            continue

        endungen = regel.get("endung") or []
        if endungen and not any(m.pfad.endswith(e) for e in endungen):
            continue

        kinds = regel.get("ist_kind") or []
        if kinds:
            # ist_kind zielt auf den Atlas-kind, nicht auf unsere Sprache
            rueck = {v: k for k, v in _KIND_ZU_SPRACHE.items()}
            if rueck.get(m.ist) not in kinds:
                continue

        muster = regel.get("enthaelt_muster") or []
        if muster and not _datei_enthaelt(m.pfad, muster):
            continue

        regexe = regel.get("enthaelt_regex") or []
        if regexe and not _datei_matcht(m.pfad, regexe):
            continue

        if (not (prefixe or endungen or kinds or muster or regexe)
                and regel.get("id") != "normalfall"):
            # Regel ohne jedes Kriterium waere ein stiller Auffangbecken —
            # nur der ausdrueckliche Normalfall darf das.
            continue

        return (
            str(regel.get("soll") or ""),
            str(regel.get("id") or ""),
            str(regel.get("signal") or "").strip(),
            str(regel.get("hinweis") or "").strip(),
        )
    return ("", "", "", "")


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def _render_markdown(r: Dict[str, Any]) -> str:
    z: List[str] = []
    z.append("# Sprachbindung — Ist gegen Soll")
    z.append("")
    z.append(f"Platform {r['platform_version']} · `python -m fusion_hero_os.core.translate_controller`")
    z.append("")
    z.append(f"**UTC:** {r['generated_at']}  ")
    z.append(
        f"**Module:** {r['counts']['module_gesamt']} · "
        f"**Abweichungen:** {r['counts']['abweichungen']} — davon "
        f"**{r['counts']['gebunden']} durch Bindung geschlossen**, "
        f"**{r['counts']['luecken']} offen**"
    )
    z.append("")
    z.append("Der Controller übersetzt nichts. Er ordnet zu und weist die Lücke aus.")
    z.append("")
    z.append(
        "Eine Abweichung ist nur dann Arbeit, wenn das Modul die Zielsprache "
        "nicht bereits über die vorgesehene Bindung aufruft."
    )
    z.append("")
    z.append("## Verteilung")
    z.append("")
    z.append("| Sprache | ist | soll |")
    z.append("|---|---:|---:|")
    for s in sorted(set(r["counts"]["ist"]) | set(r["counts"]["soll"])):
        z.append(f"| {s} | {r['counts']['ist'].get(s, 0)} | {r['counts']['soll'].get(s, 0)} |")
    z.append("")
    z.append("## Lücken")
    z.append("")
    if not r["luecken"]:
        z.append("Keine — jedes Modul liegt in seiner Zielsprache.")
    else:
        z.append("| Modul | ist | soll | Regel | Bindung |")
        z.append("|---|---|---|---|---|")
        for m in r["luecken"]:
            z.append(
                f"| `{m['pfad']}` | {m['ist']} | {m['soll']} | {m['regel']} | {m['bindung']} |"
            )
        z.append("")
        z.append("### Signale")
        z.append("")
        for rid, sig in sorted(r["signale"].items()):
            z.append(f"- **{rid}** — {sig}")
    z.append("")
    z.append("## Durch Bindung geschlossen")
    z.append("")
    if not r.get("durch_bindung_geschlossen"):
        z.append("Keine.")
    else:
        z.append("Diese Module weichen ab, rufen die Zielsprache aber bereits auf:")
        z.append("")
        z.append("| Modul | ist | soll | Bindung |")
        z.append("|---|---|---|---|")
        for m in r["durch_bindung_geschlossen"]:
            z.append(f"| `{m['pfad']}` | {m['ist']} | {m['soll']} | {m['bindung']} |")
    z.append("")
    z.append(f"**Geltung:** {r['geltung']}")
    z.append("")
    return "\n".join(z)


def report(*, schreiben: bool = True) -> Dict[str, Any]:
    """Ist gegen Soll fuer alle Module."""
    cfg = load_config()
    regeln = cfg.get("regeln") or []
    sprachen = cfg.get("sprachen") or {}
    bindungen = cfg.get("bindungen") or {}

    inv = inventar()
    module: List[Modul] = inv["module"]

    for m in module:
        soll, rid, signal, hinweis = zielsprache(m, regeln)
        m.soll, m.regel, m.signal, m.hinweis = soll, rid, signal, hinweis
        m.bindung = str((sprachen.get(soll) or {}).get("bindung") or "")
        if m.abweichung and m.bindung:
            erkennung = (bindungen.get(m.bindung) or {}).get("erkennung") or []
            m.gebunden = bool(erkennung) and _datei_enthaelt(m.pfad, erkennung)

    abweichungen = [m for m in module if m.abweichung]
    luecken = [m for m in module if m.luecke]
    gebunden = [m for m in abweichungen if m.gebunden]

    def _zaehl(attr: str) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for m in module:
            v = getattr(m, attr) or "?"
            out[v] = out.get(v, 0) + 1
        return dict(sorted(out.items(), key=lambda kv: -kv[1]))

    signale = {m.regel: m.signal for m in luecken if m.regel and m.signal}

    r: Dict[str, Any] = {
        "kind": "SPRACHBINDUNG",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "platform_version": str(cfg.get("platform_version") or "13.0.0"),
        "ok": bool(cfg) and inv["ok"],
        "config_ok": bool(cfg),
        "atlas_fehler": inv["atlas_fehler"],
        "uebersetzt_automatisch": False,
        "counts": {
            "module_gesamt": len(module),
            "abweichungen": len(abweichungen),
            "gebunden": len(gebunden),
            "luecken": len(luecken),
            "ist": _zaehl("ist"),
            "soll": _zaehl("soll"),
        },
        "luecken": [m.to_dict() for m in luecken],
        "durch_bindung_geschlossen": [m.to_dict() for m in gebunden],
        "signale": signale,
        "geltung": str(cfg.get("geltung") or "").strip()
        or "Ist = Satz · Soll = Spezifikation",
    }

    if schreiben:
        rep = cfg.get("report") or {}
        jp = ROOT / str(rep.get("json") or "docs/ops/SPRACHBINDUNG.latest.json")
        mp = ROOT / str(rep.get("markdown") or "docs/ops/SPRACHBINDUNG.md")
        jp.parent.mkdir(parents=True, exist_ok=True)
        jp.write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        mp.write_text(_render_markdown(r), encoding="utf-8")
        r["docs"] = str(jp.relative_to(ROOT))
        r["markdown"] = str(mp.relative_to(ROOT))

    return r


def status() -> Dict[str, Any]:
    cfg = load_config()
    return {
        "ok": True,
        "module": "translate_controller",
        "platform_version": str(cfg.get("platform_version") or "13.0.0"),
        "config": str(CONFIG.relative_to(ROOT)),
        "config_ok": bool(cfg),
        "sprachen": sorted((cfg.get("sprachen") or {}).keys()),
        "regeln": [str(x.get("id")) for x in (cfg.get("regeln") or [])],
        "uebersetzt_automatisch": False,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Translate-Controller — je Modul die optimale Sprache, Ist gegen Soll. "
        "Uebersetzt nichts; ordnet zu und weist die Luecke aus."
    )
    ap.add_argument("--status", action="store_true", help="nur Modul-Status")
    ap.add_argument("--json", action="store_true", help="vollen Report als JSON")
    ap.add_argument("--no-write", action="store_true", help="keine Report-Dateien schreiben")
    args = ap.parse_args(argv)

    if args.status:
        print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0

    r = report(schreiben=not args.no_write)
    if args.json:
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return 0 if r["ok"] else 1

    print(json.dumps({
        "ok": r["ok"],
        "counts": r["counts"],
        "uebersetzt_automatisch": r["uebersetzt_automatisch"],
        "docs": r.get("docs"),
    }, indent=2, ensure_ascii=False))

    if r["luecken"]:
        print(f"\n  Luecken ({len(r['luecken'])}) — Modul liegt nicht in seiner Zielsprache:")
        for m in r["luecken"][:20]:
            print(f"    {m['ist']:>6} -> {m['soll']:<6} {m['pfad']}  [{m['regel']}]")
        if len(r["luecken"]) > 20:
            print(f"    … {len(r['luecken']) - 20} weitere im Report")
    else:
        print("\n  Keine Luecken — jedes Modul liegt in seiner Zielsprache.")
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
