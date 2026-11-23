# Governança editorial

O Hermes separa **validação técnica** de **decisão editorial**. O validador garante que o documento está completo e coerente; a equipe decide se o conteúdo é fiel às fontes, se a didática é adequada e se a aula pode ser publicada.

## Ciclo de vida

```text
rascunho ──> revisao ──> publicado ──> arquivado
   ^            |             |
   |            +-------------+
   +--------------------------+
```

| Estado | Quando usar | O que precisa estar pronto |
|---|---|---|
| `rascunho` | Primeira versão, experimento, adaptação. | JSON válido; fontes registradas; seções e blocos esboçados. |
| `revisao` | Conteúdo pronto para outra pessoa ler. | Fontes conferidas; quiz íntegro; acessibilidade verificada. |
| `publicado` | Pode ser usado por outras pessoas. | Revisor identificado; licença definida; links e fontes checados. |
| `arquivado` | Substituído ou fora de circulação. | Motivo registrado em `metadados.alteracoes` ou `notas`. |

Uma aula em `rascunho` **também precisa validar**. O estado descreve maturidade editorial, não permissão para quebrar o contrato.

## Papéis

- **Autoria** — escreve o conteúdo, organiza as seções e mantém `metadados.autores`.
- **Revisão de conteúdo** — confere fidelidade às fontes, precisão das afirmações e coerência do quiz.
- **Revisão de acessibilidade** — confere linguagem, estrutura, alternativas de texto e necessidades do gerador HTML.
- **Revisão editorial** — confere título, resumo, links, licença, tags e metadados.
- **Manutenção do schema** — decide mudanças de contrato e migrações.

Uma pessoa pode acumular papéis, mas uma aula `publicada` precisa de ao menos um nome em `revisores`.

## Regras de fontes e conteúdo

1. **Nada sem fonte.** Toda afirmação relevante deve poder ser rastreada até uma fonte em `fontes`.
2. **Não cite dispositivo legal de memória.** Abra o texto oficial, confira a versão e registre o detalhe. Se a fonte da aula não traz o dispositivo, não invente.
3. **Distinga fonte primária de material didático.** O MRPR, uma lei ou um decreto são fontes primárias; um curso ou apostila é material didático. Registre o tipo corretamente.
4. **Edital é a lei.** Para concursos, o edital define o manual, a banca e o recorte. Uma regra do MRPR pode não valer para um órgão com manual próprio.
5. **Não transforme dúvida em certeza.** Se a fonte é omissa ou há conflito normativo, registre a ressalva em `notas` ou no bloco adequado.
6. **Não remova contexto.** Uma regra antiga ou revogada precisa explicar por que ainda aparece ou por que saiu do radar.

## Checklist de publicação

### Conteúdo

- [ ] O `id` é único e estável; o título descreve a aula.
- [ ] O resumo explica o recorte sem copiar a ementa.
- [ ] As fontes existem, estão completas e são citadas nos blocos relevantes.
- [ ] As seções estão numeradas e têm progressão lógica.
- [ ] As tabelas têm todas as linhas com o mesmo número de células.
- [ ] Não há seção de “questões comentadas” ou “gabarito final” no corpo.
- [ ] As afirmações legais foram conferidas no texto oficial.

### Quiz

- [ ] 4 a 8 questões.
- [ ] 4 alternativas por questão.
- [ ] Exatamente uma correta por questão.
- [ ] Explicação em todas as alternativas, inclusive na correta.
- [ ] `secao_id` e `fonte_id` existem.
- [ ] As questões cobram recall útil, não curiosidade irrelevante.

### Incidência e revisão

- [ ] A incidência registra apenas temas efetivamente cobrados.
- [ ] Quando há temas, os pesos somam 100 e as seções existem.
- [ ] Se não há questões, `temas` está vazio e a `observacao` explica.
- [ ] `revisao` tem status, próxima data e ritual.
- [ ] As datas de revisão são coerentes com `metadados.atualizado_em`.

### Metadados e direitos

- [ ] `metadados.versao` reflete a mudança.
- [ ] `atualizado_em` foi atualizada e não é anterior a `criado_em`.
- [ ] `alteracoes` explica o que mudou.
- [ ] `revisores` contém quem revisou de fato.
- [ ] A licença está explícita e não é `NOASSERTION` na publicação.
- [ ] Materiais de terceiros têm licença compatível com o uso previsto.

### Apresentação

- [ ] O gerador HTML usa HTML semântico (`h1`–`h6`, `table`, `thead`, `th scope`).
- [ ] O conteúdo não depende de cor, posição ou movimento para ser compreendido.
- [ ] Há texto alternativo para imagens e transcrição para conteúdo falado, quando aplicável.
- [ ] O layout funciona em teclado e em telas pequenas.
- [ ] O modo de revisão e o quiz são acessíveis e não exibem a resposta antes do clique.

## Convenções de arquivo

- Uma aula por arquivo, em `exemplos/<materia>/aula-XX.json` ou no diretório editorial do projeto.
- Nome do arquivo: `aula-XX.json`, com dois dígitos quando possível.
- Não use espaços, acentos ou parênteses no nome do arquivo.
- Não versione materiais binários dentro do JSON; referencie-os em `fontes` e mantenha-os no local definido pelo projeto.
- Não edite a fonte JSON a partir de um PDF ou slide; edite o JSON e gere as representações.

## Mudanças e revisões

1. **Correção de texto** — aumenta `metadados.versao` em patch (`1.0.0` → `1.0.1`) quando há mudança de conteúdo.
2. **Nova seção, bloco ou questão** — minor (`1.0.0` → `1.1.0`) se o recorte continua compatível.
3. **Mudança de recorte, fontes ou avaliação** — major (`1.0.0` → `2.0.0`), porque pode alterar o uso da aula.
4. **Ajuste de schema** — mude `schema_version` separadamente; nunca use a versão do conteúdo para esconder uma mudança de contrato.

## Arquivamento

Arquive em vez de apagar quando a aula tiver histórico relevante. Mantenha o `id` e registre o motivo em `notas` ou `alteracoes`. Se o conteúdo for substituído, crie uma nova aula ou atualize a versão com clareza sobre a substituição.

## O que a validação não decide

A validação não diz se uma aula é boa, se uma fonte é confiável, se uma atividade é inclusiva na prática ou se uma licença é adequada. Ela reduz erros mecânicos para que a revisão humana gaste tempo com o que realmente importa.
