# -*- coding: utf-8 -*-
"""Supabase-Integration für das ALTE_Frau_95g / Fusion Hero OS Dashboard (FastAPI Backend).

Liest die Client-Konfiguration aus Umgebungsvariablen (.env) und stellt einen
lazy-initialisierten Supabase-Client bereit. Alle Fehler werden defensiv
behandelt, damit das Dashboard auch ohne erreichbares Supabase startet
(konsistent mit den optionalen Imports in app.py).

Projekt: https://supabase.com/dashboard/project/swmmoxhdzarmoupyssqe

Status-Reporting ist bewusst ehrlich gehalten und unterscheidet:
  - configured         : .env-Variablen vorhanden?
  - package_available  : supabase-Paket importierbar?
  - client_initialized : create_client() erfolgreich?
  - probe (opt-in)     : echter Netzwerk-Check gegen das Supabase-Projekt

Der PUBLISHABLE_KEY ist per Design öffentlich (für Browser-Code gedacht) und
wird serverseitig hier verwendet; der Zugriff bleibt durch Row-Level-Security
(RLS) auf Supabase-Seite begrenzt.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

# --- .env laden (neben diesem Modul) ----------------------------------------
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).with_name(".env"))
except Exception:
    pass


def _env(*names: str, default: str = "") -> str:
    """Liest die erste gesetzte Variable aus mehreren möglichen Namen (Alias-Support)."""
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return default


# --- supabase-Paket optional importieren ------------------------------------
SUPABASE_URL = _env("SUPABASE_URL", "PUBLIC_SUPABASE_URL")
SUPABASE_KEY = _env("SUPABASE_PUBLISHABLE_KEY", "PUBLIC_SUPABASE_PUBLISHABLE_KEY")
SUPABASE_SECRET_KEY = _env("SUPABASE_SECRET_KEY")
SUPABASE_JWKS_URL = _env("SUPABASE_JWKS_URL")
SUPABASE_PROJECT_REF = _env("SUPABASE_PROJECT_REF", "PUBLIC_SUPABASE_PROJECT_REF", default="swmmoxhdzarmoupyssqe")

try:
    from supabase import Client, create_client  # type: ignore
    import supabase as _supabase_pkg

    _SUPABASE_VERSION: Optional[str] = getattr(_supabase_pkg, "__version__", None)
    _PACKAGE_AVAILABLE = True
    _IMPORT_ERROR = ""
except Exception as e:  # pragma: no cover - nur ohne Paket
    create_client = None  # type: ignore
    Client = Any  # type: ignore
    _SUPABASE_VERSION = None
    _PACKAGE_AVAILABLE = False
    _IMPORT_ERROR = str(e)

_client: "Optional[Client]" = None
_client_error: str = ""


def is_configured() -> bool:
    """True, wenn URL und Key aus der .env vorhanden sind (beide Namensvarianten)."""
    return bool(SUPABASE_URL and SUPABASE_KEY)


def get_client() -> "Optional[Client]":
    """Lazy-Singleton. Gibt None zurück, wenn nicht konfiguriert oder bei Fehler.

    Hinweis: create_client() baut nur den Client auf und macht KEINEN
    Netzwerk-Aufruf. Echte Erreichbarkeit prüft probe()/status(probe=True).
    """
    global _client, _client_error
    if _client is not None:
        return _client
    if not _PACKAGE_AVAILABLE or create_client is None:
        _client_error = f"supabase package not available: {_IMPORT_ERROR}"
        return None
    if not is_configured():
        _client_error = "missing SUPABASE_URL/PUBLIC_SUPABASE_URL oder SUPABASE_PUBLISHABLE_KEY/PUBLIC_SUPABASE_PUBLISHABLE_KEY"
        return None
    try:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        _client_error = ""
    except Exception as e:
        _client = None
        _client_error = f"create_client failed: {e}"
    return _client


def probe(timeout: float = 4.0) -> Dict[str, Any]:
    """Echter, tabellen-unabhängiger Reachability-Check via GoTrue-Settings.

    Endpoint: GET /auth/v1/settings (akzeptiert den PUBLISHABLE/anon-Key und
    liefert dann 200). Bewusst NICHT der PostgREST-Root /rest/v1/, da dieser im
    neuen Supabase-Key-System nur SECRET-Keys erlaubt und mit einem Publishable-
    Key 401 zurückgibt – das wäre kein aussagekräftiger Check.

    Felder:
      reachable    : Projekt hat überhaupt geantwortet (HTTP < 500, keine Exception)
      key_accepted : Publishable-Key wurde akzeptiert (HTTP 200)

    Blockierender Aufruf (httpx.get) – aus async-Code via Threadpool aufrufen.
    """
    result: Dict[str, Any] = {
        "reachable": False,
        "key_accepted": False,
        "http_status": None,
        "latency_ms": None,
        "error": None,
        "project_ref": SUPABASE_PROJECT_REF,
    }
    if not is_configured():
        result["error"] = "not configured"
        return result
    try:
        import httpx  # supabase-Abhängigkeit -> vorhanden
    except Exception as e:
        result["error"] = f"httpx not available: {e}"
        return result

    url = f"{SUPABASE_URL.rstrip('/')}/auth/v1/settings"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    start = time.perf_counter()
    try:
        resp = httpx.get(url, headers=headers, timeout=timeout)
        result["http_status"] = resp.status_code
        result["latency_ms"] = round((time.perf_counter() - start) * 1000, 1)
        result["reachable"] = resp.status_code < 500
        result["key_accepted"] = resp.status_code == 200
    except Exception as e:
        result["latency_ms"] = round((time.perf_counter() - start) * 1000, 1)
        result["error"] = str(e)
    return result


def status(do_probe: bool = False, timeout: float = 4.0) -> Dict[str, Any]:
    """Ehrlicher Status. Mit do_probe=True zusätzlich echter Netzwerk-Check."""
    client = get_client()
    info: Dict[str, Any] = {
        "configured": is_configured(),
        "package_available": _PACKAGE_AVAILABLE,
        "package_version": _SUPABASE_VERSION,
        "url": SUPABASE_URL or None,
        "jwks_url": SUPABASE_JWKS_URL or None,
        "secret_key_configured": bool(SUPABASE_SECRET_KEY),
        "project_ref": SUPABASE_PROJECT_REF,
        "dashboard_url": f"https://supabase.com/dashboard/project/{SUPABASE_PROJECT_REF}",
        "client_initialized": client is not None,
        "error": _client_error or None,
    }
    if do_probe:
        info["probe"] = probe(timeout=timeout)
    return info
