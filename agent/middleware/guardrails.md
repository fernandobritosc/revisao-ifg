# Guardrails / hooks

## Antes de tool call
- confirmar escopo; nao editar `index.html`.
- nao inventar fonte/artigo; nao editar `bruto`.
- JSON seguro; nao NaN; nao chaves duplicadas.
- nao apagar dados sem confirmacao.
- nao vazar segredos.

## Apos tool call
- `python -m json.tool mapa.json`
- `python normalizar_jsonl.py --check`
- `python test_rapido.py`

## Fim de conversa / harness
- se incerteza ou erro recorrente: escalar `memory/casos/`.
- propor patch; humano aprova; commit revertivel.
