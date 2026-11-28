#!/usr/bin/env python3
"""Hook: roda eval harness antes de permitir push (via PreToolUse no git push).

Lê JSON do stdin (formato PreToolUse), verifica se é git push.
Se for, roda evals/run.py --model sonnet.
Se falhar (< 80%), bloqueia o push com permissionDecision: deny.
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

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Só intercepta Bash com git push
    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command or "git push" not in command:
        sys.exit(0)

    project_dir = Path(__file__).parent.parent.resolve()

    # Rodar eval harness
    result = subprocess.run(
        [sys.executable, "evals/run.py", "--model", "sonnet"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=180
    )

    if result.returncode != 0:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Eval harness falhou (acurácia < 80%):\n{result.stdout}\n{result.stderr}"
            }
        }
        json.dump(output, sys.stdout)
        sys.exit(0)

    sys.exit(0)

if __name__ == "__main__":
    main()