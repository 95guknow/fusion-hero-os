# -*- coding: utf-8 -*-
"""Fusion Hero OS — Regex-Validierung mit getrennten Versionsschichten.

Inversionskorrektur: VERSION-Datei, Git-Tag und GitHub-Release tragen
drei verschiedene Zahlen, nicht eine. Login, Repo-Name und Insta-Marker
sind eigene Muster.

    >>> from pyclon import validate, LOGIN
    >>> validate(LOGIN, [("95guknow", True), ("95Guknow", False)])["ok"]
    True
"""

from __future__ import annotations

import re
from typing import Iterable, Sequence

Sample = str | tuple[str, bool]

# --- kanonische Muster -------------------------------------------------------

LOGIN = r"^95guknow$"
"""Exakter GitHub-/Mesh-Login. Case-sensitiv, kein Prefix/Suffix."""

REPO = r"fusion-hero-os"
"""Repo-Slug, Kleinbuchstaben + Bindestrich. Kein ``Fusion-Hero-OS`` / ``fusion_hero_os``."""

VERSION_FILE = r"(?:^|VERSION=)(\d+\.\d+\.\d+)"
"""Schicht 1: Inhalt der ``VERSION``-Datei bzw. ``VERSION=x.y.z`` (Gruppe 1)."""

TAG = r"\bv((?:10|13|15)\.\d+\.\d+)\b"
"""Schicht 2: Git-Tag ``v10|v13|v15``. Gruppe 1 ohne führendes ``v``."""

RELEASE = r"\brelease v(\d+\.\d+\.\d+)\b"
"""Schicht 3: Release-Erwähnung im Fließtext. Gruppe 1 ohne führendes ``v``."""

INSTA = r"(Huhu|Uhu|Miau)"
"""Insta-Marker, case-sensitiv. ``UHU`` / ``Saumagen`` treffen nicht."""

TAG_ANCHORED = r"^v(10|13|15)\.\d+\.\d+$"
"""Ganzer String = Tag. ``V15.2.0`` und ``v15.2.0-rc1`` fallen raus."""


def validate(pattern: str, samples: Iterable[Sample], *, flags: int = 0) -> dict:
    """Kompiliert ``pattern`` einmal und prüft jede Probe.

    Args:
        pattern: Python-``re``-Muster.
        samples: Entweder der Rohstring (dann wird ein Treffer erwartet)
            oder ``(text, expected_match)``.
        flags: Optionale ``re``-Flags (z. B. ``re.IGNORECASE``).

    Returns:
        Dict mit ``pattern``, ``ok`` (alle Proben wie erwartet) und
        ``rows`` — je Probe ``text``, ``got``, ``expected``, ``ok``.

    Raises:
        re.error: Ungültiges Muster.
    """
    rx = re.compile(pattern, flags)
    rows = []
    ok = True
    for item in samples:
        text, expected = item if isinstance(item, tuple) else (item, True)
        got = rx.search(text) is not None
        hit = got == expected
        ok = ok and hit
        rows.append({"text": text, "got": got, "expected": expected, "ok": hit})
    return {"pattern": pattern, "ok": ok, "rows": rows}


def extract_layers(text: str) -> dict[str, str | None]:
    """Zieht die drei Versionsschichten unabhängig aus ``text``.

    Die Schichten dürfen nicht auf eine Zahl kollabieren:

    - ``version_file`` → VERSION-Datei (z. B. ``15.2.0``)
    - ``tag`` → Git-Tag 10/13/15 (z. B. ``13.0.0``)
    - ``release`` → Release-Erwähnung (z. B. ``10.0.0``)

    Fehlende Schicht → ``None``.
    """
    vf = re.search(VERSION_FILE, text)
    tg = re.search(TAG, text)
    rl = re.search(RELEASE, text)
    return {
        "version_file": vf.group(1) if vf else None,
        "tag": tg.group(1) if tg else None,
        "release": rl.group(1) if rl else None,
    }


def _selftest() -> int:
    """Fährt die Inversions-Suiten. Rückgabe 0 bei Erfolg, sonst 1."""
    suites: Sequence[tuple[str, list[Sample]]] = [
        (
            LOGIN,
            [
                ("95guknow", True),
                ("95Guknow", False),
                ("x95guknow", False),
                ("95guknow/fusion-hero-os", False),
            ],
        ),
        (
            REPO,
            [
                ("fusion-hero-os", True),
                ("siehe fusion-hero-os README", True),
                ("Fusion-Hero-OS", False),
                ("fusion_hero_os", False),
            ],
        ),
        (
            TAG_ANCHORED,
            [
                ("v10.0.0", True),
                ("v13.0.0", True),
                ("v15.2.0", True),
                ("V15.2.0", False),
                ("v15.2.0-rc1", False),
                ("VERSION=15.2.0", False),
                ("v8.3", False),
            ],
        ),
        (
            INSTA,
            [
                ("Huhu", True),
                ("Miau uwu huhu", True),
                ("UHU", False),
                ("Saumagen", False),
            ],
        ),
    ]
    failed = False
    for pat, samples in suites:
        report = validate(pat, samples)
        mark = "OK" if report["ok"] else "FAIL"
        print(f"{mark}  {pat}")
        for row in report["rows"]:
            if not row["ok"]:
                failed = True
                print(f"   miss  {row['text']!r}  got={row['got']}")
        failed = failed or not report["ok"]

    blob = "VERSION=15.2.0 last published tag v13.0.0 README release v10.0.0"
    layers = extract_layers(blob)
    expected = {"version_file": "15.2.0", "tag": "13.0.0", "release": "10.0.0"}
    layers_ok = layers == expected
    print(("OK" if layers_ok else "FAIL") + f"  layers={layers}")
    if not layers_ok:
        failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
