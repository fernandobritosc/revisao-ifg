#!/usr/bin/env python3
"""Validador dos arquivos de aula do Hermes.

O Hermes guarda cada aula em JSON e usa JSON Schema 2020-12 como contrato
estrutural. Este validador usa apenas a biblioteca padrão do Python e cobre:

* o subconjunto de JSON Schema usado por ``schema/aula.schema.json``;
* referências cruzadas entre seções, blocos, fontes e quiz;
* numeração sequencial das seções;
* integridade das tabelas e das alternativas do quiz;
* pesos de incidência, datas de revisão e condições de publicação.

Uso:
    python validate.py
    python validate.py exemplos/redacao-oficial/aula-00.json --json
    python validate.py --schema schema/aula.schema.json exemplos/

Códigos de saída:
    0  todos os arquivos válidos
    1  ao menos um arquivo inválido ou ausente
    2  uso incorreto, esquema inválido ou nenhum arquivo encontrado
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
DEFAULT_SCHEMA_PATH = ROOT / "schema" / "aula.schema.json"
DEFAULT_INPUT_PATH = ROOT / "exemplos"
VALIDATOR_VERSION = "1.0.0"
SCHEMA_VERSION = "1.1.0"
EXIT_VALID = 0
EXIT_INVALID = 1
EXIT_USAGE = 2


class SchemaError(Exception):
    """Erro na estrutura do próprio JSON Schema."""


class DuplicateKeyError(ValueError):
    """Uma chave repetida foi encontrada em um objeto JSON."""


@dataclass(frozen=True)
class Issue:
    """Uma falha localizada em um documento."""

    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


def _reject_duplicate_keys(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    """Constrói um objeto JSON recusando chaves duplicadas."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"chave duplicada: {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"constante JSON não permitida: {value}")


def read_json(path: Path) -> tuple[Any | None, Issue | None]:
    """Lê UTF-8 com ou sem BOM, recusando NaN, Infinity e chaves duplicadas."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        return None, Issue("io", "$", f"{path}: não foi possível ler: {exc}")

    try:
        document = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        return None, Issue("json", "$", f"{path}: JSON inválido: {exc}")
    return document, None


class SchemaValidator:
    """Validador pequeno para o subconjunto de JSON Schema usado pelo Hermes.

    Suporta type, required, properties, additionalProperties, items, minItems,
    maxItems, uniqueItems, minLength, maxLength, pattern, format, enum, const,
    minimum, maximum, exclusiveMinimum, exclusiveMaximum, allOf, anyOf, oneOf,
    not, minProperties, maxProperties, propertyNames e $ref local.
    """

    def __init__(self, schema: dict[str, Any]):
        if not isinstance(schema, dict):
            raise SchemaError("o esquema precisa ser um objeto JSON")
        self.schema = schema

    def validate(self, value: Any) -> list[Issue]:
        errors: list[Issue] = []
        self._validate(value, self.schema, "$", errors, 0)
        return errors

    def _resolve_ref(self, reference: str) -> Any:
        if reference == "#":
            return self.schema
        if not reference.startswith("#/"):
            raise SchemaError(f"referência externa não suportada: {reference!r}")

        node: Any = self.schema
        for raw_token in reference[2:].split("/"):
            token = unquote(raw_token).replace("~1", "/").replace("~0", "~")
            if not isinstance(node, dict) or token not in node:
                raise SchemaError(f"referência inexistente no esquema: {reference!r}")
            node = node[token]
        return node

    def _validate(
        self,
        value: Any,
        schema: Any,
        path: str,
        errors: list[Issue],
        depth: int,
    ) -> None:
        if depth > 100:
            raise SchemaError("profundidade máxima de referências excedida")
        if schema is True:
            return
        if schema is False:
            errors.append(Issue("schema", path, "valor não permitido pelo esquema"))
            return
        if not isinstance(schema, dict):
            raise SchemaError("subschema inválido: esperado objeto ou booleano")

        reference = schema.get("$ref")
        if isinstance(reference, str):
            self._validate(value, self._resolve_ref(reference), path, errors, depth + 1)

        expected_types = schema.get("type")
        if expected_types is not None:
            types = [expected_types] if isinstance(expected_types, str) else expected_types
            if isinstance(types, list) and not any(_has_type(value, item) for item in types):
                expected = " | ".join(str(item) for item in types)
                actual = _type_name(value)
                errors.append(
                    Issue("schema", path, f"tipo esperado: {expected}; recebido: {actual}")
                )

        if "enum" in schema and not any(_json_equal(value, item) for item in schema["enum"]):
            errors.append(
                Issue("schema", path, f"valor fora das opções permitidas: {schema['enum']!r}")
            )
        if "const" in schema and not _json_equal(value, schema["const"]):
            errors.append(Issue("schema", path, f"valor deve ser igual a {schema['const']!r}"))

        if isinstance(value, dict):
            for key in schema.get("required", []):
                if key not in value:
                    errors.append(Issue("schema", f"{path}.{key}", "campo obrigatório ausente"))

            properties = schema.get("properties", {})
            if isinstance(properties, dict):
                for key, subschema in properties.items():
                    if key in value:
                        self._validate(
                            value[key], subschema, _child_path(path, key), errors, depth + 1
                        )

            if "additionalProperties" in schema:
                known = set(properties) if isinstance(properties, dict) else set()
                extra = sorted(set(value) - known)
                additional = schema["additionalProperties"]
                if additional is False and extra:
                    errors.append(
                        Issue(
                            "schema",
                            path,
                            "propriedades não permitidas: " + ", ".join(extra),
                        )
                    )
                elif additional is not True:
                    for key in extra:
                        self._validate(
                            value[key], additional, _child_path(path, key), errors, depth + 1
                        )

            minimum_properties = schema.get("minProperties")
            if isinstance(minimum_properties, int) and len(value) < minimum_properties:
                errors.append(
                    Issue(
                        "schema",
                        path,
                        f"objeto precisa ter ao menos {minimum_properties} propriedade(s)",
                    )
                )
            maximum_properties = schema.get("maxProperties")
            if isinstance(maximum_properties, int) and len(value) > maximum_properties:
                errors.append(
                    Issue(
                        "schema",
                        path,
                        f"objeto aceita no máximo {maximum_properties} propriedade(s)",
                    )
                )

            property_names = schema.get("propertyNames")
            if property_names is not None:
                for key in value:
                    self._validate(key, property_names, f"{path}.{key}", errors, depth + 1)

        if isinstance(value, list):
            items = schema.get("items")
            if items is not None:
                for index, item in enumerate(value):
                    self._validate(item, items, f"{path}[{index}]", errors, depth + 1)

            minimum_items = schema.get("minItems")
            if isinstance(minimum_items, int) and len(value) < minimum_items:
                errors.append(
                    Issue("schema", path, f"lista precisa ter ao menos {minimum_items} item(ns)")
                )
            maximum_items = schema.get("maxItems")
            if isinstance(maximum_items, int) and len(value) > maximum_items:
                errors.append(
                    Issue("schema", path, f"lista aceita no máximo {maximum_items} item(ns)")
                )
            if schema.get("uniqueItems") is True and not _unique_items(value):
                errors.append(Issue("schema", path, "lista não pode conter itens duplicados"))

        if isinstance(value, str):
            minimum_length = schema.get("minLength")
            if isinstance(minimum_length, int) and len(value) < minimum_length:
                errors.append(
                    Issue(
                        "schema",
                        path,
                        f"texto precisa ter ao menos {minimum_length} caractere(s)",
                    )
                )
            maximum_length = schema.get("maxLength")
            if isinstance(maximum_length, int) and len(value) > maximum_length:
                errors.append(
                    Issue(
                        "schema",
                        path,
                        f"texto aceita no máximo {maximum_length} caractere(s)",
                    )
                )

            pattern = schema.get("pattern")
            if isinstance(pattern, str):
                try:
                    if re.search(pattern, value) is None:
                        errors.append(
                            Issue("schema", path, f"valor não corresponde ao padrão {pattern!r}")
                        )
                except re.error as exc:
                    raise SchemaError(
                        f"padrão de expressão regular inválido {pattern!r}: {exc}"
                    ) from exc

            format_name = schema.get("format")
            if isinstance(format_name, str) and not _has_format(value, format_name):
                errors.append(Issue("schema", path, f"valor não é um {format_name!r} válido"))

        if _is_number(value):
            if "minimum" in schema and value < schema["minimum"]:
                errors.append(Issue("schema", path, f"valor deve ser >= {schema['minimum']!r}"))
            if "maximum" in schema and value > schema["maximum"]:
                errors.append(Issue("schema", path, f"valor deve ser <= {schema['maximum']!r}"))
            if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
                errors.append(
                    Issue("schema", path, f"valor deve ser > {schema['exclusiveMinimum']!r}")
                )
            if "exclusiveMaximum" in schema and value >= schema["exclusiveMaximum"]:
                errors.append(
                    Issue("schema", path, f"valor deve ser < {schema['exclusiveMaximum']!r}")
                )

        for subschema in schema.get("allOf", []):
            self._validate(value, subschema, path, errors, depth + 1)

        any_of = schema.get("anyOf")
        if isinstance(any_of, list):
            if not any(self._matches(value, item, depth + 1) for item in any_of):
                errors.append(
                    Issue("schema", path, "valor não corresponde a nenhuma alternativa de anyOf")
                )

        one_of = schema.get("oneOf")
        if isinstance(one_of, list):
            matches = sum(1 for item in one_of if self._matches(value, item, depth + 1))
            if matches != 1:
                errors.append(
                    Issue(
                        "schema",
                        path,
                        "valor precisa corresponder a exatamente uma alternativa de oneOf",
                    )
                )

        if "not" in schema and self._matches(value, schema["not"], depth + 1):
            errors.append(Issue("schema", path, "valor não deveria corresponder ao esquema negado"))

    def _matches(self, value: Any, schema: Any, depth: int) -> bool:
        local_errors: list[Issue] = []
        self._validate(value, schema, "$", local_errors, depth)
        return not local_errors


def _has_type(value: Any, type_name: str) -> bool:
    if type_name == "object":
        return isinstance(value, dict)
    if type_name == "array":
        return isinstance(value, list)
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "number":
        return _is_number(value)
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "null":
        return value is None
    return True


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _json_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) != isinstance(right, bool):
        return False
    return left == right


def _unique_items(items: list[Any]) -> bool:
    seen: set[str] = set()
    for item in items:
        try:
            key = json.dumps(item, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        except (TypeError, ValueError):
            return False
        if key in seen:
            return False
        seen.add(key)
    return True


def _child_path(path: str, key: str) -> str:
    return f"{path}.{key}"


def _has_format(value: str, format_name: str) -> bool:
    if format_name == "date":
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
            return False
        try:
            date.fromisoformat(value)
        except ValueError:
            return False
        return True

    if format_name == "date-time":
        text = value[:-1] + "+00:00" if value.endswith("Z") else value
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return False
        return parsed.tzinfo is not None

    if format_name == "uri":
        if any(character.isspace() for character in value):
            return False
        try:
            parts = urlsplit(value)
        except ValueError:
            return False
        return bool(parts.scheme)

    if format_name == "email":
        return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value) is not None

    if format_name == "uuid":
        return (
            re.fullmatch(
                r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}",
                value,
            )
            is not None
        )

    return True


def _ids(items: Any) -> set[str]:
    if not isinstance(items, list):
        return set()
    return {
        item.get("id")
        for item in items
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def _date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _duplicate_id_errors(document: dict[str, Any]) -> list[Issue]:
    errors: list[Issue] = []

    def check(items: Any, path_prefix: str, label: str) -> None:
        if not isinstance(items, list):
            return
        seen: dict[str, int] = {}
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            identifier = item.get("id")
            if not isinstance(identifier, str):
                continue
            if identifier in seen:
                first = seen[identifier]
                errors.append(
                    Issue(
                        "duplicate-id",
                        f"{path_prefix}[{index}].id",
                        f"{label} com id {identifier!r} duplicado; primeira ocorrência em [{first}]",
                    )
                )
            else:
                seen[identifier] = index

    check(document.get("fontes"), "$.fontes", "fonte")
    check(document.get("secoes"), "$.secoes", "seção")

    sections = document.get("secoes")
    if isinstance(sections, list):
        seen_blocks: dict[str, str] = {}
        for section_index, section in enumerate(sections):
            if not isinstance(section, dict):
                continue
            blocks = section.get("blocos")
            if not isinstance(blocks, list):
                continue
            for block_index, block in enumerate(blocks):
                if not isinstance(block, dict):
                    continue
                identifier = block.get("id")
                if not isinstance(identifier, str):
                    continue
                path = f"$.secoes[{section_index}].blocos[{block_index}].id"
                if identifier in seen_blocks:
                    errors.append(
                        Issue(
                            "duplicate-id",
                            path,
                            f"bloco com id {identifier!r} duplicado; primeira ocorrência em {seen_blocks[identifier]}",
                        )
                    )
                else:
                    seen_blocks[identifier] = path

    quiz = document.get("quiz")
    if isinstance(quiz, dict):
        check(quiz.get("questoes"), "$.quiz.questoes", "questão")
    return errors


def _structure_errors(document: dict[str, Any]) -> list[Issue]:
    errors: list[Issue] = []
    sections = document.get("secoes")
    if not isinstance(sections, list):
        return errors

    for section_index, section in enumerate(sections):
        if not isinstance(section, dict):
            continue
        number = section.get("numero")
        if isinstance(number, int) and not isinstance(number, bool):
            expected = section_index + 1
            if number != expected:
                errors.append(
                    Issue(
                        "section-number",
                        f"$.secoes[{section_index}].numero",
                        f"seção com número {number}; esperado {expected} para manter a sequência",
                    )
                )

        title = section.get("titulo")
        if isinstance(title, str) and title.strip().casefold() in {
            "questões comentadas",
            "gabarito final",
        }:
            errors.append(
                Issue(
                    "forbidden-section-title",
                    f"$.secoes[{section_index}].titulo",
                    "questões comentadas e gabarito pertencem ao quiz, não ao corpo da aula",
                )
            )

        blocks = section.get("blocos")
        if not isinstance(blocks, list):
            continue
        for block_index, block in enumerate(blocks):
            if not isinstance(block, dict) or block.get("tipo") != "tabela":
                continue
            columns = block.get("colunas")
            rows = block.get("linhas")
            if not isinstance(columns, list) or not isinstance(rows, list):
                continue
            width = len(columns)
            for row_index, row in enumerate(rows):
                if isinstance(row, list) and len(row) != width:
                    errors.append(
                        Issue(
                            "table-row-width",
                            f"$.secoes[{section_index}].blocos[{block_index}].linhas[{row_index}]",
                            f"linha tem {len(row)} célula(s); esperado {width}",
                        )
                    )
    return errors


def _reference_errors(document: dict[str, Any]) -> list[Issue]:
    errors: list[Issue] = []
    source_ids = _ids(document.get("fontes"))
    section_ids = _ids(document.get("secoes"))
    sections = document.get("secoes")

    if isinstance(sections, list):
        for section_index, section in enumerate(sections):
            if not isinstance(section, dict):
                continue
            section_sources = section.get("fontes")
            for source_id in section_sources if isinstance(section_sources, list) else []:
                if isinstance(source_id, str) and source_id not in source_ids:
                    errors.append(
                        Issue(
                            "unknown-source",
                            f"$.secoes[{section_index}].fontes",
                            f"fonte {source_id!r} não existe em $.fontes",
                        )
                    )
            blocks = section.get("blocos")
            if not isinstance(blocks, list):
                continue
            for block_index, block in enumerate(blocks):
                if not isinstance(block, dict):
                    continue
                block_sources = block.get("fontes")
                for source_id in block_sources if isinstance(block_sources, list) else []:
                    if isinstance(source_id, str) and source_id not in source_ids:
                        errors.append(
                            Issue(
                                "unknown-source",
                                f"$.secoes[{section_index}].blocos[{block_index}].fontes",
                                f"fonte {source_id!r} não existe em $.fontes",
                            )
                        )

    quiz = document.get("quiz")
    if isinstance(quiz, dict):
        questions = quiz.get("questoes")
        if isinstance(questions, list):
            for question_index, question in enumerate(questions):
                if not isinstance(question, dict):
                    continue
                section_id = question.get("secao_id")
                if isinstance(section_id, str) and section_id not in section_ids:
                    errors.append(
                        Issue(
                            "quiz-unknown-section",
                            f"$.quiz.questoes[{question_index}].secao_id",
                            f"seção {section_id!r} não existe em $.secoes",
                        )
                    )
                source_id = question.get("fonte_id")
                if isinstance(source_id, str) and source_id not in source_ids:
                    errors.append(
                        Issue(
                            "quiz-unknown-source",
                            f"$.quiz.questoes[{question_index}].fonte_id",
                            f"fonte {source_id!r} não existe em $.fontes",
                        )
                    )

    incidence = document.get("incidencia")
    if isinstance(incidence, dict):
        themes = incidence.get("temas")
        if isinstance(themes, list):
            for theme_index, theme in enumerate(themes):
                if not isinstance(theme, dict):
                    continue
                theme_sections = theme.get("secao_ids")
                for section_id in theme_sections if isinstance(theme_sections, list) else []:
                    if isinstance(section_id, str) and section_id not in section_ids:
                        errors.append(
                            Issue(
                                "incidence-unknown-section",
                                f"$.incidencia.temas[{theme_index}].secao_ids",
                                f"seção {section_id!r} não existe em $.secoes",
                            )
                        )
    return errors


def _quiz_errors(document: dict[str, Any]) -> list[Issue]:
    errors: list[Issue] = []
    quiz = document.get("quiz")
    if not isinstance(quiz, dict):
        return errors
    questions = quiz.get("questoes")
    if not isinstance(questions, list):
        return errors

    for question_index, question in enumerate(questions):
        if not isinstance(question, dict):
            continue
        options = question.get("opcoes")
        if not isinstance(options, list):
            continue
        if not 2 <= len(options) <= 5:
            errors.append(
                Issue(
                    "quiz-option-count",
                    f"$.quiz.questoes[{question_index}].opcoes",
                    f"a questão precisa ter entre 2 e 5 alternativas; encontradas {len(options)}",
                )
            )

        correct_count = sum(
            1
            for option in options
            if isinstance(option, dict) and option.get("correta") is True
        )
        if correct_count != 1:
            errors.append(
                Issue(
                    "quiz-answer-count",
                    f"$.quiz.questoes[{question_index}].opcoes",
                    f"a questão precisa ter exatamente 1 alternativa correta; encontradas {correct_count}",
                )
            )

        seen_texts: set[str] = set()
        for option_index, option in enumerate(options):
            if not isinstance(option, dict):
                continue
            explanation = option.get("explicacao")
            if not isinstance(explanation, str) or not explanation.strip():
                errors.append(
                    Issue(
                        "quiz-feedback-missing",
                        f"$.quiz.questoes[{question_index}].opcoes[{option_index}].explicacao",
                        "toda alternativa precisa de explicação, inclusive a correta",
                    )
                )
            text = option.get("texto")
            if isinstance(text, str):
                normalized = " ".join(text.strip().casefold().split())
                if normalized in seen_texts:
                    errors.append(
                        Issue(
                            "quiz-duplicate-option",
                            f"$.quiz.questoes[{question_index}].opcoes[{option_index}].texto",
                            "alternativas duplicadas não são permitidas",
                        )
                    )
                seen_texts.add(normalized)
    return errors


def _incidence_errors(document: dict[str, Any]) -> list[Issue]:
    incidence = document.get("incidencia")
    if not isinstance(incidence, dict):
        return []
    themes = incidence.get("temas")
    if not isinstance(themes, list) or not themes:
        return []

    errors: list[Issue] = []
    weights: list[int] = []
    names: set[str] = set()
    for index, theme in enumerate(themes):
        if not isinstance(theme, dict):
            continue
        weight = theme.get("peso")
        if isinstance(weight, int) and not isinstance(weight, bool):
            weights.append(weight)
        name = theme.get("nome")
        if isinstance(name, str):
            normalized = " ".join(name.strip().casefold().split())
            if normalized in names:
                errors.append(
                    Issue(
                        "incidence-duplicate-theme",
                        f"$.incidencia.temas[{index}].nome",
                        f"tema de incidência {name!r} duplicado",
                    )
                )
            names.add(normalized)

    if len(weights) == len(themes) and sum(weights) != 100:
        errors.append(
            Issue(
                "incidence-weight-sum",
                "$.incidencia.temas",
                f"os pesos de incidência somam {sum(weights)}, mas devem somar 100",
            )
        )
    return errors


def _review_errors(document: dict[str, Any]) -> list[Issue]:
    errors: list[Issue] = []
    review = document.get("revisao")
    metadata = document.get("metadados")
    if not isinstance(review, dict) or not isinstance(metadata, dict):
        return errors

    updated = _date(metadata.get("atualizado_em"))
    next_review = _date(review.get("proxima_em"))
    last_review = _date(review.get("ultima_em"))

    if updated and next_review and next_review < updated:
        errors.append(
            Issue(
                "review-date-order",
                "$.revisao.proxima_em",
                "a próxima revisão não pode ser anterior à atualização da aula",
            )
        )
    if last_review and next_review and last_review > next_review:
        errors.append(
            Issue(
                "review-date-order",
                "$.revisao.ultima_em",
                "a última revisão não pode ser posterior à próxima revisão",
            )
        )
    return errors


def _metadata_errors(document: dict[str, Any]) -> list[Issue]:
    errors: list[Issue] = []
    metadata = document.get("metadados")
    if not isinstance(metadata, dict):
        return errors

    created = _date(metadata.get("criado_em"))
    updated = _date(metadata.get("atualizado_em"))
    if created and updated and updated < created:
        errors.append(
            Issue(
                "date-order",
                "$.metadados.atualizado_em",
                "atualizado_em não pode ser anterior a criado_em",
            )
        )

    if document.get("status") == "publicado":
        reviewers = metadata.get("revisores")
        if isinstance(reviewers, list) and not reviewers:
            errors.append(
                Issue(
                    "missing-reviewer",
                    "$.metadados.revisores",
                    "uma aula publicada precisa de ao menos um revisor identificado",
                )
            )
        if metadata.get("licenca") == "NOASSERTION":
            errors.append(
                Issue(
                    "undefined-license",
                    "$.metadados.licenca",
                    "uma aula publicada precisa de uma licença definida",
                )
            )
    return errors


def validate_document(document: Any) -> list[Issue]:
    """Valida as regras semânticas de uma aula já parseada."""
    if not isinstance(document, dict):
        return []
    errors: list[Issue] = []
    errors.extend(_duplicate_id_errors(document))
    errors.extend(_structure_errors(document))
    errors.extend(_reference_errors(document))
    errors.extend(_quiz_errors(document))
    errors.extend(_incidence_errors(document))
    errors.extend(_review_errors(document))
    errors.extend(_metadata_errors(document))
    return errors


def load_schema(path: Path) -> tuple[SchemaValidator | None, Issue | None]:
    schema, issue = read_json(path)
    if issue is not None:
        return None, issue
    try:
        return SchemaValidator(schema), None
    except SchemaError as exc:
        return None, Issue("schema-error", str(path), str(exc))


def _iter_json_files(directory: Path) -> Iterator[Path]:
    for path in sorted(directory.rglob("*.json")):
        if path.is_file():
            yield path


def _collect_inputs(paths: Iterable[Path]) -> tuple[list[Path], list[Path]]:
    files: list[Path] = []
    missing: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        if path.is_dir():
            candidates = _iter_json_files(path)
        elif path.is_file():
            candidates = iter([path])
        else:
            missing.append(path)
            continue
        for candidate in candidates:
            try:
                resolved = candidate.resolve()
            except OSError:
                resolved = candidate
            if resolved not in seen:
                seen.add(resolved)
                files.append(candidate)
    return files, missing


def validate_path(path: Path, validator: SchemaValidator) -> dict[str, Any]:
    document, issue = read_json(path)
    if issue is not None:
        errors = [issue]
    else:
        errors = validator.validate(document)
        errors.extend(validate_document(document))
    return {
        "path": str(path),
        "valid": not errors,
        "errors": [error.as_dict() for error in errors],
    }


def _print_human(reports: Sequence[dict[str, Any]]) -> None:
    for report in reports:
        if report["valid"]:
            print(f"OK      {report['path']}")
            continue
        print(f"FALHOU  {report['path']}")
        for error in report["errors"]:
            print(f"        [{error['code']}] {error['path']}: {error['message']}")
    valid_count = sum(1 for report in reports if report["valid"])
    invalid_count = len(reports) - valid_count
    print(f"\n{len(reports)} arquivo(s): {valid_count} válido(s), {invalid_count} com erro.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Valida aulas do Hermes contra o schema e as regras semânticas.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="arquivos ou diretórios .json; diretórios são lidos recursivamente (padrão: exemplos/)",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA_PATH,
        help=f"JSON Schema alternativo (padrão: {DEFAULT_SCHEMA_PATH})",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="imprime um relatório JSON em vez do formato legível",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Hermes validator {VALIDATOR_VERSION} (schema {SCHEMA_VERSION})",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validator, schema_issue = load_schema(args.schema)
    if validator is None:
        assert schema_issue is not None
        if args.as_json:
            print(
                json.dumps(
                    {
                        "valid": False,
                        "schema": str(args.schema),
                        "schema_error": schema_issue.as_dict(),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(f"Erro no esquema: {schema_issue.message}", file=sys.stderr)
        return EXIT_USAGE

    input_paths = list(args.paths) or [DEFAULT_INPUT_PATH]
    files, missing = _collect_inputs(input_paths)
    if not files and not missing:
        message = "Nenhum arquivo JSON encontrado; informe um arquivo ou diretório."
        if args.as_json:
            print(json.dumps({"valid": False, "error": message}, ensure_ascii=False, indent=2))
        else:
            print(f"Erro: {message}", file=sys.stderr)
        return EXIT_USAGE

    reports: list[dict[str, Any]] = []
    for path in missing:
        reports.append(
            {
                "path": str(path),
                "valid": False,
                "errors": [
                    {
                        "code": "missing-path",
                        "path": "$",
                        "message": "arquivo ou diretório não encontrado",
                    }
                ],
            }
        )
    for path in files:
        reports.append(validate_path(path, validator))

    valid = all(report["valid"] for report in reports)
    if args.as_json:
        print(
            json.dumps(
                {
                    "valid": valid,
                    "schema": str(args.schema),
                    "validator_version": VALIDATOR_VERSION,
                    "schema_version": SCHEMA_VERSION,
                    "files": reports,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        _print_human(reports)
    return EXIT_VALID if valid else EXIT_INVALID


if __name__ == "__main__":
    raise SystemExit(main())
