# -*- coding: utf-8 -*-
"""
structured_output.py — Schema-validierte LLM-Outputs mit Repair-Retry
=====================================================================
Bringt die "Structured Output"-Fähigkeit moderner Harnesses in Fusion Hero OS:
ein Backend wird aufgefordert, JSON nach Schema zu liefern; die Antwort wird
extrahiert, gegen das Schema validiert und bei Fehlern mit einem Repair-Prompt
erneut angefragt.

Ehrlich (Code-Honesty):
  * Unterstützt eine UNTERMENGE von JSON Schema: type, properties, required,
    items, enum, minimum/maximum, minLength/maxLength. Kein $ref, kein oneOf,
    keine Pattern-Validierung. Für volle Abdeckung -> jsonschema-Paket.
  * Die Extraktion sucht den ersten balancierten JSON-Block (auch in
    ```json-Fences). Mehrere JSON-Blöcke in einer Antwort: nur der erste zählt.

Aufruf:  python structured_output.py   # Demo mit Fake-Backend
"""
from __future__ import annotations

import json
import os
from typing import Any, Callable, Dict, List, Optional, Tuple

BackendFn = Callable[[str, str], str]  # (prompt, role) -> antwort

_MAX_RETRIES = int(os.getenv("FUSION_STRUCTURED_RETRIES", "2"))


# ---------------------------------------------------------------------------
# JSON-Extraktion
# ---------------------------------------------------------------------------

def extract_json(text: str) -> Optional[Any]:
    """Extrahiert den ersten balancierten JSON-Block ({} oder []) aus Text."""
    if not text:
        return None
    s = str(text)
    # Code-Fences bevorzugen
    if "```" in s:
        for part in s.split("```"):
            candidate = part.strip()
            if candidate.startswith("json"):
                candidate = candidate[4:].strip()
            if candidate[:1] in "{[":
                parsed = _parse_balanced(candidate)
                if parsed is not None:
                    return parsed
    return _parse_balanced(s)


def _parse_balanced(s: str) -> Optional[Any]:
    """Findet ab dem ersten { oder [ den balancierten Block und parst ihn."""
    start = None
    for i, ch in enumerate(s):
        if ch in "{[":
            start = i
            break
    if start is None:
        return None
    opener = s[start]
    closer = "}" if opener == "{" else "]"
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(s)):
        ch = s[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(s[start:i + 1])
                except Exception:
                    return None
    return None


# ---------------------------------------------------------------------------
# Schema-Validierung (Untermenge)
# ---------------------------------------------------------------------------

_TYPE_MAP = {
    "object": dict,
    "array": list,
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "null": type(None),
}


def validate(instance: Any, schema: Dict[str, Any], path: str = "$") -> List[str]:
    """Validiert instance gegen die unterstützte Schema-Untermenge.

    Returns: Liste von Problemen (leer = gültig).
    """
    issues: List[str] = []
    stype = schema.get("type")
    if stype:
        expected = _TYPE_MAP.get(stype)
        if expected is None:
            issues.append(f"{path}: unbekannter Schema-Typ {stype!r}")
            return issues
        if stype == "integer" and isinstance(instance, bool):
            issues.append(f"{path}: erwartet integer, ist boolean")
            return issues
        if not isinstance(instance, expected):
            issues.append(f"{path}: erwartet {stype}, ist {type(instance).__name__}")
            return issues

    if "enum" in schema and instance not in schema["enum"]:
        issues.append(f"{path}: Wert {instance!r} nicht in enum {schema['enum']!r}")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            issues.append(f"{path}: {instance} < minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            issues.append(f"{path}: {instance} > maximum {schema['maximum']}")

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            issues.append(f"{path}: Länge {len(instance)} < minLength {schema['minLength']}")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            issues.append(f"{path}: Länge {len(instance)} > maxLength {schema['maxLength']}")

    if isinstance(instance, dict):
        for req in schema.get("required", []):
            if req not in instance:
                issues.append(f"{path}: Pflichtfeld {req!r} fehlt")
        for key, sub in (schema.get("properties") or {}).items():
            if key in instance:
                issues.extend(validate(instance[key], sub, f"{path}.{key}"))

    if isinstance(instance, list) and "items" in schema:
        for i, item in enumerate(instance):
            issues.extend(validate(item, schema["items"], f"{path}[{i}]"))

    return issues


# ---------------------------------------------------------------------------
# Anfrage-Schleife mit Repair-Retry
# ---------------------------------------------------------------------------

def _schema_instruction(schema: Dict[str, Any]) -> str:
    return (
        "\n\nAntworte AUSSCHLIESSLICH mit einem einzigen JSON-Objekt (kein Text "
        "davor/danach), das exakt diesem Schema entspricht:\n"
        f"```json\n{json.dumps(schema, ensure_ascii=False, indent=1)}\n```"
    )


def request_structured(
    backend: BackendFn,
    prompt: str,
    schema: Dict[str, Any],
    role: str = "agent",
    retries: int = _MAX_RETRIES,
) -> Dict[str, Any]:
    """Fordert schema-konformes JSON vom Backend an; repariert per Retry.

    Returns dict: ok, data (bei Erfolg), attempts, issues (letzter Stand),
    raw (letzte Rohantwort).
    """
    full_prompt = prompt + _schema_instruction(schema)
    raw = ""
    issues: List[str] = []
    attempts = 0
    for attempt in range(1, max(1, retries + 1) + 1):
        attempts = attempt
        try:
            raw = backend(full_prompt, role)
        except Exception as exc:
            issues = [f"backend-fehler: {exc}"]
            continue
        data = extract_json(raw)
        if data is None:
            issues = ["kein JSON-Block in der Antwort gefunden"]
        else:
            issues = validate(data, schema)
            if not issues:
                return {"ok": True, "data": data, "attempts": attempts, "issues": [], "raw": raw}
        # Repair-Prompt für den nächsten Versuch
        full_prompt = (
            prompt
            + _schema_instruction(schema)
            + "\n\nDeine vorherige Antwort war ungültig:\n- "
            + "\n- ".join(issues[:8])
            + f"\n\nVorherige Antwort (gekürzt):\n{str(raw)[:1500]}\n\n"
            "Korrigiere und antworte NUR mit dem gültigen JSON-Objekt."
        )
    return {"ok": False, "data": None, "attempts": attempts, "issues": issues, "raw": raw}


def status() -> Dict[str, Any]:
    return {
        "module": "structured_output",
        "max_retries": _MAX_RETRIES,
        "schema_support": [
            "type", "properties", "required", "items", "enum",
            "minimum", "maximum", "minLength", "maxLength",
        ],
        "honesty": "JSON-Schema-Untermenge; kein $ref/oneOf/pattern — dafür jsonschema-Paket nutzen",
    }


if __name__ == "__main__":
    demo_schema = {
        "type": "object",
        "required": ["idee", "risiko"],
        "properties": {
            "idee": {"type": "string", "minLength": 5},
            "risiko": {"type": "string", "enum": ["niedrig", "mittel", "hoch"]},
        },
    }

    calls = {"n": 0}

    def fake_backend(prompt: str, role: str) -> str:
        calls["n"] += 1
        if calls["n"] == 1:
            return "Hier meine Idee als Fließtext ohne JSON."
        return 'Gern: ```json\n{"idee": "Kontext-Anker pro Schritt", "risiko": "niedrig"}\n```'

    out = request_structured(fake_backend, "Nenne eine Idee gegen Kontextverlust.", demo_schema)
    print(f"ok={out['ok']} attempts={out['attempts']} data={out['data']}")
