---
name: revisao-ifg
description: Registrar questoes, atualizar incidencias/pegadinhas, gerar site, melhorar harness com humano no loop.
---

# Revisao IFG

Use para trabalhar em `C:\IFG\revisao-ifg`.

## Workflow
1. Ler `AGENTS.md`.
2. Identificar ID, banca, ano, cargo, acerto/erro, assunto.
3. Gravar bruto em `questoes.jsonl`.
4. Classificar no no do edital.
5. Fundir mesmo nucleo (`+1`, ID, nuance) ou criar incidencia.
6. Atualizar `questoes`, `erros`, `fontes`, `decore`, `explicacao`.
7. `python normalizar_jsonl.py`, `python build.py`, `python test_rapido.py`.
8. git commit/push.
9. **harness**: se erro recorrente, propor patch; humano aprova.

## Harness
- memory: `memory/AGENTS.md`, `memory/casos/`, `memory/usuarios/`
- evals: `evals/`, `test_rapido.py`
- no auto-merge.
