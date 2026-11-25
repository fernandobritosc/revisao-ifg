# AGENTS.md — manual de operação do Mapa de revisão

**Leia isto antes de responder.** Se você é uma LLM, um agente ou uma sessão nova,
este arquivo é a memória do projeto. Ele viaja junto com a pasta: onde o usuário
abrir o projeto, a essência está aqui.

## TL;DR — 5 regras

1. O usuário **aprende com questões**, não com PDF. O mapa existe para **revisar e memorizar**.
2. **Bruto se acumula** (`questoes.jsonl`); **explicação se comprime** (cartão com teto).
3. **Fonte vem da resolução da questão** — nunca invente artigo, lei, manual ou edição.
4. Cartão com teto (5 incidências / 7 pegadinhas / 6 parágrafos); excedente em
   "Ver mais" **dentro dele**. Nunca diga "está no bruto" se estiver no `mapa.json`.
5. Após qualquer mudança, **rode `python build.py` e confira no navegador** —
   ligando **e desligando** cada filtro.

---

## 1. O que este projeto é

Um **mapa de incidência para revisão** do concurso IFG 2026, cargo **301 — Assistente em Administração** (Edital 001/2026, banca Instituto AOCP, prova 14/02/2027).

A prova tem 50 questões e 100 pontos: Língua Portuguesa 10q/peso 2/mín 12; Legislação 10q/peso 1/mín 5; RLM 5q/peso 1/mín 2; Informática 5q/peso 1/mín 2; Específicos 20q/peso 3/mín 39. Para aprovar: 60 pontos **e** o mínimo em cada disciplina.

O usuário **aprende com questões**. O mapa existe para **revisar e memorizar**, não para estudar teoria.

## 2. O que este projeto NÃO é — erros já cometidos

Não refaça estes erros:

- ❌ Não é resumo de PDF. PDF de cursinho (Estratégia etc.) é consulta eventual do usuário; **nunca transcreva** a teoria dele para o mapa.
- ❌ Não é caderno de estudo. O aprendizado vem das questões que o usuário responde.
- ❌ Não jogue a resolução longa da questão dentro do card. Comprima.
- ❌ Não invente incidência, peso, "o que mais cai" ou teoria sem questão que sustente.
- ❌ Não crie HTML grande, dependências externas ou JavaScript fora do arquivo gerado.
- ❌ Não acumule bullets sem fim. Informação bruta se acumula; **explicação se comprime**.
- ❌ Não edite `index.html` na mão. Ele é gerado.

## 3. Arquivos

| Arquivo | Papel |
|---|---|
| `AGENTS.md` | Este manual. Leia primeiro. |
| `edital-001-2026.md` | Fonte da hierarquia (Anexo III). |
| `mapa.json` | Árvore de assuntos + cards (explicação, incidência, pegadinhas). |
| `questoes.jsonl` | Arquivo bruto: uma linha por questão, com texto completo. Cresce livre, nunca é podado. |
| `build.py` | Gera `index.html`. Sem dependências. |
| `README.md` | Visão geral para humanos. |

A hierarquia espelha o edital: `CC-1.1`, `CC-2.3`, `CE-7.5` etc. O edital pulou o item 6 dos específicos; aqui ele virou `CE-6` com nota explicando.

## 4. Protocolo para cada questão que o usuário mandar

1. **Identificar**: ID, banca, ano, cargo de origem, acerto/erro, assunto. Questão de outro cargo serve — o filtro é o assunto, não o cargo.
2. **Gravar o bruto**: acrescente uma linha em `questoes.jsonl` com o texto completo que o usuário colou (`bruto`), mais `id`, `assunto`, `banca`, `ano`, `cargo`, `acerto`. Sem cortes.
3. **Classificar**: escolha o nó do edital (`id` no `mapa.json`). Se não houver nó adequado, crie um com numeração coerente e avise.
4. **Comparar o núcleo** com as `incidencias` existentes do nó:
   - **Mesmo núcleo com palavras diferentes** → some `+1` em `vezes`, inclua o ID em `questoes` e registre a variação curta se trouxer nuance nova. **Não crie outro ponto.**
   - **Núcleo novo** → crie incidência com `vezes: 1`.
5. **Atualizar** `questoes`, `erros`, `questoes_lista`, `fontes`.
6. **Garantir o bloco `decore`** com `chave`, `truque`, `erro` e a `explicacao` curta (3–4 parágrafos, com sigla quando ajudar). É obrigatório para todo card com incidência.
7. **Fechar**: `python build.py`. Nunca escreva HTML na mão.
8. **Deploy**: envie as alterações ao repositório remoto (`git add -A`, `git commit`, `git push`) para o GitHub Pages refletir a mudança; faça isso antes de responder.
9. **Responder** ao usuário dizendo: onde a questão caiu, o que foi fundido ou criado, e a contagem atual. Nada mais.

Status: `nao-mapeado` → `em-mapeamento` → `mapeado`. Só mude para `mapeado` quando o usuário disser explicitamente `fechou <id>`.

**Cabeçalho "(e mais N concursos)": desconsiderar.** É ruído estatístico: não entra
como incidência, não ganha destaque e nunca vira anotação como "forte sinal" ou
"reapareceu em N provas". O texto integral permanece no bruto apenas por fidelidade
à questão original. Incidência é contada por questão efetivamente mapeada, não por
quantas vezes o enunciado diz ter sido aplicado.

**Revisão espaçada:** quando o usuário disser `revisei <id>`, atualize `revisado_em`
com a data de hoje (ISO `AAAA-MM-DD`). A página mostra `revisado hoje` / `há N dia(s)`
com cor: até 3 dias verde, 4–7 âmbar, acima de 7 vermelho. Nunca preencha essa data
por conta própria. Sem data, nenhum aviso aparece.

## 4.1 Das fontes — o edital não facilita

O edital dá **só o esqueleto**: os assuntos e a numeração. Ele **não** nomeia o MRPR,
não cita artigos de lei, decretos, regulamentos, autores ou manuais. Quem faz essa
ponte é a **resolução da questão** (TEC Concursos e bancas), onde aparecem:

- a letra da lei / o artigo exato (ex.: CF art. 37, Lei 8.112, MRPR 3.1 e 3.6);
- regulamentos, normas e técnicas;
- conceitos e autores de referência (ex.: KASPARY 2017, p. 136).

**Regra:** a fonte entra no cartão **porque a questão a citou**. Registre o item/trecho
exato em `fontes` e mantenha o texto integral no `questoes.jsonl`. Nunca invente
fonte, nunca "deduza" artigo de memória, nunca complete a citação sem lastro.
Se a resolução não trouxer a fonte e ela precisar ser consultada, diga isso
explicitamente ao usuário antes de registrar.

É esse trabalho de "achar a fonte" que transforma uma questão solta em material
de revisão rastreável — e é por isso que o PDF do cursinho fica como consulta
eventual, nunca como fonte do cartão.

## 5. Regras de volume e memória (usuário tem TDH)

- Bruto se acumula; explicação se comprime.
- Cartão com **teto fixo**: no máximo **5 incidências visíveis** (sempre as de maior `vezes`), **7 pegadinhas** e **6 parágrafos** de explicação. O excesso de incidências e de pegadinhas aparece numa cauda recolhida ("Ver mais N...") **dentro do próprio cartão**, nunca atrás de aviso que diga "no arquivo bruto". Nada é apagado: o texto integral da questão está no `questoes.jsonl`.
- **Ponto novo com `1x` não ganha linha no cartão**: funda-se numa incidência existente ou entra na cauda. Só crie incidência visível se ela já tiver 3+ questões ou trouxer um núcleo claramente distinto.
- Não existe limite de questões: cada uma gera uma linha no bruto. Quem cresce é o arquivo, não o cartão.
- **Saturação:** depois de ~25–30 questões no mesmo assunto, se a maioria apenas reconfirma núcleos já registrados, diga ao usuário que o assunto está mapeado e sugira `fechou <id>` — parar de questionalo é parte do método.
- Toda explicação tem âncora visual: **CHAVE** (conceito), **TRUQUE** (sigla/regra), **ERRO CLÁSSICO** (pegadinha principal).
- Frases curtas, termos em negrito, sigla quando possível. Nada de parágrafos longos de teoria.
- O botão **⚡ Revisão rápida (3+ vezes)** filtra só o que caiu 3+ vezes e esconde tudo que não é âncora. É a visão de revisão do usuário.
- Incidência decide prioridade: o que caiu 5 vezes vem primeiro; 1 ou 2 vezes pode ser ignorado na revisão final.

## 5.1 Regras de interface — lições aprendidas na prática

Estes erros já aconteceram e o usuário os pegou. Não repita:

- **IDs das questões:** ficam **inline em cada incidência**, dentro de um `<details>`
  com `<summary>IDs</summary>` (`▸ IDs`). Nunca remova os IDs do cartão, nunca
  crie um bloco global "Ver IDs das questões", nunca esconda dizendo "está no bruto".
- **Não mostre `(N concursos)`** ao lado da incidência. O dado fica no `mapa.json`,
  mas a leitura do cartão fica limpa.
- **Excedente** de incidências (acima de 5) e de pegadinhas (acima de 7) vai em
  `<details class="cauda">` com "Ver mais N...", **dentro do cartão**. Nunca use
  texto como "+ N no arquivo bruto" — isso foi um erro e era mentira.
- **Questões e Fontes** ficam sempre dobradas em `<details class="bloco-dobra">`
  com contador (`7 questão(ões) — ver mais`). Não aparecem abertas.
- **"Fora do resumo"** só é renderizado se houver conteúdo. Nunca mostre o
  placeholder "Nada marcado como teoria de baixo rendimento".
- **Nunca duplique rótulo** entre CSS `::before` e `<summary>` — isso gerou
  "IDsIDs" na tela. O `::before` só coloca a seta (`▸` / `▾`).
- **Contadores das disciplinas** contam **mapeamento iniciado**, não só `mapeado`:
  `status != nao-mapeado` OU `questoes > 0` OU `incidencias` não vazia. Assim
  CE-1.1 (`em-mapeamento`, 7 questões) aparece como `1/36`, não `0/36`.
- **Termos importantes em negrito:** o `build.py` aplica `_negrito()` em explicações,
  incidências, pegadinhas e notas, com uma única passada de regex (evita `<strong>`
  aninhado). Não remova esse destaque — é âncora visual para o usuário (TDH).
- **Contar itens com `conteudo.count("<li")`, nunca `"<li>"`:** itens marcados
  (erros em vermelho) usam `<li class="...">` e eram subcontados no rótulo do
  "ver mais".
- **Padronizar valores dos filtros no JS:** use sempre `'todos'` para "sem filtro"
  (status e prioridade) e `'todas'` apenas para incidência. Um `todos`/`todas`
  trocado fez todos os assuntos com score 0 ficarem escondidos para sempre.
- **Sempre conferir no navegador após mudança visual**: procurar texto duplicado,
  contadores zerados, toggles que não abrem e `innerText` com IDs indevidos. Teste
  cada filtro **liga e desliga**, não só liga.

## 6. Formato de dados — modelo canônico

Exemplo simplificado (valores reais e atualizados sempre em `mapa.json`), use como referência de formato:

```json
{
  "id": "CE-1.1",
  "titulo": "Aspectos gerais da redação oficial",
  "status": "em-mapeamento",
  "questoes": 7,
  "erros": 1,
  "decore": {
    "chave": "CLAREZA + IMPERSOALIDADE",
    "truque": "C-O-C-C-I-F-N = Clareza, Objetividade, Concisão, Coesão, Impessoalidade, Formalidade, Norma-padrão",
    "erro": "Culta ≠ rebuscada. Nunca aceite 'estilo', 'originalidade', 'detalhamento', 'pessoalidade' ou figuras literárias. O certo é C: consulta ao dicionário."
  },
  "explicacao": ["parágrafo curto 1", "parágrafo curto 2"],
  "incidencias": [
    {
      "texto": "Lista dos 7 atributos do MRPR (C-O-C-C-I-F-N)",
      "vezes": 3,
      "questoes": ["#3803997", "#3563761", "#3564013"]
    }
  ],
  "pegadinhas": ["pegadinha curta"],
  "questoes_lista": ["#3803997 · AOCP 2026 · acerto (E)"],
  "fora_do_resumo": [],
  "fontes": ["MRPR 3ª ed., item 3.1", "MRPR 3ª ed., item 3.6", "CF/88 art. 37"],
  "notas": "Contexto opcional."
}
```

`questoes.jsonl` — uma linha JSON por questão, com `bruto` contendo o texto integral.

## 7. Comandos

```bash
python build.py                       # regera index.html
python -m json.tool mapa.json          # checa JSON
python -c "import json; [json.loads(l) for l in open('questoes.jsonl',encoding='utf-8') if l.strip()]"  # checa bruto
```

Abra `index.html` no navegador para conferir o resultado visual.

---

## 8. Como retomar em outra LLM / outra sessão

Cole isto no início da conversa, junto com a pasta do projeto:

> Leia `AGENTS.md` e `README.md` na raiz deste projeto antes de responder. Siga o
> protocolo da seção 4. Não resuma PDF, não invente incidência, não inche os cards.
> Trabalhe só com as questões que eu mandar e com os arquivos `mapa.json` e
> `questoes.jsonl`. Sempre rode `python build.py` e confira a interface no navegador
> antes de responder (seção 5.1).

Se a outra LLM não puder ler arquivos, cole o conteúdo deste `AGENTS.md` junto.
