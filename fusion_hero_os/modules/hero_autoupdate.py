"""HeroAutoupdateCoreModule — logisches 1-Min-Polling + 5-Min-Android-Erinnerung."""

from __future__ import annotations

from typing import Any

from fusion_hero_os.core.base_module import BaseModule
from fusion_hero_os.core.hero_autoupdate import get_hero_autoupdate


class HeroAutoupdateCoreModule(BaseModule):
    """``process(payload)`` Aktionen:

    - ``status`` (default) — Idle, Poll-Zähler, Android-Notify-Config
    - ``touch`` — Interaktion zum Held markieren (setzt Idle-Timer zurück)
    - ``tick`` — einen logischen Poll-Zyklus ausführen
    - ``startup`` — Startup-Notification ans Android senden
    - ``config`` — aktive Defaults (1 Min / 5 Min)
    """

    def process(self, payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
        payload = payload or {}
        action = str(payload.get("action", "status")).lower()
        svc = get_hero_autoupdate()

        if action == "status":
            return svc.status()
        if action == "touch":
            return svc.touch(source=str(payload.get("source", "module")))
        if action == "tick":
            return svc.tick(
                force_reminder=bool(payload.get("force_reminder", False)),
                do_fetch=bool(payload.get("do_fetch", False)),
            )
        if action == "startup":
            return {"ok": True, "notify": svc.notify_startup()}
        if action == "config":
            st = svc.status()
            return {
                "ok": True,
                "poll_interval_sec": st["poll_interval_sec"],
                "reminder_after_sec": st["reminder_after_sec"],
                "android_channel": "system_notification",
                "android_notify_configured": st["android_notify_configured"],
                "enabled": st["enabled"],
            }
        raise ValueError(f"Unbekannte action: {action!r}")
