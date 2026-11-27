"""Smoke test Pydantic AI without API key.

Uses model='test'. Does not edit. Does not auto-apply.
"""
from __future__ import annotations

from agent.agent import create_agent


def main() -> int:
    agent = create_agent(model="test")
    result = agent.run_sync("Teste local: proponha melhoria mas nao aplique.")
    print(type(result.output).__name__)
    print(result.output.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
