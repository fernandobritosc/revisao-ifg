# Hermes

O **Hermes** é a camada de dados do acervo de estudos do `revisao-ifg`. Ele separa o conteúdo de uma aula da apresentação em HTML: cada aula vira um arquivo JSON com fontes, seções, blocos, quiz, incidência e revisão. Um validador local garante que o contrato seja respeitado antes de qualquer publicação.

O nome **RO**, no exemplo deste repositório, significa **Redação Oficial** — não é um formato de arquivo. O formato é o **contrato de aula do Hermes**.

## O que está incluído

| Caminho | Conteúdo |
|---|---|
| [`schema/aula.schema.json`](schema/aula.schema.json) | Modelo de dados em JSON Schema 2020-12, versão `1.1.0`. |
| [`exemplos/redacao-oficial/aula-00.json`](exemplos/redacao-oficial/aula-00.json) | Exemplo completo: **RO — Aula 00**, com 12 seções, 8 questões e campos de incidência/revisão. |
| [`exemplos/informatica/aula-01.json`](exemplos/informatica/aula-01.json) | **Informática — Aula 01**, migrada do acervo legado: 8 seções, 142 blocos e quiz Certo/Errado. |
| [`exemplos/arquivologia/aula-01.json`](exemplos/arquivologia/aula-01.json) | **Arquivologia — Aula 01**, migrada do acervo legado: 10 seções, 26 blocos e quiz de 6 questões. |
| [`exemplos/etica/aula-01.json`](exemplos/etica/aula-01.json) | **Ética geral e profissional — Aula 01** (cargo 301): conceitos e fundamentos, ética profissional, relações de trabalho, responsabilidade social, assédio; 6 seções, 40 blocos e 8 questões. |
| [`exemplos/administracao-de-pessoas/`](exemplos/administracao-de-pessoas/) | **Administração de pessoas — 2 aulas** (cargo 301): conceito, funções, estratégia, liderança, equipe e motivação; recrutamento e seleção, cargos e remuneração, treinamento e desenvolvimento e avaliação de desempenho; 11 seções, 81 blocos e 16 questões. |
| [`exemplos/portugues/aula-01.json`](exemplos/portugues/aula-01.json) | **Língua Portuguesa — Aula 01** (cargo 301): concordância, crase, regência e pontuação; 5 seções, 37 blocos e 8 questões. |
| [`exemplos/rlm/aula-01.json`](exemplos/rlm/aula-01.json) | **Raciocínio Lógico e Matemática — Aula 01** (cargo 301): lógica proposicional, conjuntos, combinatória, aritmética e geometria; 5 seções, 32 blocos e 8 questões. |
| [`exemplos/legislacao/`](exemplos/legislacao/) | **Legislação federal — 11 aulas** escritas a partir do texto das normas (CF/88, 8.112, D. 1.171 e D. 6.029, LDB, 11.892, 11.091, 9.784, LGPD, LAI, 8.429, 14.133): 91 seções, 435 blocos e 84 questões de 5 alternativas, com fonte Planalto por bloco. |
| [`validate.py`](validate.py) | Validador estrutural e semântico, sem dependências externas. |
| [`build.py`](build.py) | Gerador de HTML autocontido e Markdown a partir do JSON. |
| [`docs/`](docs/) | Formato de conteúdo, modelo de dados, validação, governança, migração e decisões. |
| [`tests/`](tests/) | Testes do validador e do exemplo. |
| [`GLOSSARY.md`](GLOSSARY.md) | Vocabulário do contrato: aula, seção, bloco, quiz, incidência e revisão. |
| [`docs/exemplo-ro-aula-00.md`](docs/exemplo-ro-aula-00.md) | Leitura humana do exemplo, com mapa de seções e quiz. |

## Início rápido

Requisitos: **Python 3.11 ou superior**. Não há dependências de terceiros.

```bash
# Valida o diretório de exemplos (padrão)
python validate.py

# Valida um arquivo específico
python validate.py exemplos/redacao-oficial/aula-00.json

# Relatório JSON para CI
python validate.py --json

# Testes
python -m unittest discover -s tests -v

# Gera dist/ com HTML autocontido e index.html
python build.py

# HTML e Markdown de uma aula específica
python build.py exemplos/redacao-oficial/aula-00.json --format html --format md
```

Saída esperada para o exemplo:

```text
OK      exemplos/redacao-oficial/aula-00.json

1 arquivo(s): 1 válido(s), 0 com erro.
```

O validador retorna `0` quando tudo está válido, `1` quando há documento inválido ou ausente e `2` para erro de uso ou de esquema. Veja [docs/validacao.md](docs/validacao.md).

O `build.py` usa os mesmos códigos e **nada escreve** se alguma aula for inválida. A saída padrão é `dist/` (ignorada pelo Git). Veja [docs/renderizacao.md](docs/renderizacao.md).

## Publicação

O acervo renderizado fica em **<https://fernandobritosc.github.io/revisao-ifg/>**: o `index.html` lista todas as aulas e cada aula abre em uma página autocontida, legível no celular e sem depender de internet depois de carregada.

A publicação é automática: qualquer push na `main` dispara o workflow [`.github/workflows/pages.yml`](.github/workflows/pages.yml), que valida todas as aulas, roda os testes, gera o `dist/` e publica no GitHub Pages. Se a validação falhar, **nada é publicado** — o site nunca fica em um estado inválido. Também é possível disparar à mão em *Actions → Publicar acervo → Run workflow*.

**Pré-requisito (uma vez só, já feito neste repositório):** o Pages precisa estar habilitado em *Settings → Pages → Source: **GitHub Actions***. Essa etapa é manual por limitação do GitHub: criar o site do Pages pela API não é permitido para tokens de integração, então o `GITHUB_TOKEN` do Actions recebe `Resource not accessible by integration` mesmo com `pages: write`. Depois de habilitado, o workflow cuida de tudo sozinho.

Para conferir o site localmente antes de subir:

```bash
python build.py
python -m http.server 8000 --directory dist   # http://localhost:8000
```

## Por que JSON?

O acervo anterior mantinha o conteúdo final dentro de HTML monolítico. Isso funcionava para publicar, mas dificultava revisão, busca, reuso e validação de relações. O Hermes move a fonte da verdade para JSON:

- **Revisão por diff:** uma mudança de conteúdo aparece como uma mudança de dados, não como uma edição CSS.
- **Validação antes da publicação:** referências, números de seção, quiz e incidência são checados no editor/CI.
- **Reuso:** o mesmo dado pode gerar HTML, Markdown, PDF, cards de revisão ou um índice de busca.
- **Separação de responsabilidades:** conteúdo, apresentação e automação deixam de estar acoplados no mesmo arquivo.

O HTML continua sendo uma representação derivada; não é a fonte do contrato.

## Visão rápida do modelo

```text
Aula
├── identificação: schema_version, id, matéria, número, título, resumo, status
├── contexto: idioma, tags, fontes
├── seções: número, título, subtítulo, blocos e fontes
│   └── blocos: parágrafo, lista, tabela, destaque, pegadinha, mnemônico, exemplo
├── quiz: 4 a 8 questões, 4 alternativas, uma correta e explicação em todas
├── incidência: temas efetivamente cobrados, pesos e seções
├── revisão: status, datas e ritual
└── metadados: versão SemVer, datas, autoria, revisão, licença e origem
```

## Documentação

- [Formato de conteúdo](docs/formato-conteudo.md) — como escrever uma aula, blocos, quiz e incidência.
- [Modelo de dados](docs/modelo-de-dados.md) — entidades, relacionamentos, dicionário e invariantes.
- [Validação](docs/validacao.md) — comandos, códigos de erro e saída JSON.
- [Renderização](docs/renderizacao.md) — como o JSON vira HTML autocontido e Markdown.
- [Governança](docs/governanca.md) — fluxo editorial, fontes, acessibilidade e publicação.
- [Migração do acervo legado](docs/migracao.md) — como converter `Resumo_estudos` e `quiz.json` para o Hermes.
- [Decisões de projeto](docs/decisoes.md) — por que JSON, blocos estruturados e validador próprio.
- [Exemplo RO Aula 00](docs/exemplo-ro-aula-00.md) — explicação humana do exemplo.
- [Glossário](GLOSSARY.md) — vocabulário do contrato e da equipe.
- [Plano IFG 2026/2027](docs/plano-ifg-2026.md) — o que o edital do cargo 301 cobra e o que produzir antes da prova.

## Princípios

1. **Nada sem fonte.** Toda afirmação relevante deve poder ser rastreada até uma fonte registrada em `fontes`.
2. **Conteúdo separado de apresentação.** HTML, PDF e slides são derivados; o JSON é a fonte.
3. **Quiz não é conteúdo de aula.** Questões comentadas e gabarito ficam fora do corpo; o quiz é um objeto separado, validado.
4. **Revisão explícita.** Toda aula tem `revisao` com status, próxima data e ritual; a incidência registra o que de fato foi cobrado.
5. **Validação barata e local.** O mesmo comando roda no laptop, no editor e no CI.

## Escopo e limites

- O validador cobre **o subconjunto de JSON Schema usado pelo schema** e as regras semânticas do Hermes. Ele não é uma implementação completa de JSON Schema; ferramentas externas ainda podem usar `schema/aula.schema.json`.
- URLs são checadas quanto ao formato, **não** quanto à existência ou ao conteúdo remoto.
- O Hermes não calcula nota nem executa o quiz; ele garante a integridade das questões e das explicações.
- O exemplo está em `rascunho` e é material de estudo, não um manual oficial. Antes de publicar, confira o edital, a versão do MRPR, os links e as licenças de materiais de terceiros.
- A licença do código não foi presumida nesta reconstrução. O conteúdo do exemplo está marcado como `CC-BY-4.0` apenas para demonstração; ajuste antes de adotar.

## Versionamento

Há três versões independentes:

- **`schema_version`** — contrato de dados; hoje `1.0.0`. Mudanças incompatíveis exigem nova versão e migração.
- **`metadados.versao`** — conteúdo da aula, em SemVer; pode mudar sem alterar o schema.
- **Versão no Git** — história editorial do repositório, mantida por quem versiona o projeto.

Campos desconhecidos são rejeitados para evitar que um erro de digitação crie um dado invisível.
