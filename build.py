#!/usr/bin/env python3
"""Gera a página índice do mapa de revisão a partir de mapa.json.

Card = explicação para memorizar + incidência (quantas vezes o mesmo ponto
já caiu, com palavras diferentes ou não) + pegadinhas + questões.

Uso:
    python build.py                 # lê mapa.json -> index.html
    python build.py --out site.html # saída alternativa

Sem dependências externas.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from json_seguro import loads

ROOT = Path(__file__).resolve().parent
DEFAULT_MAP = ROOT / "mapa.json"
DEFAULT_OUT = ROOT / "index.html"
DEFAULT_BRUTO = ROOT / "questoes.jsonl"

CORES = {
    "CC-1": ("#2563eb", "#e8effd"),
    "CC-2": ("#7c3aed", "#f1eafe"),
    "CC-3": ("#d97706", "#fdf1e0"),
    "CC-4": ("#0891b2", "#e2f5f8"),
    "CE": ("#059669", "#e4f6ee"),
}
STATUS_LABEL = {
    "nao-mapeado": "não mapeado",
    "em-mapeamento": "em mapeamento",
    "mapeado": "mapeado",
}


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


TERMOS_IMPORTANTES = [
    "suspensão dos direitos políticos", "perda dos direitos políticos",
    "perda da função pública", "indisponibilidade dos bens",
    "ressarcimento ao erário", "suspensão", "indisponibilidade", "ressarcimento",
    "readaptação", "enquanto permanecer", "acréscimos pecuniários",
    "não serão computados", "não serão acumulados", "rompimento do vínculo",
    "promoção pessoal", "não podendo constar", "culta", "rebuscada",
    "figuras de linguagem", "regionalismos", "modismos", "jargão burocrático",
    "até dois anos", "Supremo Tribunal Federal", "Superior Tribunal de Justiça",
    "funções de confiança", "cargos em comissão", "direção, chefia e assessoramento",
    "natureza e complexidade",
    "LIMPE", "Legalidade", "Impessoalidade", "Moralidade", "Publicidade",
    "Eficiência", "princípios expressos",
    "hierarquia", "razoabilidade", "autotutela", "economicidade", "finalidade",
    "continuidade", "supremacia do interesse público",
    "autarquia", "lei específica", "ato administrativo",
    "estrangeiros", "deficiência", "readaptação", "subsidiárias",
    "controle social", "Tribunais de Contas", "sociedade civil",
    "Ministério Público", "controle externo", "transparência",
    "qualquer natureza", "técnico ou científico", "EC 138/2025",
    "inacumulabilidade", "sociedade de economia mista",
    "condição necessária", "acumulação", "profissões regulamentadas", "administração indireta",
    "compatibilidade de horários",
    "teto do Executivo", "vinculação", "equiparação", "estrangeiros",
    "Legislativo", "Judiciário", "Executivo", "vencimentos",
    "clareza", "precisão", "objetividade", "concisão", "coesão", "coerência",
    "impessoalidade", "formalidade", "padronização", "norma padrão",
    "art. 37, §4º", "art. 37, §13", "art. 37, §14", "art. 37, XIV",
    "art. 37, §1º", "art. 18", "art. 20", "art. 21", "art. 26", "art. 28",
    "§4º", "§13", "§14", "§1º", "XIV", "CF/88", "MRPR",
    "territórios", "entes autônomos", "recursos minerais", "subsolo",
    "primeiro domingo", "último domingo", "material bélico",
    "mandato eletivo", "vereador", "compatibilidade de horários", "afastamento",
    "art. 38",
    "ERRO", "acerto",
]
# Lookarounds de palavra: sem eles, "culta" casava dentro de "ocultar" e
# "formalidade" dentro de "informalidade", corrompendo o texto exibido.
_palavras = re.compile(
    "|".join(
        r"(?<!\w)" + re.escape(t) + r"(?!\w)"
        for t in sorted(TERMOS_IMPORTANTES, key=len, reverse=True)
    ),
    re.IGNORECASE,
)


def _negrito(texto: Any) -> str:
    """Escapa e coloca em negrito os termos importantes, numa única passada."""
    return _palavras.sub(lambda m: f"<strong>{m.group(0)}</strong>", esc(texto))


def _data_pt(value: Any) -> str:
    """Converte AAAA-MM-DD em DD/MM/AAAA para exibição."""
    if not isinstance(value, str):
        return ""
    partes = value.split("-")
    if len(partes) == 3 and all(p.isdigit() for p in partes):
        return f"{partes[2]}/{partes[1]}/{partes[0]}"
    return value


def carregar(caminho: Path) -> dict[str, Any]:
    with caminho.open(encoding="utf-8") as arquivo:
        dados = loads(arquivo.read())
    if not isinstance(dados, dict):
        raise ValueError("mapa.json precisa ser um objeto JSON")
    return dados


def carregar_bruto(caminho: Path) -> list[dict[str, Any]]:
    """Lê questoes.jsonl. Arquivo ausente = lista vazia (o build não quebra)."""
    if not caminho.exists():
        return []
    registros: list[dict[str, Any]] = []
    with caminho.open(encoding="utf-8") as arquivo:
        for numero, linha in enumerate(arquivo, 1):
            if not linha.strip():
                continue
            try:
                registros.append(loads(linha))
            except ValueError as erro:
                raise ValueError(f"{caminho.name} linha {numero}: JSON inválido ({erro})") from erro
    return registros


# O gabarito nem sempre está num campo próprio: muitas resoluções do TEC trazem
# "Gabarito: LETRA C" ou "A RESPOSTA É A LETRA D" no corpo do texto do bruto.
_PADROES_GABARITO = (
    re.compile(r"gabarito\s*:?\s*(?:letra\s*)?([A-E])\b", re.IGNORECASE),
    re.compile(r"resposta\s+[ée]\s+(?:a\s+)?letra\s*([A-E])\b", re.IGNORECASE),
    re.compile(r"alternativa\s+correta\s+[ée]\s+(?:a\s+)?letra\s*([A-E])\b", re.IGNORECASE),
)


def _letra(registro: dict[str, Any]) -> str:
    """Letra da resposta: resposta_dada > gabarito > texto do bruto."""
    for campo in ("resposta_dada", "gabarito"):
        valor = registro.get(campo)
        if isinstance(valor, str) and valor.strip():
            return valor.strip()[0].upper()
        if isinstance(valor, int):
            return str(valor)
    texto = str(registro.get("bruto", ""))
    for padrao in _PADROES_GABARITO:
        achado = padrao.search(texto)
        if achado:
            return achado.group(1).upper()
    return "?"


def _banca_curta(banca: Any) -> str:
    """'Instituto AOCP' -> 'AOCP'; preserva o que já é curto."""
    texto = str(banca or "").strip()
    return texto[len("Instituto "):] if texto.lower().startswith("instituto ") else texto


def _questao_linha(registro: dict[str, Any]) -> str:
    """Linha do cartão derivada do bruto: '#ID · BANCA ANO · CARGO — resultado'."""
    cabeca = (
        f"#{registro.get('id', '?')} · {_banca_curta(registro.get('banca'))} "
        f"{registro.get('ano', '?')} · {registro.get('cargo', '')}"
    )
    letra = _letra(registro)
    if registro.get("acerto") is True:
        return f"{cabeca} — acerto ({letra})"
    gabarito = _letra(
        {"gabarito": registro.get("gabarito"), "bruto": registro.get("bruto", "")}
    )
    return f"{cabeca} — ERRO (marquei {letra}, gabarito {gabarito})"


def _registros_do_assunto(
    node: dict[str, Any], bruto: list[dict[str, Any]]
) -> list[str]:
    """Questões do assunto, derivadas do bruto na ordem de registro.

    O `questoes_lista` do mapa.json deixa de ser fonte: se ainda houver linhas
    lá que não existam no bruto, elas são preservadas no fim, para nada se perder.
    """
    ident = str(node.get("id", ""))
    derivadas = [
        _questao_linha(r) for r in bruto
        if str(r.get("assunto", "")) == ident
    ]
    ids_bruto = {str(r.get("id", "")) for r in bruto}
    legado = []
    for linha in node.get("questoes_lista", []) or []:
        texto = str(linha).split(" · reapareceu em")[0]
        id_linha = texto.split(" · ")[0].lstrip("#").strip()
        if id_linha and id_linha not in ids_bruto:
            legado.append(texto)
    return derivadas + legado


def _filhos(node: dict[str, Any]) -> list[dict[str, Any]]:
    return [f for f in node.get("filhos", []) if isinstance(f, dict)]


def _numero(node: dict[str, Any]) -> str:
    if "numero" in node:
        return str(node["numero"])
    ident = str(node.get("id", ""))
    return ident.split("-")[-1] if "-" in ident else ident


def _normalizar(node: dict[str, Any]) -> dict[str, Any]:
    node.setdefault("status", "nao-mapeado")
    node.setdefault("questoes", 0)
    node.setdefault("erros", 0)
    for campo in (
        "explicacao", "incidencias", "pegadinhas", "fora_do_resumo",
        "fontes", "questoes_lista",
    ):
        node.setdefault(campo, [])
    for filho in _filhos(node):
        _normalizar(filho)
    return node


def _folhas(node: dict[str, Any]) -> list[dict[str, Any]]:
    filhos = _filhos(node)
    if not filhos:
        return [node]
    return [folha for filho in filhos for folha in _folhas(filho)]


def _progresso(folhas: list[dict[str, Any]]) -> tuple[int, int]:
    """Conta assuntos com mapeamento iniciado, não só os fechados."""
    total = len(folhas)
    iniciados = sum(
        1 for n in folhas
        if n.get("status") != "nao-mapeado"
        or int(n.get("questoes", 0)) > 0
        or bool(n.get("incidencias"))
    )
    return iniciados, total


def _revisado_info(node: dict[str, Any]) -> tuple[str, str] | None:
    """Aviso de revisão espaçada: (texto, classe) ou None se sem data."""
    valor = node.get("revisado_em")
    if not isinstance(valor, str):
        return None
    try:
        quando = date.fromisoformat(valor)
    except ValueError:
        return None
    dias = (date.today() - quando).days
    if dias < 0:
        return None
    if dias <= 3:
        classe = "recente"
    elif dias <= 7:
        classe = "atencao"
    else:
        classe = "atrasado"
    texto = "revisado hoje" if dias == 0 else f"há {dias} dia(s)"
    return texto, classe


def _max_incidencia(node: dict[str, Any]) -> int:
    return max(
        (int(i.get("vezes", 0)) for i in node.get("incidencias", []) if isinstance(i, dict)),
        default=0,
    )


def estatisticas(dados: dict[str, Any]) -> dict[str, int]:
    todas: list[dict[str, Any]] = []
    for disciplina in dados["arvore"].values():
        todas.extend(_folhas(_normalizar(disciplina)))
    tocados = sum(
        1 for n in todas
        if int(n.get("questoes", 0)) > 0
        or n.get("status") != "nao-mapeado"
        or bool(n.get("incidencias"))
    )
    return {
        "assuntos": len(todas),
        "tocados": tocados,
        "vazios": len(todas) - tocados,
        "mapeados": sum(1 for n in todas if n["status"] == "mapeado"),
        "em_mapeamento": sum(1 for n in todas if n["status"] == "em-mapeamento"),
        "questoes": sum(int(n.get("questoes", 0)) for n in todas),
        "erros": sum(int(n.get("erros", 0)) for n in todas),
        "assuntos_com_erros": sum(1 for n in todas if int(n.get("erros", 0)) > 0),
        "com_incidencia": sum(1 for n in todas if _max_incidencia(n) >= 2),
    }


def _lista(itens: Any, vazio: str) -> str:
    if not itens:
        return f'<p class="vazio">{esc(vazio)}</p>'
    return "<ul>" + "".join(
        f"<li>{_negrito(item.get('texto', item)) if isinstance(item, dict) else _negrito(item)}</li>"
        for item in itens
    ) + "</ul>"


def _inc_linha(item: dict[str, Any]) -> str:
    vezes = int(item.get("vezes", 0))
    classe = "alta" if vezes >= 3 else ("media" if vezes == 2 else "baixa")
    questoes = [str(q) for q in item.get("questoes", [])]
    ids_html = ""
    if questoes:
        limpos = [q.split("(")[0].strip() for q in questoes]
        ids_html = (
            '<details class="ids-linha"><summary>IDs</summary>'
            f'<small>{", ".join(esc(q) for q in limpos)}</small></details>'
        )
    return (
        f'<li><span class="vezes vezes-{classe}">{vezes}x</span>'
        f'<span class="inc-texto">{_negrito(item.get("texto", ""))}{ids_html}</span></li>'
    )


def _incidencias_html(incidencias: list[dict[str, Any]]) -> str:
    """Mostra no máximo 5 incidências (as maiores); o resto vai numa cauda recolhida.

    O cartão precisa continuar curto mesmo depois de dezenas de questões.
    Nenhuma informação é perdida: a cauda traz todas as demais e o texto integral
    está em questoes.jsonl.
    """
    validas = [i for i in incidencias if isinstance(i, dict)]
    if not validas:
        return '<p class="vazio">Nenhuma incidência registrada ainda.</p>'
    ordenadas = sorted(validas, key=lambda i: int(i.get("vezes", 0)), reverse=True)
    principais, cauda = ordenadas[:5], ordenadas[5:]
    html = f'<ul class="incidencias">{"".join(_inc_linha(i) for i in principais)}</ul>'
    if cauda:
        linhas = "".join(_inc_linha(i) for i in cauda)
        html += (
            f'<details class="cauda"><summary>Ver mais {len(cauda)} ponto(s) '
            f'de menor incidência</summary><ul class="incidencias">{linhas}</ul></details>'
        )

    return html


def _lista_marcada(itens: list[Any], vazio: str) -> str:
    """Lista que marca em vermelho as questões registradas como erro."""
    if not itens:
        return f'<p class="vazio">{esc(vazio)}</p>'
    linhas = []
    for item in itens:
        texto = str(item)
        classe = ' class="questao-erro"' if "ERRO" in texto else ""
        linhas.append(f"<li{classe}>{_negrito(texto)}</li>")
    return "<ul>" + "".join(linhas) + "</ul>"


def _lista_com_cauda(
    itens: list[Any], vazio: str, limite: int, rotulo: str
) -> str:
    """Lista curta + details com o excedente, sem esconder dados atrás de aviso."""
    if not itens:
        return f'<p class="vazio">{esc(vazio)}</p>'
    html = "<ul>" + "".join(f"<li>{_negrito(i)}</li>" for i in itens[:limite]) + "</ul>"
    resto = itens[limite:]
    if resto:
        linhas = "".join(f"<li>{_negrito(i)}</li>" for i in resto)
        html += (
            f'<details class="cauda"><summary>Ver mais {len(resto)} {rotulo}</summary>'
            f'<ul class="incidencias">{linhas}</ul></details>'
        )
    return html


def _bloco_html(titulo: str, conteudo: str, manter: bool) -> str:
    """Questões, fontes e pegadinhas ficam dobradas; o resto aparece aberto no cartão."""
    if titulo in {"Questões", "Fontes", "Pegadinhas"}:
        total = conteudo.count("<li")
        if titulo == "Questões":
            rotulo = "questão(ões)"
        elif titulo == "Fontes":
            rotulo = "fonte(s)"
        else:
            rotulo = "pegadinha(s)"
        contador = f"{total} {rotulo} · ver mais" if total else f"{total} {rotulo}"
        return (
            '<details class="bloco bloco-dobra">'
            f'<summary>{esc(titulo)} · <span class="conta">{contador}</span>'
            '</summary>'
            f'<div class="dobra-conteudo">{conteudo}</div></details>'
        )
    classe = " keep" if manter else ""
    extra = " como-decorar" if titulo == "Como decorar" else ""
    return f'<section class="bloco{classe}{extra}"><h5>{esc(titulo)}</h5>{conteudo}</section>'


def _cartao(node: dict[str, Any], bruto: list[dict[str, Any]]) -> str:
    cabecalho = ""
    decore = node.get("decore")
    if isinstance(decore, dict) and decore:
        linhas = "".join(
            f'<div><span>{esc(rotulo)}</span><b>{esc(decore[chave])}</b></div>'
            for rotulo, chave in (
                ("CHAVE", "chave"), ("TRUQUE", "truque"), ("ERRO CLÁSSICO", "erro")
            )
            if decore.get(chave)
        )
        cabecalho = f'<div class="decore keep">{linhas}</div>'

    blocos: list[tuple[str, str, bool]] = []
    explicacao = [p for p in (node.get("explicacao") or []) if str(p).strip()]
    if explicacao:
        # Teto de 6 parágrafos: o excesso não é apagado, vai para a cauda dobrada.
        visiveis, excedente = explicacao[:6], explicacao[6:]
        texto = "".join(f'<p class="explic-par">{_negrito(p)}</p>' for p in visiveis)
        if excedente:
            resto = "".join(f'<p class="explic-par">{_negrito(p)}</p>' for p in excedente)
            texto += (
                f'<details class="cauda"><summary>Ver mais {len(excedente)} '
                f'parágrafo(s)</summary><div class="explicacao">{resto}</div></details>'
            )
        blocos.append(("Como decorar", f'<div class="explicacao">{texto}</div>', True))
    blocos.append(("Onde já caiu (incidência)", _incidencias_html(node.get("incidencias", [])), True))
    registro = _registros_do_assunto(node, bruto)
    blocos.append(("Questões", _lista_marcada(registro, "Nenhuma questão colada ainda."), False))
    if node.get("fora_do_resumo"):
        blocos.append(("Fora do resumo", _lista(node.get("fora_do_resumo")), False))
    blocos.append(("Fontes", _lista(node.get("fontes"), "Nenhuma fonte registrada."), False))
    blocos.append((
        "Pegadinhas",
        _lista_com_cauda(
            node.get("pegadinhas", []),
            "Nenhuma pegadinha registrada ainda.",
            7,
            "pegadinha(s)",
        ),
        False,
    ))
    corpo = "".join(
        _bloco_html(titulo, conteudo, manter)
        for titulo, conteudo, manter in blocos
    )
    nota = node.get("notas") or node.get("nota")
    if nota:
        corpo += f'<p class="nota"><strong>Edital:</strong> {_negrito(nota)}</p>'
    return f'<div class="cartao">{cabecalho}{corpo}</div>'


def _topico(
    node: dict[str, Any], peso: int = 1, bruto: list[dict[str, Any]] | None = None
) -> str:
    numero = _numero(node)
    titulo = node.get("titulo", "")
    status = node["status"]
    vezes = _max_incidencia(node)
    score = vezes * int(peso)
    busca = f"{numero} {titulo}".lower()
    freq = ""
    if vezes:
        classe = "alta" if vezes >= 3 else ("media" if vezes == 2 else "baixa")
        freq = f'<span class="freq freq-{classe}">{vezes}x</span>'
        freq += f'<span class="score" title="incidência × peso da disciplina">P{score}</span>'
    extra = ""
    if node.get("questoes") or node.get("erros"):
        extra = f'<span class="conta">{int(node["questoes"])} q · {int(node["erros"])} e</span>'
    cobertura = min(int(node.get("questoes", 0)), 3)
    revisado = _revisado_info(node)
    revisado_html = (
        f'<span class="revisado revisado-{revisado[1]}">{esc(revisado[0])}</span>'
        if revisado else ""
    )
    return (
        f'<details class="topico" data-status="{esc(status)}" data-inc="{vezes}" '
        f'data-score="{score}" data-erros="{int(node.get("erros", 0))}" '
        f'data-busca="{esc(busca)}">'
        f'<summary><span class="num cobertura-{cobertura}">{esc(numero)}</span>'
        f'<span class="titulo">{esc(titulo)}</span>{freq}{revisado_html}'
        f'<span class="ponto ponto-{esc(status)}" title="{esc(STATUS_LABEL.get(status, status))}"></span>'
        f'{extra}</summary>{_cartao(node, bruto or [])}</details>'
    )


def _grupo(
    node: dict[str, Any], peso: int = 1, bruto: list[dict[str, Any]] | None = None
) -> str:
    filhos = _filhos(node)
    if not filhos:
        return _topico(node, peso, bruto)
    itens = "".join(_topico(filho, peso, bruto) for filho in filhos)
    return (
        f'<div class="grupo" data-status="{esc(node["status"])}">'
        f'<div class="grupo-head"><span class="num">{esc(_numero(node))}</span>'
        f'<h4>{esc(node.get("titulo", ""))}</h4>'
        f'<span class="conta">{len(filhos)} assuntos</span></div>'
        f'<div class="topicos">{itens}</div></div>'
    )


def _disciplina(
    dados: dict[str, Any], disc_id: str, bruto: list[dict[str, Any]] | None = None
) -> str:
    disc = next(d for d in dados["disciplinas"] if d["id"] == disc_id)
    raiz = dados["arvore"][disc_id]
    raiz.setdefault("id", disc_id)
    raiz.setdefault("numero", "" if disc_id == "CE" else disc_id.split("-")[-1])
    _normalizar(raiz)
    folhas = _folhas(raiz)
    feitos, total = _progresso(folhas)
    pct = round(100 * feitos / total) if total else 0
    peso = int(disc["peso"])
    corpo = "".join(
        _grupo(f, peso, bruto) if _filhos(f) else _topico(f, peso, bruto)
        for f in _filhos(raiz)
    )
    return (
        f'<section class="disciplina" id="disc-{esc(disc_id)}" '
        f'style="--accent:{CORES[disc_id][0]};--soft:{CORES[disc_id][1]}">'
        '<div class="disc-head">'
        f'<div class="disc-num">{esc(disc_id.split("-")[-1])}</div>'
        '<div class="disc-info">'
        f'<h3>{esc(disc["nome"])}</h3>'
        f'<p>{disc["questoes"]} questões · peso {disc["peso"]} · '
        f'mín {disc["minimo"]:.1f} / máx {disc["maximo"]:.1f} pts</p></div>'
        f'<div class="donut" style="--p:{pct}%" title="{feitos} de {total} com mapeamento iniciado">'
        f'<span>{feitos}/{total}</span></div></div>'
        f'<div class="grupos">{corpo}</div></section>'
    )


def _nav(dados: dict[str, Any]) -> str:
    partes: list[str] = []
    for area in dados["areas"]:
        itens = []
        for did in area["disciplinas"]:
            disc = next(d for d in dados["disciplinas"] if d["id"] == did)
            folhas = _folhas(_normalizar(dados["arvore"][did]))
            feitos, total = _progresso(folhas)
            itens.append(
                f'<a class="nav-item" href="#disc-{esc(did)}" style="--accent:{CORES[did][0]}">'
                f'<span class="nav-num">{esc(did.split("-")[-1])}</span>'
                f'<span class="nav-nome">{esc(disc["nome"])}</span>'
                f'<span class="nav-bar"><i style="width:{round(100 * feitos / total) if total else 0}%"></i></span>'
                f'<span class="nav-conta">{feitos}/{total}</span></a>'
            )
        partes.append(f'<p class="nav-titulo">{esc(area["titulo"])}</p>' + "".join(itens))
    return "".join(partes)


CSS = """\
:root{--bg:#f4f5f7;--card:#fff;--ink:#1b2430;--text2:#4d586b;--muted:#7c8797;
--line:#e3e6eb;--shadow:0 2px 6px rgba(20,30,50,.05),0 10px 24px rgba(20,30,50,.04);--r:14px}
html.modo-escuro{--bg:#11151c;--card:#1a2029;--ink:#e9edf4;--text2:#b4bfce;
--muted:#8592a3;--line:#2b3441;--shadow:none}
@media(prefers-color-scheme:dark){html:not(.modo-claro){--bg:#11151c;--card:#1a2029;--ink:#e9edf4;
--text2:#b4bfce;--muted:#8592a3;--line:#2b3441;--shadow:none}}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;-webkit-text-size-adjust:100%}
button,input{font:inherit}
.topo{background:linear-gradient(120deg,#1d4ed8,#4338ca 55%,#0f766e);color:#fff;padding:1.4rem 0 1.6rem}
.topo-inner{max-width:1400px;margin:0 auto;padding:0 1.5rem;display:flex;flex-wrap:wrap;gap:1.2rem;align-items:flex-end;justify-content:space-between}
.eyebrow{font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;opacity:.8;margin:0 0 .3rem}
.topo h1{font-size:clamp(1.5rem,3vw,2.1rem);line-height:1.15;margin:0}
.topo h1 span{font-weight:400;opacity:.85}
.meta{opacity:.85;font-size:.86rem;margin:.35rem 0 0}
.chips{display:flex;gap:.55rem;flex-wrap:wrap}
.chip{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.22);border-radius:12px;padding:.55rem .85rem;min-width:78px}
.chip b{display:block;font-size:1.35rem;line-height:1}
.chip span{font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;opacity:.85}
.layout{max-width:1400px;margin:0 auto;padding:1.4rem 1.5rem 4rem;display:grid;grid-template-columns:250px minmax(0,1fr);gap:1.5rem;align-items:start}
@media(max-width:900px){.layout{grid-template-columns:1fr}.nav{position:static!important;max-height:none!important}}
.nav{position:sticky;top:1rem;max-height:calc(100vh - 2rem);overflow:auto;background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:1rem;box-shadow:var(--shadow)}
.busca{width:100%;padding:.65rem .8rem;border:1px solid var(--line);border-radius:9px;background:var(--bg);color:var(--ink);outline:none}
.busca:focus{border-color:#2563eb;box-shadow:0 0 0 3px rgba(37,99,235,.12)}
.filtros{display:flex;gap:.3rem;margin:.7rem 0 .2rem}
.filtros button{flex:1;font-size:.7rem;padding:.35rem .2rem;border:1px solid var(--line);border-radius:7px;background:transparent;color:var(--text2);cursor:pointer}
.filtros button.ativo{background:var(--ink);color:var(--card);border-color:var(--ink)}
.revisao-btn{width:100%;margin-top:.7rem;padding:.55rem;border:1px solid #be185d;border-radius:9px;background:transparent;color:#be185d;font-size:.8rem;font-weight:700;cursor:pointer}
.revisao-btn.ligado{background:#be185d;color:#fff}
.erro-btn{border-color:#b91c1c;color:#b91c1c}
.erro-btn.ligado{background:#b91c1c;color:#fff}
.questao-erro{color:#b91c1c;font-weight:600;background:rgba(220,38,38,.08);border-left:3px solid #b91c1c;padding:.15rem .45rem;border-radius:4px}
.legenda{font-size:.68rem;color:var(--muted);margin:.85rem 0 0;line-height:1.5}
.nav-titulo{font-size:.68rem;text-transform:uppercase;letter-spacing:.09em;color:var(--muted);margin:1rem 0 .45rem}
.nav-item{display:grid;grid-template-columns:20px 1fr auto;grid-template-rows:auto auto;gap:.1rem .5rem;text-decoration:none;color:var(--ink);padding:.5rem .35rem;border-radius:9px}
.nav-item:hover{background:var(--bg)}
.nav-num{font-weight:800;color:var(--accent);grid-row:1}
.nav-nome{font-size:.86rem;grid-column:2/4;line-height:1.25}
.nav-bar{grid-column:2;height:5px;background:var(--bg);border-radius:9px;overflow:hidden;align-self:center}
.nav-bar i{display:block;height:100%;background:var(--accent);border-radius:9px}
.nav-conta{font-size:.7rem;color:var(--muted);grid-column:3}
.resultado{font-size:.75rem;color:var(--muted);margin:.8rem 0 0}
.disciplina{background:var(--card);border:1px solid var(--line);border-radius:var(--r);box-shadow:var(--shadow);margin:0 0 1.4rem;overflow:hidden;scroll-margin-top:1rem}
.disc-head{display:flex;gap:.85rem;align-items:center;padding:1rem 1.2rem;background:var(--soft);border-left:5px solid var(--accent)}
.disc-num{font-size:1.6rem;font-weight:800;color:var(--accent);line-height:1}
.disc-info{flex:1;min-width:0}
.disc-info h3{margin:0;font-size:1.05rem}
.disc-info p{margin:.15rem 0 0;font-size:.78rem;color:var(--text2)}
.donut{width:52px;height:52px;border-radius:50%;flex:none;background:conic-gradient(var(--accent) var(--p),rgba(127,127,127,.14) 0);display:grid;place-items:center;position:relative}
.donut::before{content:"";position:absolute;width:40px;height:40px;border-radius:50%;background:var(--card)}
.donut span{position:relative;z-index:1;font-size:.7rem;font-weight:700;color:var(--text2)}
.grupos{padding:.6rem 1.1rem 1.2rem}
.grupo{margin:.8rem 0}
.grupo-head{display:flex;align-items:baseline;gap:.5rem;padding:.35rem 0;border-bottom:1px solid var(--line);margin-bottom:.35rem}
.grupo-head h4{margin:0;font-size:.9rem;flex:1}
.grupo .topicos{padding-left:.9rem;border-left:2px solid var(--soft)}
.topicos{display:grid;gap:.35rem}
.topico{border:1px solid var(--line);border-radius:9px;background:var(--card)}
.topico[open]{border-color:var(--accent);box-shadow:0 4px 14px rgba(20,30,50,.06)}
.topico summary{list-style:none;cursor:pointer;padding:.6rem .75rem;display:flex;align-items:center;gap:.55rem;font-size:.88rem}
.topico summary::-webkit-details-marker{display:none}
.topico summary:hover{background:var(--soft)}
.num{font-size:.72rem;font-weight:700;color:var(--accent);background:var(--soft);border-radius:5px;padding:.1rem .35rem;flex:none}
.num.cobertura-0{background:rgba(127,127,127,.13);color:var(--muted)}
.num.cobertura-1{background:#fef3c7;color:#b45309}
.num.cobertura-2{background:#fed7aa;color:#9a3412}
.num.cobertura-3{background:#d1fae5;color:#047857}
.titulo{flex:1;min-width:0}
.freq{font-size:.7rem;font-weight:800;border-radius:99px;padding:.1rem .45rem;flex:none;background:#eef1f5;color:#64748b}
.freq-media{background:#fef3c7;color:#b45309}
.freq-alta{background:#fee2e2;color:#b91c1c}
.score{font-size:.7rem;font-weight:800;border-radius:6px;padding:.1rem .35rem;flex:none;background:#ede9fe;color:#6d28d9}
.revisado{font-size:.68rem;font-weight:700;border-radius:99px;padding:.1rem .45rem;flex:none;white-space:nowrap}
.revisado-recente{background:#d1fae5;color:#047857}
.revisado-atencao{background:#fef3c7;color:#b45309}
.revisado-atrasado{background:#fee2e2;color:#b91c1c}
.ponto{width:9px;height:9px;border-radius:50%;background:#b6bfcb;flex:none}
.ponto-em-mapeamento{background:#f59e0b}
.ponto-mapeado{background:#10b981;box-shadow:0 0 0 3px rgba(16,185,129,.16)}
.conta{font-size:.72rem;color:var(--muted);flex:none}
.cartao{padding:.2rem 1rem 1.1rem;display:grid;gap:1rem;grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.decore{grid-column:1/-1;background:linear-gradient(120deg,#1e293b,#0f766e);color:#fff;border-radius:10px;padding:.8rem 1rem;display:grid;gap:.45rem}
.decore div{display:grid;grid-template-columns:88px 1fr;gap:.6rem;align-items:start}
.decore span{font-size:.62rem;letter-spacing:.1em;text-transform:uppercase;opacity:.7;font-weight:700;padding-top:.15rem}
.decore b{font-size:.9rem;line-height:1.4}
.cauda{margin-top:.5rem}
.cauda summary{font-size:.75rem;color:var(--muted);cursor:pointer;list-style:none}
.cauda summary::-webkit-details-marker{display:none}
.cauda summary::before{content:"▸ ";font-weight:700}
.cauda[open] summary::before{content:"▾ "}
.bloco-dobra{border-top:1px solid var(--line);padding-top:.5rem}.como-decorar{grid-column:1/-1}.como-decorar .explicacao{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:.55rem}.como-decorar .explic-par{margin:0;border-top:0;padding-top:0}.como-decorar .explic-par::before{margin-bottom:.25rem}
.bloco-dobra summary{list-style:none;cursor:pointer;display:flex;align-items:baseline;gap:.35rem;font-size:.66rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
.bloco-dobra summary::-webkit-details-marker{display:none}
.bloco-dobra summary::before{content:"▸";font-weight:700}
.bloco-dobra[open] summary::before{content:"▾"}
.bloco-dobra .conta{text-transform:none;letter-spacing:0}
.dobra-conteudo{margin-top:.45rem}
.modo-revisao .bloco:not(.keep),.modo-revisao .nota,.modo-revisao .cauda{display:none}
.modo-revisao .cartao{gap:.7rem}
.modo-revisao .decore{background:linear-gradient(120deg,#7c3aed,#be185d)}
.bloco h5{font-size:.66rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:0 0 .3rem}
.bloco ul{margin:0;padding-left:1.1rem;font-size:.85rem}
.bloco strong{font-weight:700;color:var(--ink)}
.bloco li{margin:.18rem 0}
.explicacao{font-size:.9rem;color:var(--text2);counter-reset:explic}
.explicacao p{margin:0 0 .55rem}
.explicacao p:last-child{margin:0}
.explic-par{counter-increment:explic;border-top:1px solid var(--line);padding-top:.55rem;margin-top:.55rem}
.explic-par:first-child{border-top:0;padding-top:0;margin-top:0}
.explic-par::before{content:'PARTE ' counter(explic);display:block;font-size:.62rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:800;margin-bottom:.25rem}
.cauda .explic-par::before{counter-increment:explic}
.incidencias{list-style:none;padding:0;margin:0}
.incidencias li{display:flex;gap:.5rem;align-items:flex-start;padding:.3rem 0;border-bottom:1px solid var(--line)}
.incidencias li:last-child{border-bottom:0}
.vezes{font-size:.72rem;font-weight:800;border-radius:6px;padding:.1rem .35rem;flex:none;background:#eef1f5;color:#64748b}
.vezes-media{background:#fef3c7;color:#b45309}
.vezes-alta{background:#fee2e2;color:#b91c1c}
.inc-texto{font-size:.85rem}
.inc-texto small{display:block;font-size:.7rem;color:var(--muted);margin-top:.1rem}
.ids-linha{display:inline-block;margin-left:.4rem}
.ids-linha summary{list-style:none;display:inline;font-size:.66rem;color:var(--muted);cursor:pointer}
.ids-linha summary::-webkit-details-marker{display:none}
.ids-linha summary::before{content:"▸";font-weight:700;margin-right:.2rem}
.ids-linha[open] summary::before{content:"▾"}
.vazio{color:var(--muted);font-style:italic;font-size:.82rem;margin:0}
.nota{grid-column:1/-1;font-size:.8rem;color:var(--text2);background:var(--soft);padding:.55rem .7rem;border-radius:8px;margin:0}
.rodape{max-width:1400px;margin:0 auto;padding:0 1.5rem 2rem;color:var(--muted);font-size:.78rem}
.skip{position:absolute;left:-9999px;top:0;z-index:999;background:var(--card);color:var(--ink);
padding:.6rem .9rem;border:2px solid var(--ink);border-radius:8px;text-decoration:none;font-weight:700}
.skip:focus{left:.75rem;top:.75rem}
main:focus{outline:none}
@media print{.nav{display:none}.layout{display:block;padding:0}.topo{background:#333}.disciplina,.topico{box-shadow:none;break-inside:avoid}}
"""


JS = """
const busca = document.getElementById('busca');
const botoesStatus = document.querySelectorAll('[data-filtro]');
const botoesFreq = document.querySelectorAll('[data-freq]');
const botoesScore = document.querySelectorAll('[data-score-filtro]');
const btnErros = document.getElementById('meus-erros');
let filtro = 'todos';
let freq = 'todas';
let scoreFiltro = 'todos';
let soErros = false;

function marcar(botoes, ativo) {
  botoes.forEach(b => {
    const on = typeof ativo === 'function' ? ativo(b) : b === ativo;
    b.classList.toggle('ativo', on);
    b.setAttribute('aria-pressed', on ? 'true' : 'false');
  });
}

function aplicar() {
  const q = busca.value.toLowerCase().trim();
  document.querySelectorAll('.topico').forEach(el => {
    const okBusca = !q || (el.dataset.busca || '').includes(q);
    const okStatus = filtro === 'todos' ||
      (filtro === 'pendente' ? el.dataset.status !== 'mapeado' : el.dataset.status === filtro);
    const n = Number(el.dataset.inc || 0);
    const okFreq = freq === 'todas' || (freq === '3+' ? n >= 3 : n === Number(freq.replace('x','')));
    const okScore = scoreFiltro === 'todos' || Number(el.dataset.score || 0) >= 9;
    const okErro = !soErros || Number(el.dataset.erros || 0) > 0;
    el.hidden = !(okBusca && okStatus && okFreq && okScore && okErro);
  });
  document.querySelectorAll('.grupo').forEach(g => {
    g.hidden = ![...g.querySelectorAll('.topico')].some(t => !t.hidden);
  });
  document.querySelectorAll('.disciplina').forEach(d => {
    d.hidden = ![...d.querySelectorAll('.topico')].some(t => !t.hidden);
  });
  const visiveis = [...document.querySelectorAll('.topico')].filter(t => !t.hidden).length;
  document.getElementById('resultado').textContent =
    (q || filtro !== 'todos' || freq !== 'todas' || scoreFiltro !== 'todos' || soErros)
      ? visiveis + ' assunto(s) encontrado(s)' : '';
}
busca.addEventListener('input', aplicar);
botoesStatus.forEach(b => b.addEventListener('click', () => {
  filtro = b.dataset.filtro;
  marcar(botoesStatus, b);
  aplicar();
}));
botoesFreq.forEach(b => b.addEventListener('click', () => {
  freq = b.dataset.freq;
  marcar(botoesFreq, b);
  aplicar();
}));
botoesScore.forEach(b => b.addEventListener('click', () => {
  scoreFiltro = b.dataset.scoreFiltro;
  marcar(botoesScore, b);
  aplicar();
}));

btnErros.addEventListener('click', () => {
  soErros = !soErros;
  btnErros.classList.toggle('ligado', soErros);
  btnErros.setAttribute('aria-pressed', soErros ? 'true' : 'false');
  if (soErros) {
    filtro = 'todos';
    freq = 'todas';
    scoreFiltro = 'todos';
    marcar(botoesStatus, b => b.dataset.filtro === 'todos');
    marcar(botoesFreq, b => b.dataset.freq === 'todas');
    marcar(botoesScore, b => b.dataset.scoreFiltro === 'todos');
  }
  aplicar();
  if (soErros) document.querySelectorAll('.topico').forEach(t => {
    if (!t.hidden) t.open = true;
  });
});

const btnRevisao = document.getElementById('revisao-rapida');
btnRevisao.addEventListener('click', () => {
  const ativo = document.body.classList.toggle('modo-revisao');
  btnRevisao.classList.toggle('ligado', ativo);
  btnRevisao.setAttribute('aria-pressed', ativo ? 'true' : 'false');
  freq = ativo ? '3+' : 'todas';
  scoreFiltro = 'todos';
  soErros = false;
  btnErros.classList.remove('ligado');
  btnErros.setAttribute('aria-pressed', 'false');
  marcar(botoesFreq, b => b.dataset.freq === freq);
  marcar(botoesScore, b => b.dataset.scoreFiltro === 'todos');
  aplicar();
  if (ativo) document.querySelectorAll('.topico').forEach(t => {
    if (!t.hidden) t.open = true;
  });
});

const botoesModo = document.querySelectorAll('[data-modo]');
function aplicarModo(modo) {
  if (modo === 'escuro') {
    document.documentElement.classList.remove('modo-claro');
    document.documentElement.classList.add('modo-escuro');
  } else {
    document.documentElement.classList.remove('modo-escuro');
    document.documentElement.classList.add('modo-claro');
  }
  marcar(botoesModo, b => b.dataset.modo === modo);
  try { localStorage.setItem('mapa-modo', modo); } catch (e) { /* navegação restrita */ }
}
let savedModo = null;
try { savedModo = localStorage.getItem('mapa-modo'); } catch (e) { /* navegação restrita */ }
aplicarModo(savedModo || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'escuro' : 'claro'));
botoesModo.forEach(b => b.addEventListener('click', () => aplicarModo(b.dataset.modo)));
marcar(botoesStatus, b => b.classList.contains('ativo'));
marcar(botoesFreq, b => b.classList.contains('ativo'));
marcar(botoesScore, b => b.classList.contains('ativo'));
btnErros.setAttribute('aria-pressed', 'false');
btnRevisao.setAttribute('aria-pressed', 'false');
"""


def renderizar(dados: dict[str, Any], bruto: list[dict[str, Any]] | None = None) -> str:
    bruto = bruto or []
    concurso = dados["concurso"]
    stats = estatisticas(dados)
    conteudo = "".join(
        '<div class="area-bloco">'
        + "".join(_disciplina(dados, did, bruto) for did in a["disciplinas"])
        + "</div>"
        for a in dados["areas"]
    )
    chips = "".join(
        f'<div class="chip"><b>{valor}</b><span>{rotulo}</span></div>'
        for valor, rotulo in [
            (stats["assuntos"], "assuntos"),
            (stats["tocados"], "tocados"),
            (stats["vazios"], "vazios"),
            (stats["questoes"], "questões"),
            (stats["erros"], "erros"),
        ]
    )
    return (
        "<!DOCTYPE html>\n<html lang=\"pt-BR\">\n<head>\n<meta charset=\"utf-8\">\n"
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>Mapa de revisão — {esc(concurso['cargo'])}</title>\n"
        f"<style>{CSS}</style>\n</head>\n<body>\n"
        '<a class="skip" href="#conteudo">Pular para o conteúdo</a>\n'
        '<header class="topo"><div class="topo-inner">'
        f'<div><p class="eyebrow">{esc(concurso["edital"])} · {esc(concurso["banca"])}</p>'
        f'<h1>Mapa de revisão <span>— {esc(concurso["cargo"])}</span></h1>'
        f'<p class="meta">Prova {esc(_data_pt(concurso["prova"]))} · {esc(concurso["local"])} · '
        f'{esc(concurso["regra"])}</p></div>'
        f'<div class="chips">{chips}</div></div></header>'
        '<div class="layout"><aside class="nav">'
        '<input class="busca" id="busca" type="search" placeholder="Buscar assunto...">'
        '<p class="nav-titulo">Aparência</p>'
        '<div class="filtros">'
        '<button data-modo="claro">Modo claro</button>'
        '<button data-modo="escuro">Modo escuro</button></div>'
        '<div class="filtros">'
        '<button data-filtro="todos" class="ativo">Todos</button>'
        '<button data-filtro="mapeado">Mapeados</button>'
        '<button data-filtro="pendente">Pendentes</button></div>'
        '<p class="nav-titulo">Filtrar por incidência</p>'
        '<div class="filtros">'
        '<button data-freq="todas" class="ativo">Todas</button>'
        '<button data-freq="3+">3+ vezes</button>'
        '<button data-freq="2x">2 vezes</button>'
        '<button data-freq="1x">1 vez</button></div>'
        '<button class="revisao-btn" id="revisao-rapida">⚡ Revisão rápida (3+ vezes)</button>'
        '<button class="revisao-btn erro-btn" id="meus-erros">'
        f'⚠ Meus erros · {stats["erros"]} em {stats["assuntos_com_erros"]} assunto(s)</button>'
        '<p class="nav-titulo">Prioridade (incidência × peso)</p>'
        '<div class="filtros">'
        '<button data-score-filtro="todos" class="ativo">Todas</button>'
        '<button data-score-filtro="alto">Alta (9+)</button></div>'
        '<p class="legenda">Cobertura: <b>cinza</b> = 0 questão · '
        '<b>âmbar</b> = 1–2 · <b>verde</b> = 3+</p>'
        f'{_nav(dados)}<p class="resultado" id="resultado"></p>'
        '</aside><main id="conteudo" tabindex="-1">' + conteudo + '</main></div>'
        f'<footer class="rodape">Fonte da hierarquia: {esc(concurso["fonte"])}. '
        'Gerado por build.py a partir de mapa.json.</footer>'
        f"<script>{JS}</script>\n</body>\n</html>\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera o índice do mapa de revisão.")
    parser.add_argument("--mapa", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--bruto", type=Path, default=DEFAULT_BRUTO,
        help="questoes.jsonl de onde sai a lista de questões de cada assunto",
    )
    args = parser.parse_args()
    dados = carregar(args.mapa)
    bruto = carregar_bruto(args.bruto)
    args.out.write_text(renderizar(dados, bruto), encoding="utf-8")
    stats = estatisticas(dados)
    print(
        f"OK  {args.out} — {stats['assuntos']} assuntos, "
        f"{stats['com_incidencia']} com incidência, {stats['questoes']} questões, "
        f"{stats['erros']} erros, {len(bruto)} no bruto."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
