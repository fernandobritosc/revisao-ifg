"""Pydantic AI agent for revisao-ifg.

Replaces the optional LangChain/Managed Deep Agents scaffold.
No automatic editing. Human approval + tests + git remain required.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_ai import Agent

PROJECT_ROOT = Path(__file__).resolve().parents[1]
NAME = "revisao-ifg"
DEFAULT_MODEL = os.environ.get("REVISAO_IFG_MODEL", "test")

INSTRUCTIONS = """Voce e um agente de revisao do concurso IFG cargo 301 no projeto revisao-ifg.

Regras:
- leia AGENTS.md antes de responder.
- aprenda com questoes, nao com PDF transcrevido.
- bruto se acumula; explicacao se comprime.
- fonte vem da resolucao da questao; nunca invente artigo/lei/edicao.
- nao edite index.html na mao.
- nao invente incidencia; mesmo nucleo funde; nucleo novo cria.
- registre resposta_dada/gabarito/acerto; sem informar, null ou pergunte.
- python normalizar_jsonl.py; python build.py; python test_rapido.py.
- harness engineering: observe erros reais; proponha patch pequeno; humano aprova; teste; commit; revert.
- NUNCA aplique mudanca, auto-merge, auto-edit ou auto-push.
- memoria: memory/AGENTS.md, memory/casos/, memory/usuarios/.
- evals: evals/ + test_rapido.py.
"""


class HarnessProposal(BaseModel):
    summary: str
    evidence: list[str] = Field(default_factory=list)
    files_to_change: list[str] = Field(default_factory=list)
    proposed_patch: str | None = None
    tests_to_run: list[str] = Field(default_factory=list)
    risk: Literal["low", "medium", "high"] = "medium"
    needs_human_approval: bool = True


def create_agent(model: str | None = None) -> Agent:
    return Agent(
        model or DEFAULT_MODEL,
        name=NAME,
        instructions=INSTRUCTIONS,
        output_type=HarnessProposal,
    )


agent = create_agent()


@agent.tool_plain
def read_agents_md() -> str:
    """Read project AGENTS.md rules."""
    return (PROJECT_ROOT / "AGENTS.md").read_text(encoding="utf-8")


@agent.tool_plain
def read_mapa_json() -> str:
    """Read mapa.json. Read-only."""
    return (PROJECT_ROOT / "mapa.json").read_text(encoding="utf-8")


@agent.tool_plain
def list_questoes_jsonl() -> str:
    """Read questoes.jsonl. Read-only."""
    return (PROJECT_ROOT / "questoes.jsonl").read_text(encoding="utf-8")


@agent.tool_plain
def read_harness_engineering() -> str:
    """Read harness engineering rules."""
    return (PROJECT_ROOT / "HARNESS-ENGINEERING.md").read_text(encoding="utf-8")


@agent.tool_plain
def run_rapido_tests() -> str:
    """Run python test_rapido.py. Read-only validation; does not edit."""
    proc = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "test_rapido.py")],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        timeout=120,
    )
    out = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    return f"returncode={proc.returncode}\n{out[-6000:]}"
