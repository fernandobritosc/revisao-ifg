# Documentação do Hermes

O Hermes é o contrato de conteúdo das aulas do `revisao-ifg`. Esta documentação explica o modelo, a autoria, a validação e a governança.

## Ordem de leitura

1. **[Formato de conteúdo](formato-conteudo.md)** — anatomia de uma aula, blocos, quiz e incidência.
2. **[Modelo de dados](modelo-de-dados.md)** — entidades, relacionamentos, dicionário e invariantes.
3. **[Exemplo RO Aula 00](exemplo-ro-aula-00.md)** — leitura humana do exemplo completo.
4. **[Validação](validacao.md)** — como rodar o validador e interpretar os erros.
5. **[Renderização](renderizacao.md)** — como o JSON vira HTML autocontido e Markdown.
6. **[Governança](governanca.md)** — fontes, revisão, acessibilidade e ciclo de vida.
7. **[Migração](migracao.md)** — conversão do acervo HTML legado para o Hermes.
8. **[Decisões](decisoes.md)** — restrições e alternativas consideradas.
9. **[Glossário](../GLOSSARY.md)** — vocabulário do contrato e da equipe.
10. **[Plano IFG 2026/2027](plano-ifg-2026.md)** — cobertura do edital e cronograma de produção.

## Arquivos de referência

- [`schema/aula.schema.json`](../schema/aula.schema.json) — contrato estrutural.
- [`exemplos/redacao-oficial/aula-00.json`](../exemplos/redacao-oficial/aula-00.json) — exemplo completo.
- [`exemplos/etica/`](../exemplos/etica/) — aula de Ética geral e profissional (cargo 301), com conceitos, fundamentos, ética profissional, assédio e pontos que mais caem.
- [`exemplos/administracao-de-pessoas/`](../exemplos/administracao-de-pessoas/) — duas aulas de Administração de pessoas (cargo 301): conceito e funções, e recrutamento, cargos, T&D e avaliação de desempenho.
- [`exemplos/portugues/`](../exemplos/portugues/) — aula de Língua Portuguesa (cargo 301): concordância, crase, regência e pontuação.
- [`exemplos/rlm/`](../exemplos/rlm/) — aula de Raciocínio Lógico e Matemática (cargo 301): lógica proposicional, conjuntos, combinatória, aritmética e geometria.
- [`exemplos/legislacao/`](../exemplos/legislacao/) — dez aulas de Legislação federal escritas a partir das normas (8.112, D. 1.171 e D. 6.029, LDB, 11.892, 11.091, 9.784, LGPD, LAI, 8.429, 14.133), com fonte por bloco e quiz de 5 alternativas; índice em [`exemplos/README.md`](../exemplos/README.md).
- [`validate.py`](../validate.py) — validador executável.
- [`build.py`](../build.py) — gerador de HTML e Markdown.
- [`tests/test_validate.py`](../tests/test_validate.py) — testes de regressão.

## Convenções

- Idioma editorial: português brasileiro (`pt-BR`).
- Datas no formato ISO `AAAA-MM-DD`.
- Identificadores em `kebab-case`, estáveis e legíveis.
- Números de seção começam em 1 e são sequenciais.
- Fontes são registradas em `fontes` e referenciadas por id em seções, blocos e questões.
- O quiz é separado do corpo da aula; questões comentadas e gabarito não entram nas seções.
- O JSON é a fonte da verdade. Documentação derivada deve indicar a versão do schema e da aula.
