from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build  # noqa: E402
import validate  # noqa: E402


def _ids(html: str) -> set[str]:
    return set(re.findall(r'\bid="([^"]+)"', html))


def _hrefs(html: str) -> set[str]:
    return set(re.findall(r'href="#([^"]+)"', html))


class BuildHtmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document, issue = validate.read_json(
            ROOT / "exemplos" / "redacao-oficial" / "aula-00.json"
        )
        if cls.document is None or issue is not None:
            raise AssertionError(f"exemplo inválido: {issue}")
        cls.html = build.render_html(cls.document)

    def test_document_is_self_contained(self) -> None:
        self.assertIn("<!DOCTYPE html>", self.html)
        self.assertIn('lang="pt-BR"', self.html)
        self.assertIn("<style>", self.html)
        self.assertNotIn("<script", self.html)
        self.assertNotIn("http://", self.html.split("<body>")[0])
        self.assertNotIn("https://", self.html.split("<body>")[0])

    def test_every_section_has_an_anchor(self) -> None:
        for section in self.document["secoes"]:
            self.assertIn(f'id="sec-{section["id"]}"', self.html)
            self.assertIn(section["titulo"], self.html)

    def test_every_block_has_an_anchor(self) -> None:
        for section in self.document["secoes"]:
            for block in section["blocos"]:
                self.assertIn(f'id="blk-{block["id"]}"', self.html)

    def test_internal_anchors_resolve(self) -> None:
        self.assertEqual(_hrefs(self.html) - _ids(self.html), set())

    def test_all_block_types_are_rendered(self) -> None:
        blocos = [
            {"tipo": "topico", "id": "b0", "texto": "Assunto"},
            {"tipo": "paragrafo", "id": "b1", "texto": "texto", "titulo": "Título do parágrafo"},
            {"tipo": "lista", "id": "b2", "titulo": "Lista", "itens": ["a", "b"], "ordenada": True},
            {
                "tipo": "tabela",
                "id": "b3",
                "titulo": "Tabela",
                "colunas": ["A", "B"],
                "linhas": [["1", "2"]],
            },
            {"tipo": "destaque", "id": "b4", "nivel": "atencao", "texto": "atenção"},
            {"tipo": "gotcha", "id": "b5", "texto": "pegadinha"},
            {"tipo": "mnemonico", "id": "b6", "texto": "mnemônico"},
            {"tipo": "exemplo", "id": "b7", "texto": "exemplo"},
        ]
        document = {
            "schema_version": "1.0.0",
            "id": "teste-blocos",
            "materia": "Teste",
            "numero": 1,
            "titulo": "Todos os blocos",
            "resumo": "Documento sintético para cobrir todos os tipos de bloco.",
            "status": "rascunho",
            "idioma": "pt-BR",
            "tags": ["teste"],
            "fontes": [{"id": "f1", "tipo": "outro", "titulo": "Fonte"}],
            "secoes": [{"id": "s1", "numero": 1, "titulo": "Seção", "blocos": blocos}],
            "revisao": {"status": "pendente", "proxima_em": "2026-12-01", "ritual": ["reler"]},
            "metadados": {
                "versao": "1.0.0",
                "criado_em": "2026-11-22",
                "atualizado_em": "2026-11-22",
                "autores": ["Teste"],
                "revisores": [],
                "licenca": "CC-BY-4.0",
                "origem": "teste",
                "alteracoes": "teste",
            },
        }
        html = build.render_html(document)
        self.assertIn("<table>", html)
        self.assertIn("<caption>", html)
        self.assertIn('scope="col"', html)
        self.assertIn('class="destaque destaque-atencao"', html)
        self.assertIn('class="gotcha"', html)
        self.assertIn('class="mnemonico"', html)
        self.assertIn('class="exemplo"', html)
        self.assertIn("<ol><li>a</li><li>b</li></ol>", html)
        self.assertIn('<h3 id="blk-b0" class="topico">Assunto</h3>', html)
        self.assertIn('<h3 class="bloco-titulo">Título do parágrafo</h3>', html)
        # O exemplo real precisa exercitar ao menos os tipos que ele usa.
        self.assertIn("<table>", self.html)
        self.assertIn('class="destaque', self.html)
        self.assertIn('class="gotcha"', self.html)

    def test_quiz_has_four_options_and_one_correct_answer_each(self) -> None:
        self.assertEqual(self.html.count("<details>"), 32)
        self.assertEqual(self.html.count('class="feedback correta"'), 8)
        self.assertEqual(self.html.count('class="feedback incorreta"'), 24)

    def test_landmarks_and_skip_link(self) -> None:
        self.assertIn('class="skip"', self.html)
        self.assertIn("<main", self.html)
        self.assertIn('id="conteudo"', self.html)
        self.assertIn("<nav", self.html)

    def test_html_is_balanced(self) -> None:
        from html.parser import HTMLParser

        void = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

        class Checker(HTMLParser):
            def __init__(self) -> None:
                super().__init__()
                self.stack: list[str] = []
                self.errors: list[str] = []

            def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
                if tag not in void:
                    self.stack.append(tag)

            def handle_endtag(self, tag: str) -> None:
                if tag in void:
                    return
                if not self.stack or self.stack[-1] != tag:
                    self.errors.append(f"</{tag}> inesperado")
                else:
                    self.stack.pop()

        checker = Checker()
        checker.feed(self.html)
        self.assertEqual(checker.errors, [])
        self.assertEqual(checker.stack, [])

    def test_html_escapes_raw_tags(self) -> None:
        document = copy.deepcopy(self.document)
        document["secoes"][0]["blocos"][0]["texto"] = "<script>alert(1)</script> & <b>x</b>"
        html = build.render_html(document)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertNotIn("<b>x</b>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_inline_markdown_is_converted(self) -> None:
        self.assertEqual(
            build.inline_html("**a** *b* `c`"),
            "<strong>a</strong> <em>b</em> <code>c</code>",
        )
        self.assertEqual(
            build.inline_html("`**não**`"),
            "<code>**não**</code>",
        )


class BuildMarkdownTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document, issue = validate.read_json(
            ROOT / "exemplos" / "redacao-oficial" / "aula-00.json"
        )
        if cls.document is None or issue is not None:
            raise AssertionError(f"exemplo inválido: {issue}")
        cls.markdown = build.render_markdown(cls.document)

    def test_has_title_summary_and_toc(self) -> None:
        self.assertTrue(self.markdown.startswith("# Fundamentos"))
        self.assertIn("## Sumário", self.markdown)
        self.assertIn("(#sec-o-que-e-redacao-oficial)", self.markdown)
        self.assertIn('<a id="sec-o-que-e-redacao-oficial"></a>', self.markdown)

    def test_has_gfm_table(self) -> None:
        self.assertIn("| Atributo | Cuida de |", self.markdown)
        self.assertIn("|---|---|", self.markdown)

    def test_has_quiz_feedback(self) -> None:
        self.assertIn("## Quiz", self.markdown)
        self.assertEqual(self.markdown.count("<summary>Feedback</summary>"), 32)

    def test_has_sources_and_review(self) -> None:
        self.assertIn("## Fontes", self.markdown)
        self.assertIn("## Revisão e metadados", self.markdown)
        self.assertIn("CC-BY-4.0", self.markdown)


class BuildIndexTests(unittest.TestCase):
    def test_certo_errado_quiz_renders_two_options(self) -> None:
        document = {
            "schema_version": "1.1.0",
            "id": "teste-certo-errado",
            "materia": "Teste",
            "numero": 1,
            "titulo": "Certo ou errado",
            "resumo": "Documento sintético com uma questão de duas alternativas.",
            "status": "rascunho",
            "idioma": "pt-BR",
            "tags": ["teste"],
            "fontes": [{"id": "f1", "tipo": "outro", "titulo": "Fonte"}],
            "secoes": [{"id": "s1", "numero": 1, "titulo": "Seção", "blocos": [{"tipo": "paragrafo", "id": "b1", "texto": "texto"}]}],
            "quiz": {
                "id": "quiz-teste",
                "instrucoes": "Escolha Certo ou Errado.",
                "questoes": [
                    {
                        "id": "q1",
                        "enunciado": "Afirmação.",
                        "opcoes": [
                            {"texto": "Certo", "correta": True, "explicacao": "Está certo."},
                            {"texto": "Errado", "correta": False, "explicacao": "Está errado."},
                        ],
                        "secao_id": "s1",
                        "fonte_id": "f1",
                    }
                ],
            },
            "revisao": {"status": "pendente", "proxima_em": "2026-12-01", "ritual": ["reler"]},
            "metadados": {
                "versao": "1.0.0",
                "criado_em": "2026-11-22",
                "atualizado_em": "2026-11-22",
                "autores": ["Teste"],
                "revisores": [],
                "licenca": "NOASSERTION",
                "origem": "teste",
                "alteracoes": "teste",
            },
        }
        html = build.render_html(document)
        self.assertEqual(html.count("<details>"), 2)
        self.assertEqual(html.count('class="feedback correta"'), 1)
        self.assertEqual(html.count('class="feedback incorreta"'), 1)

    def test_index_links_to_every_lesson(self) -> None:
        document, issue = validate.read_json(
            ROOT / "exemplos" / "redacao-oficial" / "aula-00.json"
        )
        assert document is not None
        index = build.render_index([(document, "ro-aula-00.html")])
        self.assertIn('href="ro-aula-00.html"', index)
        self.assertIn("Índice de aulas", index)

    def test_index_groups_lessons_by_materia(self) -> None:
        base = {
            "schema_version": "1.1.0",
            "id": "teste",
            "titulo": "Aula de teste",
            "resumo": "resumo",
            "status": "rascunho",
            "secoes": [{"numero": 1, "titulo": "Um", "blocos": []}],
            "quiz": {"questoes": []},
        }
        legislacao_2 = {**base, "id": "leg-2", "materia": "Legislação", "numero": 2}
        legislacao_1 = {**base, "id": "leg-1", "materia": "Legislação", "numero": 1}
        portugues = {**base, "id": "por-1", "materia": "Língua Portuguesa", "numero": 1}
        index = build.render_index(
            [
                (legislacao_2, "leg-2.html"),
                (portugues, "por-1.html"),
                (legislacao_1, "leg-1.html"),
            ]
        )
        self.assertEqual(index.count('<section class="grupo"'), 2)
        self.assertIn('href="#materia-legislacao"', index)
        self.assertIn('href="#materia-lingua-portuguesa"', index)
        # cada matéria aparece uma vez no cabeçalho do grupo, não por aula
        self.assertEqual(index.count(">Legislação</h2>"), 1)
        # aulas da mesma matéria ficam em ordem numérica
        self.assertLess(index.index("leg-1.html"), index.index("leg-2.html"))


class BuildCliTests(unittest.TestCase):
    def _run(self, *args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ROOT / "build.py"), *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_html_and_markdown_are_generated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self._run(
                str(ROOT / "exemplos" / "redacao-oficial" / "aula-00.json"),
                "--out",
                directory,
                "--format",
                "html",
                "--format",
                "md",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((Path(directory) / "ro-aula-00.html").exists())
            self.assertTrue((Path(directory) / "ro-aula-00.md").exists())

    def test_single_file_does_not_generate_index_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self._run(
                str(ROOT / "exemplos" / "redacao-oficial" / "aula-00.json"),
                "--out",
                directory,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((Path(directory) / "index.html").exists())

    def test_directory_generates_index(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self._run(str(ROOT / "exemplos"), "--out", directory)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((Path(directory) / "index.html").exists())

    def test_index_can_be_forced(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self._run(
                str(ROOT / "exemplos" / "redacao-oficial" / "aula-00.json"),
                "--out",
                directory,
                "--index",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((Path(directory) / "index.html").exists())

    def test_invalid_document_aborts_build(self) -> None:
        document, issue = validate.read_json(
            ROOT / "exemplos" / "redacao-oficial" / "aula-00.json"
        )
        assert document is not None
        broken = copy.deepcopy(document)
        broken["secoes"][2]["numero"] = 9
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.json"
            path.write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
            out = Path(directory) / "out"
            result = self._run(str(path), "--out", str(out))
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("section-number", result.stdout)
            self.assertFalse(out.exists())

    def test_force_builds_invalid_document(self) -> None:
        document, issue = validate.read_json(
            ROOT / "exemplos" / "redacao-oficial" / "aula-00.json"
        )
        assert document is not None
        broken = copy.deepcopy(document)
        broken["secoes"][2]["numero"] = 9
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.json"
            path.write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
            out = Path(directory) / "out"
            result = self._run(str(path), "--out", str(out), "--force")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("ignorado(s)", result.stdout)
            self.assertTrue((out / "ro-aula-00.html").exists())

    def test_missing_path_is_usage_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self._run(str(Path(directory) / "nao-existe.json"))
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("não encontrado", result.stdout)

    def test_empty_directory_is_usage_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self._run(directory, "--out", str(Path(directory) / "out"))
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("nenhum arquivo", result.stdout)

    def test_non_object_json_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lista.json"
            path.write_text("[]", encoding="utf-8")
            out = Path(directory) / "out"
            result = self._run(str(path), "--out", str(out))
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("objeto JSON", result.stdout)

    def test_version(self) -> None:
        result = self._run("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Hermes build", result.stdout)


if __name__ == "__main__":
    unittest.main()
