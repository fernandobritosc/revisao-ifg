# Contribuindo

O Hermes é um contrato pequeno e versionado. Antes de abrir uma mudança:

1. Leia [docs/formato-conteudo.md](docs/formato-conteudo.md) e [docs/modelo-de-dados.md](docs/modelo-de-dados.md).
2. Rode `python validate.py` e `python -m unittest discover -s tests -v`.
3. Para uma regra nova, escreva o caso de falha antes de implementar.
4. Não inclua materiais binários, dados pessoais ou links que não possa conferir.
5. Mantenha o exemplo `exemplos/redacao-oficial/aula-00.json` válido; ele é o teste de fumaça do projeto.
6. Não commitar em nome de outra pessoa; revise o `git diff` antes de versionar.

## Escopo de uma mudança

- **Conteúdo de uma aula:** edite o JSON, atualize `metadados.versao` e `alteracoes`.
- **Contrato:** edite `schema/aula.schema.json`, documente a migração e só então os exemplos.
- **Validador:** adicione testes para o caminho válido e para cada novo código de erro.
- **Documentação derivada:** não a trate como fonte da verdade; atualize a partir do JSON.

## Regras de conteúdo

- Não cite dispositivo legal de memória; confira a fonte e registre-a em `fontes`.
- Não invente incidência do TEC; se não houver questões, deixe `temas` vazio e explique.
- Não publique conteúdo com revisor fictício ou licença indefinida.
- Mantenha o quiz separado do corpo da aula.
