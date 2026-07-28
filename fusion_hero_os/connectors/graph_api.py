"""Unified Graph API hub for all connectors.

Dry-run by default. Live HTTP only when:
  1) connector token env is set, AND
  2) FUSION_GRAPH_LIVE=1 (or force_live=True on the call)

Code honesty: no fake success without would_execute=True.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "graph_api_connectors.yaml"


def _load_yaml() -> dict[str, Any]:
    if not CONFIG_PATH.is_file():
        return {}
    try:
        import yaml  # type: ignore

        return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _env(name: str) -> str:
    return (os.environ.get(name) or "").strip()


def _live_enabled(force: bool = False) -> bool:
    if force:
        return True
    return _env("FUSION_GRAPH_LIVE").lower() in ("1", "true", "yes", "on")


@dataclass
class GraphConnectorSpec:
    id: str
    kind: str
    skill_module: str
    base_url: str
    env_token: str
    actions: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def token(self) -> str:
        t = _env(self.env_token)
        if t:
            return t
        alt = self.extra.get("alt_token")
        if alt:
            return _env(str(alt))
        return ""

    def available(self) -> bool:
        return bool(self.token())


class GraphAPIHub:
    """Routes graph/REST operations across registered connectors."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config if config is not None else _load_yaml()
        self.defaults = dict(self.config.get("defaults") or {})
        self.timeout = float(self.defaults.get("timeout_sec") or 30)
        self.api_version = str(self.defaults.get("api_version") or "v21.0")
        self.connectors: dict[str, GraphConnectorSpec] = {}
        for cid, raw in (self.config.get("connectors") or {}).items():
            if not isinstance(raw, dict):
                continue
            self.connectors[cid] = GraphConnectorSpec(
                id=cid,
                kind=str(raw.get("kind") or "rest"),
                skill_module=str(raw.get("skill_module") or "GenericCoreModule"),
                base_url=str(raw.get("base_url") or "").rstrip("/"),
                env_token=str(raw.get("env_token") or ""),
                actions=list(raw.get("actions") or []),
                extra={k: v for k, v in raw.items() if k not in {
                    "kind", "skill_module", "base_url", "env_token", "actions"
                }},
            )

    def list_connectors(self) -> dict[str, Any]:
        out = {}
        for cid, c in self.connectors.items():
            out[cid] = {
                "id": cid,
                "kind": c.kind,
                "skill_module": c.skill_module,
                "base_url": c.base_url,
                "token_env": c.env_token,
                "token_present": c.available(),
                "live_ready": c.available() and _live_enabled(),
                "actions": c.actions,
                "mode": "LIVE_READY" if (c.available() and _live_enabled()) else (
                    "TOKEN_PRESENT_DRY" if c.available() else "DRY-RUN"
                ),
            }
        return {
            "ok": True,
            "platform_version": self.config.get("platform_version"),
            "policy": self.config.get("policy"),
            "fusion_graph_live": _live_enabled(),
            "connectors": out,
        }

    def status(self, connector_id: str) -> dict[str, Any]:
        c = self.connectors.get(connector_id)
        if not c:
            return {"ok": False, "error": f"unknown connector: {connector_id}"}
        return {
            "ok": True,
            "connector": connector_id,
            "kind": c.kind,
            "available": c.available(),
            "live_enabled": _live_enabled(),
            "would_execute": c.available() and _live_enabled(),
            "actions": c.actions,
            "public_profile": c.extra.get("public_profile"),
            "note": (
                "Live Graph calls require token + FUSION_GRAPH_LIVE=1"
                if not (c.available() and _live_enabled())
                else "Live mode armed"
            ),
        }

    def _dry(
        self,
        connector_id: str,
        action: str,
        *,
        method: str = "GET",
        path: str = "",
        body: dict[str, Any] | None = None,
        reason: str = "",
    ) -> dict[str, Any]:
        c = self.connectors.get(connector_id)
        return {
            "ok": True,
            "connector": connector_id,
            "action": action,
            "method": method,
            "path": path,
            "body": body or {},
            "would_execute": False,
            "available": bool(c and c.available()),
            "live_enabled": _live_enabled(),
            "note": reason
            or (
                "DRY-RUN: set token env + FUSION_GRAPH_LIVE=1 to execute real Graph API call"
            ),
        }

    def request(
        self,
        connector_id: str,
        *,
        method: str = "GET",
        path: str = "",
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        action: str = "request",
        force_live: bool = False,
    ) -> dict[str, Any]:
        c = self.connectors.get(connector_id)
        if not c:
            return {"ok": False, "error": f"unknown connector: {connector_id}"}

        live = _live_enabled(force_live) and c.available()
        if not live:
            reason = []
            if not c.available():
                reason.append(f"missing env {c.env_token}")
            if not _live_enabled(force_live):
                reason.append("FUSION_GRAPH_LIVE not set")
            return self._dry(
                connector_id,
                action,
                method=method,
                path=path,
                body=body,
                reason="DRY-RUN: " + "; ".join(reason),
            )

        # Build URL
        if c.kind == "meta_graph":
            url = f"{c.base_url}/{self.api_version}/{path.lstrip('/')}"
        else:
            url = f"{c.base_url}/{path.lstrip('/')}" if path else c.base_url

        q = dict(query or {})
        if c.kind == "meta_graph" and "access_token" not in q:
            q["access_token"] = c.token()
        if q:
            url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(
                {k: v for k, v in q.items() if v is not None}
            )

        headers = {
            "User-Agent": "FusionHeroOS-GraphAPIHub/12.0",
            "Accept": "application/json",
        }
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if c.kind in ("rest", "graphql") and c.token():
            headers["Authorization"] = f"Bearer {c.token()}"
        if connector_id == "notion":
            headers["Notion-Version"] = "2022-06-28"

        try:
            req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                try:
                    parsed = json.loads(raw)
                except Exception:
                    parsed = {"raw": raw[:2000]}
                return {
                    "ok": True,
                    "connector": connector_id,
                    "action": action,
                    "method": method.upper(),
                    "path": path,
                    "would_execute": True,
                    "available": True,
                    "status_code": getattr(resp, "status", 200),
                    "result": parsed,
                    "note": "Live Graph/REST call executed",
                }
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")[:2000]
            return {
                "ok": False,
                "connector": connector_id,
                "action": action,
                "would_execute": True,
                "available": True,
                "status_code": e.code,
                "error": err_body,
                "note": "Live call failed (HTTP error)",
            }
        except Exception as e:  # noqa: BLE001
            return {
                "ok": False,
                "connector": connector_id,
                "action": action,
                "would_execute": True,
                "available": True,
                "error": str(e)[:300],
                "note": "Live call failed",
            }

    # --- Instagram convenience (Meta Graph) ---------------------------------

    def instagram_publish(
        self,
        *,
        image_url: str,
        caption: str,
        force_live: bool = False,
    ) -> dict[str, Any]:
        """Two-step IG publish: media container → media_publish."""
        c = self.connectors.get("instagram")
        if not c:
            return {"ok": False, "error": "instagram connector missing from config"}
        user_id = _env(str(c.extra.get("env_user_id") or "IG_USER_ID"))
        if not user_id:
            plan = self._dry(
                "instagram",
                "media_publish",
                method="POST",
                path="{ig-user-id}/media",
                body={"image_url": image_url, "caption": caption},
                reason="DRY-RUN: set IG_USER_ID + INSTAGRAM_ACCESS_TOKEN + FUSION_GRAPH_LIVE=1",
            )
            plan["steps"] = ["media_container", "media_publish"]
            plan["image_url"] = image_url
            plan["caption_preview"] = (caption or "")[:200]
            return plan

        # Step 1 container
        step1 = self.request(
            "instagram",
            method="POST",
            path=f"{user_id}/media",
            query={
                "image_url": image_url,
                "caption": caption,
            },
            action="media_container",
            force_live=force_live,
        )
        if not step1.get("would_execute"):
            step1["steps"] = ["media_container", "media_publish"]
            return step1
        if not step1.get("ok"):
            return {"ok": False, "step": "media_container", "detail": step1}

        creation_id = None
        res = step1.get("result") or {}
        if isinstance(res, dict):
            creation_id = res.get("id")
        if not creation_id:
            return {
                "ok": False,
                "step": "media_container",
                "error": "no creation_id in response",
                "detail": step1,
            }

        step2 = self.request(
            "instagram",
            method="POST",
            path=f"{user_id}/media_publish",
            query={"creation_id": creation_id},
            action="media_publish",
            force_live=force_live,
        )
        return {
            "ok": bool(step2.get("ok")),
            "would_execute": True,
            "steps": {
                "media_container": step1,
                "media_publish": step2,
            },
            "creation_id": creation_id,
            "note": "Instagram Graph two-step publish",
        }

    def dispatch(self, connector_id: str, action: str, **kwargs: Any) -> dict[str, Any]:
        """High-level action router per connector."""
        action = (action or "status").lower()
        if action == "status":
            return self.status(connector_id)
        if connector_id == "instagram" and action in ("publish", "media_publish"):
            return self.instagram_publish(
                image_url=str(kwargs.get("image_url") or ""),
                caption=str(kwargs.get("caption") or ""),
                force_live=bool(kwargs.get("force_live")),
            )
        if connector_id == "instagram" and action == "me":
            return self.request("instagram", path="me", query={"fields": "id,username"}, action="me", force_live=bool(kwargs.get("force_live")))
        if connector_id == "github_graphql" and action == "query":
            q = kwargs.get("query") or "{ viewer { login } }"
            return self.request(
                "github_graphql",
                method="POST",
                path="",
                body={"query": q},
                action="query",
                force_live=bool(kwargs.get("force_live")),
            )
        if action in ("get", "request"):
            return self.request(
                connector_id,
                method=str(kwargs.get("method") or "GET"),
                path=str(kwargs.get("path") or ""),
                query=kwargs.get("query"),
                body=kwargs.get("body"),
                action=action,
                force_live=bool(kwargs.get("force_live")),
            )
        # generic status-like
        return self.status(connector_id)


def build_default_hub() -> GraphAPIHub:
    return GraphAPIHub()


def status_all() -> dict[str, Any]:
    return build_default_hub().list_connectors()
