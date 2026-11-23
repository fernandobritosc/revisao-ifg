# Decisões de projeto

Registro curto das escolhas que explicam o Hermes atual. O objetivo não é congelar o design, mas tornar as trocas explícitas.

## 001 — JSON como fonte da verdade

**Decisão.** Cada aula é um arquivo JSON. HTML, Markdown, PDF e slides são representações derivadas.

**Por quê.** O acervo anterior concentrava conteúdo, CSS e JavaScript em HTML monolítico. Isso dificultava revisão por diff, busca, reuso e validação de relações. JSON é fácil de ler, tem schema maduro, funciona em qualquer linguagem e não exige um parser específico.

**Alternativas.** YAML é mais confortável para autoria, mas adiciona ambiguidades e uma dependência. Markdown com frontmatter é ótimo para leitura, mas ruim para relações cruzadas e quiz. Um banco de dados é inadequado para um artefato de revisão.

**Consequências.** Autores precisam respeitar vírgulas e aspas. Um editor com validação de JSON Schema ajuda. A experiência de escrita pode melhorar depois com um formulário ou conversor, sem mudar a fonte.

## 002 — Blocos estruturados, não HTML

**Decisão.** O conteúdo usa tipos de bloco (`paragrafo`, `lista`, `tabela`, `destaque`, `gotcha`, `mnemonico`, `exemplo`) em vez de HTML bruto.

**Por quê.** Blocos permitem validar estrutura, gerar acessibilidade consistente e adaptar a apresentação sem reescrever o conteúdo. HTML no JSON transferiria a dívida visual para a fonte e impediria reuso.

**Trade-off.** Autores perdem parte da liberdade visual. Isso é intencional: o design system deve ser responsabilidade do gerador, não de cada aula.

## 003 — Quiz separado do corpo

**Decisão.** O quiz é um objeto `quiz`, com 4–8 questões e 4 alternativas. Seções de “questões comentadas” e “gabarito final” são proibidas no corpo.

**Por quê.** O corpo deve servir à leitura e à revisão; o quiz serve ao recall ativo. Separar os dois permite validar o quiz, gerar diferentes experiências de prática e evitar que a resposta apareça antes do clique.

**Consequências.** Questões comentadas do acervo legado precisam ser convertidas, não copiadas como seção.

## 004 — Fontes e referências cruzadas

**Decisão.** Toda aula tem `fontes`; seções, blocos, questões e incidência referenciam fontes e seções por id.

**Por quê.** O projeto exige rastreabilidade. Uma afirmação sem fonte é uma pendência, não um conteúdo pronto. O validador impede referências quebradas.

**Trade-off.** Registrar fontes dá trabalho. O ganho é uma revisão mais rápida e uma resposta clara quando a banca ou o edital divergem do material didático.

## 005 — Incidência pode ser vazia

**Decisão.** `incidencia.temas` pode ser `[]`; quando há temas, os pesos devem somar 100.

**Por quê.** Nem toda aula já tem questões TEC coladas. Inventar uma incidência para parecer completo é pior do que declarar a ausência. O campo `observacao` registra o estado.

**Consequências.** O acervo pode ter aulas completas sem incidência; a priorização de revisão precisa considerar outros sinais, como o status de revisão.

## 006 — Validador sem dependências

**Decisão.** `validate.py` usa apenas a biblioteca padrão e implementa o subconjunto de JSON Schema necessário.

**Por quê.** O comando deve funcionar em uma máquina recém-configurada, em CI e em um ambiente sem acesso a pacotes. O schema usa constructs limitados e estáveis; o custo de manter um validador pequeno é menor do que o custo de uma dependência para uma tarefa simples.

**Trade-off.** O validador não cobre todos os constructs de JSON Schema. Documentos com `$ref` externo, `if/then`, `patternProperties` ou outros recursos avançados devem usar uma implementação completa. O schema atual evita esses constructs.

## 007 — Exemplo RO Aula 00 em rascunho

**Decisão.** O exemplo completo está com `status: "rascunho"`, sem revisores fictícios.

**Por quê.** O arquivo demonstra o formato sem fingir uma revisão que não aconteceu. Ele serve como contrato de referência e caso de teste, não como conteúdo oficial do IFG.

**Consequências.** Para publicar, alguém precisa revisar e assinar. O exemplo usa `CC-BY-4.0` apenas para demonstrar o campo de licença; a licença real deve ser confirmada.

## 008 — Uma aula por arquivo

**Decisão.** Cada arquivo contém exatamente uma aula. Não há coleção no mesmo documento.

**Por quê.** Simplifica diff, revisão, validação isolada e versionamento. Uma coleção pode ser montada por diretório ou por um índice futuro.

**Consequências.** Uma aula dividida em várias partes precisa de uma decisão editorial: um único arquivo com seções longas ou vários arquivos relacionados por uma trilha.

## 009 — 1.1.0: Certo/Errado e subtítulos internos

**Decisão.** O contrato passou a aceitar **2 a 5 alternativas** por questão, ganhou o bloco **`topico`** e o `paragrafo` passou a aceitar `titulo`.

**Por quê.** O stress test com a Aula 01 de Informática mostrou dois gaps reais. O quiz legado é **Certo/Errado**, com duas alternativas; exigir exatamente quatro forçaria inventar opções, violando o princípio de não inventar conteúdo. E as seções do resumo tinham `h3` internos que agrupavam dez ou mais cards; achatar tudo perderia a hierarquia didática. O título do card, por sua vez, precisava de um lar: passou a ser `paragrafo.titulo` ou `lista.titulo`.

**Consequências.** A mudança é aditiva: documentos `1.0.0` com quatro alternativas continuam válidos, por isso o bump é minor. O validador aceita 2–5 alternativas, o gerador renderiza `topico` como `h3` e a migração passou a expandir `rowspan`/`colspan` em células repetidas. O caso real está em `exemplos/informatica/aula-01.json`.

## 010 — Sem bloco de imagem (por enquanto)

**Decisão.** O contrato **não** tem bloco de imagem, e o sketchnote do acervo não é tratado como conteúdo.

**Por quê.** O inventário do repositório de origem mostrou **zero imagens de conteúdo**: os únicos PNG são ícones de PWA (`icons/`) e snapshots de teste visual (`tests/snapshots/`). O sketchnote de algumas aulas é um HTML com CSS — ou seja, apresentação derivada, não um dado. Adicionar `imagem` ao schema seria especular sobre uma necessidade que o acervo não tem.

**Consequências.** Quando uma aula trouxer diagramas ou figuras, o bloco deve entrar como `{"tipo": "imagem", "id": "...", "src": "...", "alt": "..."}`, com `alt` obrigatório por acessibilidade, `titulo?` e `fontes?`. O validador deverá checar a existência de `src` relativo (`missing-image`) e o gerador deverá usar `<figure>` com `<figcaption>`. Até lá, o sketchnote continua sendo um artefato de apresentação fora do JSON.
