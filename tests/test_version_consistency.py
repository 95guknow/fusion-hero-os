# -*- coding: utf-8 -*-
"""Version-consistency gate (v10 Stage-A).

All shipped manifests must declare the same project version. This prevents the
drift observed pre-v10 (VERSION/pyproject/package.json at 8.3.0 while
fusion_hero_os/__init__.py read 8.0.0).
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(p: Path) -> str:
    return (ROOT / p).read_text(encoding="utf-8")


def _toml_version(p: str) -> str:
    m = re.search(r'(?m)^version\s*=\s*"([^"]+)"', _read(Path(p)))
    assert m, f"no version in {p}"
    return m.group(1)


def _json_version(p: str) -> str:
    return json.loads(_read(Path(p)))["version"]


def _init_version() -> str:
    m = re.search(r'__version__\s*=\s*"([^"]+)"',
                  _read(Path("fusion_hero_os/__init__.py")))
    assert m, "no __version__ in fusion_hero_os/__init__.py"
    return m.group(1)


def test_all_manifests_agree():
    versions = {
        "VERSION": _read(Path("VERSION")).strip(),
        "pyproject.toml": _toml_version("pyproject.toml"),
        "package.json": _json_version("package.json"),
        "fusion_hero_os/__init__.py": _init_version(),
        "pms_rust_kernel_crate/Cargo.toml": _toml_version("pms_rust_kernel_crate/Cargo.toml"),
        "rust_engine_crate/Cargo.toml": _toml_version("rust_engine_crate/Cargo.toml"),
        "workstation/package.json": _json_version("workstation/package.json"),
    }
    distinct = set(versions.values())
    assert len(distinct) == 1, f"version mismatch across manifests: {versions}"


def test_version_is_at_least_v10():
    """Stage-A-Untergrenze statt fest verdrahteter Zahl.

    Frueher stand hier ``== "10.0.0"``. Das brach bei jedem Plattform-Bump
    (zuletzt 12.1.0) und hielt damit die CI auf main dauerhaft rot, ohne einen
    echten Defekt zu zeigen. Die eigentliche Aussage des Gates — alle Manifeste
    tragen DIESELBE Version — prueft ``test_all_manifests_agree``. Hier bleibt
    nur die Regressions-Untergrenze: die Plattform faellt nicht hinter v10
    zurueck (die vor-v10-Drift 8.0.0/8.3.0 ist der Anlass dieses Gates).
    """
    raw = _read(Path("VERSION")).strip()
    parts = raw.split(".")
    assert len(parts) == 3 and all(p.isdigit() for p in parts), f"kein semver: {raw!r}"
    assert tuple(int(p) for p in parts) >= (10, 0, 0), f"Plattform-Version unter v10: {raw}"
