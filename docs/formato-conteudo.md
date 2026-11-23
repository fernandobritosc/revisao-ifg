# Formato de conteúdo do Hermes

Uma **aula** é a unidade editorial do Hermes. Ela reúne identificação, fontes, seções, blocos, quiz, incidência, revisão e metadados em um único arquivo JSON. O arquivo é autocontido: pode ser lido por uma pessoa, processado por um script e convertido para HTML, Markdown ou PDF.

## Princípios de autoria

1. **Nada sem fonte.** Registre a fonte no topo e referencie-a nas seções, blocos ou questões.
2. **Uma ideia por bloco.** Parágrafos, listas, tabelas e destaques têm papéis diferentes; não transforme tudo em uma parede de texto.
3. **Conteúdo não é quiz.** O corpo da aula não tem seção de “questões comentadas” nem “gabarito final”. O quiz é um objeto separado, com alternativas e explicações.
4. **Revisão é parte do dado.** A aula registra quando foi revisada, quando será revisada e qual ritual será seguido.
5. **Incidência é evidência, não palpite.** Só registre temas efetivamente cobrados; se ainda não houver questões, deixe `incidencia.temas` vazio e explique em `observacao`.

## Anatomia do arquivo

```text
aula-00.json
├── schema_version       versão do contrato, não do conteúdo
├── id                   identificador estável em kebab-case
├── materia              nome editorial da matéria
├── numero               número ordinal da aula; Aula 00 usa 0
├── titulo               título editorial
├── resumo               síntese de 20 a 800 caracteres
├── status               rascunho | revisao | publicado | arquivado
├── idioma               BCP-47, como pt-BR
├── tags                 termos de recuperação
├── fontes               fontes citadas pela aula
├── secoes               sequência numerada de seções
│   └── blocos           conteúdo estruturado de cada seção
├── quiz                 4 a 8 questões de revisão ativa
├── incidencia           temas cobrados, pesos e seções
├── revisao              status, datas e ritual de revisão
├── metadados            versão, autoria, revisão, licença e origem
└── notas                observações editoriais opcionais
```

## Campos obrigatórios

| Campo | Tipo | Regra principal |
|---|---|---|
| `schema_version` | string | Sempre `"1.0.0"` nesta versão do contrato. |
| `id` | string | 2–100 caracteres, `^[a-z0-9]+(?:-[a-z0-9]+)*$`. |
| `materia` | string | Não vazia. |
| `numero` | inteiro | 0–999; Aula 00 usa `0`. |
| `titulo` | string | Não vazio. |
| `resumo` | string | 20–800 caracteres. |
| `status` | enum | `rascunho`, `revisao`, `publicado`, `arquivado`. |
| `idioma` | string | BCP-47, como `pt-BR`. |
| `tags` | string[] | 1–30 itens; sem duplicatas. |
| `fontes` | objeto[] | 1 ou mais fontes, com id único. |
| `secoes` | objeto[] | 1 ou mais seções, numeradas sequencialmente. |
| `quiz` | objeto | Opcional; se existir, 4–8 questões. |
| `incidencia` | objeto | Opcional; pode ter `temas` vazio. |
| `revisao` | objeto | Status, próxima data e ritual. |
| `metadados` | objeto | Versão SemVer, datas, autoria, revisão e licença. |
| `notas` | string | Opcional; até 4.000 caracteres. |

## Fontes

Cada fonte tem `id`, `tipo`, `titulo` e, opcionalmente, `detalhes`, `ano` e `url`.

```json
{
  "id": "mrpr-3",
  "tipo": "norma",
  "titulo": "Manual de Redação da Presidência da República",
  "detalhes": "3. ed., 2018. Fonte principal das regras estudadas na aula."
}
```

Tipos: `livro`, `norma`, `curso`, `artigo`, `site`, `video`, `outro`. Use um id estável (`mrpr-3`, `decreto-9758`) e cite-o em `secoes[].fontes`, `blocos[].fontes` ou `quiz.questoes[].fonte_id`. O validador impede referências a fontes inexistentes.

**Cuidado com fontes legais:** não cite artigo, inciso ou parágrafo de memória. Confira o texto e a versão; registre o detalhe da fonte. Para o IFG, o edital e a banca determinam qual manual é relevante.

## Seções

Cada seção tem:

- `id`: identificador estável para âncoras e referências do quiz;
- `numero`: posição na sequência, começando em 1;
- `titulo`: título editorial;
- `subtitulo`: opcional, para explicar o recorte;
- `fontes`: opcionais, para valer para toda a seção;
- `blocos`: 1 ou mais blocos de conteúdo.

```json
{
  "id": "clareza-e-precisao",
  "numero": 2,
  "titulo": "Atributos — clareza e precisão",
  "subtitulo": "O texto que se compreende de imediato e o vocabulário sem duplo sentido.",
  "fontes": ["mrpr-3"],
  "blocos": [
    {
      "tipo": "paragrafo",
      "id": "clar-definicao",
      "texto": "Clareza é a qualidade do texto que possibilita imediata compreensão pelo leitor.",
      "fontes": ["mrpr-3"]
    }
  ]
}
```

A numeração é validada: a primeira seção deve ser 1, a segunda 2, e assim por diante. Isso evita âncoras quebradas e sidebar fora de ordem.

## Blocos

Todo bloco tem `tipo` e `id`. Os tipos são:

| Tipo | Campos principais | Uso |
|---|---|---|
| `paragrafo` | `texto`, `titulo?` | Prosa normal, definições e explicações. |
| `topico` | `texto` | Subtítulo interno; agrupa os blocos que vêm depois. |
| `lista` | `itens`, `titulo?`, `ordenada?` | Enumerações, procedimentos e classificações. |
| `tabela` | `colunas`, `linhas`, `titulo?` | Comparações e quadros de decisão. |
| `destaque` | `nivel`, `texto`, `titulo?` | Informação adicional, alerta, dica ou erro. |
| `gotcha` | `texto`, `titulo?` | Pegadinha de banca, com a correção embutida. |
| `mnemonico` | `texto`, `titulo?` | Frase ou recurso de memorização. |
| `exemplo` | `texto`, `titulo?` | Exemplo resolvido ou modelo de aplicação. |

Níveis de `destaque`: `info`, `atencao`, `sucesso`, `erro`.

### Texto

`texto`, `itens`, `colunas` e `linhas` são strings. É permitido Markdown inline (`**negrito**`, `*itálico*`, `` `código` ``), mas não HTML bruto. A apresentação é responsabilidade do gerador, não do conteúdo.

### Tabelas

Cada linha precisa ter exatamente o mesmo número de células das colunas. O validador reporta `table-row-width` quando há divergência.

```json
{
  "tipo": "tabela",
  "id": "obj-tabela",
  "titulo": "A diferença que resolve a questão",
  "colunas": ["Atributo", "Cuida de"],
  "linhas": [
    ["Concisão", "Passar o máximo de informação com o menor número de palavras."],
    ["Objetividade", "Do modo de apresentar as ideias: direto, sem subterfúgios."]
  ]
}
```

## Quiz

O quiz é opcional, mas é a peça de revisão ativa do Hermes. Estrutura:

```json
{
  "id": "quiz-ro-aula-00",
  "titulo": "Quiz — Redação Oficial Aula 00",
  "instrucoes": "Escolha uma alternativa e confira a explicação.",
  "questoes": [
    {
      "id": "q-definicao",
      "enunciado": "Segundo o MRPR, redação oficial é:",
      "opcoes": [
        {
          "texto": "A maneira pela qual o Poder Público redige comunicações oficiais e atos normativos.",
          "correta": true,
          "explicacao": "Certo: é a definição literal do MRPR."
        },
        {
          "texto": "Uma formalidade exclusiva do Executivo Federal.",
          "correta": false,
          "explicacao": "Errado: o método alcança todo o Poder Público."
        },
        {
          "texto": "A padronização editorial dos textos publicados no Diário Oficial.",
          "correta": false,
          "explicacao": "Errado: a definição trata de método e preceitos, não apenas de publicação."
        },
        {
          "texto": "A forma solene de linguagem exigida apenas para atos normativos primários.",
          "correta": false,
          "explicacao": "Errado: o MRPR abrange comunicações oficiais em geral e atos normativos."
        }
      ],
      "secao_id": "o-que-e-redacao-oficial",
      "fonte_id": "mrpr-3"
    }
  ]
}
```

Regras validadas:

- 4 a 8 questões por quiz;
- **2 a 5 alternativas** por questão (Certo/Errado usa 2; algumas bancas usam 5);
- exatamente 1 alternativa correta;
- explicação não vazia em **todas** as alternativas, inclusive na correta;
- nenhum texto de alternativa duplicado na mesma questão;
- `secao_id` e `fonte_id` existem.

O quiz não substitui a resolução de questões da banca; ele serve para recall imediato e identificação de lacunas.

## Incidência

`incidencia` registra o que foi efetivamente cobrado, com `fonte`, `atualizado_em`, `temas` e `observacao`.

```json
{
  "fonte": "TEC Concursos",
  "atualizado_em": "2026-11-20",
  "temas": [
    {
      "nome": "Pronomes de tratamento",
      "peso": 40,
      "secao_ids": ["pronomes-tratamento", "vossa-sua-enderecamento"]
    },
    {
      "nome": "Partes do documento",
      "peso": 60,
      "secao_ids": ["partes-documento-i", "partes-documento-ii"]
    }
  ],
  "observacao": "Pesos relativos às questões coladas; não são uma estatística oficial da banca."
}
```

Quando houver temas, os pesos devem somar **100** e cada `secao_id` deve existir. Se não houver questões coladas, use `"temas": []` e explique em `observacao`; não invente incidência.

## Revisão

Toda aula tem um objeto `revisao`:

```json
{
  "status": "pendente",
  "ultima_em": "2026-11-20",
  "proxima_em": "2026-11-27",
  "ritual": [
    "Ler o resumo e refazer o quiz sem consultar as respostas.",
    "Registrar os erros e a explicação de cada alternativa errada."
  ]
}
```

`status` pode ser `pendente`, `em_andamento` ou `concluida`. `ultima_em` é opcional; `proxima_em` é obrigatória e não pode ser anterior a `metadados.atualizado_em`. A última revisão não pode ser posterior à próxima.

## Metadados

`metadados` contém `versao` (SemVer), `criado_em`, `atualizado_em`, `autores`, `revisores`, `licenca`, `origem` e `alteracoes`. Para publicar, é necessário ao menos um revisor e uma licença diferente de `NOASSERTION`. A data de atualização não pode ser anterior à de criação.

## Checklist antes de validar

- [ ] O `id` é único e estável; o título descreve a aula.
- [ ] O resumo explica o recorte sem copiar a ementa.
- [ ] As fontes estão registradas e são citadas nos blocos relevantes.
- [ ] As seções estão numeradas em sequência e têm blocos.
- [ ] As tabelas têm todas as linhas com o mesmo número de células.
- [ ] O quiz tem 4–8 questões, 4 alternativas, uma correta e explicação em todas.
- [ ] As questões apontam para seções e fontes existentes.
- [ ] A incidência tem pesos que somam 100 quando há temas, ou está vazia com explicação.
- [ ] As datas de revisão e metadados são coerentes.
- [ ] O status e os revisores correspondem ao momento editorial.

Depois, rode:

```bash
python validate.py caminho/para/aula.json
```
