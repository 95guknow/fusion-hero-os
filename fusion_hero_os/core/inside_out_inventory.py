"""
Inside-Out Inventory — what EXISTS, independent of storage location.

Not outside-in (external map → fill holes). Inside-out:
  MasterSeed / public identity → core modules → engine → surfaces → docs →
  local vaults → skills → training → creative → ops manifests.

Every hit is recorded with path, size, mtime, ring (inside-out depth),
storage_root, and content class. Storage is metadata only — existence is primary.

Policy: pseudo_inhouse_only · freemium=false · deploy=private captures
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
UTC = timezone.utc  # py3.10+compat (was datetime.UTC)
from pathlib import Path
from typing import Any
from collections.abc import Iterable

ROOT = Path(__file__).resolve().parents[2]

__all__ = ["run_inventory", "status", "INSIDE_OUT_RINGS"]

# Inside-out rings (0 = innermost)
INSIDE_OUT_RINGS: list[dict[str, Any]] = [
    {
        "ring": 0,
        "name": "masterseed_identity",
        "desc": "Public MasterSeed display + VERSION + proof anchors",
        "globs_under_repo": [
            "VERSION",
            "proof_registry.yaml",
            "masterseed_public_display.yaml",
            "fusion_hero_os/core/heroic_core_orchestrator.py",
            "fusion_hero_os/core/masterseed_public.py",
            "fusion_hero_os/core/masterseed_vault.py",
            "fusion_hero_os/core/masterseed_sync.py",
            "docs/masterseed/**",
        ],
        "extra_roots": ["~/.fusion/masterseed"],
    },
    {
        "ring": 1,
        "name": "core_runtime",
        "desc": "fusion_hero_os.core + engine + registry",
        "globs_under_repo": [
            "fusion_hero_os/core/**",
            "fusion_hero_os/engine/**",
            "fusion_hero_os/registry.py",
            "fusion_hero_os/__init__.py",
            "fusion_hero_os/config.py",
        ],
        "extra_roots": [],
    },
    {
        "ring": 2,
        "name": "modules_method_meta",
        "desc": "modules, methodology, meta, providers, orchestration, mcp, bridge",
        "globs_under_repo": [
            "fusion_hero_os/modules/**",
            "fusion_hero_os/methodology/**",
            "fusion_hero_os/meta/**",
            "fusion_hero_os/providers/**",
            "fusion_hero_os/orchestration/**",
            "fusion_hero_os/mcp/**",
            "fusion_hero_os/bridge/**",
            "fusion_hero_os/integrations/**",
        ],
        "extra_roots": [],
    },
    {
        "ring": 3,
        "name": "surfaces_dashboard_llm",
        "desc": "Dashboard, llm_frameworks, scripts ops",
        "globs_under_repo": [
            "03_Code/Dashboard/**",
            "03_Code/llm_frameworks/**",
            "03_Code/training/**",
            "03_Code/internal_llm/**",
            "scripts/**",
            "hero-docs-server.py",
            "fusion_integration_hub.py",
        ],
        "extra_roots": [],
    },
    {
        "ring": 4,
        "name": "canon_configs_docs",
        "desc": "YAML canons, dissertation, kompendium, mesh docs, ops",
        "globs_under_repo": [
            "docs/**",
            "*.yaml",
            "*.yml",
            "BEST_VERSION.md",
            "README.md",
            "BRANCH_STRATEGY.md",
            "DEPLOYMENT_GUIDE.md",
            "tests/**",
        ],
        "extra_roots": [],
    },
    {
        "ring": 5,
        "name": "ascension_and_archive",
        "desc": "ascension_os, archives, books (existence, not import-all)",
        "globs_under_repo": [
            "ascension_os/**",
            "04_Buch_und_Archiv/**",
            "06_Master_Archive/**",
            "core/**",
            "kernel/**",
            "src/**",
            "artifacts/**",
            "infra/**",
        ],
        "extra_roots": [],
    },
    {
        "ring": 6,
        "name": "operator_local_state",
        "desc": "Local runtime state independent of git storage",
        "globs_under_repo": [],
        "extra_roots": [
            "~/.fusion",
            "~/.fusion-hero-os",
            "~/.grok/skills",
            "~/.grok/docs",
        ],
    },
]

SKIP_DIR_NAMES = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "target",
    "dist",
    "build",
    ".svelte-kit",
    ".pytest_cache",
    ".ruff_cache",
    "htmlcov",
}

# Still count existence of heavy dirs as one folder marker, don't walk every file
COLLAPSE_DIR_NAMES = {"node_modules", "target", ".git", "__pycache__", ".venv", "venv"}

MAX_FILES_PER_RING = 50000
MAX_FILE_BYTES_HASH = 2_000_000  # hash only smaller files fully


@dataclass
class Item:
    path: str
    storage_root: str
    ring: int
    ring_name: str
    kind: str  # file|dir_marker
    suffix: str
    bytes: int
    mtime: float
    sha16: str = ""
    class_hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _expand(p: str) -> Path:
    return Path(os.path.expanduser(p)).resolve()


def _class_hint(path: Path) -> str:
    s = path.suffix.lower()
    name = path.name.lower()
    if "masterseed" in name or "masterseed" in str(path).lower():
        return "masterseed"
    if s in {".py"}:
        return "python"
    if s in {".md", ".txt", ".rst"}:
        return "prose"
    if s in {".yaml", ".yml", ".toml", ".json"}:
        return "config"
    if s in {".pdf", ".docx"}:
        return "document"
    if s in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}:
        return "image"
    if s in {".mp4", ".webm", ".gif"} and "vid" in name:
        return "video"
    if s in {".jsonl"}:
        return "training"
    if s in {".gpg", ".shard.gpg"} or name.endswith(".shard.gpg"):
        return "private_shard"
    if s in {".ps1", ".sh", ".bat"}:
        return "script"
    return s.lstrip(".") or "other"


def _iter_files(base: Path, max_files: int) -> Iterable[Path]:
    if not base.exists():
        return
    n = 0
    if base.is_file():
        yield base
        return
    for dirpath, dirnames, filenames in os.walk(base):
        # prune skip/collapse dirs in place (os.walk honors dirnames mutation)
        for d in list(dirnames):
            if d in SKIP_DIR_NAMES or d in COLLAPSE_DIR_NAMES:
                # emit marker once
                marker = Path(dirpath) / d
                yield marker  # will be handled as dir
                dirnames.remove(d)
        for fn in filenames:
            if n >= max_files:
                return
            p = Path(dirpath) / fn
            n += 1
            yield p


def _match_repo_globs(repo: Path, patterns: list[str]) -> list[Path]:
    """Resolve repo-relative patterns; 'foo/**' means full tree under foo/."""
    out: list[Path] = []
    for pat in patterns:
        pat = pat.replace("\\", "/").strip()
        if not pat:
            continue
        # directory tree markers
        if pat.endswith("/**"):
            root = repo / pat[:-3]
            if root.exists():
                for p in _iter_files(root, MAX_FILES_PER_RING):
                    out.append(p)
            continue
        if pat.endswith("/"):
            root = repo / pat.rstrip("/")
            if root.exists():
                for p in _iter_files(root, MAX_FILES_PER_RING):
                    out.append(p)
            continue
        # single file or dir without **
        p = repo / pat
        if p.exists():
            if p.is_dir():
                for f in _iter_files(p, MAX_FILES_PER_RING):
                    out.append(f)
            else:
                out.append(p)
            continue
        # fallback glob
        try:
            out.extend(repo.glob(pat))
        except Exception:
            pass
    return out


def _record(
    path: Path,
    storage_root: str,
    ring: int,
    ring_name: str,
) -> Item | None:
    try:
        if path.is_dir():
            return Item(
                path=str(path),
                storage_root=storage_root,
                ring=ring,
                ring_name=ring_name,
                kind="dir_marker",
                suffix="",
                bytes=0,
                mtime=path.stat().st_mtime,
                class_hint="collapsed_dir",
            )
        st = path.stat()
        sha = ""
        if st.st_size <= MAX_FILE_BYTES_HASH and st.st_size > 0:
            try:
                h = hashlib.sha256()
                with path.open("rb") as f:
                    # sample first 64k for speed on medium files
                    chunk = f.read(65536)
                    h.update(chunk)
                    if st.st_size > 65536:
                        h.update(str(st.st_size).encode())
                        h.update(path.name.encode())
                sha = h.hexdigest()[:16]
            except Exception:
                sha = ""
        return Item(
            path=str(path),
            storage_root=storage_root,
            ring=ring,
            ring_name=ring_name,
            kind="file",
            suffix=path.suffix.lower(),
            bytes=int(st.st_size),
            mtime=float(st.st_mtime),
            sha16=sha,
            class_hint=_class_hint(path),
        )
    except OSError:
        return None


def run_inventory(*, write: bool = True) -> dict[str, Any]:
    t0 = time.time()
    seen: set[str] = set()
    items: list[Item] = []
    by_ring: dict[str, int] = defaultdict(int)
    by_class: dict[str, int] = defaultdict(int)
    by_storage: dict[str, int] = defaultdict(int)
    bytes_total = 0

    # Ring 0 special: always include live public MasterSeed view
    identity_block: dict[str, Any] = {}
    try:
        from fusion_hero_os.core.masterseed_public import public_view
        from fusion_hero_os.core.ops_vocabulary import status as ops_status

        identity_block["masterseed_public"] = public_view().to_dict()
        identity_block["ops_vocabulary"] = ops_status().get("vocabulary")
        identity_block["version_file"] = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    except Exception as e:  # noqa: BLE001
        identity_block["error"] = str(e)[:200]

    for ring_def in INSIDE_OUT_RINGS:
        ring = int(ring_def["ring"])
        rname = str(ring_def["name"])
        # repo globs
        for p in _match_repo_globs(ROOT, ring_def.get("globs_under_repo") or []):
            key = str(p.resolve()) if p.exists() else str(p)
            if key in seen:
                continue
            seen.add(key)
            it = _record(p, "repo:" + str(ROOT), ring, rname)
            if it:
                items.append(it)
                by_ring[rname] += 1
                by_class[it.class_hint] += 1
                by_storage["repo"] += 1
                bytes_total += it.bytes
        # extra roots (local)
        for er in ring_def.get("extra_roots") or []:
            base = _expand(er)
            label = f"local:{er}"
            if not base.exists():
                continue
            for p in _iter_files(base, MAX_FILES_PER_RING):
                try:
                    key = str(p.resolve())
                except Exception:
                    key = str(p)
                if key in seen:
                    continue
                seen.add(key)
                it = _record(p, label, ring, rname)
                if it:
                    items.append(it)
                    by_ring[rname] += 1
                    by_class[it.class_hint] += 1
                    by_storage[label] += 1
                    bytes_total += it.bytes

    # Sort inside-out then by path
    items.sort(key=lambda x: (x.ring, x.path))

    # Completeness heuristics (what rings have content)
    rings_nonempty = [r["name"] for r in INSIDE_OUT_RINGS if by_ring.get(r["name"], 0) > 0]

    report = {
        "ok": True,
        "method": "inside_out",
        "not": "outside_in",
        "principle": "inventory what exists; storage location is metadata only",
        "platform": "10.0.0",
        "policy": "pseudo_inhouse_only",
        "freemium": False,
        "generated_at": datetime.now(UTC).isoformat(),
        "duration_sec": round(time.time() - t0, 2),
        "identity": identity_block,
        "counts": {
            "items": len(items),
            "files": sum(1 for i in items if i.kind == "file"),
            "dir_markers": sum(1 for i in items if i.kind == "dir_marker"),
            "bytes_total": bytes_total,
            "by_ring": dict(by_ring),
            "by_class": dict(sorted(by_class.items(), key=lambda kv: -kv[1])),
            "by_storage": dict(by_storage),
        },
        "rings": INSIDE_OUT_RINGS,
        "rings_nonempty": rings_nonempty,
        "vocabulary": {
            "deploy": "private",
            "push": "public",
            "merge": "both_via_timeline",
        },
    }

    if write:
        out_dir = Path.home() / ".fusion" / "inventory" / "inside_out"
        out_dir.mkdir(parents=True, exist_ok=True)
        full_path = out_dir / "inventory_full.jsonl"
        with full_path.open("w", encoding="utf-8") as f:
            for it in items:
                f.write(json.dumps(it.to_dict(), ensure_ascii=False) + "\n")
        summary_path = out_dir / "inventory_summary.json"
        # sample paths per ring (not full dump in summary)
        samples: dict[str, list[str]] = defaultdict(list)
        for it in items:
            if len(samples[it.ring_name]) < 15 and it.kind == "file":
                samples[it.ring_name].append(it.path)
        report["sample_paths_by_ring"] = dict(samples)
        report["paths"] = {
            "full_jsonl": str(full_path),
            "summary": str(summary_path),
        }
        summary_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

        # docs mirror (summary only — may be large but ok)
        docs = ROOT / "docs" / "inventory"
        docs.mkdir(parents=True, exist_ok=True)
        # strip sample absolute paths slightly for public push safety? keep relative where possible
        pub = dict(report)
        pub["sample_paths_by_ring"] = {
            k: [p.replace(str(ROOT), "REPO").replace(str(Path.home()), "~") for p in v]
            for k, v in (report.get("sample_paths_by_ring") or {}).items()
        }
        (docs / "inside_out_inventory.latest.json").write_text(
            json.dumps(pub, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        # human markdown
        md_lines = [
            "# Inside-Out Inventory — what exists",
            "",
            f"**Generated:** {report['generated_at']}",
            "**Method:** inside-out (not outside-in)",
            f"**Items:** {report['counts']['items']} · **Files:** {report['counts']['files']} · **Bytes:** {bytes_total}",
            "",
            "## Identity (innermost)",
            "",
            "```json",
            json.dumps(identity_block, indent=2, ensure_ascii=False)[:2000],
            "```",
            "",
            "## Counts by ring (inside → out)",
            "",
        ]
        for r in INSIDE_OUT_RINGS:
            name = r["name"]
            md_lines.append(f"- **R{r['ring']} {name}**: {by_ring.get(name, 0)} — {r['desc']}")
        md_lines += ["", "## Counts by class", ""]
        for k, v in list(report["counts"]["by_class"].items())[:40]:
            md_lines.append(f"- `{k}`: {v}")
        md_lines += [
            "",
            "## Full JSONL (private operator path)",
            "",
            f"`{full_path}`",
            "",
            "Storage location is metadata only; this inventory answers *what is there*.",
        ]
        (docs / "INSIDE_OUT_INVENTORY.md").write_text("\n".join(md_lines), encoding="utf-8")
        report["paths"]["docs_md"] = str(docs / "INSIDE_OUT_INVENTORY.md")
        report["paths"]["docs_json"] = str(docs / "inside_out_inventory.latest.json")

        # coordination
        coord = Path.home() / ".fusion" / "mesh" / "coordination"
        coord.mkdir(parents=True, exist_ok=True)
        (coord / "inside_out_inventory_latest.json").write_text(
            json.dumps(
                {
                    "generated_at": report["generated_at"],
                    "counts": report["counts"],
                    "identity": identity_block,
                    "paths": report.get("paths"),
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    return report


def status() -> dict[str, Any]:
    p = Path.home() / ".fusion" / "inventory" / "inside_out" / "inventory_summary.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"ok": False, "error": "no inventory yet — run run_inventory()"}


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Inside-out inventory of everything that exists")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()
    if args.status:
        print(json.dumps(status(), indent=2, ensure_ascii=False)[:5000])
        return 0
    r = run_inventory(write=not args.dry)
    # compact stdout
    compact = {
        "ok": r.get("ok"),
        "method": r.get("method"),
        "counts": r.get("counts"),
        "identity": r.get("identity"),
        "paths": r.get("paths"),
        "duration_sec": r.get("duration_sec"),
    }
    print(json.dumps(compact, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
