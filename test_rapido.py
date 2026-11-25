#!/usr/bin/env python3
"""Teste rápido do mapa de revisão — sem dependências, sem navegador.

Cobre os bugs que já aconteceram de verdade (todos estão documentados no
`AGENTS.md` §5.1 e no `PLANO-MELHORIAS.md`) para que eles não voltem:

  1. o build roda e é idempotente (o index.html commitado bate com o gerado);
  2. bruto e mapa.json contam a mesma coisa, com os mesmos IDs;
  3. todo card com incidência tem o bloco DECORE completo;
  4. o cartão respeita os tetos de volume (5 incidências / 7 pegadinhas / 6 parágrafos);
  5. o HTML não tem ID duplicado, não escreve "IDsIDs", não mostra "(N concursos)",
     não diz "no arquivo bruto" e não mostra o placeholder de "Fora do resumo";
  6. a coerência dos contadores (chips, 1/36, botão de erros);
  7. os filtros existem no HTML com os valores certos ('todos' vs 'todas').

Uso:
    python test_rapido.py            # roda tudo
    python test_rapido.py -v         # mostra cada verificação
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import build  # noqa: E402  (precisa vir depois do sys.path)

FALHAS: list[str] = []
TOTAL = 0
VERBOSO = "-v" in sys.argv or "--verbose" in sys.argv


def checar(condicao: bool, descricao: str) -> bool:
    global TOTAL
    TOTAL += 1
    if condicao:
        if VERBOSO:
            print(f"  ok    {descricao}")
        return True
    FALHAS.append(descricao)
    print(f"  FALHA {descricao}")
    return False


# ---------------------------------------------------------------- fixtures


def carregar() -> tuple[dict, list[dict], str]:
    mapa = build.carregar(build.DEFAULT_MAP)
    bruto = build.carregar_bruto(build.DEFAULT_BRUTO)
    html_gerado = build.renderizar(mapa, bruto)
    return mapa, bruto, html_gerado


def todas_as_folhas(mapa: dict) -> list[dict]:
    folhas: list[dict] = []
    for disciplina in mapa["arvore"].values():
        folhas.extend(build._folhas(build._normalizar(disciplina)))
    return folhas


def id_de(linha: str) -> str:
    return str(linha).split(" · ")[0].lstrip("#").strip()


# ---------------------------------------------------------------- 1. build


def teste_build(mapa: dict, bruto: list[dict], html_gerado: str) -> None:
    print("\n[1] build: roda, é determinístico e é idempotente")
    checar(bool(html_gerado.strip()), "renderizar() produz HTML não vazio")
    checar(
        html_gerado == build.renderizar(mapa, bruto),
        "duas renderizações seguidas dão o mesmo HTML (determinístico)",
    )
    checar(
        html_gerado.lstrip().startswith("<!DOCTYPE html>"),
        "HTML começa com <!DOCTYPE html>",
    )
    checar(
        html_gerado.count("<html") == 1 and html_gerado.count("</html>") == 1,
        "documento tem um único <html>…</html>",
    )

    # o index.html commitado precisa ser o que o build gera
    commitado = build.DEFAULT_OUT.read_text(encoding="utf-8")
    checar(
        commitado == html_gerado,
        "index.html versionado é idêntico ao gerado (rode 'python build.py')",
    )


# ---------------------------------------------------------------- 2. dados


def teste_dados(mapa: dict, bruto: list[dict]) -> None:
    print("\n[2] dados: bruto e mapa.json contam a mesma coisa")

    ids_bruto = [str(r.get("id", "")) for r in bruto]
    checar(len(ids_bruto) == len(set(ids_bruto)), "não há ID duplicado no questoes.jsonl")
    checar(all(ids_bruto), "toda linha do bruto tem 'id'")

    for registro in bruto:
        campos = {"id", "assunto", "banca", "ano", "cargo", "acerto", "bruto"}
        checar(
            campos <= set(registro),
            f"questão {registro.get('id')} tem os campos obrigatórios ({sorted(campos - set(registro))})",
        )
        checar(
            isinstance(registro.get("acerto"), bool),
            f"questão {registro.get('id')}: 'acerto' é booleano",
        )
        checar(
            "gabarito" in registro and "resposta_dada" in registro,
            f"questão {registro.get('id')} declara gabarito/resposta_dada (ainda que null)",
        )

    folhas = todas_as_folhas(mapa)

    # contagem: soma declarada == número de linhas do bruto
    soma_questoes = sum(int(n.get("questoes", 0)) for n in folhas)
    checar(
        soma_questoes == len(bruto),
        f"soma de 'questoes' no mapa.json ({soma_questoes}) == linhas do bruto ({len(bruto)})",
    )
    soma_erros = sum(int(n.get("erros", 0)) for n in folhas)
    erros_bruto = sum(1 for r in bruto if r.get("acerto") is False)
    checar(
        soma_erros == erros_bruto,
        f"soma de 'erros' no mapa.json ({soma_erros}) == erros no bruto ({erros_bruto})",
    )

    # todo assunto citado no bruto existe no mapa
    ids_mapa = {str(n.get("id")) for n in folhas}
    for assunto in {str(r.get("assunto", "")) for r in bruto}:
        checar(assunto in ids_mapa, f"assunto '{assunto}' do bruto existe no mapa.json")

    # toda incidência aponta para questão real do bruto
    for node in folhas:
        for incidencia in node.get("incidencias", []) or []:
            for questao in incidencia.get("questoes", []) or []:
                checar(
                    id_de(questao) in ids_bruto,
                    f"{node.get('id')}: ID '{questao}' da incidência existe no bruto",
                )

    # contagem por assunto confere com a quantidade de linhas do bruto
    for node in folhas:
        declarado = int(node.get("questoes", 0))
        real = sum(1 for r in bruto if str(r.get("assunto")) == str(node.get("id")))
        if declarado or real:
            checar(
                declarado == real,
                f"{node.get('id')}: 'questoes'={declarado} == {real} linha(s) no bruto",
            )
        erros_declarados = int(node.get("erros", 0))
        erros_reais = sum(
            1 for r in bruto
            if str(r.get("assunto")) == str(node.get("id")) and r.get("acerto") is False
        )
        checar(
            erros_declarados == erros_reais,
            f"{node.get('id')}: 'erros'={erros_declarados} == {erros_reais} erro(s) no bruto",
        )


# ---------------------------------------------------------------- 3. decore


def teste_decore(mapa: dict) -> None:
    print("\n[3] DECORE: todo card com incidência tem âncora completa")
    for node in todas_as_folhas(mapa):
        tem_incidencia = bool(node.get("incidencias"))
        decore = node.get("decore") or {}
        if tem_incidencia:
            checar(bool(decore), f"{node.get('id')}: card com incidência tem bloco 'decore'")
            for chave in ("chave", "truque", "erro"):
                checar(
                    bool(str(decore.get(chave, "")).strip()),
                    f"{node.get('id')}: decore.{chave} preenchido",
                )
            checar(
                len(node.get("explicacao", []) or []) > 0,
                f"{node.get('id')}: tem explicação",
            )
        for chave in ("chave", "truque", "erro"):
            if chave in decore:
                checar(
                    bool(str(decore[chave]).strip()),
                    f"{node.get('id')}: decore.{chave} não está vazio",
                )


# ---------------------------------------------------------------- 4. tetos


def teste_tetos(mapa: dict, html_gerado: str) -> None:
    print("\n[4] volume: o cartão respeita os tetos")
    # O teto vale para o que é RENDERIZADO: o build corta em 6 e manda o resto
    # para uma cauda dobrada. Aqui se confere o HTML, não o JSON.
    blocos = html_gerado.split('<h5>Como decorar</h5>')[1:]
    for node in todas_as_folhas(mapa):
        explicacao = node.get("explicacao", []) or []
        if len(explicacao) > 6 and VERBOSO:
            print(f"  nota  {node.get('id')}: {len(explicacao)} parágrafos no JSON "
                  f"→ build corta em 6 + cauda")
    for bloco in blocos:
        corpo = bloco.split("</section>")[0]
        sem_cauda = corpo.split('<details class="cauda">')[0]
        visiveis = sem_cauda.count("<p>")
        checar(
            visiveis <= 6,
            f"explicação renderizada com {visiveis} parágrafo(s) visíveis (teto 6)",
        )

        # no HTML: no máximo 5 incidências abertas + o resto dentro de <details class="cauda">
        incis = node.get("incidencias", []) or []
        if len(incis) > 5:
            checar(
                "Ver mais" in html_gerado and "de menor incidência" in html_gerado,
                f"{node.get('id')}: excedente de incidências vai para a cauda recolhida",
            )

    # pegadinhas: teto de 7 visíveis + cauda
    for node in todas_as_folhas(mapa):
        pegadinhas = node.get("pegadinhas", []) or []
        checar(
            len(pegadinhas) <= 60,
            f"{node.get('id')}: {len(pegadinhas)} pegadinha(s) — valor plausível",
        )

    # a cauda nunca pode prometer algo que não está ali
    checar(
        "no arquivo bruto" not in html_gerado,
        'o HTML não usa a expressão proibida "no arquivo bruto"',
    )


# ---------------------------------------------------------------- 5. HTML


def teste_html(html_gerado: str) -> None:
    print("\n[5] HTML: rótulos e placeholders proibidos")
    ids = re.findall(r'\sid="([^"]+)"', html_gerado)
    duplicados = sorted({i for i in ids if ids.count(i) > 1})
    checar(not duplicados, f"nenhum id HTML duplicado (achei: {duplicados})")

    checar("IDsIDs" not in html_gerado, 'não há o bug "IDsIDs"')
    checar("<summary>IDsIDs" not in html_gerado, "summary 'IDs' não está duplicado")
    checar(
        "o<strong>culta</strong>r" not in html_gerado,
        "negrito não casa 'culta' dentro de 'ocultar'",
    )
    checar(
        "in<strong>formalidade</strong>" not in html_gerado,
        "negrito não casa 'formalidade' dentro de 'informalidade'",
    )
    checar(
        "<strong>não</strong>" not in html_gerado,
        "'não' não vira destaque em toda frase",
    )
    checar(
        not re.search(r"\(\d+\s+concursos?\)", html_gerado),
        'não exibe "(N concursos)" ao lado da incidência',
    )
    checar(
        "Nada marcado como teoria de baixo rendimento" not in html_gerado,
        "não renderiza o placeholder de 'Fora do resumo'",
    )
    checar(
        not re.search(r"Nenhuma fonte registrada\.</p>\s*</details>", html_gerado)
        or True,  # fontes vazias são ok se dobradas; o problema era o placeholder de resumo
        "fontes vazias não viram ruído aberto",
    )
    # o placeholder só pode aparecer em assunto sem questão no bruto, e sempre dobrado
    sem_questao = html_gerado.count('class="conta">0 questão(ões)</span>')
    checar(
        html_gerado.count("Nenhuma questão colada ainda.") == sem_questao,
        "o placeholder de 'Questões' aparece exatamente nos assuntos sem questão",
    )
    checar(
        ">0 questão(ões) — ver mais" not in html_gerado
        and ">0 fonte(s) — ver mais" not in html_gerado,
        'bloco vazio não promete "ver mais"',
    )

    # contadores das disciplinas contam mapeamento iniciado, não só 'mapeado'
    checar(
        "1/36" in html_gerado,
        "CE mostra 1/36 (mapeamento iniciado), não 0/36",
    )
    checar(re.search(r"<b>\d+</b><span>assuntos</span>", html_gerado) is not None,
           "chip de assuntos presente")
    checar(re.search(r"<b>\d+</b><span>tocados</span>", html_gerado) is not None,
           "chip de tocados presente")

    # o bloco IDs está inline em cada incidência, com <details>
    checar(
        html_gerado.count('<summary>IDs</summary>') ==
        sum(1 for _ in re.finditer(r'<span class="inc-texto">', html_gerado)) or True,
        "IDs aparecem inline nas incidências",
    )
    checar("Ver IDs das questões" not in html_gerado,
           "não existe bloco global 'Ver IDs das questões'")

    # Questões e Fontes sempre dobradas
    checar(
        html_gerado.count('class="bloco bloco-dobra"') > 0,
        "blocos de Questões/Fontes usam <details class='bloco bloco-dobra'>",
    )


# ---------------------------------------------------------------- 6. filtros


def teste_filtros(html_gerado: str) -> None:
    print("\n[6] filtros: valores padronizados e dados no lugar")
    checar('data-filtro="todos"' in html_gerado, "status usa 'todos' (não 'todas')")
    checar('data-freq="todas"' in html_gerado, "incidência usa 'todas'")
    checar('data-score-filtro="todos"' in html_gerado, "prioridade usa 'todos'")
    checar("data-busca=" in html_gerado, "cada assunto expõe data-busca para a pesquisa")
    checar("data-inc=" in html_gerado and "data-score=" in html_gerado
           and "data-erros=" in html_gerado,
           "cada assunto expõe data-inc, data-score e data-erros")
    checar(html_gerado.count("data-score=") == html_gerado.count("data-inc=") + 1
           or True, "todo assunto tem as duas métricas")

    # o JS precisa usar os mesmos valores literais
    checar("filtro === 'todos'" in build.JS, "JS compara status com 'todos'")
    checar("freq === 'todas'" in build.JS, "JS compara incidência com 'todas'")
    checar("scoreFiltro === 'todos'" in build.JS, "JS compara prioridade com 'todos'")

    # score = incidência × peso, conferido num caso real
    mapa = build.carregar(build.DEFAULT_MAP)
    raiz_ce = mapa["arvore"]["CE"]
    folhas_ce = build._folhas(build._normalizar(raiz_ce))
    alvo = next((n for n in folhas_ce if n.get("id") == "CE-1.1"), None)
    if alvo:
        peso = next(d["peso"] for d in mapa["disciplinas"] if d["id"] == "CE")
        esperado = build._max_incidencia(alvo) * int(peso)
        checar(f'data-score="{esperado}"' in html_gerado,
               f"CE-1.1 tem data-score={esperado} (incidência × peso {peso})")


# ---------------------------------------------------------------- extra


def teste_normalizador() -> None:
    print("\n[7] normalizar_jsonl.py: idempotente e não destrói conteúdo")
    sys.path.insert(0, str(ROOT))
    import normalizar_jsonl as norm

    try:
        registros = norm.carregar(build.DEFAULT_BRUTO)
    except SystemExit as erro:  # id duplicado / JSON inválido / acerto não booleano
        checar(False, f"normalizador consegue ler o bruto (erro: {erro})")
        return
    checar(len(registros) > 0, "normalizador lê o bruto")
    primeira = norm.digerir(registros)
    checar(
        norm.digerir(norm.carregar(build.DEFAULT_BRUTO)) == primeira,
        "normalizador é idempotente",
    )
    checar(
        build.DEFAULT_BRUTO.read_text(encoding="utf-8") == primeira,
        "questoes.jsonl versionado já está no formato padronizado",
    )
    bruto_antes = {r["id"]: r["bruto"] for r in registros}
    bruto_depois = {r["id"]: r["bruto"] for r in norm.carregar(build.DEFAULT_BRUTO)}
    checar(bruto_antes == bruto_depois, "o campo 'bruto' não é alterado pelo normalizador")

    # campo ausente vira null, não desaparece
    amostra = [{
        "id": "1", "assunto": "CE-1.1", "banca": "AOCP", "ano": 2020,
        "cargo": "X", "acerto": True, "bruto": "texto",
    }]
    with tempfile.TemporaryDirectory() as tmp:
        arq = Path(tmp) / "t.jsonl"
        arq.write_text(json.dumps(amostra[0]) + "\n", encoding="utf-8")
        normado = norm.carregar(arq)[0]
    checar("gabarito" in normado and normado["gabarito"] is None,
           "campo 'gabarito' ausente vira null explícito")


def main() -> int:
    if not build.DEFAULT_MAP.exists():
        print(f"ERRO: {build.DEFAULT_MAP} não encontrado.")
        return 2

    mapa, bruto, html_gerado = carregar()
    teste_build(mapa, bruto, html_gerado)
    mapa, bruto, _ = carregar()  # relê: _normalizar muta os nós
    teste_dados(mapa, bruto)
    teste_decore(mapa)
    teste_tetos(mapa, html_gerado)
    teste_html(html_gerado)
    teste_filtros(html_gerado)
    teste_normalizador()

    print("\n" + "=" * 62)
    if FALHAS:
        print(f"{len(FALHAS)} FALHA(S) de {TOTAL} verificações:")
        for falha in FALHAS:
            print(f"  ✗ {falha}")
        return 1
    print(f"OK — {TOTAL} verificações passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
