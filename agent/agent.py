"""Optional Managed Deep Agent scaffold for revisao-ifg.

Requires: pip install managed_deepagents (and `mda`), plus model provider keys.
Not connected to LangSmith here. Static site remains independent.
"""
from __future__ import annotations

import os

try:
    from managed_deepagents import define_deep_agent
except ImportError:  # keep project tests/static site working without `mda`
    define_deep_agent = None  # type: ignore[assignment]

NAME = "revisao-ifg"
MODEL = os.environ.get("REVISAO_IFG_MODEL", "openai:gpt-4.1-mini")

if define_deep_agent is None:
    agent = None
else:
    agent = define_deep_agent(
        name=NAME,
        model=MODEL,
    )
