"""Schema and semantic validation of registry sources."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from .loader import RegistrySources

ERROR = "error"
WARNING = "warning"

# Constructs Python accepts but ECMAScript (browser) regexps do not.
_PYTHON_ONLY_RE = re.compile(r"\(\?P[<=]|\\[AZ]|\(\?[aiLmsux]+\)|\(\?#")


@dataclass(frozen=True)
class Issue:
    level: str
    path: str
    id: str
    message: str

    def __str__(self) -> str:
        return f"{self.level.upper()}: {self.path} [{self.id}] {self.message}"


@dataclass
class ValidationResult:
    issues: list[Issue]

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.level == ERROR]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.level == WARNING]

    @property
    def ok(self) -> bool:
        return not self.errors


def _schema_issues(sources: RegistrySources, schema_dir: Path) -> list[Issue]:
    from cerberus import Validator

    issues = []
    for schema_name, records in (
        ("datatype.json", sources.datatypes),
        ("tool.json", sources.tools),
    ):
        with open(schema_dir / schema_name, encoding="utf-8") as handle:
            validator = Validator(json.load(handle))
        for rec in records:
            if not validator.validate(rec.data):
                issues.append(Issue(ERROR, rec.relpath, rec.id, f"schema: {validator.errors}"))
    return issues


def _ref_issues(sources: RegistrySources) -> list[Issue]:
    issues = []
    references = (
        ("categories", sources.categories),
        ("country", sources.countries),
        ("langs", sources.langs),
    )
    for rec in sources.datatypes:
        for field_name, reference in references:
            for raw in rec.data.get(field_name) or []:
                if str(raw).strip() not in reference:
                    issues.append(
                        Issue(ERROR, rec.relpath, rec.id, f"unknown {field_name} id '{raw}'")
                    )
    return issues


def _id_issues(sources: RegistrySources) -> list[Issue]:
    issues = []
    seen: dict[str, list[str]] = defaultdict(list)
    for rec in [*sources.datatypes, *sources.tools]:
        seen[rec.id].append(rec.relpath)
    for rid, paths in sorted(seen.items()):
        if len(paths) > 1:
            issues.append(Issue(ERROR, paths[0], rid, f"duplicate id, also in {paths[1:]}"))

    datatype_ids = {rec.id for rec in sources.datatypes}
    for rec in sources.datatypes:
        semantic_type = rec.data.get("semantic_type")
        if semantic_type is not None and str(semantic_type) not in datatype_ids:
            issues.append(
                Issue(ERROR, rec.relpath, rec.id, f"unknown semantic_type '{semantic_type}'")
            )
        parent = rec.data.get("parent")
        parent_id = parent.get("type") if isinstance(parent, dict) else parent
        if parent_id is not None and str(parent_id) not in datatype_ids:
            issues.append(Issue(ERROR, rec.relpath, rec.id, f"unknown parent '{parent_id}'"))
        stem = Path(rec.relpath).stem
        if stem != rec.id:
            issues.append(
                Issue(WARNING, rec.relpath, rec.id, f"file name should be '{rec.id}.yaml'")
            )
    for rec in sources.tools:
        for supported in rec.data.get("supported_types") or []:
            if str(supported) not in datatype_ids:
                issues.append(
                    Issue(ERROR, rec.relpath, rec.id, f"unknown supported_type '{supported}'")
                )
    return issues


def _location_issues(sources: RegistrySources) -> list[Issue]:
    issues = []
    for rec in sources.datatypes:
        parts = Path(rec.relpath).parts  # ('datatypes', '<CC|any>', ...)
        if len(parts) < 3:
            continue
        top = parts[1]
        countries = [str(c).strip().upper() for c in rec.data.get("country") or []]
        if top == "any":
            if len(countries) == 1:
                issues.append(
                    Issue(
                        ERROR,
                        rec.relpath,
                        rec.id,
                        f"record in any/ has a single country {countries}; "
                        f"move it to datatypes/{countries[0]}/ or drop the country",
                    )
                )
        elif top.upper() not in countries:
            issues.append(
                Issue(
                    ERROR,
                    rec.relpath,
                    rec.id,
                    f"record in datatypes/{top}/ must list '{top.upper()}' in country, "
                    f"has {countries}",
                )
            )
    return issues


def _regexp_issues(sources: RegistrySources) -> list[Issue]:
    issues = []
    for rec in sources.datatypes:
        pattern = rec.data.get("regexp")
        if not pattern:
            continue
        pattern = str(pattern)
        try:
            compiled = re.compile(pattern)
        except re.error as exc:
            issues.append(Issue(ERROR, rec.relpath, rec.id, f"regexp does not compile: {exc}"))
            continue
        if not (pattern.startswith("^") and pattern.endswith("$")):
            issues.append(Issue(WARNING, rec.relpath, rec.id, "regexp is not anchored (^...$)"))
        if _PYTHON_ONLY_RE.search(pattern):
            issues.append(Issue(WARNING, rec.relpath, rec.id, "regexp uses Python-only syntax"))
        for example in rec.data.get("examples") or []:
            if not isinstance(example, dict) or "value" not in example:
                continue
            value = str(example["value"])
            valid = example.get("valid", True) is not False
            matched = compiled.search(value) is not None
            if valid and not matched:
                issues.append(
                    Issue(
                        ERROR,
                        rec.relpath,
                        rec.id,
                        f"example '{value}' does not match regexp {pattern!r}",
                    )
                )
            elif not valid and matched and not rec.data.get("checksum"):
                issues.append(
                    Issue(
                        ERROR,
                        rec.relpath,
                        rec.id,
                        f"negative example '{value}' matches regexp {pattern!r}",
                    )
                )
    return issues


def validate(sources: RegistrySources, schema_dir: Path | None = None) -> ValidationResult:
    schema_dir = schema_dir or sources.data_dir / "schemes"
    issues = [Issue(ERROR, path, "-", message) for path, message in sources.load_errors]
    issues += _schema_issues(sources, schema_dir)
    issues += _ref_issues(sources)
    issues += _id_issues(sources)
    issues += _location_issues(sources)
    issues += _regexp_issues(sources)
    return ValidationResult(issues=issues)
