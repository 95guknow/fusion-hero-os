#!/usr/bin/env python3
"""Apply cherry-picks from legacy_sources into canonical fusion-hero-os paths."""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEGACY = REPO / "legacy_sources"
LOG_PATH = REPO / "docs" / "v8" / "CHERRY_PICK_LOG.md"

SKIP_NAMES = {
    "token.txt", "header.txt", "body.json", ".git", "__pycache__",
}
SKIP_SUFFIX = {".pyc", ".pyo", ".gguf"}
SKIP_GLOBS = {"**/.~lock.*"}


def should_skip(path: Path) -> bool:
    if path.name in SKIP_NAMES:
        return True
    if path.suffix.lower() in SKIP_SUFFIX:
        return True
    for pat in SKIP_GLOBS:
        if path.match(pat):
            return True
    return False


def copy_tree(src: Path, dst: Path, log: list[dict]) -> int:
    count = 0
    if not src.exists():
        return 0
    for item in src.rglob("*"):
        if item.is_dir():
            continue
        rel = item.relative_to(src)
        if any(p in SKIP_NAMES for p in rel.parts):
            continue
        if should_skip(item):
            continue
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        log.append({"action": "copy", "from": str(item), "to": str(target)})
        count += 1
    return count


def copy_file(src: Path, dst: Path, log: list[dict]) -> bool:
    if not src.exists() or should_skip(src):
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    log.append({"action": "copy", "from": str(src), "to": str(dst)})
    return True


def main() -> None:
    log: list[dict] = []
    stats: dict[str, int] = {}

    # 1) Private suite → 03_Code/suite/
    suite_src = LEGACY / "private-hacking-suite"
    suite_dst = REPO / "03_Code" / "suite"
    for folder in (
        "audio-bridge", "layers", "ghosthunting", "fusion", "gpu",
        "qubo", "tools", "tests", "launchers", "scripts",
    ):
        n = copy_tree(suite_src / folder, suite_dst / folder, log)
        stats[f"suite/{folder}"] = n
    for fname in ("launcher.py", "process_layers.py", "requirements.txt"):
        if copy_file(suite_src / fname, suite_dst / fname, log):
            stats[f"suite/{fname}"] = 1

    # 2) Dashboard legacy UI
    dash_legacy = LEGACY / "dashboard"
    dash_dst = REPO / "03_Code" / "Dashboard"
    for rel in (
        "templates/heroic.html",
        "templates/about.html",
        "static/donation.html",
        "static/wallet.json",
        ".env.example",
    ):
        if copy_file(dash_legacy / rel, dash_dst / rel, log):
            stats[f"dashboard/{rel}"] = 1

    # 3) v1 seeds + concepts
    seeds_dst = REPO / "docs" / "v8" / "seeds"
    mapping = {
        LEGACY / "fusion-hero-os-v1" / "asr" / "optimized_prompt.txt": seeds_dst / "asr_optimized_prompt.txt",
        LEGACY / "fusion-hero-os-v1" / "manifest" / "heroic_space.md": seeds_dst / "heroic_space.md",
        LEGACY / "fusion-hero-os-v1" / "core" / "master_core.md": seeds_dst / "master_core.md",
        LEGACY / "fusion-hero-os-v1" / "qubo" / "asr_turntaking.md": seeds_dst / "asr_turntaking.md",
        LEGACY / "alte-frau-95g-heroic-core" / "concepts" / "Ungueltig_Anti-Agent.md": REPO / "docs" / "v8" / "concepts" / "Ungueltig_Anti-Agent.md",
        LEGACY / "alte-frau-95g-heroic-core" / "research" / "2026-07-01_Frontend_ServerHub_Research.md": REPO / "docs" / "v8" / "research" / "2026-07-01_Frontend_ServerHub_Research.md",
    }
    for src, dst in mapping.items():
        if copy_file(src, dst, log):
            stats[str(dst.relative_to(REPO))] = 1

    # 4) Manifest philosophy assets (docs only, no binaries duplication if huge)
    phil_dst = REPO / "docs" / "v8" / "philosophy"
    for rel in (
        "Heroik_Formalisierungs_Audit.html",
        "GLOBAL-PREUPLOAD.cfg",
        "snippets/additional.xml",
        "snippets/fuse.xml",
        "snippets/remove.xml",
    ):
        src = LEGACY / "heroic-fusion-os-manifest" / rel
        if copy_file(src, phil_dst / rel, log):
            stats[f"philosophy/{rel}"] = 1

    # 5) Kilo agent prompts → 01_Framework/skills/kilo-import/
    kilo_dst = REPO / "01_Framework" / "skills" / "kilo-import"
    n = copy_tree(LEGACY / "kilo" / "agents", kilo_dst, log)
    stats["kilo/agents"] = n
    copy_file(LEGACY / "kilo" / "kilo.jsonc", kilo_dst / "kilo.jsonc", log)

    # 6) GUI heroic-core.js
    copy_file(
        LEGACY / "mister-Contributor-gui" / "lib" / "heroic-core.js",
        dash_dst / "static" / "heroic-core.js",
        log,
    )

    # Suite package marker
    init_py = suite_dst / "__init__.py"
    if not init_py.exists():
        init_py.write_text(
            '"""Cherry-picked private suite modules (layers, qubo, gpu, fusion, ghosthunting)."""\n',
            encoding="utf-8",
        )
        log.append({"action": "create", "path": str(init_py)})

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files_copied": len([e for e in log if e.get("action") == "copy"]),
        "stats": stats,
    }
    (REPO / "docs" / "v8" / "cherry_pick_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    lines = [
        "# Cherry-Pick Log (v8/bestversion)",
        "",
        f"**Generated:** {summary['generated_at']}",
        f"**Files copied:** {summary['files_copied']}",
        "",
        "## Targets",
        "",
        "| Area | Files |",
        "|------|-------|",
    ]
    for k, v in sorted(stats.items(), key=lambda x: -x[1]):
        lines.append(f"| `{k}` | {v} |")
    lines.extend([
        "",
        "## Integration notes",
        "",
        "- `03_Code/suite/` — layer pipeline, QUBO/GPU/fusion tools, ghosthunting, audio-bridge",
        "- `03_Code/Dashboard/templates/heroic.html` + `about.html` — legacy public UI pages",
        "- `docs/v8/seeds/` — ASR prompt + v1 master seeds",
        "- `docs/v8/concepts/Ungueltig_Anti-Agent.md` — Paired Victory Protocol",
        "- `01_Framework/skills/kilo-import/` — imported Kilo agent prompts",
        "",
        "Machine summary: `docs/v8/cherry_pick_summary.json`",
    ])
    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Cherry-pick complete: {summary['files_copied']} files")
    print(f"Log: {LOG_PATH}")


if __name__ == "__main__":
    main()