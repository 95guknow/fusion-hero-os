#!/usr/bin/env python3
"""CLI: Status aller LLM-Frameworks (API-Key gesetzt ja/nein)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from llm_frameworks import connector_status, invoke, list_frameworks

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        provider = sys.argv[2] if len(sys.argv) > 2 else "grok"
        result = invoke(provider, "Antworte nur mit: OK", role="worker")
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        sys.exit(0 if result.ok else 1)

    status = connector_status()
    print(json.dumps(status, indent=2, ensure_ascii=False))
    print(f"\nFrameworks: {', '.join(list_frameworks())}")
    sys.exit(0 if status.get("any_live") else 1)