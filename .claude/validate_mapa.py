#!/usr/bin/env python3
"""Hook: valida mapa.json antes de permitir Write/Edit.

Lê JSON do stdin (formato PreToolUse), extrai file_path.
Se for mapa.json, roda test_rapido.py e build.py.
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
        sys.exit(0)  # não bloqueia se não conseguir ler

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path") or tool_input.get("path", "")

    # Normalizar caminho
    file_path = str(file_path).replace("\\", "/")

    # Só valida mapa.json
    if not file_path.endswith("mapa.json"):
        sys.exit(0)

    project_dir = Path(__file__).parent.parent.resolve()

    # Rodar test_rapido.py
    result = subprocess.run(
        [sys.executable, "test_rapido.py"],
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
                "permissionDecisionReason": f"test_rapido.py falhou:\n{result.stdout}\n{result.stderr}"
            }
        }
        json.dump(output, sys.stdout)
        sys.exit(0)

    # Rodar build.py
    result = subprocess.run(
        [sys.executable, "build.py"],
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
                "permissionDecisionReason": f"build.py falhou:\n{result.stdout}\n{result.stderr}"
            }
        }
        json.dump(output, sys.stdout)
        sys.exit(0)

    # Sucesso - não imprime nada (permite)
    sys.exit(0)

if __name__ == "__main__":
    main()