# Exemplos do Hermes

| Arquivo | Aula | Matéria | Status | Quiz |
|---|---|---|---|---:|
| [`redacao-oficial/aula-00.json`](redacao-oficial/aula-00.json) | Aula 00 — Fundamentos, atributos e padrão ofício | Redação Oficial | rascunho | 8 questões |
| [`informatica/aula-01.json`](informatica/aula-01.json) | Aula 01 — Protocolos de comunicação | Informática | rascunho | 4 questões (Certo/Errado) |
| [`arquivologia/aula-01.json`](arquivologia/aula-01.json) | Aula 01 — Classificação de documentos | Arquivologia | rascunho | 6 questões |
| [`etica/aula-01.json`](etica/aula-01.json) | Aula 01 — Conceitos, fundamentos, ética profissional e assédio | Ética geral e profissional | rascunho | 8 questões |
| [`administracao-de-pessoas/aula-01.json`](administracao-de-pessoas/aula-01.json) | Aula 01 — Conceito, funções, estratégia, liderança, equipe e motivação | Administração de Pessoas | rascunho | 8 questões |
| [`administracao-de-pessoas/aula-02.json`](administracao-de-pessoas/aula-02.json) | Aula 02 — Recrutamento e seleção, cargos e remuneração, T&D e avaliação de desempenho | Administração de Pessoas | rascunho | 8 questões |
| [`portugues/aula-01.json`](portugues/aula-01.json) | Aula 01 — Concordância, crase, regência e pontuação | Língua Portuguesa | rascunho | 8 questões |
| [`rlm/aula-01.json`](rlm/aula-01.json) | Aula 01 — Lógica proposicional, conjuntos, combinatória, aritmética e geometria | Raciocínio Lógico e Matemática | rascunho | 8 questões |

### Legislação federal (cargo 301 — Assistente em Administração, IFG)

Dez aulas escritas a partir do texto consolidado de cada norma (Planalto), com `fontes` de nível aula e fonte por bloco. Todas em `rascunho`, aguardando revisão; o aviso de vigência está em `notas` de cada arquivo.

| Arquivo | Norma | Estrutura | Quiz |
|---|---|---|---:|
| [`legislacao/aula-01.json`](legislacao/aula-01.json) | Lei nº 8.112/1990 — regime jurídico do servidor federal | 13 seções, 72 blocos | 8 |
| [`legislacao/aula-02.json`](legislacao/aula-02.json) | Decreto nº 1.171/1994 (Código de Ética) e Decreto nº 6.029/2007 (Sistema de Gestão da Ética) | 8 seções, 32 blocos | 8 |
| [`legislacao/aula-03.json`](legislacao/aula-03.json) | Lei nº 9.394/1996 — LDB | 8 seções, 48 blocos | 8 |
| [`legislacao/aula-04.json`](legislacao/aula-04.json) | Lei nº 11.892/2008 — Rede Federal e Institutos Federais | 10 seções, 32 blocos | 7 |
| [`legislacao/aula-05.json`](legislacao/aula-05.json) | Lei nº 11.091/2005 — PCCTAE (com Leis nº 15.141/2025 e 15.367/2026) | 8 seções, 32 blocos | 7 |
| [`legislacao/aula-06.json`](legislacao/aula-06.json) | Lei nº 9.784/1999 — processo administrativo federal | 9 seções, 39 blocos | 8 |
| [`legislacao/aula-07.json`](legislacao/aula-07.json) | Lei nº 13.709/2018 — LGPD (com Resolução CD/ANPD nº 15/2024) | 7 seções, 34 blocos | 8 |
| [`legislacao/aula-08.json`](legislacao/aula-08.json) | Lei nº 12.527/2011 — Lei de Acesso à Informação | 5 seções, 26 blocos | 7 |
| [`legislacao/aula-09.json`](legislacao/aula-09.json) | Lei nº 8.429/1992 — improbidade (redação da Lei nº 14.230/2021) | 4 seções, 21 blocos | 7 |
| [`legislacao/aula-10.json`](legislacao/aula-10.json) | Lei nº 14.133/2021 — licitações e contratos | 7 seções, 40 blocos | 8 |

Os exemplos são válidos pelo schema `1.1.0` e pelas regras semânticas do `validate.py`. As aulas de Legislação usam quiz de 5 alternativas (formato da prova AOCP); as migradas usam 2 ou 4 e devem ser revisadas antes de virar material de prova. A leitura humana do exemplo RO, com mapa de seções e pontos-chave, está em [`docs/exemplo-ro-aula-00.md`](../docs/exemplo-ro-aula-00.md).

Para validar todos os exemplos:

```bash
python validate.py
```
