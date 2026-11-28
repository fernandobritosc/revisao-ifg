#!/usr/bin/env python3
"""Hook: auto-commit + push após editar mapa.json ou questoes.jsonl."""
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
    tool_response = data.get("tool_response", {})

    if tool_name not in ("Write", "Edit"):
        sys.exit(0)

    file_path = tool_input.get("file_path") or tool_input.get("path", "")
    if not file_path:
        file_path = tool_response.get("filePath", "")

    file_path = str(file_path).replace("\\", "/")

    if not (file_path.endswith("mapa.json") or file_path.endswith("questoes.jsonl")):
        sys.exit(0)

    project_dir = Path(__file__).parent.parent.resolve()

    result = subprocess.run(
        ["git", "add", file_path],
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=30
    )
    if result.returncode != 0:
        print(f"git add falhou: {result.stderr}", file=sys.stderr)
        sys.exit(0)

    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=project_dir,
        capture_output=True,
        timeout=10
    )
    if result.returncode == 0:
        sys.exit(0)

    arquivo = Path(file_path).name
    msg = "update: mapa.json atualizado via hook" if arquivo == "mapa.json" else "update: questoes.jsonl atualizado via hook"

    result = subprocess.run(
        ["git", "commit", "-m", msg],
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=30
    )
    if result.returncode != 0:
        print(f"git commit falhou: {result.stderr}", file=sys.stderr)
        sys.exit(0)

    result = subprocess.run(
        ["git", "push"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=60
    )
    if result.returncode != 0:
        print(f"git push falhou: {result.stderr}", file=sys.stderr)
        sys.exit(0)

    sys.exit(0)

if __name__ == "__main__":
    main()