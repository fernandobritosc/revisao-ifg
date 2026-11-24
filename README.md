# Mapa de revisão — Assistente em Administração (IFG, cargo 301)

> **Se você é uma LLM ou uma sessão nova:** leia [`AGENTS.md`](AGENTS.md) antes de qualquer coisa. É o manual de operação e a memória do projeto.

Este projeto **não é um caderno de resumo**. É um **mapa de incidência**: para cada assunto do edital, registro o que a banca realmente cobra, com que frequência e sob que pegadinha.

A teoria do PDF (Estratégia, cursinhos) **não é transcrita**. Ela fica como consulta eventual; quando precisamos dela, registramos só a fonte. O que aprendo com as questões é o que entra no resumo.

## Estrutura

| Arquivo | Papel |
|---|---|
| `edital-001-2026.md` | Cópia do edital (fonte da hierarquia) |
| `mapa.json` | Árvore de assuntos + cards (explicação, incidência, pegadinhas) |
| `questoes.jsonl` | Arquivo bruto: uma linha por questão, com texto completo. Cresce livre, nunca é podado |
| `build.py` | Gera `index.html` a partir do `mapa.json` |
| `index.html` | Página principal: painel de status, navegação lateral com busca/filtros e cartões por disciplina |

A hierarquia espelha o **Anexo III** do edital: `1`, `1.1`, `1.1.1`. O edital pulou o número 6 dos conhecimentos específicos; aqui ele virou `CE-6` com uma nota explicando.

## Como funciona

1. Você diz o assunto: `vou mapear CC-2.1 (CF/88, Administração Pública)`.
2. Você cola as questões que respondeu, pode ser bagunçado e pode marcar `errei` / `acertou`.
3. Eu classifico cada questão no assunto correto e preencho o **card**:

   - `explicacao`: texto curto para **memorizar** o assunto (com sigla ou truque quando ajuda)
   - `incidencias`: cada ponto que já caiu com `vezes` (quantas questões) e `questoes` (quais). Questões com palavras diferentes que testam o mesmo núcleo são **unidas**, não repetidas.
   - `pegadinhas`: onde a banca erra ou onde você errou
   - `questoes_lista` / `questoes` / `erros`: registro e contagens
   - `fora_do_resumo`: teoria do PDF que nunca apareceu nas questões
   - `fontes`: artigo da norma, edital ou questão de origem
   - `status`: `nao-mapeado` → `em-mapeamento` → `mapeado`

   A incidência é o que decide a revisão: na lateral há filtros por frequência
   (`3+ vezes`, `2 vezes`, `1 vez`). O que caiu 5 vezes vem primeiro; o que caiu
   1 ou 2 vezes pode ser ignorado na revisão final.
4. Rodo `python build.py` e a página índice já está atualizada.

Você nunca escreve JSON, Markdown, HTML nem roda validador. Só estuda com questões e cola o que respondeu.

## Comando

```bash
python build.py          # gera index.html
```

Sem dependências externas. Python 3.10+.

## Volume alto: anti-perda e anti-inchaço

- **Questão bruta vai para `questoes.jsonl`** com texto completo, gabarito e resultado. Nada é descartado, mesmo que o ponto já esteja mapeado.
- **Cartão recebe só o comprimido.** Se o mesmo núcleo cair de novo com palavras diferentes, aumenta `vezes` e entra a variação — não nasce outro ponto.
- Se um assunto passar de ~7 incidências, as de `1x` são agrupadas em "caiu uma vez" com os IDs no arquivo bruto. O cartão continua enxuto.
- Regra: informação bruta se acumula; explicação se comprime.

## Memória (TDH)

Todo card com incidência tem um bloco **DECORE ISSO** no topo, sempre no mesmo lugar:
**CHAVE** (o conceito-âncora), **TRUQUE** (sigla ou regra mnemônica) e **ERRO CLÁSSICO** (a pegadinha principal).

O botão **⚡ Revisão rápida (3+ vezes)** filtra só o que caiu 3 ou mais vezes, abre esses cards e esconde tudo que não é âncora. O botão **⚠ Meus erros** mostra só os assuntos com erros e marca as questões erradas em vermelho.

**Revisão espaçada:** ao dizer `revisei <id>`, o campo `revisado_em` recebe a data de hoje e o card mostra `revisado hoje` / `há N dia(s)`: verde até 3 dias, âmbar de 4 a 7, vermelho acima disso. Sem data, nada aparece.

## Regra de ouro

Se uma afirmação não apareceu em nenhuma questão, ela não entra no resumo — entra em `fora_do_resumo` para você saber que pode pular. O mapa mede o que cai, não o que o cursinho ensina.
