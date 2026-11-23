# Validação

O `validate.py` verifica duas camadas:

1. **Estrutura** — tipos, campos obrigatórios, enums, padrões, tamanhos, formatos, alternativas de blocos e propriedades extras, usando o subconjunto de JSON Schema necessário para `schema/aula.schema.json`.
2. **Semântica** — regras que atravessam o documento: numeração de seções, referências cruzadas, tabelas, quiz, incidência, revisão e publicação.

## Requisitos

Python **3.11+**, apenas biblioteca padrão. Não é preciso instalar `jsonschema`, `pydantic` ou qualquer outra dependência.

## Comandos

```bash
# Diretório padrão: exemplos/
python validate.py

# Arquivo ou diretório específico
python validate.py exemplos/redacao-oficial/aula-00.json
python validate.py exemplos/

# Schema alternativo
python validate.py --schema schema/aula.schema.json exemplos/redacao-oficial/aula-00.json

# Saída JSON estável para CI
python validate.py --json

# Testes de regressão
python -m unittest discover -s tests -v
```

Diretórios são percorridos recursivamente e apenas arquivos `.json` são considerados. A ordem é determinística (ordenada por caminho).

## Códigos de saída

| Código | Significado |
|---:|---|
| `0` | Todos os arquivos foram lidos e são válidos. |
| `1` | Ao menos um arquivo é inválido ou um caminho não existe. |
| `2` | Uso incorreto, esquema inválido ou nenhum arquivo JSON foi encontrado. |

## Regras semânticas

| Código | Caminho típico | Condição |
|---|---|---|
| `duplicate-id` | `$.secoes[2].id` | Id repetido em fontes, seções, blocos ou questões. |
| `section-number` | `$.secoes[2].numero` | A seção não está na posição sequencial esperada. |
| `forbidden-section-title` | `$.secoes[3].titulo` | Seção de “questões comentadas” ou “gabarito final” no corpo. |
| `unknown-source` | `$.secoes[0].blocos[1].fontes` | Fonte referenciada não existe em `fontes`. |
| `quiz-unknown-section` | `$.quiz.questoes[0].secao_id` | Questão aponta para seção inexistente. |
| `quiz-unknown-source` | `$.quiz.questoes[0].fonte_id` | Questão aponta para fonte inexistente. |
| `incidence-unknown-section` | `$.incidencia.temas[0].secao_ids` | Tema de incidência aponta para seção inexistente. |
| `table-row-width` | `$.secoes[0].blocos[1].linhas[0]` | Linha não tem o mesmo número de células das colunas. |
| `quiz-option-count` | `$.quiz.questoes[0].opcoes` | A questão não tem entre 2 e 5 alternativas. |
| `quiz-answer-count` | `$.quiz.questoes[0].opcoes` | A questão não tem exatamente 1 alternativa correta. |
| `quiz-feedback-missing` | `$.quiz.questoes[0].opcoes[2].explicacao` | Alternativa sem explicação. |
| `quiz-duplicate-option` | `$.quiz.questoes[0].opcoes[1].texto` | Texto de alternativa repetido na mesma questão. |
| `incidence-weight-sum` | `$.incidencia.temas` | Os pesos de incidência não somam 100. |
| `incidence-duplicate-theme` | `$.incidencia.temas[1].nome` | Tema de incidência repetido. |
| `review-date-order` | `$.revisao.proxima_em` | Datas de revisão incoerentes com a atualização ou entre si. |
| `date-order` | `$.metadados.atualizado_em` | Atualização anterior à criação. |
| `missing-reviewer` | `$.metadados.revisores` | Aula `publicada` sem revisor. |
| `undefined-license` | `$.metadados.licenca` | Aula `publicada` com licença `NOASSERTION`. |
| `json` | `$` | JSON inválido, `NaN`/`Infinity` ou chave duplicada. |
| `io` | `$` | Arquivo não pôde ser lido. |
| `missing-path` | `$` | Caminho informado não existe. |
| `schema` | campo com falha | Erro estrutural do JSON Schema. |
| `schema-error` | caminho do schema | O próprio schema não pôde ser carregado. |

## Exemplo de falha

Suponha que a seção 3 esteja numerada como 4:

```text
FALHOU  exemplos/redacao-oficial/aula-00.json
        [section-number] $.secoes[2].numero: seção com número 4; esperado 3 para manter a sequência

1 arquivo(s): 0 válido(s), 1 com erro.
```

Com `--json`, a mesma falha é representada assim:

```json
{
  "valid": false,
  "schema": "schema/aula.schema.json",
  "validator_version": "1.0.0",
  "schema_version": "1.0.0",
  "files": [
    {
      "path": "exemplos/redacao-oficial/aula-00.json",
      "valid": false,
      "errors": [
        {
          "code": "section-number",
          "path": "$.secoes[2].numero",
          "message": "seção com número 4; esperado 3 para manter a sequência"
        }
      ]
    }
  ]
}
```

## O que o validador não verifica

- **Existência de URLs, DOI ou ISBN.** Ele checa o formato, não a rede.
- **Veracidade do conteúdo.** Uma aula tecnicamente válida pode conter uma interpretação errada; a revisão humana é obrigatória.
- **Citações legais.** Ele não abre o Planalto nem confere se o artigo citado existe. A governança exige conferência na fonte.
- **Qualidade pedagógica.** O validador garante o contrato, não o mérito didático.
- **Acessibilidade da apresentação.** O JSON guarda conteúdo e estrutura; o gerador HTML precisa cuidar de HTML semântico, contraste, teclado e movimento.
- **Unicidade global de `id`.** Ele verifica ids dentro do documento, não em todo o acervo.
- **Compatibilidade com todo JSON Schema.** O validador cobre o subconjunto usado pelo schema; use uma biblioteca de JSON Schema para constructs exóticos.

## Integração com CI

Um passo simples de pull request:

```yaml
- name: Validar aulas do Hermes
  run: |
    python validate.py --json
    python -m unittest discover -s tests -v
```

Em um repositório com muitas aulas, valide o diretório inteiro e trate o código de saída `1` como falha. O relatório JSON pode ser publicado como artefato ou consumido por um bot.

## Como adicionar uma regra

1. Escreva a regra em linguagem natural e um exemplo mínimo de falha.
2. Verifique se ela pode ser expressa no JSON Schema (tipo, enum, padrão) ou se é semântica (cruzamento de campos).
3. Se for semântica, adicione uma função em `validate.py` e inclua o erro em `validate_document`.
4. Adicione um teste em `tests/test_validate.py`.
5. Documente o código nesta página e, se necessário, em `docs/modelo-de-dados.md`.
6. Rode o validador no exemplo e nos testes.

## Solução de problemas

**`schema-error` no início da execução.** O `--schema` aponta para um arquivo ausente ou inválido. Verifique o caminho e se o JSON do schema está bem formado.

**Muitos erros de uma vez.** Corrija primeiro os erros estruturais; um campo ausente pode gerar erros secundários. O validador continua coletando falhas para mostrar o máximo possível.

**`oneOf` em um bloco.** O `tipo` do bloco determina os campos obrigatórios. Um `paragrafo` precisa de `texto`; uma `lista`, de `itens`; uma `tabela`, de `colunas` e `linhas`. Campos de outro tipo não são aceitos.

**`additionalProperties` em um campo novo.** O contrato é fechado. Não adicione um campo “só para testes”; versione o schema ou use `notas` enquanto o campo não existe.

**Um arquivo com acentos.** Use UTF-8. O validador aceita BOM com `utf-8-sig`, mas o ideal é salvar sem BOM.

**Uma aula publicada continua falhando.** Confira `metadados.revisores` e `metadados.licenca`. A publicação exige pelo menos um revisor e uma licença diferente de `NOASSERTION`.

**Quiz inválido.** Conte as alternativas (entre 2 e 5), a correta (exatamente 1) e as explicações (todas). Verifique também se `secao_id` e `fonte_id` existem.
