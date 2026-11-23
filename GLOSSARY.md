# Glossário do Hermes

Termos usados no contrato, na documentação e no validador.

### Hermes
Camada de dados e validação do acervo de estudos do `revisao-ifg`. Não é o site em HTML nem um LMS; é o contrato que permite gerar essas representações a partir de JSON.

### Aula
Unidade editorial do acervo. Contém identificação, fontes, seções, blocos, quiz opcional, incidência, revisão e metadados. Uma aula corresponde a um arquivo JSON.

### RO
Sigla de **Redação Oficial**, usada no exemplo `ro-aula-00`. Não é o nome do formato nem uma extensão de arquivo.

### Fonte
Documento, norma, curso, artigo, site, vídeo ou outro material que sustenta o conteúdo. Toda fonte tem `id`, `tipo` e `titulo`; pode ter `detalhes`, `ano` e `url`. Fontes são referenciadas por seções, blocos e questões.

### Seção
Divisão numerada de uma aula, com `id`, `titulo`, `subtitulo` opcional, `fontes` opcionais e `blocos`. A numeração é sequencial a partir de 1.

### Bloco
Unidade de conteúdo dentro de uma seção. Tipos: `paragrafo`, `lista`, `tabela`, `destaque`, `gotcha`, `mnemonico` e `exemplo`. Todo bloco tem `id` único na aula.

### Tópico
Bloco de subtítulo interno de uma seção (`tipo: "topico"`). Agrupa os blocos que vêm depois dele e preserva a hierarquia que o HTML legado tinha em `h3`.

### Destaque
Bloco de informação adicional, alerta, dica ou erro, com `nivel` igual a `info`, `atencao`, `sucesso` ou `erro`.

### Pegadinha (`gotcha`)
Bloco que apresenta uma afirmação falsa ou uma confusão de banca e explica a correção. Não é apenas um alerta visual; o texto precisa deixar claro o que é errado.

### Mnemônico
Bloco com frase, sigla ou recurso de memorização. Deve ser explicado, não apenas apresentado.

### Quiz
Objeto opcional de revisão ativa, com 4 a 8 questões. Cada questão tem 4 alternativas, exatamente uma correta e explicação em todas. O quiz é separado do corpo da aula.

### Alternativa
Uma das quatro opções de uma questão. Tem `texto`, `correta` e `explicacao`. A ordem no array é a ordem de apresentação.

### Incidência
Registro dos temas efetivamente cobrados nas questões de uma fonte (por exemplo, TEC Concursos). Pode ficar vazio; quando tem temas, os pesos somam 100 e cada tema aponta para seções existentes.

### Revisão
Objeto que registra `status`, `ultima_em`, `proxima_em` e `ritual`. Serve para planejar o retorno ao conteúdo e não deve ser confundido com a revisão editorial do texto.

### Metadados
Dados de autoria e versionamento: `versao` SemVer, `criado_em`, `atualizado_em`, `autores`, `revisores`, `licenca`, `origem` e `alteracoes`.

### Contrato
Conjunto de regras estruturais e semânticas que uma aula precisa cumprir. A implementação de referência está em `schema/aula.schema.json` e `validate.py`.

### Schema
Descrição formal do contrato em JSON Schema 2020-12. O `validate.py` implementa o subconjunto usado por esse schema, sem dependências externas.

### Validação
Processo que verifica estrutura e regras semânticas. Não substitui a revisão humana de conteúdo, fontes, licenças ou acessibilidade.

### Apresentação
Representação derivada do JSON: HTML, Markdown, PDF, slides, índice de busca ou cards. Não é a fonte da verdade.

### Renderização
Processo de gerar as representações derivadas. No Hermes, o `build.py` produz HTML autocontido e Markdown; o `dist/` é a saída padrão e fica fora do Git.

### Renderizador
O `build.py`: lê uma ou mais aulas, valida, e escreve `<id>.html` e/ou `<id>.md`, mais um `index.html` quando a entrada é um diretório.

### Fonte da verdade
Arquivo JSON da aula. Se o HTML e o JSON divergirem, o JSON prevalece, desde que tenha passado por revisão e validação.

### RO Aula 00
Exemplo de referência do Hermes: a aula inicial de Redação Oficial, com 12 seções, 53 blocos, 8 questões e incidência ainda vazia. O arquivo é `exemplos/redacao-oficial/aula-00.json`.
