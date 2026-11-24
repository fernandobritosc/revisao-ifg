# Plano de melhorias — uma por vez

Cada item é independente e deve ser feito **numa sessão só**, com validação no navegador
antes de marcar como concluído. Regra: não tocar em dois itens no mesmo passo.

Ordem definida pelo usuário: **1, 2, 3, 4, 6**. Item 5 (git + teste rápido) fica para depois.

---

## [x] 1. Mapa de calor do edital (cobertura)

**Problema:** o mapa mede incidência dentro do assunto, mas não mostra onde o usuário
ainda não pisou. Hoje: 1 assunto tocado, 80 vazios — e isso não aparece.

**O que fazer:** no topo, chips `81 assuntos · 1 tocado · 80 vazios · 10 questões · 2 erros`.
Cada número de assunto ganha cor por cobertura: cinza = 0 questões, âmbar = 1–2,
verde = 3+. Legenda curta na lateral.

**Arquivos:** `build.py` (dados intactos).

**Critério de aceite:** abrir `index.html` e ver o topo com tocados/vazios; os números
dos assuntos sem questão aparecem cinza; o de CE-1.1 aparece verde; nenhum ruído novo
nos cards.

---

## [x] 2. Prioridade composta (incidência × peso)

**Problema:** o filtro `3+ vezes` ignora o peso da disciplina no edital.

**O que fazer:** calcular `score = maior incidência do assunto × peso da disciplina`.
Ex.: CE-1.1 = `6 × 3 = 18`; um ponto `3x` em Português = `3 × 2 = 6`. Mostrar o score
e oferecer filtro "Alta prioridade (score ≥ 9)".

**Arquivos:** `build.py` (dados intactos).

**Critério de aceite:** score visível nos cards com incidência; filtro novo funciona;
ordem de revisão reflete os pesos do edital.

---

## [x] 3. Botão "⚡ Meus erros"

**Problema:** 2 erros registrados estão escondidos. Para o usuário (TDH), o erro é a
âncora mais forte.

**O que fazer:** botão na lateral com contagem de erros. Clicar mostra só assuntos com
erros. Dentro do card, as questões erradas aparecem marcadas em vermelho na dobra
"Questões".

**Arquivos:** `build.py` (dados intactos).

**Critério de aceite:** clicar mostra apenas CE-1.1; as 2 questões erradas ficam
visivelmente marcadas; clicar de volta restaura tudo.

---

## [x] 4. Revisão espaçada

**Problema:** o mapa não lembra quando um assunto foi revisado.

**O que fazer:** campo `revisado_em` por assunto. Ao dizer "revisei CE-1.1", registrar
a data. A página mostra `revisado há N dias` com cor: até 3 dias verde, 4–7 âmbar,
acima de 7 vermelho. Sem data, nada aparece.

**Arquivos:** `mapa.json` + `build.py`.

**Critério de aceite:** com data registrada aparece o aviso colorido; sem data não
aparece nada; a contagem de dias está correta.

---

## [x] 6. TL;DR no topo do AGENTS.md

**Problema:** o manual ficou longo; outra LLM pode pular o essencial.

**O que fazer:** 5 regras nos primeiros 15 linhas, antes de qualquer seção:
(1) learns com questões, não com PDF; (2) bruto acumula, explicação comprime;
(3) fonte vem da resolução; (4) teto do cartão + Ver mais; (5) checar no navegador.

**Arquivos:** `AGENTS.md`.

**Critério de aceite:** as 5 regras legíveis de relance; seções detalhadas intactas.

---

## 5. (adiado) Git + teste rápido

`git init`, commits e um `test_rapido.py` com assertivas para os bugs já pegos
(`IDsIDs`, `(4 concursos)`, contador `0/36`, rótulo "no arquivo bruto").
