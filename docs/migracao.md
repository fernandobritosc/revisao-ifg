# Migração do acervo legado

O acervo anterior mantém o conteúdo final em arquivos como:

```text
Resumo_estudos/<Matéria>/Aula XX/resumo-aula-XX-<tema>.html
Resumo_estudos/<Matéria>/Aula XX/quiz.json
```

O Hermes não exige que todo o acervo seja migrado de uma vez. A recomendação é migrar **uma aula por vez**, começando pelas aulas com maior incidência ou maior uso, e manter o HTML antigo até o novo pipeline estar validado.

## Princípios da migração

1. **A fonte original vem antes do HTML.** Se existir o Markdown convertido da aula, use-o para conferir o conteúdo; não trate o HTML final como verdade absoluta.
2. **Não invente fonte.** Se o HTML cita um dispositivo ou um manual sem identificação clara, registre a lacuna em `notas` e peça revisão.
3. **Preserve o quiz, mas valide.** O `quiz.json` legado costuma ter `aula`, `tema`, `materia` e `questoes`; converta para o modelo novo e confira as explicações.
4. **Não carregue CSS nem JavaScript.** O JSON recebe conteúdo e estrutura; a apresentação será regenerada.
5. **Migre links e âncoras.** Seções e blocos precisam de ids estáveis; links antigos para `#sec12` podem exigir um mapa de redirecionamento.

## Mapa de conversão

| Legado | Hermes | Observação |
|---|---|---|
| `<title>` e `<h1>` | `titulo` | Limpar prefixos como “Resumo —”. |
| Texto de abertura da página | `resumo` | Reescrever em 20–800 caracteres, sem copiar a ementa. |
| `data-*` ou texto de fonte | `fontes[]` | Identificar tipo, título, detalhes e URL quando houver. |
| `<section id="secN">` | `secoes[]` | Usar `numero` sequencial e um `id` descritivo. |
| `<div class="card-title">` + `.card-text` | blocos | Converter cada card em um ou mais blocos; o título do card vai para `paragrafo.titulo` ou `lista.titulo`. |
| `<h3>` interno da seção | `topico` | Preserva a hierarquia interna que o HTML tinha. |
| `<td rowspan>` / `<td colspan>` | célula expandida | Repita o texto nas linhas/colunas afetadas; o modelo não tem célula mesclada. |
| `<ul>/<ol>` | `lista` | `ordenada: true` apenas para `<ol>`. |
| `<table>` | `tabela` | `colunas` e `linhas`; conferir `rowspan`/`colspan` e simplificar quando possível. |
| `.callout`, `.gotcha`, `.mnemonic` | `destaque`, `gotcha`, `mnemonico` | Mapear a semântica, não a cor. |
| `quiz.json` | `quiz` | 4–8 questões, 2 a 5 alternativas (Certo/Errado tem 2), uma correta, explicação em todas. |
| `Incidência de temas (TEC)` | `incidencia` | Não inventar pesos; se não houver dados, deixar `temas: []`. |
| Badge de revisão 🆕/🔁 | `revisao` | Traduzir o estado para `pendente`, `em_andamento` ou `concluida`. |

## Roteiro para uma aula

1. **Inventariar** os arquivos da aula: HTML final, Markdown de origem, `quiz.json`, sketchnote e links.
2. **Criar** `exemplos/<materia>/aula-XX.json` com `schema_version`, identificação, fontes e `status: "rascunho"`.
3. **Converter** o conteúdo para seções e blocos, mantendo a ordem didática e removendo HTML/CSS.
4. **Converter** o quiz, conferindo cada alternativa e explicação.
5. **Registrar** a incidência apenas com o que estiver documentado; caso contrário, deixar vazio com observação.
6. **Preencher** `revisao`, `metadados` e `notas`.
7. **Rodar** `python validate.py caminho/aula-XX.json` e corrigir os erros.
8. **Revisar** com uma pessoa que conheça a fonte; só então mudar para `publicado`.
9. **Gerar** a apresentação e conferir links, âncoras e acessibilidade.
10. **Arquivar** o HTML antigo quando o novo caminho estiver validado; não manter duas fontes de verdade.

## Conversão do quiz legado

O formato legado costuma ser:

```json
{
  "aula": "00",
  "tema": "...",
  "materia": "Redação Oficial",
  "questoes": [
    {
      "q": "...",
      "opts": [
        {"t": "...", "ok": true, "why": "..."},
        {"t": "...", "why": "..."}
      ]
    }
  ]
}
```

Mapeie:

- `q` → `enunciado`;
- `opts[].t` → `texto`;
- `opts[].ok` → `correta` (inclua `false` explicitamente quando ausente);
- `opts[].why` → `explicacao`;
- `materia`/`tema` → já estão na aula, não duplique no quiz;
- crie `id` únicos para o quiz e para cada questão;
- acrescente `secao_id` e `fonte_id` para cada questão.

Se o quiz legado tiver menos de 4 alternativas ou mais de uma correta, ele não deve ser migrado como está: revise a questão antes de publicar.

## O que não migrar

- CSS, JavaScript, toolbar, modo revisão, modo marcação e PWA: são apresentação, não conteúdo.
- Texto de “questões comentadas” ou “gabarito final” no corpo da aula: mova o que for útil para o quiz e remova do corpo.
- Dados pessoais, links de sessão, tokens ou credenciais que porventura existam no HTML.
- Imagens sem licença ou sem descrição: registre a pendência e não publique.
- **Sketchnote:** é um HTML com CSS, não uma imagem nem conteúdo. Ele é apresentação derivada e não entra no JSON; se quiser preservá-lo, gere-o a partir do JSON ou mantenha-o como artefato separado.

## Critério de pronto

Uma aula migrada está pronta quando:

- [ ] `python validate.py` passa sem erros.
- [ ] O conteúdo foi conferido contra a fonte original.
- [ ] O quiz tem 4 alternativas, uma correta e explicação em todas.
- [ ] As fontes e links foram conferidos.
- [ ] A incidência não foi inventada.
- [ ] A apresentação derivada passou por revisão de acessibilidade.
- [ ] O HTML antigo foi marcado como legado ou removido do fluxo principal.
