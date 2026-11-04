"""Schema and semantic validation of registry sources."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .loader import RegistrySources

ERROR = "error"
WARNING = "warning"

# Constructs Python accepts but ECMAScript (browser) regexps do not.
_PYTHON_ONLY_RE = re.compile(r"\(\?P[<=]|\\[AZ]|\(\?[aiLmsux]+\)|\(\?#")

# Opcodes that only Python 3.11+ understands (possessive quantifiers such as
# ``\d{1,4}+`` and atomic groups ``(?>...)``). Consumers run older Pythons and
# browsers, so these are errors even when the local interpreter accepts them.
_PY311_ONLY_OPCODES = {"POSSESSIVE_REPEAT", "ATOMIC_GROUP"}


def _looks_like_placeholder(value: str) -> bool:
    """'0000', '1234567890', 'XXXXX': values that only show a format."""
    compact = re.sub(r"[\s.\-/]", "", value)
    if len(compact) < 4:
        return False
    if len(set(compact.upper())) == 1:
        return True
    digits = "01234567890123456789"
    return compact.isdigit() and len(compact) >= 6 and compact in digits


def _uses_py311_only_syntax(pattern: str) -> bool:
    try:
        from re import _parser  # Python 3.11+
    except ImportError:  # Python 3.10: such patterns already fail to compile
        return False

    def walk(node) -> bool:
        if isinstance(node, _parser.SubPattern):
            return any(str(op) in _PY311_ONLY_OPCODES or walk(av) for op, av in node.data)
        if isinstance(node, (list, tuple)):
            return any(walk(item) for item in node)
        return False

    return walk(_parser.parse(pattern))


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


def default_schema_dir(data_dir: Path) -> Path:
    return Path(data_dir).resolve().parent / "schema"


def load_schema_validators(schema_dir: Path) -> dict[str, Any]:
    """JSON Schema (2020-12) validators for 'datatype', 'pattern' and 'tool' records."""
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource

    schemas = {}
    registry = Registry()
    for name in ("datatype", "pattern", "tool"):
        with open(Path(schema_dir) / f"{name}.schema.json", encoding="utf-8") as handle:
            schema = json.load(handle)
        schemas[name] = schema
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    return {
        name: Draft202012Validator(schema, registry=registry) for name, schema in schemas.items()
    }


def _schema_issues(sources: RegistrySources, schema_dir: Path) -> list[Issue]:
    validators = load_schema_validators(schema_dir)
    issues = []
    tool_records = {id(rec) for rec in sources.tools}
    for rec in [*sources.datatypes, *sources.tools]:
        if id(rec) in tool_records:
            kind = "tool"
        else:
            kind = "pattern" if "semantic_type" in rec.data else "datatype"
        for error in sorted(validators[kind].iter_errors(rec.data), key=lambda e: list(e.path)):
            where = ".".join(str(p) for p in error.absolute_path) or "(record)"
            issues.append(Issue(ERROR, rec.relpath, rec.id, f"schema: {where}: {error.message}"))
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
    for rec in sources.datatypes:
        for alias in rec.data.get("aliases") or []:
            seen[str(alias)].append(f"{rec.relpath} (alias)")
    for rid, paths in sorted(seen.items()):
        if len(paths) > 1:
            issues.append(
                Issue(ERROR, paths[0], rid, f"duplicate id or alias, also in {paths[1:]}")
            )

    datatype_ids = {rec.id for rec in sources.datatypes}
    for rec in sources.datatypes:
        for field_name in ("semantic_type", "parent", "replaced_by"):
            value = rec.data.get(field_name)
            target = value.get("type") if isinstance(value, dict) else value
            if target is not None and str(target) not in datatype_ids:
                issues.append(Issue(ERROR, rec.relpath, rec.id, f"unknown {field_name} '{target}'"))
    for rec in [*sources.datatypes, *sources.tools]:
        if Path(rec.relpath).stem != rec.id:
            issues.append(Issue(ERROR, rec.relpath, rec.id, f"file name must be '{rec.id}.yaml'"))
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
        if compiled.fullmatch("") is not None:
            issues.append(Issue(ERROR, rec.relpath, rec.id, "regexp matches an empty string"))
        if _uses_py311_only_syntax(pattern):
            issues.append(
                Issue(
                    ERROR,
                    rec.relpath,
                    rec.id,
                    "regexp uses possessive quantifiers or atomic groups "
                    "(Python 3.11+ only, not portable)",
                )
            )
        if not (pattern.startswith("^") and pattern.endswith("$")):
            issues.append(Issue(WARNING, rec.relpath, rec.id, "regexp is not anchored (^...$)"))
        if _PYTHON_ONLY_RE.search(pattern):
            issues.append(Issue(WARNING, rec.relpath, rec.id, "regexp uses Python-only syntax"))
        for example in rec.data.get("examples") or []:
            if not isinstance(example, dict) or "value" not in example:
                continue
            value = str(example["value"])
            if _looks_like_placeholder(value):
                issues.append(
                    Issue(
                        WARNING, rec.relpath, rec.id, f"example '{value}' looks like a placeholder"
                    )
                )
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


def _checksum_issues(sources: RegistrySources) -> list[Issue]:
    """A named checksum must exist; examples must agree with it."""
    from .checksums import ALGORITHMS

    issues = []
    for rec in sources.datatypes:
        algorithm = rec.data.get("checksum")
        if not algorithm:
            continue
        if algorithm not in ALGORITHMS:
            known = ", ".join(sorted(ALGORITHMS))
            issues.append(
                Issue(
                    ERROR, rec.relpath, rec.id, f"unknown checksum '{algorithm}' (known: {known})"
                )
            )
            continue
        pattern = rec.data.get("regexp")
        compiled = re.compile(str(pattern)) if pattern else None
        for example in rec.data.get("examples") or []:
            if not isinstance(example, dict) or "value" not in example:
                continue
            value = str(example["value"])
            passes = ALGORITHMS[algorithm](value)
            if example.get("valid", True) is not False:
                if not passes:
                    issues.append(
                        Issue(
                            ERROR,
                            rec.relpath,
                            rec.id,
                            f"example '{value}' fails the {algorithm} check digit",
                        )
                    )
            elif passes and (compiled is None or compiled.search(value)):
                issues.append(
                    Issue(
                        ERROR,
                        rec.relpath,
                        rec.id,
                        f"negative example '{value}' passes both the regexp and {algorithm}",
                    )
                )
    return issues


def _coverage_issues(sources: RegistrySources) -> list[Issue]:
    """The committed rule coverage must come from the ref pinned in ecosystem.lock."""
    from .coverage import COVERAGE_FILE, load_coverage, read_lock

    coverage = load_coverage(sources.data_dir)
    if coverage is None:
        return []
    locked = read_lock(sources.data_dir).get("metacrafter-rules", {}).get("ref")
    actual = (coverage.get("source") or {}).get("ref")
    if locked != actual:
        return [
            Issue(
                ERROR,
                str(COVERAGE_FILE),
                "-",
                f"coverage was generated from metacrafter-rules {actual}, "
                f"but ecosystem.lock pins {locked}",
            )
        ]
    return []


def validate(sources: RegistrySources, schema_dir: Path | None = None) -> ValidationResult:
    schema_dir = schema_dir or default_schema_dir(sources.data_dir)
    issues = [Issue(ERROR, path, "-", message) for path, message in sources.load_errors]
    issues += _schema_issues(sources, schema_dir)
    issues += _ref_issues(sources)
    issues += _id_issues(sources)
    issues += _location_issues(sources)
    issues += _regexp_issues(sources)
    issues += _checksum_issues(sources)
    issues += _coverage_issues(sources)
    return ValidationResult(issues=issues)
