#!/usr/bin/env python3
"""Hook: valida questoes.jsonl antes de permitir Write/Edit.

Lê JSON do stdin (formato PreToolUse), extrai file_path.
Se for questoes.jsonl, roda normalizar_jsonl.py --check.
Se falhar, imprime JSON para bloquear (permissionDecision: deny).
"""
import json
import sys
import subprocess
from pathlib import Path

def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path") or tool_input.get("path", "")

    file_path = str(file_path).replace("\\", "/")

    if not file_path.endswith("questoes.jsonl"):
        sys.exit(0)

    project_dir = Path(__file__).parent.parent.resolve()

    result = subprocess.run(
        [sys.executable, "normalizar_jsonl.py", "--check"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=60
    )

    if result.returncode != 0:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"normalizar_jsonl.py --check falhou:\n{result.stdout}\n{result.stderr}"
            }
        }
        json.dump(output, sys.stdout)
        sys.exit(0)

    sys.exit(0)

if __name__ == "__main__":
    main()