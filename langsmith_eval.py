"""Smoke test LangSmith usando variaveis de ambiente, sem salvar segredo.

Projeto escolhido: revisao-ifg.
Nao imprime API key. Nao cria traces. Nao sincroniza dataset automaticamente.
"""
from __future__ import annotations

import os
import sys

PROJECT = os.environ.get("LANGSMITH_PROJECT", "revisao-ifg")
TRACING = os.environ.get("LANGSMITH_TRACING", "")


def main() -> int:
    if not os.environ.get("LANGSMITH_API_KEY"):
        print(
            "LANGSMITH_API_KEY nao setada no ambiente; nao vou usar chave colada no chat.\n"
            "Sete fora do repo e rode novamente.",
            file=sys.stderr,
        )
        return 2

    try:
        from langsmith import Client
    except ImportError:
        print("langsmith nao instalado. pip install langsmith", file=sys.stderr)
        return 2

    client = Client()
    # nao imprime secret; nao verifica autorizacao remota sem trace real
    print(f"LangSmith Client criado. project={PROJECT!r} tracing={TRACING!r} api_key=<redacted>")
    print("Sem traces reais ainda; LangSmith Engine exige agente em producao + repo conectado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
