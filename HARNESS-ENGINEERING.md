# Harness engineering — revisao-ifg

Transformacao conservadora inspirada em **Managed Deep Agents** + **LangSmith Engine**.
Nao migra o site estatico; preserva `mapa.json + questoes.jsonl + build.py + test_rapido.py`.

## Principio

> Engenharia de harness nao e uma tarefa de uma vez. Melhore **tudo ao redor do modelo**:
> regras, skills, memoria, guardrails, ferramentas, subagentes, fluxos, evals e deploy.

## Mapeamento 1:1 (do video para este projeto)

| Video / docs | No `revisao-ifg` hoje | Alvo |
|---|---|---|
| regras / system prompt | `AGENTS.md`, `README.md`, `PLANO-MELHORIAS.md` | `agent/instructions.md` + raiz |
| skills markdown | `.github`, planos, rotinas implicitas | `agent/skills/revisao-ifg/SKILL.md` |
| memoria principal | `AGENTS.md`, `mapa.json`, `questoes.jsonl` | `memory/AGENTS.md`, `memory/` |
| subagentes / multiagente | OpenCode subagents quando usados | manter; nao inventar |
| MCP / conexoes | OpenCode MCP quando usado | manter; nao inventar |
| hooks / guardrails | `test_rapido.py`, CI, JSON seguro | `agent/middleware/guardrails.md` + testes |
| traces production | ainda sem LangSmith | conectar LangSmith quando houver agente real |
| humano no loop | usuario valida e corrige | obrigatorio |
| inbox de escalonamento | novo | `memory/casos/` |
| context hub | novo | `memory/AGENTS.md`, `memory/casos/`, `memory/usuarios/` |
| memoria por usuario | novo | `memory/usuarios/<id>/` |
| segundo loop retrospectivo | novo | `evals/`, PR/aprovacao manual |
| commits / promover / reverter | git atual | usar `git add -A`, commit, push, `git revert` |
| evals | `test_rapido.py` | `evals/`, dataset + teste |
| resultado | 4/14 -> 13/14 no video | nao repetir; medir meu projeto com `evals/` |

## Dois loops

### Loop 1: memoria principal
- agente revela incerteza quando nao sabe;
- humano corrige;
- salva `memory/casos/*.md`;
- atualiza `memory/AGENTS.md`;
- recupera depois para acertar padroes similares.

### Loop 2: harness retrospectivo
- revisa traces/logs reais;
- encontra erro recorrente;
- propoe patch pequeno em `AGENTS.md`, `agent/instructions.md`, `agent/skills/`, `memory/`, `mapa.json`, `questoes.jsonl`, `build.py`, `test_rapido.py`;
- roda `python test_rapido.py`;
- **humano aprova antes de aplicar**;
- git commit/revert permite reverter.

## Regra de ouro

> **O agente pode propor; nao aplica silenciosamente.**
> Evolucao de sistema com controle total, humano no circuito.

## LangSmith Engine (externo)

Quando houver agente em producao com LangSmith:
1. conectar projeto de tracing;
2. conectar repositorio via GitHub App/GitLab;
3. permitir Engine ler source + abrir PR;
4. **nunca auto-merge**;
5. rodar `python test_rapido.py`;
6. humano revisa, aplica, reverte.
