"""
erkenntnis_archiv.py — Hourly -> Daily -> Weekly -> Monthly -> Yearly rollup
for Erkenntnisse (insight/finding records) generated during operation.

Not to be confused with docs/v8/erkenntnisse_index.yaml (the static,
CI-gated document index) - this is a live event stream: any module calls
record() to log a finding, and on each period boundary the just-closed
period gets summarized and folded into the next level up *before* its
own bucket resets, so nothing is lost, just progressively aggregated.

Rollover is checked lazily on every record()/status() call (same
on-access pattern as local_infrastructure_kernel.py) rather than via a
background timer - nothing in this environment guarantees a process
stays alive to run one.

State lives under ~/.fusion/erkenntnis_archiv/ (local-first, matching
the existing ~/.fusion/operator/ and ~/.fusion/llm_resilience/
convention).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, UTC
from pathlib import Path
from threading import Lock
from typing import Any

__all__ = ["ErkenntnisArchiv", "record", "status", "default_archiv"]


def _state_dir() -> Path:
    custom = os.getenv("FUSION_ERKENNTNIS_ARCHIV_STATE")
    if custom:
        return Path(custom)
    return Path.home() / ".fusion" / "erkenntnis_archiv"


def _now() -> datetime:
    return datetime.now(UTC)


def _read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, rec: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def _summarize_hour(hour_key: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    by_source: dict[str, int] = {}
    for r in records:
        src = str(r.get("source", "unknown"))
        by_source[src] = by_source.get(src, 0) + 1
    return {
        "hour": hour_key,
        "count": len(records),
        "by_source": by_source,
        "first_ts": records[0]["ts"] if records else None,
        "last_ts": records[-1]["ts"] if records else None,
        "records": records,
    }


class ErkenntnisArchiv:
    """Hourly Erkenntnis-buffer that rolls up into daily/weekly/monthly/yearly archives."""

    def __init__(self, state_dir: Path | None = None):
        self.state_dir = state_dir or _state_dir()
        self._lock = Lock()

    # -- paths -------------------------------------------------------------

    def _hourly_path(self) -> Path:
        return self.state_dir / "hourly_current.jsonl"

    def _rollover_state_path(self) -> Path:
        return self.state_dir / "_rollover_state.json"

    def _daily_path(self, day_key: str) -> Path:
        return self.state_dir / "daily" / f"{day_key}.json"

    def _weekly_path(self, week_key: str) -> Path:
        return self.state_dir / "weekly" / f"{week_key}.json"

    def _monthly_path(self, month_key: str) -> Path:
        return self.state_dir / "monthly" / f"{month_key}.json"

    def _yearly_path(self, year_key: str) -> Path:
        return self.state_dir / "yearly" / f"{year_key}.json"

    # -- period keys ---------------------------------------------------------

    @staticmethod
    def _keys(dt: datetime) -> dict[str, str]:
        iso_year, iso_week, _ = dt.isocalendar()
        return {
            "hour": dt.strftime("%Y-%m-%dT%H"),
            "day": dt.strftime("%Y-%m-%d"),
            "week": f"{iso_year}-W{iso_week:02d}",
            "month": dt.strftime("%Y-%m"),
            "year": dt.strftime("%Y"),
        }

    def _last_keys(self) -> dict[str, str]:
        return _read_json(self._rollover_state_path(), {})

    def _save_keys(self, keys: dict[str, str]) -> None:
        _write_json(self._rollover_state_path(), keys)

    # -- public API ------------------------------------------------------------

    def record(self, erkenntnis: dict[str, Any], *, source: str = "unknown") -> None:
        """Log one Erkenntnis into the current hour's bucket."""
        with self._lock:
            self._maybe_rollover()
            _append_jsonl(self._hourly_path(), {
                "ts": _now().isoformat(),
                "source": source,
                **erkenntnis,
            })

    def status(self) -> dict[str, Any]:
        with self._lock:
            self._maybe_rollover()
            current = _read_jsonl(self._hourly_path())
            return {
                "ok": True,
                "current_hour_count": len(current),
                "last_keys": self._last_keys(),
            }

    def force_rollover(self) -> dict[str, Any]:
        """Manually trigger a rollover check (ops tooling / tests)."""
        with self._lock:
            return self._maybe_rollover()

    # -- rollover machinery ------------------------------------------------------

    def _maybe_rollover(self) -> dict[str, Any]:
        now_keys = self._keys(_now())
        last_keys = self._last_keys()
        if not last_keys:
            self._save_keys(now_keys)
            return {"rolled": []}

        rolled: list[str] = []
        if last_keys.get("hour") != now_keys["hour"]:
            self._roll_hour_into_day(last_keys)
            rolled.append("hour")
        if last_keys.get("day") != now_keys["day"]:
            self._roll_day_into_week(last_keys)
            rolled.append("day")
        if last_keys.get("week") != now_keys["week"]:
            self._roll_week_into_month(last_keys)
            rolled.append("week")
        if last_keys.get("month") != now_keys["month"]:
            self._roll_month_into_year(last_keys)
            rolled.append("month")
        # year is the top of the cascade - nothing rolls above it.

        self._save_keys(now_keys)
        return {"rolled": rolled}

    def _roll_hour_into_day(self, last_keys: dict[str, str]) -> None:
        records = _read_jsonl(self._hourly_path())
        if records:
            day_key = last_keys["day"]
            day_path = self._daily_path(day_key)
            day_data = _read_json(day_path, {"day": day_key, "hours": []})
            day_data["hours"].append(_summarize_hour(last_keys["hour"], records))
            _write_json(day_path, day_data)
        self._hourly_path().unlink(missing_ok=True)

    def _roll_day_into_week(self, last_keys: dict[str, str]) -> None:
        day_key = last_keys["day"]
        day_data = _read_json(self._daily_path(day_key), None)
        if day_data is None:
            return
        week_key = last_keys["week"]
        week_path = self._weekly_path(week_key)
        week_data = _read_json(week_path, {"week": week_key, "days": []})
        week_data["days"].append({
            "day": day_key,
            "count": sum(h["count"] for h in day_data.get("hours", [])),
            "hours": len(day_data.get("hours", [])),
        })
        _write_json(week_path, week_data)

    def _roll_week_into_month(self, last_keys: dict[str, str]) -> None:
        week_key = last_keys["week"]
        week_data = _read_json(self._weekly_path(week_key), None)
        if week_data is None:
            return
        month_key = last_keys["month"]
        month_path = self._monthly_path(month_key)
        month_data = _read_json(month_path, {"month": month_key, "weeks": []})
        month_data["weeks"].append({
            "week": week_key,
            "count": sum(d["count"] for d in week_data.get("days", [])),
            "days": len(week_data.get("days", [])),
        })
        _write_json(month_path, month_data)

    def _roll_month_into_year(self, last_keys: dict[str, str]) -> None:
        month_key = last_keys["month"]
        month_data = _read_json(self._monthly_path(month_key), None)
        if month_data is None:
            return
        year_key = last_keys["year"]
        year_path = self._yearly_path(year_key)
        year_data = _read_json(year_path, {"year": year_key, "months": []})
        year_data["months"].append({
            "month": month_key,
            "count": sum(w["count"] for w in month_data.get("weeks", [])),
            "weeks": len(month_data.get("weeks", [])),
        })
        _write_json(year_path, year_data)


default_archiv = ErkenntnisArchiv()


def record(erkenntnis: dict[str, Any], *, source: str = "unknown") -> None:
    default_archiv.record(erkenntnis, source=source)


def status() -> dict[str, Any]:
    return default_archiv.status()
