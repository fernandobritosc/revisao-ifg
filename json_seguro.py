#!/usr/bin/env python3
"""Leitura de JSON com duas proteções que o ``json`` puro não tem.

- chave repetida no mesmo objeto (erro de digitação silencioso);
- constantes ``NaN`` / ``Infinity`` / ``-Infinity`` (JSON inválido).

Usado por ``build.py`` e ``normalizar_jsonl.py``. Sem dependências externas.
"""

from __future__ import annotations

import json


def _sem_duplicadas(pares):
    objeto = {}
    for chave, valor in pares:
        if chave in objeto:
            raise ValueError(f"chave duplicada: {chave!r}")
        objeto[chave] = valor
    return objeto


def _sem_constantes(valor):
    raise ValueError(f"constante JSON não permitida: {valor}")


def loads(texto: str):
    """Equivale a json.loads, mas rejeita chaves duplicadas e NaN/Infinity."""
    return json.loads(
        texto,
        object_pairs_hook=_sem_duplicadas,
        parse_constant=_sem_constantes,
    )
