"""Totmannschalter — 24h arm, inverse-log soft taper, annual hard check.

Operator set 2026-08-16:
  * soft interval starts at 24 hours
  * then phases inverse-logarithmically to 1 soft check per month
  * hard check: 1× per year at the declared public toponym (Schwarzkollm)
  * that pair is the standard through 2027-12-31; after the horizon
    the target rates hold, they do not keep stretching

Inverse-log interpolation (log-linear in the interval)::

    u(t)  = clip((t - t0) / (t1 - t0), 0, 1)
    i(u)  = i0 * (i1 / i0) ** u

Discrete phases are the same curve sampled at k/(N-1).

Honesty (enforced by tests, not prose):
  * trip writes a local alert and flips state.tripped
  * trip does not delete files, push git, or call a phone
  * hard check is a signed-in-software attestation, not a GPS lock
"""
from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from collections.abc import Mapping

UTC = timezone.utc

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "totmann_schalter.yaml"
DEFAULT_STATE_DIR = Path.home() / ".fusion" / "totmann"
DEFAULT_ALERT = Path.home() / ".fusion" / "alerts" / "totmann_schalter.json"

SOFT_START_HOURS = 24.0
SOFT_END_DAYS = 30.0
HARD_PERIOD_DAYS = 365
DEFAULT_PHASES = 8
DEFAULT_SITE = "Schwarzkollm"
DEFAULT_EPOCH = date(2026, 8, 16)
DEFAULT_HORIZON = date(2027, 12, 31)

__all__ = [
    "TotmannConfig",
    "load_config",
    "soft_interval_hours",
    "phase_table",
    "current_phase",
    "evaluate",
    "arm",
    "soft_check",
    "hard_check",
    "reset_trip",
    "status",
]


def _expand(raw: str | Path) -> Path:
    return Path(os.path.expanduser(str(raw)))


def _parse_date(value: Any, fallback: date) -> date:
    if value is None:
        return fallback
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return fallback
    return date.fromisoformat(text[:10])


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _now() -> datetime:
    return datetime.now(UTC)


def _tzinfo(name: str):
    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo(name)
    except Exception:  # noqa: BLE001
        return UTC


@dataclass(frozen=True)
class TotmannConfig:
    epoch: date = DEFAULT_EPOCH
    horizon_end: date = DEFAULT_HORIZON
    timezone_name: str = "Europe/Berlin"
    soft_start_hours: float = SOFT_START_HOURS
    soft_end_days: float = SOFT_END_DAYS
    phases: int = DEFAULT_PHASES
    hard_period_days: int = HARD_PERIOD_DAYS
    hard_site: str = DEFAULT_SITE
    state_dir: Path = DEFAULT_STATE_DIR
    alert_path: Path = DEFAULT_ALERT
    auto_reset: bool = False
    wipe_on_trip: bool = False
    phone_home: bool = False

    @property
    def soft_end_hours(self) -> float:
        return float(self.soft_end_days) * 24.0

    @property
    def t0(self) -> datetime:
        tz = _tzinfo(self.timezone_name)
        return datetime(self.epoch.year, self.epoch.month, self.epoch.day, tzinfo=tz)

    @property
    def t1(self) -> datetime:
        tz = _tzinfo(self.timezone_name)
        return datetime(
            self.horizon_end.year,
            self.horizon_end.month,
            self.horizon_end.day,
            23,
            59,
            59,
            tzinfo=tz,
        )

    @property
    def horizon_seconds(self) -> float:
        return max((_aware(self.t1) - _aware(self.t0)).total_seconds(), 1.0)

    def progress(self, when: datetime | None = None) -> float:
        instant = _aware(when or _now())
        u = (instant - _aware(self.t0)).total_seconds() / self.horizon_seconds
        return min(1.0, max(0.0, u))


def load_config(path: Path | None = None) -> TotmannConfig:
    cfg: dict[str, Any] = {}
    src = path or CONFIG_PATH
    if src.exists():
        try:
            import yaml

            loaded = yaml.safe_load(src.read_text(encoding="utf-8")) or {}
            if isinstance(loaded, dict):
                cfg = loaded
        except Exception:  # noqa: BLE001
            cfg = {}
    soft = cfg.get("soft") or {}
    hard = cfg.get("hard") or {}
    trip = cfg.get("trip") or {}
    paths = cfg.get("paths") or {}
    return TotmannConfig(
        epoch=_parse_date(cfg.get("epoch"), DEFAULT_EPOCH),
        horizon_end=_parse_date(cfg.get("horizon_end"), DEFAULT_HORIZON),
        timezone_name=str(cfg.get("timezone") or "Europe/Berlin"),
        soft_start_hours=float(soft.get("start_hours", SOFT_START_HOURS)),
        soft_end_days=float(soft.get("end_days", SOFT_END_DAYS)),
        phases=max(2, int(soft.get("phases", DEFAULT_PHASES))),
        hard_period_days=int(hard.get("period_days", HARD_PERIOD_DAYS)),
        hard_site=str(hard.get("site") or DEFAULT_SITE),
        state_dir=_expand(paths.get("state_dir") or DEFAULT_STATE_DIR),
        alert_path=_expand(paths.get("alert") or DEFAULT_ALERT),
        auto_reset=bool(trip.get("auto_reset", False)),
        wipe_on_trip=bool(trip.get("wipe", False)),
        phone_home=bool(trip.get("phone_home", False)),
    )


def soft_interval_hours(cfg: TotmannConfig, when: datetime | None = None) -> float:
    """Inverse-log interval at instant ``when`` (hours)."""
    u = cfg.progress(when)
    i0 = float(cfg.soft_start_hours)
    i1 = float(cfg.soft_end_hours)
    if i0 <= 0 or i1 <= 0:
        raise ValueError("soft intervals must be positive")
    if math.isclose(i0, i1):
        return i0
    return i0 * (i1 / i0) ** u


def phase_table(cfg: TotmannConfig | None = None) -> list[dict[str, Any]]:
    cfg = cfg or load_config()
    n = cfg.phases
    span = cfg.horizon_end - cfg.epoch
    rows: list[dict[str, Any]] = []
    for k in range(n):
        u = k / (n - 1)
        hours = cfg.soft_start_hours * (cfg.soft_end_hours / cfg.soft_start_hours) ** u
        start = cfg.epoch + timedelta(days=span.days * k / n)
        end = cfg.horizon_end if k == n - 1 else cfg.epoch + timedelta(days=span.days * (k + 1) / n)
        rows.append(
            {
                "phase": k,
                "u": u,
                "interval_hours": hours,
                "interval_days": hours / 24.0,
                "window_start": start.isoformat(),
                "window_end": end.isoformat(),
            }
        )
    return rows


def current_phase(cfg: TotmannConfig, when: datetime | None = None) -> dict[str, Any]:
    u = cfg.progress(when)
    n = cfg.phases
    idx = min(n - 1, max(0, int(u * n)))
    table = phase_table(cfg)
    row = dict(table[idx])
    row["progress_u"] = u
    row["interval_hours_continuous"] = soft_interval_hours(cfg, when)
    return row


def _state_path(cfg: TotmannConfig) -> Path:
    return cfg.state_dir / "state.json"


def _log_path(cfg: TotmannConfig) -> Path:
    return cfg.state_dir / "log.jsonl"


def _empty_state(cfg: TotmannConfig, now: datetime) -> dict[str, Any]:
    return {
        "schema": "fusion.totmann.state/1",
        "armed": False,
        "armed_at": None,
        "last_soft": None,
        "last_hard": None,
        "hard_site": cfg.hard_site,
        "tripped": False,
        "tripped_at": None,
        "trip_reason": None,
        "soft_count": 0,
        "hard_count": 0,
        "updated_at": now.isoformat(),
    }


def _read_state(cfg: TotmannConfig) -> dict[str, Any]:
    path = _state_path(cfg)
    if not path.exists():
        return _empty_state(cfg, _now())
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else _empty_state(cfg, _now())
    except (OSError, json.JSONDecodeError):
        return _empty_state(cfg, _now())


def _write_state(cfg: TotmannConfig, state: dict[str, Any]) -> None:
    from fusion_hero_os.core.race_guard import locked_atomic_write_json

    cfg.state_dir.mkdir(parents=True, exist_ok=True)
    locked_atomic_write_json(_state_path(cfg), state)


def _append_log(cfg: TotmannConfig, record: Mapping[str, Any]) -> None:
    cfg.state_dir.mkdir(parents=True, exist_ok=True)
    line = json.dumps(dict(record), ensure_ascii=False)
    with _log_path(cfg).open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def _parse_iso(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        return _aware(datetime.fromisoformat(text))
    except ValueError:
        return None


def _write_alert(cfg: TotmannConfig, payload: dict[str, Any]) -> None:
    from fusion_hero_os.core.race_guard import locked_atomic_write_json

    cfg.alert_path.parent.mkdir(parents=True, exist_ok=True)
    locked_atomic_write_json(cfg.alert_path, payload)


def _clear_alert(cfg: TotmannConfig) -> None:
    if cfg.alert_path.exists():
        cfg.alert_path.unlink()


def evaluate(
    cfg: TotmannConfig | None = None,
    *,
    now: datetime | None = None,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = cfg or load_config()
    instant = _aware(now or _now())
    st = dict(state if state is not None else _read_state(cfg))
    last_soft = _parse_iso(st.get("last_soft")) or _parse_iso(st.get("armed_at"))
    last_hard = _parse_iso(st.get("last_hard"))
    # Freeze the interval at the last accepted ping. Evaluating i(now)
    # would grow the window while the operator is silent and hide a miss.
    interval_h = soft_interval_hours(cfg, last_soft or instant)
    interval = timedelta(hours=interval_h)
    armed = bool(st.get("armed"))
    overdue = False
    remaining_h: float | None = None
    if armed and last_soft is not None:
        remaining_h = (last_soft + interval - instant).total_seconds() / 3600.0
        overdue = remaining_h < 0
    hard_due_after = last_hard or _aware(cfg.t0)
    next_hard = hard_due_after + timedelta(days=cfg.hard_period_days)
    hard_overdue = instant >= next_hard
    tripped = bool(st.get("tripped"))
    if overdue and armed:
        tripped = True
    phase = current_phase(cfg, instant)
    return {
        "ok": armed and not tripped and not overdue,
        "armed": armed,
        "tripped": tripped,
        "soft_overdue": overdue,
        "hard_overdue": hard_overdue,
        "progress_u": cfg.progress(instant),
        "soft_interval_hours": interval_h,
        "soft_interval_days": interval_h / 24.0,
        "remaining_hours": remaining_h,
        "last_soft": last_soft.isoformat() if last_soft else None,
        "last_hard": last_hard.isoformat() if last_hard else None,
        "next_hard_due": next_hard.isoformat(),
        "hard_site": cfg.hard_site,
        "phase": phase,
        "horizon_end": cfg.horizon_end.isoformat(),
        "evaluated_at": instant.isoformat(),
        "claims": {
            "wipe_on_trip": cfg.wipe_on_trip,
            "phone_home": cfg.phone_home,
            "auto_reset": cfg.auto_reset,
        },
    }


def arm(
    cfg: TotmannConfig | None = None,
    *,
    now: datetime | None = None,
    source: str = "cli",
) -> dict[str, Any]:
    cfg = cfg or load_config()
    instant = _aware(now or _now())
    st = _read_state(cfg)
    if not st.get("armed"):
        st["armed"] = True
        st["armed_at"] = instant.isoformat()
        st["last_soft"] = instant.isoformat()
        st["hard_site"] = cfg.hard_site
        st["tripped"] = False
        st["tripped_at"] = None
        st["trip_reason"] = None
        st["updated_at"] = instant.isoformat()
        _write_state(cfg, st)
        _append_log(
            cfg,
            {
                "kind": "arm",
                "at": instant.isoformat(),
                "source": source,
                "soft_hours": SOFT_START_HOURS,
                "hard_site": cfg.hard_site,
            },
        )
    ev = evaluate(cfg, now=instant, state=st)
    ev["armed_now"] = True
    return ev


def _trip(cfg: TotmannConfig, st: dict[str, Any], instant: datetime, reason: str) -> dict[str, Any]:
    st["tripped"] = True
    st["tripped_at"] = instant.isoformat()
    st["trip_reason"] = reason
    st["updated_at"] = instant.isoformat()
    _write_state(cfg, st)
    _write_alert(
        cfg,
        {
            "schema": "fusion.totmann.alert/1",
            "tripped": True,
            "at": instant.isoformat(),
            "reason": reason,
            "hard_site": cfg.hard_site,
            "wipe": False,
            "phone_home": False,
        },
    )
    _append_log(cfg, {"kind": "trip", "at": instant.isoformat(), "reason": reason})
    # Honesty: no wipe, no phone, no git push. Alert file is the action.
    return evaluate(cfg, now=instant, state=st)


def persist_trip_if_due(cfg: TotmannConfig | None = None, *, now: datetime | None = None) -> dict[str, Any]:
    cfg = cfg or load_config()
    instant = _aware(now or _now())
    st = _read_state(cfg)
    ev = evaluate(cfg, now=instant, state=st)
    if ev["soft_overdue"] and ev["armed"] and not st.get("tripped"):
        return _trip(cfg, st, instant, "soft_interval_exceeded")
    return ev


def soft_check(
    cfg: TotmannConfig | None = None,
    *,
    now: datetime | None = None,
    source: str = "cli",
) -> dict[str, Any]:
    cfg = cfg or load_config()
    instant = _aware(now or _now())
    st = _read_state(cfg)
    if not st.get("armed"):
        return arm(cfg, now=instant, source=source)
    ev_before = evaluate(cfg, now=instant, state=st)
    if ev_before["soft_overdue"] and not cfg.auto_reset:
        if not st.get("tripped"):
            _trip(cfg, st, instant, "soft_interval_exceeded")
            st = _read_state(cfg)
        ev = evaluate(cfg, now=instant, state=st)
        ev["accepted"] = False
        ev["note"] = "late ping recorded as trip; --reset-trip required (auto_reset=false)"
        _append_log(
            cfg,
            {"kind": "soft_rejected_late", "at": instant.isoformat(), "source": source},
        )
        return ev
    st["last_soft"] = instant.isoformat()
    st["soft_count"] = int(st.get("soft_count") or 0) + 1
    st["updated_at"] = instant.isoformat()
    _write_state(cfg, st)
    _append_log(cfg, {"kind": "soft", "at": instant.isoformat(), "source": source})
    ev = evaluate(cfg, now=instant, state=st)
    ev["accepted"] = True
    return ev


def hard_check(
    site: str,
    cfg: TotmannConfig | None = None,
    *,
    now: datetime | None = None,
    source: str = "cli",
    note: str = "",
) -> dict[str, Any]:
    cfg = cfg or load_config()
    instant = _aware(now or _now())
    declared = cfg.hard_site.strip().casefold()
    given = (site or "").strip().casefold()
    if not given or given != declared:
        return {
            "ok": False,
            "accepted": False,
            "error": "hard_site_mismatch",
            "expected_site": cfg.hard_site,
            "given_site": site,
            "note": "Hard check is presence at the declared toponym (self-attestation).",
        }
    st = _read_state(cfg)
    if not st.get("armed"):
        arm(cfg, now=instant, source=source)
        st = _read_state(cfg)
    st["last_hard"] = instant.isoformat()
    st["hard_count"] = int(st.get("hard_count") or 0) + 1
    st["updated_at"] = instant.isoformat()
    _write_state(cfg, st)
    _append_log(
        cfg,
        {
            "kind": "hard",
            "at": instant.isoformat(),
            "site": cfg.hard_site,
            "source": source,
            "note": note,
            "attestation": "operator_self",
            "gps": False,
        },
    )
    ev = evaluate(cfg, now=instant, state=st)
    ev["accepted"] = True
    ev["attestation"] = "operator_self"
    ev["gps"] = False
    return ev


def reset_trip(
    cfg: TotmannConfig | None = None,
    *,
    now: datetime | None = None,
    source: str = "cli",
) -> dict[str, Any]:
    cfg = cfg or load_config()
    instant = _aware(now or _now())
    st = _read_state(cfg)
    st["tripped"] = False
    st["tripped_at"] = None
    st["trip_reason"] = None
    st["last_soft"] = instant.isoformat()
    st["updated_at"] = instant.isoformat()
    _write_state(cfg, st)
    _clear_alert(cfg)
    _append_log(cfg, {"kind": "reset_trip", "at": instant.isoformat(), "source": source})
    ev = evaluate(cfg, now=instant, state=st)
    ev["reset"] = True
    return ev


def status(cfg: TotmannConfig | None = None, *, now: datetime | None = None) -> dict[str, Any]:
    cfg = cfg or load_config()
    ev = persist_trip_if_due(cfg, now=now)
    ev["phases"] = phase_table(cfg)
    ev["config"] = {
        "epoch": cfg.epoch.isoformat(),
        "horizon_end": cfg.horizon_end.isoformat(),
        "soft_start_hours": cfg.soft_start_hours,
        "soft_end_days": cfg.soft_end_days,
        "phases": cfg.phases,
        "hard_period_days": cfg.hard_period_days,
        "hard_site": cfg.hard_site,
        "interpolation": "inverse_log",
    }
    return ev


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="totmann_schalter")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--arm", action="store_true")
    parser.add_argument("--ping", action="store_true", help="soft check (24h…monthly)")
    parser.add_argument("--hard-check", action="store_true")
    parser.add_argument("--site", default="")
    parser.add_argument("--note", default="")
    parser.add_argument("--evaluate", action="store_true")
    parser.add_argument("--reset-trip", action="store_true")
    parser.add_argument("--phases", action="store_true")
    args = parser.parse_args(argv)

    cfg = load_config()
    if args.arm:
        payload: Any = arm(cfg)
    elif args.ping:
        payload = soft_check(cfg)
    elif args.hard_check:
        payload = hard_check(args.site or cfg.hard_site, cfg, note=args.note)
    elif args.reset_trip:
        payload = reset_trip(cfg)
    elif args.phases:
        payload = {"phases": phase_table(cfg)}
    elif args.evaluate:
        payload = persist_trip_if_due(cfg)
    else:
        payload = status(cfg)

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if isinstance(payload, dict) and payload.get("tripped"):
        return 2
    if isinstance(payload, dict) and payload.get("hard_overdue"):
        return 3
    if isinstance(payload, dict) and payload.get("accepted") is False:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
