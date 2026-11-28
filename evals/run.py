#!/usr/bin/env python3
"""Eval harness: mede acurácia de classificação de assunto e fusão de incidência.

Uso:
    python evals/run.py                    # roda todos
    python evals/run.py --tipo classificacao
    python evals/run.py --tipo fusao
    python evals/run.py --model sonnet     # troca modelo (sonnet/opus/haiku/fable)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
EVALS_DIR = ROOT / "evals"

# Prompt para classificação
PROMPT_CLASSIFICACAO = """Você é um classificador de questões para o concurso IFG 2026 (Assistente em Administração).

Hierarquia de assuntos (mapa.json):
CC-1: Língua Portuguesa (peso 2)
CC-2: Legislação (peso 1)
CC-3: Regime Jurídico Único (peso 1)
CC-4: Processo Administrativo (peso 1)
CE-1: Redação Oficial (peso 3)
CE-2: Noções de Direito Constitucional (peso 3)
CE-3: Noções de Direito Administrativo (peso 3)
CE-4: Noções de Direito Penal (peso 3)
CE-5: Noções de Direito Processual (peso 3)
CE-6: Ética no Serviço Público (peso 3)
CE-7: Noções de Informática (peso 1)

Questão:
{questao}

Responda APENAS com o ID do assunto (ex: CE-1.1, CC-2.3)."""

# Prompt para fusão
PROMPT_FUSAO = """Você decide se uma nova questão deve FUNDIR com incidência existente ou criar NOVA INCIDÊNCIA.

Assunto: {assunto}
Incidências existentes:
{incidencias}

Nova questão:
{questao}

Regras:
- FUNDIR se mesmo núcleo conceitual (mesmo artigo, mesmo princípio, mesma regra), mesmo com palavras diferentes
- NOVA INCIDÊNCIA se núcleo claramente distinto (artigo diferente, princípio diferente, exceção diferente)

Responda APENAS em JSON:
{{"acao": "fundir" ou "nova_incidencia", "incidencia_alvo": "texto da incidência alvo ou null", "razao": "breve" }}"""


def load_cases(tipo: str) -> list[dict[str, Any]]:
    arquivo = EVALS_DIR / f"cases_{tipo}.jsonl"
    if not arquivo.exists():
        return []
    casos = []
    with arquivo.open(encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if linha:
                casos.append(json.loads(linha))
    return casos


def run_llm(prompt: str, model: str = "sonnet") -> str:
    """Chama claude via CLI (precisa estar autenticado)."""
    cmd = ["claude", "-p", prompt, "--model", model]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"Claude CLI falhou: {result.stderr}")
    return result.stdout.strip()


def eval_classificacao(casos: list[dict], model: str) -> dict:
    acertos = 0
    detalhes = []

    for caso in casos:
        prompt = PROMPT_CLASSIFICACAO.format(questao=caso["questao_bruto"])
        try:
            resposta = run_llm(prompt, model)
            previsto = resposta.strip().upper()
            esperado = caso["assunto_esperado"].upper()
            ok = previsto == esperado
            if ok:
                acertos += 1
            detalhes.append({
                "id": caso["id"],
                "esperado": esperado,
                "previsto": previsto,
                "ok": ok,
                "justificativa": caso["justificativa"]
            })
        except Exception as e:
            detalhes.append({
                "id": caso["id"],
                "esperado": caso["assunto_esperado"],
                "previsto": f"ERRO: {e}",
                "ok": False,
                "justificativa": caso["justificativa"]
            })

    total = len(casos)
    return {
        "tipo": "classificacao",
        "total": total,
        "acertos": acertos,
        "acuracia": round(100 * acertos / total, 1) if total else 0,
        "detalhes": detalhes
    }


def eval_fusao(casos: list[dict], model: str) -> dict:
    acertos = 0
    detalhes = []

    for caso in casos:
        incidencias_str = json.dumps(caso["incidencias_existentes"], ensure_ascii=False, indent=2)
        prompt = PROMPT_FUSAO.format(
            assunto=caso["assunto"],
            incidencias=incidencias_str,
            questao=caso["nova_questao"]
        )
        try:
            resposta = run_llm(prompt, model)
            resultado = json.loads(resposta)
            acao_ok = resultado.get("acao") == caso["acao_esperada"]
            alvo_ok = True
            if caso["acao_esperada"] == "fundir":
                alvo_ok = resultado.get("incidencia_alvo") == caso["incidencia_alvo"]
            ok = acao_ok and alvo_ok
            if ok:
                acertos += 1
            detalhes.append({
                "id": caso["id"],
                "esperado_acao": caso["acao_esperada"],
                "previsto_acao": resultado.get("acao"),
                "esperado_alvo": caso["incidencia_alvo"],
                "previsto_alvo": resultado.get("incidencia_alvo"),
                "ok": ok,
                "justificativa": caso["justificativa"]
            })
        except Exception as e:
            detalhes.append({
                "id": caso["id"],
                "esperado_acao": caso["acao_esperada"],
                "previsto_acao": f"ERRO: {e}",
                "ok": False,
                "justificativa": caso["justificativa"]
            })

    total = len(casos)
    return {
        "tipo": "fusao",
        "total": total,
        "acertos": acertos,
        "acuracia": round(100 * acertos / total, 1) if total else 0,
        "detalhes": detalhes
    }


def main():
    parser = argparse.ArgumentParser(description="Eval harness para classificação e fusão")
    parser.add_argument("--tipo", choices=["classificacao", "fusao", "todos"], default="todos")
    parser.add_argument("--model", choices=["sonnet", "opus", "haiku", "fable"], default="sonnet")
    parser.add_argument("--output", help="Arquivo JSON para salvar resultados")
    args = parser.parse_args()

    resultados = []

    if args.tipo in ("classificacao", "todos"):
        casos = load_cases("classificacao")
        if casos:
            print(f"\n[Classificacao] {len(casos)} casos...")
            r = eval_classificacao(casos, args.model)
            resultados.append(r)
            print(f"   Acuracia: {r['acuracia']}% ({r['acertos']}/{r['total']})")
        else:
            print("[AVISO] Nenhum caso de classificacao encontrado")

    if args.tipo in ("fusao", "todos"):
        casos = load_cases("fusao")
        if casos:
            print(f"\n[Fusao] {len(casos)} casos...")
            r = eval_fusao(casos, args.model)
            resultados.append(r)
            print(f"   Acuracia: {r['acuracia']}% ({r['acertos']}/{r['total']})")
        else:
            print("[AVISO] Nenhum caso de fusao encontrado")

    # Resumo geral
    if resultados:
        total_geral = sum(r["total"] for r in resultados)
        acertos_geral = sum(r["acertos"] for r in resultados)
        print(f"\n{'='*50}")
        print(f"GERAL: {round(100*acertos_geral/total_geral,1)}% ({acertos_geral}/{total_geral})")
        print(f"{'='*50}")

        # Mostrar erros
        for r in resultados:
            erros = [d for d in r["detalhes"] if not d["ok"]]
            if erros:
                print(f"\n[ERROS] {r['tipo']}:")
                for e in erros:
                    print(f"  {e['id']}: esperado={e.get('esperado') or e.get('esperado_acao')}, previsto={e.get('previsto') or e.get('previsto_acao')}")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] Resultados salvos em {args.output}")

    # Exit code: 0 se >= 80%, 1 caso contrário
    if resultados:
        geral = sum(r["acertos"] for r in resultados) / sum(r["total"] for r in resultados)
        sys.exit(0 if geral >= 0.8 else 1)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()