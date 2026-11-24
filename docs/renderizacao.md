# Renderização

O JSON é a fonte da verdade; o `build.py` produz as representações derivadas. Ele gera **HTML autocontido** e/ou **Markdown (GFM)** a partir de uma ou mais aulas, sempre validando antes de escrever.

## Comandos

```bash
# Diretório de exemplos -> dist/ (HTML + index.html)
python build.py

# Uma aula, em HTML e Markdown, em um diretório específico
python build.py exemplos/redacao-oficial/aula-00.json --out site --format html --format md

# Somente Markdown
python build.py --format md

# Sem validação prévia (não recomendado) ou forçando a geração
python build.py --no-validate
python build.py --force

# Sem índice, ou forçando o índice
python build.py --no-index
python build.py --index
```

| Opção | Efeito |
|---|---|
| `paths` | Arquivos ou diretórios `.json`; diretórios são lidos recursivamente. Padrão: `exemplos/`. |
| `--out DIR` | Diretório de saída. Padrão: `dist/`. |
| `--format html` | Gera `<id>.html` autocontido. |
| `--format md` | Gera `<id>.md` em Markdown. |
| `--no-validate` | Pula a validação (o JSON continua precisando ser legível). |
| `--force` | Gera mesmo com erros de validação e avisa quantos foram ignorados. |
| `--index` / `--no-index` | Força ou impede o `index.html`. |
| `--quiet` | Não lista os arquivos gerados. |
| `--version` | Imprime a versão do gerador e do schema. |

### Códigos de saída

| Código | Significado |
|---:|---|
| `0` | Geração concluída. |
| `1` | Ao menos uma aula inválida; **nada é escrito** (a menos que `--force`). |
| `2` | Uso incorreto, caminho inexistente ou nenhum `.json` encontrado. |

### Quando o índice é gerado

- Entrada é um **diretório** → `index.html` agrupado por matéria, com navegação por disciplina, contagens (aulas, seções e questões) e um cartão por aula.
- Mais de um arquivo de aula → `index.html`.
- Um único arquivo → sem índice, a menos que `--index` seja informado.

## HTML gerado

Cada aula vira um arquivo `.html` com CSS embutido em `<style>`. Não há JavaScript, fontes remotas, imagens externas nem requisições de rede: o arquivo funciona aberto por `file://`, hospedado em qualquer servidor estático ou anexado a um e-mail.

### Estrutura

```text
<html lang="pt-BR">
├── <a class="skip">          pular para o conteúdo
├── <header class="topo">     matéria, aula, status, título, resumo, tags
├── <div class="layout">
│   ├── <nav class="toc">     sumário com âncoras
│   └── <main id="conteudo">
│       ├── <section id="sec-…">   uma por seção
│       │   └── <p|div|aside id="blk-…">  um por bloco
│       ├── <section id="quiz">
│       ├── <section id="incidencia">
│       ├── <section id="fontes">
│       ├── <section id="revisao">
│       └── <section id="notas">
└── <footer class="rodape">
```

Âncoras estáveis: `sec-<id da seção>`, `blk-<id do bloco>`, `q-<id da questão>`, `fonte-<id da fonte>`, além de `quiz`, `incidencia`, `fontes`, `revisao` e `notas`. O prefixo evita colisão entre ids de entidades diferentes.

### Acessibilidade

- `<main>` com `tabindex="-1"` e link de salto visível no foco.
- Hierarquia `h1` → `h2` (seções) → `h3` (títulos de bloco e enunciados).
- Tabelas com `<caption>`, `<thead>` e `<th scope="col">`.
- Callouts em `<aside role="note">` com rótulo textual, nunca só cor.
- `:focus-visible` com contorno de 3px; `prefers-reduced-motion` desliga animações.
- Status da aula (rascunho, publicado etc.) é texto, não apenas cor.

### Quiz sem JavaScript

Cada alternativa é um `<details>` nativo. O estudante clica na opção que escolheu e vê se acertou; a resposta correta não aparece antes do clique. Teclado, leitor de tela e modo leitura funcionam sem script. Na impressão, o `summary` some e todos os feedbacks aparecem.

### Impressão e tema escuro

- `@media print` remove sombras e navegação, evita quebra dentro de seções e expõe o gabarito.
- `@media (prefers-color-scheme: dark)` troca os tokens de cor; não há botão de tema (o site antigo tinha, o Hermes não).

### Design tokens

As variáveis CSS (`--bg`, `--card`, `--text`, `--mat`, `--radius`, `--shadow` etc.) **espelham** `design-system/css/tokens.css` do `pdfrevisao`, para que o HTML do Hermes possa ser absorvido pelo site sem retrabalho visual. As fontes usam pilha de sistema: o gerador não faz download de webfonts para manter o arquivo autocontido.

## Markdown gerado

O `.md` usa GFM e âncoras explícitas (`<a id="sec-…"></a>`) para que o sumário funcione no GitHub, no Obsidian e em geradores estáticos.

- Parágrafo → texto; lista → `-` ou `1.`; tabela → tabela GFM.
- `destaque`, `gotcha`, `mnemonico` e `exemplo` → citações com rótulo.
- Quiz → lista com `<details><summary>Feedback</summary>` por alternativa.
- Fontes → lista com âncoras e links; revisão e metadados → lista de definição.

## Pipeline recomendado

```bash
python validate.py --json          # falha antes de gerar
python build.py                    # gera dist/
python -m unittest discover -s tests -v
```

Em CI, valide e construa em passos separados; publique `dist/` como artefato ou faça deploy do diretório.

## Como adicionar um tipo de bloco

1. Adicione o tipo ao `oneOf` em `schema/aula.schema.json`.
2. Trate-o em `_block_html` e `_md_block` em `build.py`.
3. Cubra o tipo em `tests/test_build.py`.
4. Atualize `docs/formato-conteudo.md` e `docs/modelo-de-dados.md`.
5. Rode validador, testes e build.

## Limites do gerador

- Não gera busca, sidebar global, PWA, service worker ou modo marcação.
- Não renderiza LaTeX, mermaid ou código com destaque de sintaxe.
- Não baixa nem embute imagens: o modelo atual não tem bloco de imagem (decisão 010).
- Não gera sketchnote: é uma apresentação derivada, fora do JSON.
- Não calcula nota nem salva progresso do quiz.
- O índice agrupa por matéria em ordem alfabética e ordena as aulas pelo número; não há busca, filtro por tag nem ordenação por peso no edital.
