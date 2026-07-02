# -*- coding: utf-8 -*-
"""Isolierter Worker-Prozess — stdin JSON → stdout JSON."""
from __future__ import annotations

import json
import sys
from pathlib import Path

DASHBOARD = Path(__file__).resolve().parent
CODE_ROOT = DASHBOARD.parent
for p in (str(DASHBOARD), str(CODE_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from worker_tasks import execute_job


def main() -> None:
    raw = sys.stdin.read()
    job = json.loads(raw) if raw.strip() else {}
    sys.stdout.write(json.dumps(execute_job(job), default=str))


if __name__ == "__main__":
    main()