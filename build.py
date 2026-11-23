#!/usr/bin/env python3
"""Gerador de apresentação para as aulas do Hermes.

Converte ``aula-XX.json`` em HTML autocontido (sem JavaScript, sem fontes
remotas) e/ou em Markdown. O JSON continua sendo a fonte da verdade: tudo o
que este módulo produz é derivado e pode ser regerado a qualquer momento.

Uso:
    python build.py                                   # exemplos/ -> dist/
    python build.py exemplos/redacao-oficial/aula-00.json --out site
    python build.py --format html --format md         # HTML e Markdown
    python build.py --format md                       # somente Markdown
    python build.py --no-index                        # não gera index.html

Códigos de saída:
    0  geração concluída
    1  ao menos uma aula inválida (a geração é abortada)
    2  uso incorreto ou nenhum arquivo encontrado
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path
from typing import Any, Sequence

try:
    import validate as hermes_validate
except ImportError:  # pragma: no cover - execução fora da raiz do repositório
    import importlib.util

    _spec = importlib.util.spec_from_file_location(
        "hermes_validate", Path(__file__).resolve().parent / "validate.py"
    )
    if _spec is None or _spec.loader is None:
        raise
    hermes_validate = importlib.util.module_from_spec(_spec)
    sys.modules[_spec.name] = hermes_validate
    _spec.loader.exec_module(hermes_validate)

ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT_PATH = ROOT / "exemplos"
DEFAULT_OUTPUT_PATH = ROOT / "dist"
BUILD_VERSION = "1.0.0"

EXIT_OK = 0
EXIT_INVALID = 1
EXIT_USAGE = 2

STATUS_LABEL = {
    "rascunho": "Rascunho",
    "revisao": "Em revisão",
    "publicado": "Publicado",
    "arquivado": "Arquivado",
}
NIVEL_LABEL = {
    "info": "Informação",
    "atencao": "Atenção",
    "sucesso": "Certo",
    "erro": "Erro",
}
TIPO_LABEL = {
    "livro": "Livro",
    "norma": "Norma",
    "curso": "Curso",
    "artigo": "Artigo",
    "site": "Site",
    "video": "Vídeo",
    "outro": "Outro",
}

_CODE_TOKEN = "\x00{}\x00"
_CODE_SPAN = re.compile(r"`([^`\n]+)`")
_BOLD_SPAN = re.compile(r"\*\*(.+?)\*\*")
_ITALIC_SPAN = re.compile(r"(?<![*\w])\*([^*\n]+)\*(?![*\w])")


# ---------------------------------------------------------------------------
# Utilitários de texto
# ---------------------------------------------------------------------------


def escape_attr(value: str) -> str:
    """Escapa um valor para uso dentro de atributo HTML."""
    return html.escape(value, quote=True).replace("\n", " ")


def inline_html(text: str) -> str:
    """Converte Markdown inline em HTML seguro.

    Suporta ``**negrito**``, ``*itálico*`` e ```` `código` ````. O texto é
    escapado antes, então tags HTML presentes no JSON nunca são executadas.
    """
    escaped = html.escape(text, quote=False)
    codes: list[str] = []

    def _stash(match: re.Match[str]) -> str:
        codes.append(f"<code>{match.group(1)}</code>")
        return _CODE_TOKEN.format(len(codes) - 1)

    escaped = _CODE_SPAN.sub(_stash, escaped)
    escaped = _BOLD_SPAN.sub(r"<strong>\1</strong>", escaped)
    escaped = _ITALIC_SPAN.sub(r"<em>\1</em>", escaped)
    for index, code in enumerate(codes):
        escaped = escaped.replace(_CODE_TOKEN.format(index), code)
    return escaped


def _date_pt(value: Any) -> str:
    """Converte ``AAAA-MM-DD`` em ``DD/MM/AAAA``; devolve o original se falhar."""
    if not isinstance(value, str):
        return ""
    parts = value.split("-")
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    return value


def _numero_aula(value: Any) -> str:
    return f"{int(value):02d}" if isinstance(value, int) else str(value)


def _tags_html(tags: Sequence[Any]) -> str:
    items = "".join(f"<li>{inline_html(str(tag))}</li>" for tag in tags)
    return f'<ul class="tags">{items}</ul>' if items else ""


def _fonte_por_id(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(f.get("id")): f for f in document.get("fontes", []) if isinstance(f, dict)}


def _fontes_ref_html(
    refs: Sequence[Any],
    fontes: dict[str, dict[str, Any]],
    rotulo: str = "Fontes",
) -> str:
    """Linha ``Fontes: ...`` com âncoras para a seção de referências."""
    if not isinstance(refs, list) or not refs:
        return ""
    links = []
    for ref in refs:
        if not isinstance(ref, str) or ref not in fontes:
            continue
        titulo = str(fontes[ref].get("titulo", ref))
        links.append(f'<a href="#fonte-{escape_attr(ref)}">{inline_html(titulo)}</a>')
    if not links:
        return ""
    return (
        f'<p class="fontes-ref"><span>{inline_html(rotulo)}:</span> '
        f'{", ".join(links)}</p>'
    )


# ---------------------------------------------------------------------------
# HTML — blocos
# ---------------------------------------------------------------------------


def _block_html(block: dict[str, Any], fontes: dict[str, dict[str, Any]]) -> str:
    tipo = str(block.get("tipo", ""))
    anchor = f' id="blk-{escape_attr(str(block.get("id", "")))}"'
    titulo = block.get("titulo")
    titulo_html = (
        f'<h3 class="bloco-titulo">{inline_html(str(titulo))}</h3>' if titulo else ""
    )
    refs = _fontes_ref_html(block.get("fontes", []), fontes)

    if tipo == "paragrafo":
        return (
            f'<div{anchor} class="bloco paragrafo">'
            f"{titulo_html}<p>{inline_html(str(block.get('texto', '')))}</p>"
            f"{refs}</div>"
        )

    if tipo == "topico":
        return (
            f'<h3{anchor} class="topico">{inline_html(str(block.get("texto", "")))}</h3>'
        )

    if tipo == "lista":
        ordered = bool(block.get("ordenada"))
        tag = "ol" if ordered else "ul"
        itens = "".join(
            f"<li>{inline_html(str(item))}</li>" for item in block.get("itens", [])
        )
        return (
            f'<div{anchor} class="bloco lista">'
            f"{titulo_html}<{tag}>{itens}</{tag}>{refs}</div>"
        )

    if tipo == "tabela":
        colunas = [str(c) for c in block.get("colunas", [])]
        head = "".join(
            f'<th scope="col">{inline_html(coluna)}</th>' for coluna in colunas
        )
        body = []
        for linha in block.get("linhas", []):
            cells = "".join(f"<td>{inline_html(str(cell))}</td>" for cell in linha)
            body.append(f"<tr>{cells}</tr>")
        caption = ""
        if titulo:
            caption = f"<caption>{inline_html(str(titulo))}</caption>"
        return (
            f'<div{anchor} class="table-wrap"><table>{caption}'
            f"<thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody>"
            f"</table>{refs}</div>"
        )

    if tipo == "destaque":
        nivel = str(block.get("nivel", "info"))
        rotulo = NIVEL_LABEL.get(nivel, "Informação")
        return (
            f'<aside{anchor} class="destaque destaque-{escape_attr(nivel)}" '
            f'role="note">'
            f'<p class="rotulo">{inline_html(rotulo)}</p>'
            f"{titulo_html}"
            f'<p>{inline_html(str(block.get("texto", "")))}</p>{refs}</aside>'
        )

    if tipo == "gotcha":
        return (
            f'<aside{anchor} class="gotcha" role="note">'
            f'<p class="rotulo">Pegadinha</p>{titulo_html}'
            f'<p>{inline_html(str(block.get("texto", "")))}</p>{refs}</aside>'
        )

    if tipo == "mnemonico":
        return (
            f'<aside{anchor} class="mnemonico" role="note">'
            f'<p class="rotulo">Mnemônico</p>{titulo_html}'
            f'<p>{inline_html(str(block.get("texto", "")))}</p>{refs}</aside>'
        )

    if tipo == "exemplo":
        return (
            f'<aside{anchor} class="exemplo" role="note">'
            f'<p class="rotulo">Exemplo</p>{titulo_html}'
            f'<p>{inline_html(str(block.get("texto", "")))}</p>{refs}</aside>'
        )

    # Tipo desconhecido: o validador já deveria ter barrado. Renderiza como
    # parágrafo para não perder silenciosamente o conteúdo.
    return f'<p{anchor} class="paragrafo">{inline_html(str(block))}</p>'


def _section_html(
    section: dict[str, Any], fontes: dict[str, dict[str, Any]]
) -> str:
    sid = escape_attr(str(section.get("id", "")))
    numero = section.get("numero", "")
    titulo = inline_html(str(section.get("titulo", "")))
    subtitulo = section.get("subtitulo")
    subtitulo_html = (
        f'<p class="sec-subtitulo">{inline_html(str(subtitulo))}</p>' if subtitulo else ""
    )
    blocos = "".join(
        _block_html(block, fontes)
        for block in section.get("blocos", [])
        if isinstance(block, dict)
    )
    refs = _fontes_ref_html(section.get("fontes", []), fontes, rotulo="Fontes da seção")
    return (
        f'<section id="sec-{sid}" class="secao">'
        f'<div class="sec-header"><span class="sec-num">{numero}</span>'
        f'<h2>{titulo}</h2></div>{subtitulo_html}{refs}{blocos}</section>'
    )


def _quiz_html(quiz: dict[str, Any]) -> str:
    questoes = [q for q in quiz.get("questoes", []) if isinstance(q, dict)]
    if not questoes:
        return ""
    titulo = inline_html(str(quiz.get("titulo") or "Quiz"))
    instrucoes = inline_html(str(quiz.get("instrucoes", "")))

    itens: list[str] = []
    for index, questao in enumerate(questoes, start=1):
        qid = escape_attr(str(questao.get("id", f"q{index}")))
        alternativas = [o for o in questao.get("opcoes", []) if isinstance(o, dict)]
        opcoes_html = []
        for opcao in alternativas:
            correta = bool(opcao.get("correta"))
            classe = "correta" if correta else "incorreta"
            veredito = "Correta." if correta else "Incorreta."
            opcoes_html.append(
                "<li><details>"
                f"<summary>{inline_html(str(opcao.get('texto', '')))}</summary>"
                f'<p class="feedback {classe}"><strong>{veredito}</strong> '
                f"{inline_html(str(opcao.get('explicacao', '')))}</p>"
                "</details></li>"
            )
        itens.append(
            f'<li class="questao" id="q-{qid}">'
            f'<h3 class="enunciado"><span class="qnum">{index}.</span> '
            f"{inline_html(str(questao.get('enunciado', '')))}</h3>"
            f'<ol class="opcoes" type="A">{"".join(opcoes_html)}</ol></li>'
        )

    return (
        f'<section id="quiz" class="quiz">'
        f'<div class="sec-header"><span class="sec-num" aria-hidden="true">Q</span>'
        f"<h2>{titulo}</h2></div>"
        f'<p class="instrucoes">{instrucoes}</p>'
        f'<p class="dica">Toque ou clique em uma alternativa para conferir o feedback.</p>'
        f'<ol class="questoes">{"".join(itens)}</ol></section>'
    )


def _incidencia_html(incidencia: dict[str, Any] | None) -> str:
    if not isinstance(incidencia, dict):
        return ""
    meta = f"Fonte: {inline_html(str(incidencia.get('fonte', '')))}"
    atualizado = _date_pt(incidencia.get("atualizado_em"))
    if atualizado:
        meta += f" · atualizado em {atualizado}"

    temas = [t for t in incidencia.get("temas", []) if isinstance(t, dict)]
    if temas:
        linhas = []
        for tema in temas:
            secoes = "".join(
                f'<a href="#sec-{escape_attr(str(sid))}">{inline_html(str(sid))}</a>'
                for sid in tema.get("secao_ids", [])
            )
            nome = inline_html(str(tema.get("nome", "")))
            peso = tema.get("peso", 0)
            linhas.append(
                f'<tr><td>{nome}</td>'
                f'<td class="num">{peso}</td>'
                f'<td class="secoes">{secoes}</td></tr>'
            )
        corpo = (
            '<div class="table-wrap"><table>'
            "<caption>Temas cobrados e peso relativo</caption>"
            "<thead><tr><th scope=\"col\">Tema</th><th scope=\"col\">Peso</th>"
            '<th scope="col">Seções</th></tr></thead>'
            f"<tbody>{''.join(linhas)}</tbody></table></div>"
        )
    else:
        corpo = '<p class="vazio">Nenhum tema registrado por enquanto.</p>'

    observacao = incidencia.get("observacao")
    obs_html = (
        f'<p class="observacao">{inline_html(str(observacao))}</p>' if observacao else ""
    )
    return (
        f'<section id="incidencia" class="incidencia">'
        f'<div class="sec-header"><span class="sec-num" aria-hidden="true">%</span>'
        "<h2>Incidência de temas</h2></div>"
        f'<p class="meta">{meta}</p>{corpo}{obs_html}</section>'
    )


def _fontes_html(fontes: Sequence[Any]) -> str:
    itens = []
    for fonte in fontes:
        if not isinstance(fonte, dict):
            continue
        fid = escape_attr(str(fonte.get("id", "")))
        tipo = str(fonte.get("tipo", "outro"))
        titulo = inline_html(str(fonte.get("titulo", "")))
        detalhes = fonte.get("detalhes")
        ano = fonte.get("ano")
        url = fonte.get("url")
        extra = []
        if detalhes:
            extra.append(inline_html(str(detalhes)))
        if ano:
            extra.append(str(ano))
        if url:
            extra.append(f'<a href="{escape_attr(str(url))}">{inline_html(str(url))}</a>')
        dd = f"<dd>{' · '.join(extra)}</dd>" if extra else ""
        itens.append(
            f'<div class="fonte" id="fonte-{fid}">'
            f'<dt><span class="fonte-tipo">{inline_html(TIPO_LABEL.get(tipo, tipo))}</span>'
            f" {titulo}</dt>{dd}</div>"
        )
    if not itens:
        return ""
    return (
        f'<section id="fontes" class="fontes">'
        '<div class="sec-header"><span class="sec-num" aria-hidden="true">§</span>'
        f"<h2>Fontes</h2></div><dl>{''.join(itens)}</dl></section>"
    )


def _revisao_html(document: dict[str, Any]) -> str:
    revisao = document.get("revisao") or {}
    metadados = document.get("metadados") or {}
    status = STATUS_LABEL.get(str(revisao.get("status", "")), str(revisao.get("status", "")))

    def _linha(rotulo: str, valor: Any) -> str:
        if valor in (None, "", []):
            return ""
        if isinstance(valor, list):
            valor = ", ".join(str(item) for item in valor)
        return (
            f"<div><dt>{inline_html(rotulo)}</dt>"
            f"<dd>{inline_html(str(valor))}</dd></div>"
        )

    linhas = [
        _linha("Status da revisão", status),
        _linha("Última revisão", _date_pt(revisao.get("ultima_em"))),
        _linha("Próxima revisão", _date_pt(revisao.get("proxima_em"))),
        _linha("Versão da aula", metadados.get("versao")),
        _linha("Criada em", _date_pt(metadados.get("criado_em"))),
        _linha("Atualizada em", _date_pt(metadados.get("atualizado_em"))),
        _linha("Autoria", metadados.get("autores")),
        _linha("Revisão", metadados.get("revisores")),
        _linha("Licença", metadados.get("licenca")),
        _linha("Origem", metadados.get("origem")),
        _linha("Alterações", metadados.get("alteracoes")),
    ]

    ritual = revisao.get("ritual") or []
    ritual_html = ""
    if ritual:
        itens = "".join(f"<li>{inline_html(str(item))}</li>" for item in ritual)
        ritual_html = (
            f'<h3 class="subtitulo-meta">Ritual de revisão</h3><ol class="ritual">{itens}</ol>'
        )

    return (
        f'<section id="revisao" class="meta">'
        '<div class="sec-header"><span class="sec-num" aria-hidden="true">i</span>'
        "<h2>Revisão e metadados</h2></div>"
        f'<dl class="dl">{"".join(linhas)}</dl>{ritual_html}</section>'
    )


def _notas_html(document: dict[str, Any]) -> str:
    notas = document.get("notas")
    if not notas:
        return ""
    return (
        f'<section id="notas" class="notas">'
        '<div class="sec-header"><span class="sec-num" aria-hidden="true">!</span>'
        f"<h2>Notas</h2></div><p>{inline_html(str(notas))}</p></section>"
    )


# ---------------------------------------------------------------------------
# HTML — documento
# ---------------------------------------------------------------------------


CSS = """\
:root{
  --bg:#f5f4f0; --sidebar:#ecebe5; --card:#ffffff; --border:#e2dfd7;
  --text:#1f2733; --text2:#455064; --muted:#6b7484;
  --blue:#2563eb; --amber:#d97706; --green:#059669; --red:#dc2626;
  --purple:#7c3aed; --teal:#0d9488;
  --mat:#2563eb; --mat-strong:#1d4ed8; --mat-soft:#e8effd; --mat-line:#c3d5fa;
  --radius:14px; --radius-sm:8px;
  --font-display:"Space Grotesk","Segoe UI",system-ui,sans-serif;
  --font-body:"IBM Plex Sans","Segoe UI",system-ui,sans-serif;
  --font-mono:"JetBrains Mono",Consolas,monospace;
  --shadow:0 1px 3px rgba(31,39,51,.06),0 4px 16px rgba(31,39,51,.04);
}
@media (prefers-color-scheme: dark){
  :root{
    --bg:#12161d; --sidebar:#171c24; --card:#1a2029; --border:#2a323e;
    --text:#e8ecf2; --text2:#b6c0cf; --muted:#8b97a8;
    --blue:#60a5fa; --amber:#f59e0b; --green:#34d399; --red:#f87171;
    --purple:#a78bfa; --teal:#2dd4bf;
    --mat:#60a5fa; --mat-strong:#93c5fd; --mat-soft:#16233a; --mat-line:#24406e;
    --shadow:none;
  }
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
@media (prefers-reduced-motion: reduce){ html{scroll-behavior:auto} *{transition:none!important} }
body{
  margin:0; background:var(--bg); color:var(--text);
  font:400 1.02rem/1.65 var(--font-body);
  -webkit-text-size-adjust:100%;
}
.skip{
  position:absolute; left:-9999px; top:auto; width:1px; height:1px; overflow:hidden;
}
.skip:focus{
  left:.75rem; top:.75rem; width:auto; height:auto; padding:.55rem .9rem;
  background:var(--card); color:var(--text); border:2px solid var(--mat);
  border-radius:var(--radius-sm); z-index:100;
}
a{color:var(--mat-strong); text-underline-offset:2px}
a:hover{color:var(--mat)}
:focus-visible{outline:3px solid var(--mat); outline-offset:2px; border-radius:3px}
code{
  font-family:var(--font-mono); font-size:.9em; background:var(--mat-soft);
  padding:.1em .35em; border-radius:4px;
}
.topo{
  background:linear-gradient(180deg,var(--mat-soft),transparent 85%);
  border-bottom:1px solid var(--border); padding:2rem 1rem 1.5rem;
}
.topo-inner{max-width:1100px;margin:0 auto}
.topo-meta{
  margin:0 0 .5rem; font-size:.8rem; letter-spacing:.02em;
  color:var(--text2); text-transform:uppercase; font-weight:600;
}
.topo-meta .materia{color:var(--mat-strong)}
.status{
  display:inline-block; padding:.15rem .55rem; border-radius:999px;
  background:var(--card); border:1px solid var(--border); color:var(--text2);
  text-transform:none; letter-spacing:0; font-weight:600;
}
.status-publicado{border-color:var(--green); color:var(--green)}
.status-revisao{border-color:var(--amber); color:var(--amber)}
.status-rascunho{border-color:var(--muted)}
.status-arquivado{border-color:var(--border); color:var(--muted)}
.topo h1{
  font-family:var(--font-display); font-size:clamp(1.6rem,4vw,2.4rem);
  line-height:1.15; margin:.2rem 0 .75rem; letter-spacing:-.01em;
}
.resumo{margin:0 0 .9rem; color:var(--text2); max-width:70ch}
.tags{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:.4rem}
.tags li{
  font-size:.72rem; padding:.15rem .55rem; border-radius:999px;
  background:var(--card); border:1px solid var(--border); color:var(--text2);
}
.layout{
  max-width:1100px; margin:0 auto; padding:1.5rem 1rem 3rem;
  display:grid; grid-template-columns:minmax(0,1fr); gap:1.5rem;
}
@media (min-width: 960px){
  .layout{grid-template-columns:260px minmax(0,1fr); align-items:start}
}
.toc{
  background:var(--card); border:1px solid var(--border); border-radius:var(--radius);
  padding:1rem 1.1rem; box-shadow:var(--shadow);
}
.toc h2{
  font-family:var(--font-display); font-size:.78rem; text-transform:uppercase;
  letter-spacing:.08em; color:var(--muted); margin:0 0 .6rem;
}
.toc ol{list-style:none;margin:0;padding:0;font-size:.9rem}
.toc li{margin:.15rem 0}
.toc a{display:block;padding:.25rem .4rem;border-radius:6px;text-decoration:none}
.toc a:hover{background:var(--mat-soft)}
.toc .toc-extra{list-style:none;margin:.6rem 0 0;padding:.6rem 0 0;border-top:1px solid var(--border)}
main{min-width:0}
.secao{
  background:var(--card); border:1px solid var(--border); border-radius:var(--radius);
  padding:1.4rem 1.5rem; margin:0 0 1.25rem; box-shadow:var(--shadow);
}
.sec-header{display:flex;align-items:baseline;gap:.65rem;margin:0 0 .75rem}
.sec-num{
  font-family:var(--font-display); font-weight:700; font-size:1.05rem;
  color:var(--mat-strong); background:var(--mat-soft); border-radius:8px;
  padding:.1rem .5rem; min-width:2rem; text-align:center; flex:none;
}
.sec-header h2{
  font-family:var(--font-display); font-size:1.3rem; line-height:1.25;
  margin:0; letter-spacing:-.01em;
}
.sec-subtitulo{margin:-.4rem 0 1rem; color:var(--text2); font-size:.95rem}
.paragrafo{margin:0 0 1rem}
.paragrafo p{margin:0}
.bloco{margin:0 0 1rem}
.bloco-titulo{font-size:.95rem;font-weight:700;margin:0 0 .4rem;color:var(--text)}
.topico{
  font-family:var(--font-display); font-size:1.05rem; font-weight:700;
  margin:1.6rem 0 .7rem; padding-top:.9rem; border-top:1px solid var(--border);
  color:var(--mat-strong); letter-spacing:-.01em;
}
.topico:first-of-type{margin-top:.4rem;border-top:0;padding-top:0}
.lista ul,.lista ol{margin:0;padding-left:1.3rem}
.lista li{margin:.25rem 0}
.table-wrap{overflow-x:auto;margin:0 0 1rem;border:1px solid var(--border);border-radius:var(--radius-sm)}
table{border-collapse:collapse;width:100%;font-size:.93rem;background:var(--card)}
caption{
  text-align:left; padding:.6rem .8rem; font-weight:700;
  font-family:var(--font-display); border-bottom:1px solid var(--border);
}
th,td{padding:.55rem .8rem;text-align:left;vertical-align:top;border-bottom:1px solid var(--border)}
thead th{background:var(--mat-soft);color:var(--text);font-size:.85rem}
tbody tr:last-child td{border-bottom:0}
tbody tr:nth-child(even){background:rgba(127,127,127,.04)}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.destaque,.gotcha,.mnemonico,.exemplo{
  border-left:4px solid var(--blue); background:var(--mat-soft);
  border-radius:0 var(--radius-sm) var(--radius-sm) 0; padding:.85rem 1rem; margin:0 0 1rem;
}
.destaque-atencao{border-left-color:var(--amber);background:rgba(217,119,6,.1)}
.destaque-sucesso{border-left-color:var(--green);background:rgba(5,150,105,.09)}
.destaque-erro{border-left-color:var(--red);background:rgba(220,38,38,.08)}
.gotcha{border-left-color:var(--amber);background:rgba(217,119,6,.09)}
.mnemonico{border-left-color:var(--purple);background:rgba(124,58,237,.08)}
.exemplo{border-left-color:var(--teal);background:rgba(13,148,136,.08)}
.rotulo{
  margin:0 0 .25rem; font-size:.7rem; font-weight:700; text-transform:uppercase;
  letter-spacing:.09em; color:var(--text2);
}
.destaque p:last-child,.gotcha p:last-child,.mnemonico p:last-child,.exemplo p:last-child{
  margin:0;
}
.fontes-ref{margin:-.5rem 0 1rem;font-size:.8rem;color:var(--muted)}
.quiz{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:1.4rem 1.5rem;margin:0 0 1.25rem;box-shadow:var(--shadow)}
.instrucoes{margin:0 0 .3rem;color:var(--text2)}
.dica{margin:0 0 1rem;font-size:.82rem;color:var(--muted)}
.questoes{list-style:none;margin:0;padding:0}
.questao{border-top:1px solid var(--border);padding:1rem 0}
.questao:first-child{border-top:0;padding-top:0}
.enunciado{font-size:1rem;margin:0 0 .6rem;line-height:1.45}
.qnum{color:var(--mat-strong);font-weight:700;margin-right:.15rem}
.opcoes{list-style:none;margin:0;padding:0;counter-reset:opcao}
.opcoes li{margin:.35rem 0}
.opcoes details{
  border:1px solid var(--border); border-radius:var(--radius-sm);
  background:var(--card); overflow:hidden;
}
.opcoes details[open]{border-color:var(--mat-line);background:var(--mat-soft)}
.opcoes summary{
  cursor:pointer; padding:.55rem .75rem; list-style:none; position:relative;
  padding-left:2.1rem;
}
.opcoes summary::-webkit-details-marker{display:none}
.opcoes summary::before{
  counter-increment:opcao;
  content:counter(opcao,upper-alpha);
  position:absolute; left:.6rem; top:.5rem;
  font-size:.75rem; font-weight:700; color:var(--mat-strong);
  background:var(--card); border:1px solid var(--border);
  border-radius:50%; width:1.25rem; height:1.25rem;
  display:flex; align-items:center; justify-content:center;
}
.opcoes details[open] summary::before{border-color:var(--mat-line)}
.feedback{margin:0; padding:.6rem .75rem .7rem 2.1rem; font-size:.9rem; border-top:1px solid var(--border)}
.feedback.correta strong{color:var(--green)}
.feedback.incorreta strong{color:var(--red)}
.incidencia{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:1.4rem 1.5rem;margin:0 0 1.25rem;box-shadow:var(--shadow)}
.meta{font-size:.85rem;color:var(--muted);margin:0 0 .8rem}
.vazio{color:var(--text2);font-style:italic;margin:0 0 .8rem}
.observacao{font-size:.9rem;color:var(--text2);margin:.5rem 0 0}
.secoes{font-size:.85rem}
.fontes{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:1.4rem 1.5rem;margin:0 0 1.25rem;box-shadow:var(--shadow)}
.fontes dl{margin:0}
.fonte{padding:.55rem 0;border-top:1px solid var(--border)}
.fonte:first-child{border-top:0;padding-top:0}
.fonte dt{font-weight:600;margin:0 0 .15rem}
.fonte dd{margin:0 0 .35rem;font-size:.88rem;color:var(--text2)}
.fonte-tipo{
  display:inline-block;font-size:.68rem;text-transform:uppercase;letter-spacing:.07em;
  background:var(--mat-soft);color:var(--mat-strong);border-radius:4px;
  padding:.1rem .4rem;margin-right:.35rem;
}
.meta-bloco,.notas{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:1.4rem 1.5rem;margin:0 0 1.25rem;box-shadow:var(--shadow)}
.dl{margin:0;display:grid;grid-template-columns:1fr;gap:.4rem}
@media (min-width:700px){ .dl{grid-template-columns:200px 1fr;gap:.3rem 1rem} }
.dl div{display:contents}
.dl dt{font-size:.82rem;color:var(--muted);font-weight:600}
.dl dd{margin:0;font-size:.92rem}
.subtitulo-meta{font-size:.9rem;margin:1.1rem 0 .4rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.ritual{margin:0;padding-left:1.2rem}
.ritual li{margin:.25rem 0;font-size:.93rem}
.notas p{margin:0;color:var(--text2)}
.rodape{
  max-width:1100px;margin:0 auto;padding:0 1rem 3rem;
  font-size:.78rem;color:var(--muted);
}
.rodape a{color:var(--muted)}
.indice{max-width:1100px;margin:0 auto;padding:2rem 1rem 3rem}
.indice h1{font-family:var(--font-display);font-size:1.9rem;margin:.2rem 0 .5rem}
.indice p.sub{color:var(--text2);margin:0 0 1.5rem}
.cartoes{list-style:none;margin:0;padding:0;display:grid;gap:1rem;grid-template-columns:repeat(auto-fill,minmax(280px,1fr))}
.cartoes a{
  display:block;height:100%;text-decoration:none;color:var(--text);
  background:var(--card);border:1px solid var(--border);border-radius:var(--radius);
  padding:1rem 1.1rem;box-shadow:var(--shadow);
}
.cartoes a:hover{border-color:var(--mat-line)}
.cartoes .cartao-meta{font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin:0 0 .35rem}
.cartoes h2{font-family:var(--font-display);font-size:1.05rem;margin:0 0 .4rem;line-height:1.3}
.cartoes p{margin:0;font-size:.88rem;color:var(--text2)}
@media print{
  body{background:#fff;color:#000;font-size:11pt}
  .topo{background:none;border-bottom:1px solid #999;padding:0 0 1rem}
  .layout{display:block;max-width:none;padding:0}
  .toc,.skip{display:none}
  .secao,.quiz,.incidencia,.fontes,.meta-bloco,.notas{
    box-shadow:none;border:1px solid #ccc;break-inside:avoid-page;
  }
  .opcoes details{display:block}
  .opcoes summary{display:none}
  .feedback{display:block;border-top:0;padding-left:.75rem}
  .opcoes li{margin:.15rem 0}
  a{color:#000;text-decoration:none}
}
"""


def _toc_html(document: dict[str, Any]) -> str:
    itens = []
    for section in document.get("secoes", []):
        if not isinstance(section, dict):
            continue
        sid = escape_attr(str(section.get("id", "")))
        numero = section.get("numero", "")
        titulo = inline_html(str(section.get("titulo", "")))
        itens.append(
            f'<li><a href="#sec-{sid}"><span class="toc-num">{numero}.</span> {titulo}</a></li>'
        )
    extras = []
    if document.get("quiz"):
        extras.append('<li><a href="#quiz">Quiz</a></li>')
    if document.get("incidencia"):
        extras.append('<li><a href="#incidencia">Incidência de temas</a></li>')
    extras.append('<li><a href="#fontes">Fontes</a></li>')
    extras.append('<li><a href="#revisao">Revisão e metadados</a></li>')
    if document.get("notas"):
        extras.append('<li><a href="#notas">Notas</a></li>')
    extras_html = f'<ul class="toc-extra">{"".join(extras)}</ul>' if extras else ""
    return (
        f'<nav class="toc" aria-labelledby="toc-titulo">'
        f'<h2 id="toc-titulo">Nesta aula</h2>'
        f'<ol>{"".join(itens)}</ol>{extras_html}</nav>'
    )


def render_html(document: dict[str, Any]) -> str:
    """Gera o HTML autocontido de uma aula."""
    materia = inline_html(str(document.get("materia", "")))
    numero = _numero_aula(document.get("numero", 0))
    titulo = inline_html(str(document.get("titulo", "")))
    resumo = inline_html(str(document.get("resumo", "")))
    idioma = escape_attr(str(document.get("idioma", "pt-BR")))
    status = str(document.get("status", "rascunho"))
    status_label = STATUS_LABEL.get(status, status)
    fontes = _fonte_por_id(document)

    secoes = "".join(
        _section_html(section, fontes)
        for section in document.get("secoes", [])
        if isinstance(section, dict)
    )
    corpo = (
        secoes
        + _quiz_html(document.get("quiz") or {})
        + _incidencia_html(document.get("incidencia"))
        + _fontes_html(document.get("fontes", []))
        + _revisao_html(document)
        + _notas_html(document)
    )

    metadados = document.get("metadados") or {}
    licenca = escape_attr(str(metadados.get("licenca", "")))
    rodape = (
        f'<footer class="rodape">Gerado por <strong>Hermes build.py {BUILD_VERSION}</strong> '
        f"· schema {escape_attr(str(document.get('schema_version', '')))} "
        f"· aula v{escape_attr(str(metadados.get('versao', '')))} "
        f"· {licenca}. O JSON é a fonte da verdade.</footer>"
    )

    return (
        "<!DOCTYPE html>\n"
        f'<html lang="{idioma}">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{titulo} — {materia} Aula {numero}</title>\n"
        f'<meta name="description" content="{escape_attr(str(document.get("resumo", "")))}">\n'
        f'<meta name="generator" content="Hermes build.py {BUILD_VERSION}">\n'
        f"<style>{CSS}</style>\n</head>\n<body>\n"
        '<a class="skip" href="#conteudo">Pular para o conteúdo</a>\n'
        '<header class="topo"><div class="topo-inner">'
        f'<p class="topo-meta"><span class="materia">{materia}</span> '
        f'<span aria-hidden="true">·</span> <span>Aula {numero}</span> '
        f'<span aria-hidden="true">·</span> '
        f'<span class="status status-{escape_attr(status)}">{inline_html(status_label)}</span></p>'
        f"<h1>{titulo}</h1>"
        f'<p class="resumo">{resumo}</p>'
        f"{_tags_html(document.get('tags', []))}"
        "</div></header>\n"
        f'<div class="layout">{_toc_html(document)}'
        f'<main id="conteudo" tabindex="-1">{corpo}</main>'
        "</div>\n"
        f"{rodape}\n</body>\n</html>\n"
    )


def render_index(entries: Sequence[tuple[dict[str, Any], str]]) -> str:
    """Gera um índice com cartões para as aulas construídas."""
    cartoes = []
    for document, filename in entries:
        materia = inline_html(str(document.get("materia", "")))
        numero = _numero_aula(document.get("numero", 0))
        titulo = inline_html(str(document.get("titulo", "")))
        resumo = inline_html(str(document.get("resumo", "")))
        status = str(document.get("status", "rascunho"))
        quiz = document.get("quiz") or {}
        questoes = len(quiz.get("questoes", [])) if isinstance(quiz, dict) else 0
        extra = f"{questoes} questão(ões) de quiz" if questoes else "sem quiz"
        cartoes.append(
            "<li><a href=\""
            + escape_attr(filename)
            + '">'
            f'<p class="cartao-meta">{materia} · Aula {numero} · '
            f'{inline_html(STATUS_LABEL.get(status, status))}</p>'
            f"<h2>{titulo}</h2><p>{resumo}</p>"
            f'<p class="cartao-meta" style="margin-top:.5rem">{extra}</p>'
            "</a></li>"
        )
    return (
        "<!DOCTYPE html>\n"
        '<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>Índice — Hermes</title>\n"
        f'<meta name="generator" content="Hermes build.py {BUILD_VERSION}">\n'
        f"<style>{CSS}</style>\n</head>\n<body>\n"
        '<a class="skip" href="#conteudo">Pular para o conteúdo</a>\n'
        '<main id="conteudo" tabindex="-1" class="indice">'
        "<h1>Índice de aulas</h1>"
        f'<p class="sub">{len(cartoes)} aula(s) gerada(s) a partir do JSON do Hermes.</p>'
        f'<ul class="cartoes">{"".join(cartoes)}</ul>'
        "</main>\n</body>\n</html>\n"
    )


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------


def _md_escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def _md_fontes(
    refs: Sequence[Any],
    fontes: dict[str, dict[str, Any]],
    rotulo: str = "Fontes",
) -> str:
    if not isinstance(refs, list) or not refs:
        return ""
    links = []
    for ref in refs:
        if isinstance(ref, str) and ref in fontes:
            titulo = str(fontes[ref].get("titulo", ref))
            links.append(f"[{titulo}](#fonte-{ref})")
    return f"*{rotulo}: {', '.join(links)}.*\n" if links else ""


def _md_block(block: dict[str, Any], fontes: dict[str, dict[str, Any]]) -> list[str]:
    tipo = str(block.get("tipo", ""))
    titulo = block.get("titulo")
    refs = _md_fontes(block.get("fontes", []), fontes)
    out: list[str] = []

    if tipo == "paragrafo":
        if titulo:
            out.append(f"**{titulo}**")
            out.append("")
        out.append(str(block.get("texto", "")))
    elif tipo == "topico":
        out.append(f"### {block.get('texto', '')}")
    elif tipo == "lista":
        if titulo:
            out.append(f"**{titulo}**")
        out.append("")
        for index, item in enumerate(block.get("itens", []), start=1):
            marker = f"{index}." if block.get("ordenada") else "-"
            out.append(f"{marker} {item}")
    elif tipo == "tabela":
        colunas = [str(c) for c in block.get("colunas", [])]
        if titulo:
            out.append(f"**{titulo}**")
            out.append("")
        out.append("| " + " | ".join(_md_escape_cell(c) for c in colunas) + " |")
        out.append("|" + "|".join(["---"] * len(colunas)) + "|")
        for linha in block.get("linhas", []):
            cells = [_md_escape_cell(str(cell)) for cell in linha]
            out.append("| " + " | ".join(cells) + " |")
    elif tipo == "destaque":
        rotulo = NIVEL_LABEL.get(str(block.get("nivel", "info")), "Informação")
        out.append(f"> **{rotulo}.** {block.get('texto', '')}")
    elif tipo == "gotcha":
        out.append(f"> ⚠️ **Pegadinha.** {block.get('texto', '')}")
    elif tipo == "mnemonico":
        out.append(f"> 🧠 **Mnemônico.** {block.get('texto', '')}")
    elif tipo == "exemplo":
        out.append(f"> ✅ **Exemplo.** {block.get('texto', '')}")
    else:
        out.append(str(block))

    if refs:
        out.append("")
        out.append(refs.rstrip())
    out.append("")
    return out


def render_markdown(document: dict[str, Any]) -> str:
    """Gera Markdown (GFM) de uma aula, com âncoras explícitas."""
    fontes = _fonte_por_id(document)
    status = STATUS_LABEL.get(str(document.get("status", "")), str(document.get("status", "")))
    metadados = document.get("metadados") or {}
    numero = _numero_aula(document.get("numero", 0))
    tags = document.get("tags", [])

    lines: list[str] = [
        f"# {document.get('titulo', '')}",
        "",
        f"**Matéria:** {document.get('materia', '')} · **Aula:** {numero} · "
        f"**Status:** {status}",
        f"**Versão:** {metadados.get('versao', '')} · "
        f"**Atualizada em:** {_date_pt(metadados.get('atualizado_em'))}",
        "",
        f"> {document.get('resumo', '')}",
        "",
    ]
    if tags:
        lines.append("**Tags:** " + ", ".join(f"`{tag}`" for tag in tags))
        lines.append("")

    lines.append("## Sumário")
    lines.append("")
    for section in document.get("secoes", []):
        if not isinstance(section, dict):
            continue
        lines.append(
            f"{section.get('numero', '')}. [{section.get('titulo', '')}]"
            f"(#sec-{section.get('id', '')})"
        )
    if document.get("quiz"):
        lines.append("- [Quiz](#quiz)")
    if document.get("incidencia"):
        lines.append("- [Incidência de temas](#incidencia)")
    lines.append("- [Fontes](#fontes)")
    lines.append("- [Revisão e metadados](#revisao)")
    lines.append("")

    for section in document.get("secoes", []):
        if not isinstance(section, dict):
            continue
        lines.append(f'<a id="sec-{section.get("id", "")}"></a>')
        lines.append("")
        lines.append(f"## {section.get('numero', '')}. {section.get('titulo', '')}")
        lines.append("")
        if section.get("subtitulo"):
            lines.append(f"_{section.get('subtitulo')}_")
            lines.append("")
        refs = _md_fontes(section.get("fontes", []), fontes, rotulo="Fontes da seção")
        if refs:
            lines.append(refs.rstrip())
            lines.append("")
        for block in section.get("blocos", []):
            if isinstance(block, dict):
                lines.extend(_md_block(block, fontes))

    quiz = document.get("quiz")
    if isinstance(quiz, dict) and quiz.get("questoes"):
        lines.append('<a id="quiz"></a>')
        lines.append("")
        lines.append(f"## {quiz.get('titulo') or 'Quiz'}")
        lines.append("")
        lines.append(str(quiz.get("instrucoes", "")))
        lines.append("")
        for index, questao in enumerate(quiz.get("questoes", []), start=1):
            if not isinstance(questao, dict):
                continue
            lines.append(f'<a id="q-{questao.get("id", index)}"></a>')
            lines.append("")
            lines.append(f"### {index}. {questao.get('enunciado', '')}")
            lines.append("")
            for opcao in questao.get("opcoes", []):
                if not isinstance(opcao, dict):
                    continue
                veredito = "Correta." if opcao.get("correta") else "Incorreta."
                lines.append(
                    f"**{opcao.get('texto', '')}**  "
                    f"<details><summary>Feedback</summary>"
                    f"**{veredito}** {opcao.get('explicacao', '')}</details>"
                )
            lines.append("")

    incidencia = document.get("incidencia")
    if isinstance(incidencia, dict):
        lines.append('<a id="incidencia"></a>')
        lines.append("")
        lines.append("## Incidência de temas")
        lines.append("")
        meta = f"**Fonte:** {incidencia.get('fonte', '')}"
        if incidencia.get("atualizado_em"):
            meta += f" · **Atualizado em:** {_date_pt(incidencia.get('atualizado_em'))}"
        lines.append(meta)
        lines.append("")
        temas = [t for t in incidencia.get("temas", []) if isinstance(t, dict)]
        if temas:
            lines.append("| Tema | Peso | Seções |")
            lines.append("|---|---:|---|")
            for tema in temas:
                secoes = ", ".join(
                    f"[{sid}](#sec-{sid})" for sid in tema.get("secao_ids", [])
                )
                lines.append(
                    f"| {_md_escape_cell(str(tema.get('nome', '')))} | "
                    f"{tema.get('peso', 0)} | {secoes} |"
                )
        else:
            lines.append("_Nenhum tema registrado por enquanto._")
        if incidencia.get("observacao"):
            lines.append("")
            lines.append(str(incidencia["observacao"]))
        lines.append("")

    if document.get("fontes"):
        lines.append('<a id="fontes"></a>')
        lines.append("")
        lines.append("## Fontes")
        lines.append("")
        for fonte in document["fontes"]:
            if not isinstance(fonte, dict):
                continue
            linha = (
                f'<a id="fonte-{fonte.get("id", "")}"></a>'
                f"**{TIPO_LABEL.get(str(fonte.get('tipo', 'outro')), fonte.get('tipo', 'outro'))}** "
                f"— {fonte.get('titulo', '')}"
            )
            extra = []
            if fonte.get("detalhes"):
                extra.append(str(fonte["detalhes"]))
            if fonte.get("ano"):
                extra.append(str(fonte["ano"]))
            if fonte.get("url"):
                extra.append(f"[{fonte['url']}]({fonte['url']})")
            if extra:
                linha += ". " + " · ".join(extra)
            lines.append(f"- {linha}")
        lines.append("")

    revisao = document.get("revisao") or {}
    lines.append('<a id="revisao"></a>')
    lines.append("")
    lines.append("## Revisão e metadados")
    lines.append("")
    lines.append(f"- **Status da revisão:** {STATUS_LABEL.get(str(revisao.get('status', '')), revisao.get('status', ''))}")
    if revisao.get("ultima_em"):
        lines.append(f"- **Última revisão:** {_date_pt(revisao.get('ultima_em'))}")
    if revisao.get("proxima_em"):
        lines.append(f"- **Próxima revisão:** {_date_pt(revisao.get('proxima_em'))}")
    lines.append(f"- **Versão:** {metadados.get('versao', '')}")
    lines.append(f"- **Criada em:** {_date_pt(metadados.get('criado_em'))}")
    lines.append(f"- **Atualizada em:** {_date_pt(metadados.get('atualizado_em'))}")
    lines.append(f"- **Autoria:** {', '.join(metadados.get('autores', [])) or '—'}")
    lines.append(
        f"- **Revisão:** {', '.join(metadados.get('revisores', [])) or '—'}"
    )
    lines.append(f"- **Licença:** {metadados.get('licenca', '')}")
    lines.append(f"- **Origem:** {metadados.get('origem', '')}")
    lines.append(f"- **Alterações:** {metadados.get('alteracoes', '')}")
    lines.append("")
    if revisao.get("ritual"):
        lines.append("### Ritual de revisão")
        lines.append("")
        for item in revisao["ritual"]:
            lines.append(f"- {item}")
        lines.append("")

    if document.get("notas"):
        lines.append("### Notas")
        lines.append("")
        lines.append(str(document["notas"]))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Orquestração
# ---------------------------------------------------------------------------


def _collect(paths: Sequence[Path]) -> tuple[list[Path], list[Path]]:
    """Expande diretórios em arquivos ``.json``, em ordem determinística."""
    found: list[Path] = []
    missing: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        if path.is_dir():
            for candidate in sorted(path.rglob("*.json")):
                if "dist" in candidate.parts:
                    continue
                resolved = candidate.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    found.append(candidate)
        elif path.exists():
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                found.append(path)
        else:
            missing.append(path)
    return found, missing


def _load_and_validate(
    path: Path, validator: Any
) -> tuple[dict[str, Any] | None, list[str]]:
    document, issue = hermes_validate.read_json(path)
    if issue is not None:
        return None, [f"[{issue.code}] {issue.path}: {issue.message}"]
    if not isinstance(document, dict):
        return None, ["[schema] $: o documento precisa ser um objeto JSON"]
    errors: list[str] = []
    if validator is not None:
        errors.extend(f"[{e.code}] {e.path}: {e.message}" for e in validator.validate(document))
    errors.extend(f"[{e.code}] {e.path}: {e.message}" for e in hermes_validate.validate_document(document))
    return document, errors


def build(
    paths: Sequence[Path],
    out_dir: Path,
    formats: Sequence[str] = ("html",),
    validate_first: bool = True,
    force: bool = False,
    make_index: bool | None = None,
    quiet: bool = False,
) -> tuple[list[Path], list[str]]:
    """Gera os arquivos derivados e devolve ``(caminhos_gerados, mensagens)``."""
    files, missing = _collect(paths)
    if missing:
        return [], [f"caminho não encontrado: {path}" for path in missing]
    if not files:
        return [], ["nenhum arquivo .json encontrado"]

    validator = None
    if validate_first:
        schema, issue = hermes_validate.load_schema(hermes_validate.DEFAULT_SCHEMA_PATH)
        if issue is not None or schema is None:
            return [], [f"esquema inválido: {issue.message if issue else 'desconhecido'}"]
        validator = schema

    loaded: list[tuple[dict[str, Any], Path, list[str]]] = []
    all_errors: list[str] = []
    for path in files:
        document, errors = _load_and_validate(path, validator)
        loaded.append((document, path, errors))  # type: ignore[arg-type]
        all_errors.extend(f"{path}: {error}" for error in errors)

    if all_errors and not force:
        return [], all_errors

    out_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    entries: list[tuple[dict[str, Any], str]] = []

    for document, path, errors in loaded:
        if document is None:
            continue
        stem = str(document.get("id") or path.stem)
        if "html" in formats:
            target = out_dir / f"{stem}.html"
            target.write_text(render_html(document), encoding="utf-8")
            generated.append(target)
            entries.append((document, target.name))
        if "md" in formats:
            target = out_dir / f"{stem}.md"
            target.write_text(render_markdown(document), encoding="utf-8")
            generated.append(target)

    if make_index is None:
        # Diretório como entrada gera índice mesmo com uma única aula: é o
        # comportamento esperado para um site. Um arquivo isolado não gera.
        write_index = len(entries) > 1 or any(path.is_dir() for path in paths)
    else:
        write_index = make_index
    if write_index and entries:
        index = out_dir / "index.html"
        index.write_text(render_index(entries), encoding="utf-8")
        generated.append(index)

    messages: list[str] = []
    if all_errors:
        messages.append(
            f"gerado com {len(all_errors)} erro(s) ignorado(s) por --force"
        )
    if not quiet:
        for target in generated:
            messages.append(f"gerado: {target}")
    return generated, messages


def _print_human(generated: Sequence[Path], messages: Sequence[str]) -> None:
    for message in messages:
        if message.startswith("gerado:"):
            print(f"OK      {message[len('gerado: '):]}")
        else:
            print(message)
    print(f"\n{len(generated)} arquivo(s) gerado(s).")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gera HTML autocontido e/ou Markdown a partir das aulas do Hermes.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="arquivos ou diretórios .json (padrão: exemplos/)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=f"diretório de saída (padrão: {DEFAULT_OUTPUT_PATH})",
    )
    parser.add_argument(
        "--format",
        dest="formats",
        action="append",
        choices=["html", "md"],
        help="formato de saída; repita para gerar os dois (padrão: html)",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="não valida o JSON antes de gerar (não recomendado)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="gera mesmo com erros de validação",
    )
    parser.add_argument(
        "--index",
        dest="make_index",
        action="store_true",
        default=None,
        help="força a geração de index.html",
    )
    parser.add_argument(
        "--no-index",
        dest="make_index",
        action="store_false",
        default=None,
        help="não gera index.html",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="não lista os arquivos gerados",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Hermes build {BUILD_VERSION} (schema {hermes_validate.SCHEMA_VERSION})",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    paths = args.paths or [DEFAULT_INPUT_PATH]
    formats = tuple(dict.fromkeys(args.formats or ["html"]))
    generated, messages = build(
        paths,
        args.out,
        formats=formats,
        validate_first=not args.no_validate,
        force=args.force,
        make_index=args.make_index,
        quiet=args.quiet,
    )
    _print_human(generated, messages)
    if not generated:
        return EXIT_USAGE if any("não encontrado" in m or "nenhum arquivo" in m for m in messages) else EXIT_INVALID
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
