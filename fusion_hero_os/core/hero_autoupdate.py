"""Hero Autoupdate — logisches Polling + Android-Erinnerung (Held).

Standards (explizite User-Direktive):
- Poll-Intervall: **60 s** (1 Min) — logischer Status/Update-Check
- Erinnerung: nach **300 s** (5 Min) ohne Interaktion zum Held
- Zustellung: **Android System-Notifications** via ``PHONE_NOTIFY_WEBHOOK_URL``
  (ntfy.sh / kompatibler Webhook → ntfy-App auf dem Handy)

Code-Honesty: Ohne Webhook-URL wird nur geloggt, kein Fake-Erfolg.
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Defaults (kanonisch)
# ---------------------------------------------------------------------------
DEFAULT_POLL_INTERVAL_SEC = 60.0
DEFAULT_REMINDER_AFTER_SEC = 300.0
DEFAULT_REMINDER_COOLDOWN_SEC = 300.0
DEFAULT_HEALTH_URL = "http://127.0.0.1:8000/api/health?light=true"
DEFAULT_STATE_NAME = "hero_autoupdate_state.json"

_REPO_ROOT = Path(__file__).resolve().parents[2]
_lock = threading.RLock()
_instance: HeroAutoupdateService | None = None


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _repo_root() -> Path:
    env = os.environ.get("FUSION_REPO_ROOT", "").strip()
    if env:
        return Path(env)
    return _REPO_ROOT


def _load_yaml_config() -> dict[str, Any]:
    path = _repo_root() / "hero_autoupdate.yaml"
    if not path.is_file():
        return {}
    try:
        import yaml  # type: ignore

        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


@dataclass
class HeroAutoupdateConfig:
    enabled: bool = True
    poll_interval_sec: float = DEFAULT_POLL_INTERVAL_SEC
    reminder_after_sec: float = DEFAULT_REMINDER_AFTER_SEC
    reminder_cooldown_sec: float = DEFAULT_REMINDER_COOLDOWN_SEC
    notify_on_update: bool = True
    notify_on_health_change: bool = True
    health_url: str = DEFAULT_HEALTH_URL
    state_path: str = ""
    reminder_title: str = "Held — Interaktion fällig"
    reminder_message: str = (
        "Seit {idle_min} Min keine Interaktion zum Held. Mainframe wartet (v{version})."
    )
    update_title: str = "Held — Autoupdate"
    update_message: str = "Update erkannt: {detail}"
    startup_title: str = "Held — Autoupdate aktiv"
    startup_message: str = (
        "Polling {poll_min} Min · Erinnerung nach {remind_min} Min · Android-Notify"
    )
    android_priority: str = "high"
    android_tags: str = "heroic,bell"
    android_click_url: str = "http://127.0.0.1:8000/"

    @classmethod
    def load(cls) -> HeroAutoupdateConfig:
        y = _load_yaml_config()
        android = y.get("android") if isinstance(y.get("android"), dict) else {}
        cfg = cls(
            enabled=bool(y.get("enabled", True)),
            poll_interval_sec=float(y.get("poll_interval_sec", DEFAULT_POLL_INTERVAL_SEC)),
            reminder_after_sec=float(y.get("reminder_after_sec", DEFAULT_REMINDER_AFTER_SEC)),
            reminder_cooldown_sec=float(
                y.get("reminder_cooldown_sec", DEFAULT_REMINDER_COOLDOWN_SEC)
            ),
            notify_on_update=bool(y.get("notify_on_update", True)),
            notify_on_health_change=bool(y.get("notify_on_health_change", True)),
            health_url=str(y.get("health_url", DEFAULT_HEALTH_URL)),
            state_path=str(y.get("state_path", "")),
            reminder_title=str(y.get("reminder_title", cls.reminder_title)),
            reminder_message=str(y.get("reminder_message", cls.reminder_message)),
            update_title=str(y.get("update_title", cls.update_title)),
            update_message=str(y.get("update_message", cls.update_message)),
            startup_title=str(y.get("startup_title", cls.startup_title)),
            startup_message=str(y.get("startup_message", cls.startup_message)),
            android_priority=str(android.get("priority", "high")),
            android_tags=str(android.get("tags", "heroic,bell")),
            android_click_url=str(android.get("click_url", "http://127.0.0.1:8000/")),
        )
        # Env overrides (kanonische Knöpfe)
        if os.environ.get("FUSION_HERO_AUTOUPDATE", "").strip():
            cfg.enabled = _env_bool("FUSION_HERO_AUTOUPDATE", cfg.enabled)
        cfg.poll_interval_sec = _env_float(
            "FUSION_HERO_POLL_INTERVAL_SEC", cfg.poll_interval_sec
        )
        cfg.reminder_after_sec = _env_float(
            "FUSION_HERO_REMINDER_AFTER_SEC", cfg.reminder_after_sec
        )
        cfg.reminder_cooldown_sec = _env_float(
            "FUSION_HERO_REMINDER_COOLDOWN_SEC", cfg.reminder_cooldown_sec
        )
        if os.environ.get("FUSION_DASHBOARD_URL", "").strip():
            base = os.environ["FUSION_DASHBOARD_URL"].rstrip("/")
            cfg.health_url = f"{base}/api/health?light=true"
            cfg.android_click_url = f"{base}/"
        health_override = os.environ.get("FUSION_HERO_HEALTH_URL", "").strip()
        if health_override:
            cfg.health_url = health_override
        prio = os.environ.get("PHONE_NOTIFY_PRIORITY", "").strip()
        if prio:
            cfg.android_priority = prio
        tags = os.environ.get("PHONE_NOTIFY_TAGS", "").strip()
        if tags:
            cfg.android_tags = tags
        # Sanity clamps
        cfg.poll_interval_sec = max(15.0, cfg.poll_interval_sec)
        cfg.reminder_after_sec = max(cfg.poll_interval_sec, cfg.reminder_after_sec)
        cfg.reminder_cooldown_sec = max(60.0, cfg.reminder_cooldown_sec)
        return cfg


@dataclass
class HeroAutoupdateState:
    last_interaction_ts: float = 0.0
    last_poll_ts: float = 0.0
    last_reminder_ts: float = 0.0
    last_git_head: str = ""
    last_health: str = ""
    last_version: str = ""
    poll_count: int = 0
    reminder_count: int = 0
    update_notify_count: int = 0
    started_at: str = ""
    last_events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HeroAutoupdateState:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in known}
        st = cls(**kwargs)
        if not isinstance(st.last_events, list):
            st.last_events = []
        return st


class HeroAutoupdateService:
    """Singleton service: tick / touch / status."""

    def __init__(self, config: HeroAutoupdateConfig | None = None) -> None:
        self.config = config or HeroAutoupdateConfig.load()
        self._state = HeroAutoupdateState(started_at=_utc_now())
        self._load_state()
        if self._state.last_interaction_ts <= 0:
            # First boot: treat as just interacted so we don't spam immediately
            self._state.last_interaction_ts = time.time()
            self._save_state()

    # -- paths ---------------------------------------------------------------

    def state_file(self) -> Path:
        raw = (self.config.state_path or "").strip()
        if raw:
            p = Path(raw)
            if not p.is_absolute():
                p = _repo_root() / p
            return p
        fusion_dir = Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".fusion"
        fusion_dir.mkdir(parents=True, exist_ok=True)
        return fusion_dir / DEFAULT_STATE_NAME

    def _load_state(self) -> None:
        path = self.state_file()
        if not path.is_file():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self._state = HeroAutoupdateState.from_dict(data)
        except Exception:
            pass

    def _save_state(self) -> None:
        path = self.state_file()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(self._state.to_dict(), indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        except Exception:
            pass

    def _push_event(self, kind: str, detail: str) -> None:
        self._state.last_events.append(
            {"ts": _utc_now(), "kind": kind, "detail": detail[:240]}
        )
        self._state.last_events = self._state.last_events[-40:]

    # -- probes --------------------------------------------------------------

    def _read_version(self) -> str:
        vf = _repo_root() / "VERSION"
        try:
            if vf.is_file():
                return vf.read_text(encoding="utf-8").strip() or "unknown"
        except Exception:
            pass
        return os.environ.get("FUSION_PLATFORM_VERSION", "10.0.0")

    def _git_head(self) -> str:
        try:
            r = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=str(_repo_root()),
                capture_output=True,
                text=True,
                timeout=8,
            )
            if r.returncode == 0:
                return (r.stdout or "").strip()
        except Exception:
            pass
        return ""

    def _git_behind_origin(self) -> int | None:
        """Return commits behind origin/main if fetchable; None if unknown."""
        try:
            subprocess.run(
                ["git", "fetch", "origin", "--quiet"],
                cwd=str(_repo_root()),
                capture_output=True,
                timeout=45,
            )
            r = subprocess.run(
                ["git", "rev-list", "--count", "HEAD..origin/main"],
                cwd=str(_repo_root()),
                capture_output=True,
                text=True,
                timeout=15,
            )
            if r.returncode == 0:
                return int((r.stdout or "0").strip() or "0")
        except Exception:
            return None
        return None

    def _health(self) -> dict[str, Any]:
        url = self.config.health_url
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                try:
                    data = json.loads(body)
                except Exception:
                    data = {"raw": body[:200]}
                return {"ok": resp.status < 300, "status_code": resp.status, "body": data}
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:160]}

    # -- notify (Android system notifications) -------------------------------

    def notify_android(
        self,
        message: str,
        title: str = "Held",
        *,
        priority: str | None = None,
        tags: str | None = None,
        click: str | None = None,
    ) -> dict[str, Any]:
        """Send Android system notification via phone notify path (ntfy webhook)."""
        try:
            from tailscale_phone_notify import send_phone_notification

            result = send_phone_notification(
                message,
                title=title,
                priority=priority or self.config.android_priority,
                tags=tags or self.config.android_tags,
                click=click or self.config.android_click_url,
            )
            if isinstance(result, dict):
                return result
            return {"ok": True, "channel": "phone_notify", "result": result}
        except TypeError:
            # Older signature without kwargs
            try:
                from tailscale_phone_notify import send_phone_notification

                send_phone_notification(message, title=title)
                return {"ok": True, "channel": "phone_notify", "legacy": True}
            except Exception as exc:
                return {"ok": False, "error": str(exc)[:160]}
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:160]}

    # -- public API ----------------------------------------------------------

    def touch(self, source: str = "api") -> dict[str, Any]:
        """Mark an interaction with the Held (resets 5-min reminder timer)."""
        with _lock:
            now = time.time()
            self._state.last_interaction_ts = now
            self._push_event("touch", f"source={source}")
            self._save_state()
            return {
                "ok": True,
                "touched_at": _utc_now(),
                "source": source,
                "idle_sec": 0.0,
            }

    def idle_sec(self) -> float:
        with _lock:
            if self._state.last_interaction_ts <= 0:
                return 0.0
            return max(0.0, time.time() - self._state.last_interaction_ts)

    def status(self) -> dict[str, Any]:
        with _lock:
            idle = self.idle_sec()
            cfg = self.config
            webhook = bool(os.environ.get("PHONE_NOTIFY_WEBHOOK_URL", "").strip())
            return {
                "ok": True,
                "enabled": cfg.enabled,
                "poll_interval_sec": cfg.poll_interval_sec,
                "reminder_after_sec": cfg.reminder_after_sec,
                "reminder_cooldown_sec": cfg.reminder_cooldown_sec,
                "idle_sec": round(idle, 1),
                "idle_min": round(idle / 60.0, 2),
                "reminder_due": idle >= cfg.reminder_after_sec,
                "android_notify_configured": webhook,
                "android_channel": "system_notification",
                "version": self._read_version(),
                "git_head": self._state.last_git_head or self._git_head(),
                "last_health": self._state.last_health,
                "poll_count": self._state.poll_count,
                "reminder_count": self._state.reminder_count,
                "update_notify_count": self._state.update_notify_count,
                "last_interaction_ts": self._state.last_interaction_ts,
                "last_poll_ts": self._state.last_poll_ts,
                "last_reminder_ts": self._state.last_reminder_ts,
                "started_at": self._state.started_at,
                "state_file": str(self.state_file()),
                "recent_events": list(self._state.last_events[-10:]),
            }

    def tick(self, *, force_reminder: bool = False, do_fetch: bool = False) -> dict[str, Any]:
        """One logical poll cycle.

        - Probes health + git head (+ optional origin behind-count)
        - Emits Android update notifications on change
        - Emits Android reminder if idle ≥ 5 min
        """
        with _lock:
            if not self.config.enabled and not force_reminder:
                return {"ok": True, "skipped": True, "reason": "disabled"}

            now = time.time()
            self._state.last_poll_ts = now
            self._state.poll_count += 1
            version = self._read_version()
            self._state.last_version = version

            actions: list[dict[str, Any]] = []
            health = self._health()
            health_label = "ok" if health.get("ok") else "down"
            if health.get("body") and isinstance(health["body"], dict):
                health_label = str(health["body"].get("status", health_label))

            if (
                self.config.notify_on_health_change
                and self._state.last_health
                and self._state.last_health != health_label
            ):
                detail = f"Health {self._state.last_health} → {health_label}"
                msg = self.config.update_message.format(detail=detail, version=version)
                n = self.notify_android(msg, title=self.config.update_title)
                self._state.update_notify_count += 1
                self._push_event("health_change", detail)
                actions.append({"kind": "health_change", "notify": n, "detail": detail})
            self._state.last_health = health_label

            head = self._git_head()
            if head and self._state.last_git_head and head != self._state.last_git_head:
                detail = f"git HEAD {self._state.last_git_head} → {head}"
                if self.config.notify_on_update:
                    msg = self.config.update_message.format(detail=detail, version=version)
                    n = self.notify_android(msg, title=self.config.update_title)
                    self._state.update_notify_count += 1
                    actions.append({"kind": "git_head_change", "notify": n, "detail": detail})
                self._push_event("git_head_change", detail)
            if head:
                self._state.last_git_head = head

            behind: int | None = None
            if do_fetch or _env_bool("FUSION_HERO_POLL_FETCH", False):
                behind = self._git_behind_origin()
                if behind is not None and behind > 0 and self.config.notify_on_update:
                    detail = f"{behind} Commit(s) hinter origin/main"
                    msg = self.config.update_message.format(detail=detail, version=version)
                    n = self.notify_android(msg, title=self.config.update_title)
                    self._state.update_notify_count += 1
                    self._push_event("behind_origin", detail)
                    actions.append({"kind": "behind_origin", "behind": behind, "notify": n})

            idle = now - self._state.last_interaction_ts if self._state.last_interaction_ts else 0.0
            reminder_sent = False
            cooldown_ok = (now - self._state.last_reminder_ts) >= self.config.reminder_cooldown_sec
            if force_reminder or (
                idle >= self.config.reminder_after_sec and cooldown_ok
            ):
                idle_min = max(1, int(idle // 60))
                msg = self.config.reminder_message.format(
                    idle_min=idle_min,
                    version=version,
                    idle_sec=int(idle),
                )
                n = self.notify_android(
                    msg,
                    title=self.config.reminder_title,
                    priority="high",
                    tags="warning,bell,heroic",
                )
                self._state.last_reminder_ts = now
                self._state.reminder_count += 1
                reminder_sent = True
                self._push_event("reminder", f"idle_min={idle_min}")
                actions.append({"kind": "reminder", "idle_sec": round(idle, 1), "notify": n})

            self._save_state()
            return {
                "ok": True,
                "ts": _utc_now(),
                "poll_count": self._state.poll_count,
                "idle_sec": round(idle, 1),
                "health": health_label,
                "git_head": head,
                "behind_origin": behind,
                "version": version,
                "reminder_sent": reminder_sent,
                "actions": actions,
                "android_notify_configured": bool(
                    os.environ.get("PHONE_NOTIFY_WEBHOOK_URL", "").strip()
                ),
            }

    def notify_startup(self) -> dict[str, Any]:
        cfg = self.config
        msg = cfg.startup_message.format(
            poll_min=max(1, int(cfg.poll_interval_sec // 60)),
            remind_min=max(1, int(cfg.reminder_after_sec // 60)),
            version=self._read_version(),
        )
        n = self.notify_android(msg, title=cfg.startup_title, tags="rocket,heroic")
        self._push_event("startup", msg)
        self._save_state()
        return n


def get_hero_autoupdate() -> HeroAutoupdateService:
    global _instance
    with _lock:
        if _instance is None:
            _instance = HeroAutoupdateService()
        return _instance


def reset_hero_autoupdate_for_tests() -> None:
    """Test helper — drop singleton."""
    global _instance
    with _lock:
        _instance = None
