#!/usr/bin/env python3
"""Padroniza o questoes.jsonl num único formato (item 4 do relatório).

O arquivo bruto cresceu com dois formatos: 12 linhas sem gabarito/resposta_dada
e 11 com eles. Este script reescreve **todas** as linhas com o superconjunto de
campos, na ordem canônica, sem tocar no conteúdo do campo `bruto`.

- `gabarito` e `resposta_dada` ausentes viram `null` (explicitamente, não omitidos).
- Nenhuma linha é apagada, reordenada ou reescrita em conteúdo.
- Falha se houver ID duplicado ou linha inválida.
- É idempotente: rodar duas vezes não muda nada.

Uso:
    python normalizar_jsonl.py             # reescreve questoes.jsonl
    python normalizar_jsonl.py --check     # só verifica, não escreve
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARQUIVO = ROOT / "questoes.jsonl"

# Ordem canônica dos campos. Campos novos entram no fim desta lista.
CAMPOS = (
    "id",
    "assunto",
    "banca",
    "ano",
    "cargo",
    "acerto",
    "resposta_dada",
    "gabarito",
    "bruto",
)
OBRIGATORIOS = ("id", "assunto", "banca", "ano", "cargo", "acerto", "bruto")


def normalizar(registro: dict) -> dict:
    faltando = [c for c in OBRIGATORIOS if c not in registro]
    if faltando:
        raise ValueError(f"id={registro.get('id')!r}: faltam campos {faltando}")

    padronizado = {campo: registro.get(campo) for campo in CAMPOS}
    # Preserva qualquer campo extra que alguém venha a adicionar no futuro.
    for chave, valor in registro.items():
        if chave not in padronizado:
            padronizado[chave] = valor

    if not isinstance(padronizado["acerto"], bool):
        raise ValueError(f"id={registro['id']!r}: 'acerto' precisa ser true/false")
    if not isinstance(padronizado["bruto"], str) or not padronizado["bruto"].strip():
        raise ValueError(f"id={padronizado['id']!r}: 'bruto' vazio")
    if padronizado["acerto"] is False and not padronizado["resposta_dada"]:
        raise ValueError(
            f"id={padronizado['id']!r}: questão marcada como erro sem 'resposta_dada'"
        )
    return padronizado


def carregar(caminho: Path) -> list[dict]:
    registros, vistos = [], set()
    with caminho.open(encoding="utf-8") as arquivo:
        for numero, linha in enumerate(arquivo, 1):
            if not linha.strip():
                continue
            try:
                registro = json.loads(linha)
            except json.JSONDecodeError as erro:
                raise SystemExit(f"linha {numero}: JSON inválido ({erro})") from erro
            registro = normalizar(registro)
            if registro["id"] in vistos:
                raise SystemExit(f"linha {numero}: id duplicado {registro['id']!r}")
            vistos.add(registro["id"])
            registros.append(registro)
    return registros


def digerir(registros: list[dict]) -> str:
    return "".join(
        json.dumps(r, ensure_ascii=False, separators=(", ", ": ")) + "\n"
        for r in registros
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Padroniza questoes.jsonl.")
    parser.add_argument("--arquivo", type=Path, default=ARQUIVO)
    parser.add_argument("--check", action="store_true", help="só verifica, não escreve")
    args = parser.parse_args()

    registros = carregar(args.arquivo)
    novo = digerir(registros)
    atual = args.arquivo.read_text(encoding="utf-8")
    mudou = novo != atual

    if args.check:
        print(
            f"{'DIFERENTE' if mudou else 'OK'}  {args.arquivo.name}: "
            f"{len(registros)} questões, formato {'a padronizar' if mudou else 'já padronizado'}."
        )
        return 1 if mudou else 0

    if mudou:
        args.arquivo.write_text(novo, encoding="utf-8")
    sem = sum(1 for r in registros if r["gabarito"] is None)
    print(
        f"OK  {args.arquivo.name}: {len(registros)} questões padronizadas "
        f"({sem} sem gabarito registrado, campo agora explícito como null)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
