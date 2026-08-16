# -*- coding: utf-8 -*-
"""Totmannschalter: 24h start, inverse-log taper, annual hard check."""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fusion_hero_os.core.totmann_schalter import (
    CONFIG_PATH,
    DEFAULT_HORIZON,
    DEFAULT_SITE,
    SOFT_END_DAYS,
    SOFT_START_HOURS,
    TotmannConfig,
    arm,
    current_phase,
    evaluate,
    hard_check,
    load_config,
    persist_trip_if_due,
    phase_table,
    reset_trip,
    soft_check,
    soft_interval_hours,
    status,
)

UTC = timezone.utc
CLOCK = datetime(2026, 8, 16, 12, 0, 0, tzinfo=UTC)


def _cfg(tmp_path: Path, **kwargs) -> TotmannConfig:
    base = dict(
        state_dir=tmp_path / "state",
        alert_path=tmp_path / "alert.json",
        auto_reset=False,
        wipe_on_trip=False,
        phone_home=False,
    )
    base.update(kwargs)
    return TotmannConfig(**base)


def test_repo_config_is_24h_then_monthly_and_annual_schwarzkollm():
    cfg = load_config()
    assert cfg.soft_start_hours == 24.0
    assert cfg.soft_end_days == 30.0
    assert cfg.hard_period_days == 365
    assert cfg.hard_site == "Schwarzkollm"
    assert cfg.epoch.isoformat() == "2026-08-16"
    assert cfg.horizon_end.isoformat() == "2027-12-31"
    assert cfg.wipe_on_trip is False
    assert cfg.phone_home is False
    assert cfg.auto_reset is False
    assert CONFIG_PATH.is_file()


def test_soft_interval_at_epoch_is_24_hours():
    cfg = TotmannConfig()
    assert math.isclose(soft_interval_hours(cfg, cfg.t0), SOFT_START_HOURS, rel_tol=1e-12)


def test_soft_interval_at_horizon_is_one_month():
    cfg = TotmannConfig()
    hours = soft_interval_hours(cfg, cfg.t1)
    assert math.isclose(hours, SOFT_END_DAYS * 24.0, rel_tol=1e-6)


def test_soft_interval_is_inverse_log_and_monotone():
    cfg = TotmannConfig()
    i0 = SOFT_START_HOURS
    i1 = SOFT_END_DAYS * 24.0
    span = cfg.t1 - cfg.t0
    samples = []
    for k in range(11):
        u = k / 10
        when = cfg.t0 + span * u
        got = soft_interval_hours(cfg, when)
        expected = i0 * (i1 / i0) ** u
        assert math.isclose(got, expected, rel_tol=1e-9), (u, got, expected)
        samples.append(got)
    assert samples == sorted(samples)
    assert samples[0] < samples[-1]
    mid = samples[5]
    assert math.isclose(math.log(mid), 0.5 * (math.log(i0) + math.log(i1)), rel_tol=1e-9)


def test_interval_holds_at_bounds_outside_horizon():
    cfg = TotmannConfig()
    before = cfg.t0 - timedelta(days=10)
    after = cfg.t1 + timedelta(days=40)
    assert math.isclose(soft_interval_hours(cfg, before), 24.0, rel_tol=1e-12)
    assert math.isclose(soft_interval_hours(cfg, after), 720.0, rel_tol=1e-9)


def test_phase_table_has_eight_log_spaced_rows():
    rows = phase_table(TotmannConfig())
    assert len(rows) == 8
    assert math.isclose(rows[0]["interval_hours"], 24.0, rel_tol=1e-12)
    assert math.isclose(rows[-1]["interval_hours"], 720.0, rel_tol=1e-9)
    assert rows[-1]["window_end"] == DEFAULT_HORIZON.isoformat()


def test_current_phase_at_start_is_phase_zero():
    cfg = TotmannConfig()
    row = current_phase(cfg, cfg.t0)
    assert row["phase"] == 0


def test_missed_soft_check_trips_and_writes_alert(tmp_path: Path):
    cfg = _cfg(tmp_path)
    arm(cfg, now=CLOCK)
    late = CLOCK + timedelta(hours=soft_interval_hours(cfg, CLOCK), seconds=1)
    ev = persist_trip_if_due(cfg, now=late)
    assert ev["tripped"] is True
    assert ev["soft_overdue"] is True
    assert cfg.alert_path.is_file()
    assert ev["claims"]["wipe_on_trip"] is False
    assert ev["claims"]["phone_home"] is False


def test_late_ping_does_not_silently_reset(tmp_path: Path):
    cfg = _cfg(tmp_path)
    arm(cfg, now=CLOCK)
    late = CLOCK + timedelta(hours=soft_interval_hours(cfg, CLOCK) + 6)
    ev = soft_check(cfg, now=late)
    assert ev["accepted"] is False
    assert ev["tripped"] is True
    assert ev.get("last_soft") == CLOCK.isoformat()


def test_on_time_ping_extends_window(tmp_path: Path):
    cfg = _cfg(tmp_path)
    arm(cfg, now=CLOCK)
    ping_at = CLOCK + timedelta(hours=12)
    ev = soft_check(cfg, now=ping_at)
    assert ev["accepted"] is True
    assert ev["tripped"] is False
    assert ev["last_soft"] == ping_at.isoformat()
    still_ok = evaluate(cfg, now=ping_at + timedelta(hours=23))
    assert still_ok["soft_overdue"] is False


def test_hard_check_rejects_wrong_site(tmp_path: Path):
    cfg = _cfg(tmp_path)
    arm(cfg, now=CLOCK)
    ev = hard_check("elsewhere", cfg, now=CLOCK)
    assert ev["accepted"] is False
    assert ev["error"] == "hard_site_mismatch"
    assert ev["expected_site"] == DEFAULT_SITE


def test_hard_check_accepts_schwarzkollm_as_attestation_not_gps(tmp_path: Path):
    cfg = _cfg(tmp_path)
    arm(cfg, now=CLOCK)
    ev = hard_check("schwarzkollm", cfg, now=CLOCK + timedelta(days=10))
    assert ev["accepted"] is True
    assert ev["gps"] is False
    assert ev["attestation"] == "operator_self"
    assert ev["hard_overdue"] is False


def test_hard_check_due_after_365_days(tmp_path: Path):
    cfg = _cfg(tmp_path)
    arm(cfg, now=CLOCK)
    before = evaluate(cfg, now=CLOCK + timedelta(days=364))
    assert before["hard_overdue"] is False
    after = evaluate(cfg, now=CLOCK + timedelta(days=365))
    assert after["hard_overdue"] is True


def test_reset_trip_clears_alert(tmp_path: Path):
    cfg = _cfg(tmp_path)
    arm(cfg, now=CLOCK)
    persist_trip_if_due(cfg, now=CLOCK + timedelta(hours=soft_interval_hours(cfg, CLOCK) + 1))
    assert cfg.alert_path.is_file()
    ev = reset_trip(cfg, now=CLOCK + timedelta(hours=soft_interval_hours(cfg, CLOCK) + 2))
    assert ev["tripped"] is False
    assert ev.get("reset") is True
    assert not cfg.alert_path.exists()


def test_trip_does_not_wipe_state_or_foreign_files(tmp_path: Path):
    cfg = _cfg(tmp_path)
    marker = tmp_path / "must_survive.txt"
    marker.write_text("keep", encoding="utf-8")
    arm(cfg, now=CLOCK)
    persist_trip_if_due(cfg, now=CLOCK + timedelta(hours=soft_interval_hours(cfg, CLOCK) + 1))
    assert marker.read_text(encoding="utf-8") == "keep"
    assert (cfg.state_dir / "state.json").is_file()
    assert cfg.wipe_on_trip is False


def test_status_exposes_phase_table_and_site(tmp_path: Path):
    st = status(_cfg(tmp_path))
    assert st["config"]["interpolation"] == "inverse_log"
    assert st["config"]["hard_site"] == "Schwarzkollm"
    assert len(st["phases"]) == 8
    assert st["phases"][0]["interval_hours"] == 24.0
