from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "validate.py"

SPEC = importlib.util.spec_from_file_location("hermes_validate", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Não foi possível carregar {MODULE_PATH}")
validate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validate
SPEC.loader.exec_module(validate)


class HermesValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema, schema_issue = validate.load_schema(validate.DEFAULT_SCHEMA_PATH)
        if cls.schema is None or schema_issue is not None:
            raise AssertionError(f"schema inválido: {schema_issue}")
        cls.example, example_issue = validate.read_json(
            ROOT / "exemplos" / "redacao-oficial" / "aula-00.json"
        )
        if cls.example is None or example_issue is not None:
            raise AssertionError(f"exemplo inválido: {example_issue}")

    def copy_example(self) -> dict[str, Any]:
        return copy.deepcopy(self.example)

    def codes(self, errors: list[validate.Issue]) -> set[str]:
        return {error.code for error in errors}

    def test_example_passes_schema(self) -> None:
        self.assertEqual(self.schema.validate(self.example), [])

    def test_example_passes_semantic_rules(self) -> None:
        self.assertEqual(validate.validate_document(self.example), [])

    def test_unknown_root_property_is_rejected(self) -> None:
        document = self.copy_example()
        document["unexpected"] = True
        errors = self.schema.validate(document)
        self.assertIn("schema", self.codes(errors))
        self.assertTrue(any("unexpected" in error.message for error in errors))

    def test_missing_required_property_is_rejected(self) -> None:
        document = self.copy_example()
        del document["resumo"]
        errors = self.schema.validate(document)
        self.assertTrue(any(error.path == "$.resumo" and error.code == "schema" for error in errors))

    def test_invalid_block_type_is_rejected(self) -> None:
        document = self.copy_example()
        document["secoes"][0]["blocos"][0]["tipo"] = "video"
        errors = self.schema.validate(document)
        self.assertIn("schema", self.codes(errors))

    def test_missing_block_text_is_rejected(self) -> None:
        document = self.copy_example()
        del document["secoes"][0]["blocos"][0]["texto"]
        errors = self.schema.validate(document)
        self.assertIn("schema", self.codes(errors))

    def test_section_number_must_be_sequential(self) -> None:
        document = self.copy_example()
        document["secoes"][2]["numero"] = 9
        errors = validate.validate_document(document)
        self.assertIn("section-number", self.codes(errors))

    def test_unknown_source_is_rejected(self) -> None:
        document = self.copy_example()
        document["secoes"][0]["fontes"] = ["fonte-inexistente"]
        errors = validate.validate_document(document)
        self.assertIn("unknown-source", self.codes(errors))

    def test_unknown_block_source_is_rejected(self) -> None:
        document = self.copy_example()
        document["secoes"][0]["blocos"][0]["fontes"] = ["fonte-inexistente"]
        errors = validate.validate_document(document)
        self.assertIn("unknown-source", self.codes(errors))

    def test_table_row_width_is_validated(self) -> None:
        document = self.copy_example()
        table = next(
            block
            for section in document["secoes"]
            for block in section["blocos"]
            if block["tipo"] == "tabela"
        )
        table["linhas"][0] = ["apenas uma célula"]
        errors = validate.validate_document(document)
        self.assertIn("table-row-width", self.codes(errors))

    def test_duplicate_section_id_is_rejected(self) -> None:
        document = self.copy_example()
        document["secoes"][1]["id"] = document["secoes"][0]["id"]
        errors = validate.validate_document(document)
        self.assertIn("duplicate-id", self.codes(errors))

    def test_forbidden_section_title_is_rejected(self) -> None:
        document = self.copy_example()
        document["secoes"][0]["titulo"] = "Questões comentadas"
        errors = validate.validate_document(document)
        self.assertIn("forbidden-section-title", self.codes(errors))

    def test_quiz_option_count_is_validated(self) -> None:
        document = self.copy_example()
        del document["quiz"]["questoes"][0]["opcoes"][0:3]
        errors = validate.validate_document(document)
        self.assertIn("quiz-option-count", self.codes(errors))

    def test_certo_errado_with_two_options_is_valid(self) -> None:
        document = self.copy_example()
        question = document["quiz"]["questoes"][0]
        question["opcoes"] = [
            {"texto": "Certo", "correta": True, "explicacao": "Está certo."},
            {"texto": "Errado", "correta": False, "explicacao": "Está errado."},
        ]
        errors = validate.validate_document(document)
        self.assertEqual(errors, [])
        self.assertEqual(self.schema.validate(document), [])

    def test_quiz_with_six_options_is_rejected(self) -> None:
        document = self.copy_example()
        question = document["quiz"]["questoes"][0]
        extra = dict(question["opcoes"][0])
        extra["texto"] = "Alternativa extra"
        extra["correta"] = False
        question["opcoes"].extend([dict(extra), dict(extra)])
        errors = validate.validate_document(document)
        self.assertIn("quiz-option-count", self.codes(errors))

    def test_topico_block_is_accepted(self) -> None:
        document = self.copy_example()
        document["secoes"][0]["blocos"].insert(
            0,
            {
                "tipo": "topico",
                "id": "topico-teste",
                "texto": "Assunto dentro da seção",
            },
        )
        self.assertEqual(self.schema.validate(document), [])
        self.assertEqual(validate.validate_document(document), [])

    def test_paragrafo_titulo_is_accepted(self) -> None:
        document = self.copy_example()
        document["secoes"][0]["blocos"][0]["titulo"] = "Título do parágrafo"
        self.assertEqual(self.schema.validate(document), [])
        self.assertEqual(validate.validate_document(document), [])

    def test_quiz_answer_count_is_validated(self) -> None:
        document = self.copy_example()
        for option in document["quiz"]["questoes"][0]["opcoes"]:
            option["correta"] = False
        errors = validate.validate_document(document)
        self.assertIn("quiz-answer-count", self.codes(errors))

    def test_quiz_duplicate_option_is_rejected(self) -> None:
        document = self.copy_example()
        question = document["quiz"]["questoes"][0]
        question["opcoes"][1]["texto"] = question["opcoes"][0]["texto"]
        errors = validate.validate_document(document)
        self.assertIn("quiz-duplicate-option", self.codes(errors))

    def test_quiz_unknown_section_is_rejected(self) -> None:
        document = self.copy_example()
        document["quiz"]["questoes"][0]["secao_id"] = "secao-inexistente"
        errors = validate.validate_document(document)
        self.assertIn("quiz-unknown-section", self.codes(errors))

    def test_quiz_unknown_source_is_rejected(self) -> None:
        document = self.copy_example()
        document["quiz"]["questoes"][0]["fonte_id"] = "fonte-inexistente"
        errors = validate.validate_document(document)
        self.assertIn("quiz-unknown-source", self.codes(errors))

    def test_incidence_weight_sum_is_validated(self) -> None:
        document = self.copy_example()
        document["incidencia"]["temas"] = [
            {"nome": "Tema A", "peso": 60, "secao_ids": ["o-que-e-redacao-oficial"]},
            {"nome": "Tema B", "peso": 60, "secao_ids": ["clareza-e-precisao"]},
        ]
        errors = validate.validate_document(document)
        self.assertIn("incidence-weight-sum", self.codes(errors))

    def test_incidence_unknown_section_is_rejected(self) -> None:
        document = self.copy_example()
        document["incidencia"]["temas"] = [
            {"nome": "Tema A", "peso": 100, "secao_ids": ["secao-inexistente"]}
        ]
        errors = validate.validate_document(document)
        self.assertIn("incidence-unknown-section", self.codes(errors))

    def test_incidence_duplicate_theme_is_rejected(self) -> None:
        document = self.copy_example()
        document["incidencia"]["temas"] = [
            {"nome": "Tema A", "peso": 50, "secao_ids": ["o-que-e-redacao-oficial"]},
            {"nome": "tema a", "peso": 50, "secao_ids": ["clareza-e-precisao"]},
        ]
        errors = validate.validate_document(document)
        self.assertIn("incidence-duplicate-theme", self.codes(errors))

    def test_review_date_order_is_validated(self) -> None:
        document = self.copy_example()
        document["revisao"]["proxima_em"] = "2020-01-01"
        errors = validate.validate_document(document)
        self.assertIn("review-date-order", self.codes(errors))

    def test_updated_date_before_created_date_is_rejected(self) -> None:
        document = self.copy_example()
        document["metadados"]["atualizado_em"] = "2020-01-01"
        errors = validate.validate_document(document)
        self.assertIn("date-order", self.codes(errors))

    def test_published_without_reviewer_is_rejected(self) -> None:
        document = self.copy_example()
        document["status"] = "publicado"
        document["metadados"]["revisores"] = []
        errors = validate.validate_document(document)
        self.assertIn("missing-reviewer", self.codes(errors))

    def test_published_with_noassertion_license_is_rejected(self) -> None:
        document = self.copy_example()
        document["status"] = "publicado"
        document["metadados"]["revisores"] = ["Pessoa Revisora"]
        document["metadados"]["licenca"] = "NOASSERTION"
        errors = validate.validate_document(document)
        self.assertIn("undefined-license", self.codes(errors))

    def test_duplicate_json_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"id": "a", "id": "b"}', encoding="utf-8")
            document, issue = validate.read_json(path)
        self.assertIsNone(document)
        self.assertIsNotNone(issue)
        assert issue is not None
        self.assertEqual(issue.code, "json")
        self.assertIn("duplicada", issue.message)

    def test_nan_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nan.json"
            path.write_text('{"value": NaN}', encoding="utf-8")
            document, issue = validate.read_json(path)
        self.assertIsNone(document)
        self.assertIsNotNone(issue)
        assert issue is not None
        self.assertEqual(issue.code, "json")

    def test_cli_validates_example_with_json(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                str(ROOT / "exemplos" / "redacao-oficial" / "aula-00.json"),
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["valid"])
        self.assertEqual(len(report["files"]), 1)
        self.assertTrue(report["files"][0]["valid"])

    def test_cli_reports_invalid_document(self) -> None:
        document = self.copy_example()
        document["secoes"][2]["numero"] = 9
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(MODULE_PATH), str(path), "--json"],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["valid"])
        self.assertEqual(report["files"][0]["errors"][0]["code"], "section-number")

    def test_cli_missing_path_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "nao-existe.json"
            result = subprocess.run(
                [sys.executable, str(MODULE_PATH), str(missing), "--json"],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["files"][0]["errors"][0]["code"], "missing-path")

    def test_cli_empty_directory_is_usage_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(MODULE_PATH), directory, "--json"],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 2, result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["valid"])

    def test_cli_invalid_schema_is_usage_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            schema = Path(directory) / "schema.json"
            schema.write_text("não é json", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "--schema",
                    str(schema),
                    str(ROOT / "exemplos" / "redacao-oficial" / "aula-00.json"),
                    "--json",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 2, result.stderr)
        report = json.loads(result.stdout)
        self.assertIn("schema_error", report)

    def test_cli_default_command(self) -> None:
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("aula-00.json", result.stdout)

    def test_cli_version(self) -> None:
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH), "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Hermes validator", result.stdout)


if __name__ == "__main__":
    unittest.main()
