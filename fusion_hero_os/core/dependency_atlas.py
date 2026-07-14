# -*- coding: utf-8 -*-
"""Fusion Hero OS — Dependency Atlas (polyglotte Fraktal-Layer-Architektur als Code).

Leitet den tatsaechlichen Abhaengigkeitsgraphen des Repos maschinell aus dem
Code ab — statt ihn in Prosa zu behaupten. Polyglott: Python (AST-Imports),
Rust (Cargo.toml der Crates), JS/Svelte (package.json). Jeder Knoten wird
einem Layer aus fusion_unified.yaml zugeordnet (Fraktal-Layer-Mapping per
Longest-Prefix auf die dort deklarierten module/config-Pfade).

Epistemik statt Behauptung — der Atlas misst drei Arten epistemischer Schuld:
  1. UNRESOLVED: gerootete interne Imports (fusion_hero_os.*, ascension_os.*)
     und relative Imports, deren Ziel im Dateisystem nicht existiert.
     Das sind Platzhalter auf Dependency-Ebene -> FATAL im --check.
  2. CYCLES: Import-Zyklen auf Modulebene (Tarjan-SCC) ueber Top-Level-Kanten.
     Funktions-lokale (deferred) Imports zaehlen nicht als Zykluskante, werden
     aber als 'deferred' ausgewiesen.
  3. PLACEHOLDER-MARKER: ehrlich markierte Stubs im Quelltext, gezaehlt je
     Datei. Nicht fatal (bewusste Offline-Stubs sind Repo-Kultur), aber
     quantifiziert, damit Abbau messbar ist.

Nutzung:
    python -m fusion_hero_os.core.dependency_atlas            # Zusammenfassung
    python -m fusion_hero_os.core.dependency_atlas --check    # CI-Gate (exit 1 bei UNRESOLVED/CYCLES)
    python -m fusion_hero_os.core.dependency_atlas --write    # JSON + Mermaid nach docs/02_architecture/
    python -m fusion_hero_os.core.dependency_atlas --json     # Voll-JSON nach stdout
"""

from __future__ import annotations

import ast
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]

# Aktive Code-Wurzeln. legacy_sources/ sind kuratierte Fremd-Snapshots
# (siehe legacy_sources/IMPORT_MANIFEST.md) und bewusst NICHT Teil des Atlas.
PYTHON_ROOTS = (
    "fusion_hero_os",
    "ascension_os",
    "core",
    "kernel",
    "src",
    "tests",
    "tools",
    "scripts",
    "03_Code",
)
EXCLUDED_DIR_NAMES = {
    "__pycache__", "node_modules", ".git", ".svelte-kit", "legacy_sources",
    "target", "dist", "build", ".venv",
}

# Gerootete interne Namensraeume: fuer diese ist eine fehlgeschlagene
# Aufloesung ein harter Befund (UNRESOLVED), kein Rauschen.
ROOTED_INTERNAL = ("fusion_hero_os", "ascension_os")

# Bekannte, dokumentierte Zyklen (Paare von Modulnamen, richtungslos).
# Leer = Ziel; Eintraege hier MUESSEN einen Kommentar mit Grund tragen.
CYCLE_WHITELIST: Set[frozenset] = set()

# Marker fuer ehrlich deklarierte Stubs (Repo-Kultur: Code-Honesty).
# Zusammengesetzt, damit der Atlas sich nicht selbst als Treffer zaehlt.
_PLACEHOLDER_PATTERN = re.compile(
    "|".join([
        "PLATZ" + "HALTER",
        "place" + "holder",
        "offline-" + "stub",
        "not " + "implemented",
        "noch nicht " + "implementiert",
        "NICHT " + "implementiert",
    ]),
    re.IGNORECASE,
)

_STDLIB = set(getattr(sys, "stdlib_module_names", ())) | {"__future__"}


@dataclass
class Node:
    name: str                 # kanonischer Modulname (dotted) bzw. Crate-/Paketname
    path: str                 # repo-relativer Pfad
    kind: str                 # python | rust-crate | js-package
    layer: str = "unassigned"
    placeholder_markers: int = 0


@dataclass
class Edge:
    src: str
    dst: str
    deferred: bool = False    # Import innerhalb einer Funktion/Methode
    resolved_by: str = "path"  # path | basename | manifest


@dataclass
class Atlas:
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    external: Dict[str, int] = field(default_factory=dict)   # externer Import -> Nutzungen
    unresolved: List[Dict[str, str]] = field(default_factory=list)
    cycles: List[List[str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_from": "fusion_hero_os.core.dependency_atlas",
            "nodes": [vars(n) for n in self.nodes.values()],
            "edges": [vars(e) for e in self.edges],
            "external_dependencies": dict(sorted(self.external.items(), key=lambda kv: -kv[1])),
            "unresolved_imports": list(self.unresolved),
            "cycles": [list(c) for c in self.cycles],
            "epistemik": self.epistemik_summary(),
        }

    def epistemik_summary(self) -> Dict[str, Any]:
        marked = sorted(
            ((n.path, n.placeholder_markers) for n in self.nodes.values() if n.placeholder_markers),
            key=lambda kv: -kv[1],
        )
        return {
            "unresolved_count": len(self.unresolved),
            "cycle_count": len(self.cycles),
            "placeholder_marker_total": sum(m for _, m in marked),
            "files_with_markers": len(marked),
            "top_marker_files": [{"path": p, "markers": m} for p, m in marked[:10]],
        }


# ---------------------------------------------------------------------------
# Layer-Mapping (Fraktal-Layer aus fusion_unified.yaml, Longest-Prefix)
# ---------------------------------------------------------------------------

# Fallback fuer Pfade, die fusion_unified.yaml keinem Layer zuweist.
# Bewusst grob: lieber ehrlich 'unassigned' als falsch einsortiert.
_FALLBACK_PREFIXES: List[Tuple[str, str]] = [
    ("fusion_hero_os/engine", "mainframe"),
    ("fusion_hero_os/providers", "intelligence"),
    ("fusion_hero_os/core", "knowledge"),
    ("fusion_hero_os", "mainframe"),
    ("03_Code/Dashboard", "surface"),
    ("03_Code/heroic-highest-layer", "vr"),
    ("03_Code/llm_frameworks", "orchestration"),
    ("03_Code", "suite"),
    ("core", "knowledge"),
    ("kernel", "kernel"),
    ("src", "surface"),
    ("tests", "proof"),
    ("tools", "tooling"),
    ("scripts", "tooling"),
    ("rust_engine_crate", "mainframe"),
    ("pms_rust_kernel_crate", "knowledge"),
    ("package.json", "surface"),
]


def _layer_prefixes_from_unified() -> List[Tuple[str, str]]:
    """Leitet (pfad-prefix -> layer) aus fusion_unified.yaml layers ab."""
    prefixes: List[Tuple[str, str]] = []
    try:
        import yaml
        data = yaml.safe_load((REPO_ROOT / "fusion_unified.yaml").read_text(encoding="utf-8"))
    except Exception:
        return prefixes
    layers = (data or {}).get("layers") or {}
    for layer_name, spec in layers.items():
        if not isinstance(spec, dict):
            continue
        candidates: List[str] = []
        module = spec.get("module") or ""
        if isinstance(module, str) and module and module not in ("docs-only",):
            candidates.append(module.replace(".", "/"))
            candidates.append(module)
        config = spec.get("config")
        for c in (config if isinstance(config, list) else [config]):
            if isinstance(c, str) and c:
                candidates.append(c.rstrip("/"))
        for cand in candidates:
            cand = cand.strip().rstrip("/")
            if cand:
                prefixes.append((cand, layer_name))
    # Laengste Prefixe zuerst -> Longest-Prefix-Match per erster Treffer
    prefixes.sort(key=lambda kv: -len(kv[0]))
    return prefixes


def assign_layer(rel_path: str, unified_prefixes: List[Tuple[str, str]]) -> str:
    p = rel_path.replace("\\", "/")
    for prefix, layer in unified_prefixes:
        norm = prefix.replace("\\", "/")
        if p == norm or p.startswith(norm + "/") or p.startswith(norm + "."):
            return layer
    for prefix, layer in _FALLBACK_PREFIXES:
        if p == prefix or p.startswith(prefix + "/"):
            return layer
    return "unassigned"


# ---------------------------------------------------------------------------
# Python-Scan (AST)
# ---------------------------------------------------------------------------

def _iter_python_files(root: Path) -> Iterator[Path]:
    for path in sorted(root.rglob("*.py")):
        if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
            continue
        yield path


def _module_name(py_path: Path) -> str:
    rel = py_path.relative_to(REPO_ROOT)
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1][:-3]
    return ".".join(parts)


def _top_level_imports(tree: ast.AST) -> Iterator[Tuple[ast.AST, bool]]:
    """Liefert (Import-Node, deferred). deferred = nicht auf Modulebene."""
    top_level_ids = {id(n) for n in ast.iter_child_nodes(tree)}
    # try/except auf Modulebene zaehlt als top-level (Repo-Muster fuer
    # optionale Dependencies)
    for child in ast.iter_child_nodes(tree):
        if isinstance(child, ast.Try):
            for sub in ast.walk(child):
                if isinstance(sub, (ast.Import, ast.ImportFrom)):
                    top_level_ids.add(id(sub))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            yield node, id(node) not in top_level_ids


def _resolve_absolute(target: str) -> Optional[Path]:
    base = REPO_ROOT / Path(target.replace(".", "/"))
    for cand in (base.with_suffix(".py"), base / "__init__.py"):
        if cand.is_file():
            return cand
    return None


def _resolve_relative(src_file: Path, level: int, module: str) -> Optional[Path]:
    pkg_dir = src_file.parent
    for _ in range(level - 1):
        pkg_dir = pkg_dir.parent
    base = pkg_dir / Path(module.replace(".", "/")) if module else pkg_dir
    for cand in (base.with_suffix(".py"), base / "__init__.py"):
        if cand.is_file():
            return cand
    return None


def scan_python(atlas: Atlas, unified_prefixes: List[Tuple[str, str]]) -> None:
    basename_index: Dict[str, List[Path]] = {}
    files: List[Path] = []
    for root_name in PYTHON_ROOTS:
        root = REPO_ROOT / root_name
        if not root.is_dir():
            continue
        for f in _iter_python_files(root):
            files.append(f)
            basename_index.setdefault(f.stem, []).append(f)

    for f in files:
        rel = str(f.relative_to(REPO_ROOT)).replace("\\", "/")
        name = _module_name(f)
        try:
            text = f.read_text(encoding="utf-8-sig", errors="replace")
            tree = ast.parse(text)
        except SyntaxError as e:
            atlas.unresolved.append({"src": rel, "target": f"<Syntaxfehler: {e.msg} Zeile {e.lineno}>",
                                     "kind": "syntax-error"})
            continue
        atlas.nodes[name] = Node(
            name=name, path=rel, kind="python",
            layer=assign_layer(rel, unified_prefixes),
            placeholder_markers=len(_PLACEHOLDER_PATTERN.findall(text)),
        )
        for node, deferred in _top_level_imports(tree):
            if isinstance(node, ast.Import):
                targets = [(a.name, 0, None) for a in node.names]
            elif node.level and not node.module:
                # `from . import a, b`: jeder Name ist potenziell ein Submodul —
                # auf das Submodul aufloesen, NICHT aufs Paket-__init__ (sonst
                # entstehen falsche __init__<->Submodul-Zyklen).
                targets = [("", node.level, a.name) for a in node.names]
            else:
                targets = [((node.module or ""), node.level, None)]
            for target, level, sub_name in targets:
                if level:  # relativer Import
                    resolved = None
                    if sub_name:
                        resolved = _resolve_relative(f, level, sub_name)
                    if resolved is None:
                        resolved = _resolve_relative(f, level, target)
                    if resolved is None:
                        atlas.unresolved.append({"src": rel,
                                                 "target": "." * level + (sub_name or target),
                                                 "kind": "relative"})
                    else:
                        atlas.edges.append(Edge(name, _module_name(resolved), deferred))
                    continue
                top = target.split(".")[0]
                if top in _STDLIB:
                    continue
                if target.startswith(ROOTED_INTERNAL):
                    resolved = _resolve_absolute(target)
                    if resolved is None:
                        # from paket import name: auch paket/__init__.py mit Attribut zaehlt
                        parent = _resolve_absolute(target.rsplit(".", 1)[0]) if "." in target else None
                        if parent is None:
                            atlas.unresolved.append({"src": rel, "target": target, "kind": "rooted"})
                            continue
                        resolved = parent
                    atlas.edges.append(Edge(name, _module_name(resolved), deferred))
                elif top in basename_index:
                    # 03_Code-Muster: sys.path-Insert + flacher Import.
                    # Best-effort-Kante, nie fatal.
                    resolved = min(basename_index[top], key=lambda p: len(p.parts))
                    atlas.edges.append(Edge(name, _module_name(resolved), deferred, "basename"))
                else:
                    atlas.external[top] = atlas.external.get(top, 0) + 1


# ---------------------------------------------------------------------------
# Rust- und JS-Scan (Manifeste)
# ---------------------------------------------------------------------------

def _parse_cargo_dependencies(cargo_toml: Path) -> List[str]:
    try:
        import tomllib
        data = tomllib.loads(cargo_toml.read_text(encoding="utf-8"))
        return list((data.get("dependencies") or {}).keys())
    except Exception:
        deps, in_deps = [], False
        for line in cargo_toml.read_text(encoding="utf-8", errors="replace").splitlines():
            s = line.strip()
            if s.startswith("["):
                in_deps = s == "[dependencies]"
            elif in_deps and "=" in s and not s.startswith("#"):
                deps.append(s.split("=", 1)[0].strip())
        return deps


def scan_rust(atlas: Atlas, unified_prefixes: List[Tuple[str, str]]) -> None:
    for crate_dir in ("rust_engine_crate", "pms_rust_kernel_crate"):
        cargo = REPO_ROOT / crate_dir / "Cargo.toml"
        if not cargo.is_file():
            continue
        rel = f"{crate_dir}/Cargo.toml"
        atlas.nodes[crate_dir] = Node(
            name=crate_dir, path=rel, kind="rust-crate",
            layer=assign_layer(crate_dir, unified_prefixes),
        )
        for dep in _parse_cargo_dependencies(cargo):
            atlas.external[f"crates.io:{dep}"] = atlas.external.get(f"crates.io:{dep}", 0) + 1


def scan_js(atlas: Atlas, unified_prefixes: List[Tuple[str, str]]) -> None:
    pkg = REPO_ROOT / "package.json"
    if not pkg.is_file():
        return
    try:
        data = json.loads(pkg.read_text(encoding="utf-8"))
    except Exception:
        return
    name = data.get("name", "js-app")
    atlas.nodes[name] = Node(name=name, path="package.json", kind="js-package",
                             layer=assign_layer("package.json", unified_prefixes))
    for section in ("dependencies", "devDependencies"):
        for dep in (data.get(section) or {}):
            atlas.external[f"npm:{dep}"] = atlas.external.get(f"npm:{dep}", 0) + 1


# ---------------------------------------------------------------------------
# Analyse
# ---------------------------------------------------------------------------

def find_cycles(atlas: Atlas) -> List[List[str]]:
    """Tarjan-SCC ueber Top-Level-Kanten; SCCs > 1 = echte Import-Zyklen."""
    graph: Dict[str, Set[str]] = {}
    for e in atlas.edges:
        if e.deferred:
            continue
        graph.setdefault(e.src, set()).add(e.dst)
        graph.setdefault(e.dst, set())

    index_counter = [0]
    index: Dict[str, int] = {}
    lowlink: Dict[str, int] = {}
    on_stack: Set[str] = set()
    stack: List[str] = []
    sccs: List[List[str]] = []

    def strongconnect(v: str) -> None:
        index[v] = lowlink[v] = index_counter[0]
        index_counter[0] += 1
        stack.append(v)
        on_stack.add(v)
        for w in graph.get(v, ()):
            if w not in index:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif w in on_stack:
                lowlink[v] = min(lowlink[v], index[w])
        if lowlink[v] == index[v]:
            scc = []
            while True:
                w = stack.pop()
                on_stack.discard(w)
                scc.append(w)
                if w == v:
                    break
            if len(scc) > 1:
                sccs.append(sorted(scc))

    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old_limit, len(graph) * 2 + 1000))
    try:
        for v in sorted(graph):
            if v not in index:
                strongconnect(v)
    finally:
        sys.setrecursionlimit(old_limit)

    return [scc for scc in sccs
            if not any(frozenset(pair) in CYCLE_WHITELIST
                       for pair in zip(scc, scc[1:] + scc[:1]))]


def build_atlas() -> Atlas:
    atlas = Atlas()
    unified_prefixes = _layer_prefixes_cached()
    scan_python(atlas, unified_prefixes)
    scan_rust(atlas, unified_prefixes)
    scan_js(atlas, unified_prefixes)
    atlas.cycles = find_cycles(atlas)
    return atlas


# ---------------------------------------------------------------------------
# Quanten-Wörterbuch-Anbindung (zentrale Memoisierung, mtime-invalidiert)
# ---------------------------------------------------------------------------

def _repo_state_signature() -> str:
    """Billige Zustands-Signatur des gescannten Codes: Anzahl + max-mtime.

    os.stat je Datei ist um Groessenordnungen billiger als read+ast.parse;
    aendert sich irgendeine gescannte Datei (oder kommt eine hinzu/weg),
    aendert sich die Signatur -> Wörterbuch invalidiert den Atlas-Eintrag.
    """
    count, max_mtime = 0, 0.0
    for root_name in PYTHON_ROOTS:
        root = REPO_ROOT / root_name
        if not root.is_dir():
            continue
        for f in _iter_python_files(root):
            count += 1
            mt = f.stat().st_mtime
            if mt > max_mtime:
                max_mtime = mt
    for extra in ("fusion_unified.yaml", "package.json",
                  "rust_engine_crate/Cargo.toml", "pms_rust_kernel_crate/Cargo.toml"):
        p = REPO_ROOT / extra
        if p.is_file():
            count += 1
            max_mtime = max(max_mtime, p.stat().st_mtime)
    return f"{count}:{max_mtime:.6f}"


def _layer_prefixes_cached() -> List[Tuple[str, str]]:
    """Layer-Prefixe aus fusion_unified.yaml, memoisiert auf dessen mtime."""
    try:
        from fusion_hero_os.core.quantum_dictionaries import get_quantum_dictionary
    except Exception:
        return _layer_prefixes_from_unified()
    cfg = REPO_ROOT / "fusion_unified.yaml"
    sig = str(cfg.stat().st_mtime) if cfg.is_file() else "missing"
    qd = get_quantum_dictionary("layer-prefixes")
    return qd.get_or_compute("fusion_unified.layers", _layer_prefixes_from_unified,
                             signature=sig)


def build_atlas_cached() -> Atlas:
    """Wie build_atlas(), aber ueber das zentrale Quanten-Wörterbuch.

    Neu gescannt wird nur, wenn sich der Repo-Zustand (Signatur) geaendert
    hat — das macht wiederholte Dashboard-Aufrufe (/architecture,
    /api/architecture/atlas) praktisch kostenlos.
    """
    try:
        from fusion_hero_os.core.quantum_dictionaries import get_quantum_dictionary
    except Exception:
        return build_atlas()
    qd = get_quantum_dictionary("dependency-atlas", max_entries=4)
    return qd.get_or_compute("repo-atlas", build_atlas, signature=_repo_state_signature())


# ---------------------------------------------------------------------------
# Ausgabe: Mermaid (Layer-geclustert, auf Paketebene aggregiert)
# ---------------------------------------------------------------------------

def _package_key(node: Node) -> str:
    parts = node.path.replace("\\", "/").split("/")
    return "/".join(parts[:2]) if len(parts) > 1 else parts[0]


def render_mermaid(atlas: Atlas) -> str:
    pkg_layer: Dict[str, str] = {}
    node_pkg: Dict[str, str] = {}
    for n in atlas.nodes.values():
        pkg = _package_key(n)
        node_pkg[n.name] = pkg
        pkg_layer.setdefault(pkg, n.layer)

    agg_edges: Set[Tuple[str, str]] = set()
    for e in atlas.edges:
        s, d = node_pkg.get(e.src), node_pkg.get(e.dst)
        if s and d and s != d:
            agg_edges.add((s, d))

    def nid(pkg: str) -> str:
        return re.sub(r"[^A-Za-z0-9_]", "_", pkg)

    by_layer: Dict[str, List[str]] = {}
    for pkg, layer in pkg_layer.items():
        by_layer.setdefault(layer, []).append(pkg)

    lines = ["```mermaid", "graph TD"]
    for layer in sorted(by_layer):
        lines.append(f'  subgraph L_{nid(layer)}["Layer: {layer}"]')
        for pkg in sorted(by_layer[layer]):
            lines.append(f'    {nid(pkg)}["{pkg}"]')
        lines.append("  end")
    for s, d in sorted(agg_edges):
        lines.append(f"  {nid(s)} --> {nid(d)}")
    lines.append("```")
    return "\n".join(lines)


def render_markdown(atlas: Atlas) -> str:
    epi = atlas.epistemik_summary()
    ext_top = list(atlas.to_dict()["external_dependencies"].items())[:15]
    md = [
        "# Dependency Atlas — maschinell abgeleitet",
        "",
        "**Nicht von Hand pflegen.** Erzeugt durch",
        "`python -m fusion_hero_os.core.dependency_atlas --write`;",
        "Vollgraph in `dependency_atlas.json`. CI-Gate: `--check`",
        "(fatal bei unaufgeloesten gerooteten Imports und neuen Import-Zyklen).",
        "",
        f"- Knoten: **{len(atlas.nodes)}** (Python-Module, Rust-Crates, JS-Paket)",
        f"- Kanten: **{len(atlas.edges)}** (davon deferred: {sum(1 for e in atlas.edges if e.deferred)})",
        f"- Unaufgeloeste gerootete Imports: **{epi['unresolved_count']}**",
        f"- Import-Zyklen (top-level): **{epi['cycle_count']}**",
        f"- Platzhalter-Marker: **{epi['placeholder_marker_total']}** in {epi['files_with_markers']} Dateien",
        "",
        "## Layer-Graph (Paketebene)",
        "",
        render_mermaid(atlas),
        "",
        "## Externe Abhaengigkeiten (Top 15 nach Nutzung)",
        "",
        "| Abhaengigkeit | Nutzungen |",
        "|---------------|-----------|",
    ]
    md += [f"| `{dep}` | {count} |" for dep, count in ext_top]
    md += [
        "",
        "## Epistemische Schuld — Top-Dateien mit Platzhalter-Markern",
        "",
        "| Datei | Marker |",
        "|-------|--------|",
    ]
    md += [f"| `{item['path']}` | {item['markers']} |" for item in epi["top_marker_files"]]
    if atlas.cycles:
        md += ["", "## Import-Zyklen", ""]
        md += [f"- {' -> '.join(c)}" for c in atlas.cycles]
    if atlas.unresolved:
        md += ["", "## Unaufgeloeste Imports", ""]
        md += [f"- `{u['src']}` -> `{u['target']}` ({u['kind']})" for u in atlas.unresolved]
    md.append("")
    return "\n".join(md)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Fusion Hero OS Dependency Atlas")
    parser.add_argument("--check", action="store_true",
                        help="CI-Gate: exit 1 bei unaufgeloesten Imports oder Zyklen")
    parser.add_argument("--write", action="store_true",
                        help="JSON + Mermaid nach docs/02_architecture/ schreiben")
    parser.add_argument("--json", action="store_true", help="Voll-JSON nach stdout")
    args = parser.parse_args(argv)

    atlas = build_atlas()
    epi = atlas.epistemik_summary()

    if args.json:
        print(json.dumps(atlas.to_dict(), indent=2, ensure_ascii=False))
        return 0

    if args.write:
        out_dir = REPO_ROOT / "docs" / "02_architecture"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "dependency_atlas.json").write_text(
            json.dumps(atlas.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (out_dir / "DEPENDENCY_ATLAS.md").write_text(render_markdown(atlas), encoding="utf-8")
        print(f"[Atlas] geschrieben: {out_dir / 'dependency_atlas.json'}")
        print(f"[Atlas] geschrieben: {out_dir / 'DEPENDENCY_ATLAS.md'}")

    print(f"[Atlas] Knoten={len(atlas.nodes)} Kanten={len(atlas.edges)} "
          f"unresolved={epi['unresolved_count']} zyklen={epi['cycle_count']} "
          f"platzhalter-marker={epi['placeholder_marker_total']}")

    if args.check:
        failed = False
        for u in atlas.unresolved:
            print(f"[Atlas][FATAL] unaufgeloester Import: {u['src']} -> {u['target']} ({u['kind']})")
            failed = True
        for c in atlas.cycles:
            print(f"[Atlas][FATAL] Import-Zyklus: {' -> '.join(c)}")
            failed = True
        if failed:
            return 1
        print("[Atlas] --check bestanden: keine unaufgeloesten Imports, keine Zyklen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
