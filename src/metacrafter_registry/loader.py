"""Load registry YAML sources deterministically."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:  # pragma: no cover - depends on libyaml availability
    from yaml import SafeLoader


@dataclass
class SourceRecord:
    """One YAML record and where it came from."""

    path: Path
    relpath: str
    data: dict[str, Any]

    @property
    def id(self) -> str:
        return str(self.data.get("id"))


@dataclass
class RegistrySources:
    """Everything loaded from a data directory."""

    data_dir: Path
    datatypes: list[SourceRecord] = field(default_factory=list)
    tools: list[SourceRecord] = field(default_factory=list)
    countries: dict[str, dict[str, Any]] = field(default_factory=dict)
    categories: dict[str, dict[str, Any]] = field(default_factory=dict)
    langs: dict[str, dict[str, Any]] = field(default_factory=dict)
    load_errors: list[tuple[str, str]] = field(default_factory=list)


def find_data_dir(start: Path | None = None) -> Path:
    """Find the nearest ``data/`` directory with ``datatypes/`` going up from ``start``."""
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        data_dir = candidate / "data"
        if (data_dir / "datatypes").is_dir():
            return data_dir
    raise FileNotFoundError(
        "Could not find a registry data directory (data/datatypes). Use --data-dir."
    )


def _load_yaml_file(path: Path) -> Any:
    with open(path, encoding="utf-8") as handle:
        return yaml.load(handle, Loader=SafeLoader)


def load_yaml_dir(directory: Path, base: Path) -> tuple[list[SourceRecord], list[tuple[str, str]]]:
    """Load every ``*.yaml`` file under ``directory`` in sorted path order."""
    records: list[SourceRecord] = []
    errors: list[tuple[str, str]] = []
    paths = []
    for root, dirs, files in os.walk(directory):
        dirs.sort()
        for filename in files:
            if filename.lower().endswith(".yaml"):
                paths.append(Path(root) / filename)
    for path in sorted(paths):
        relpath = path.relative_to(base).as_posix()
        try:
            data = _load_yaml_file(path)
        except yaml.YAMLError as exc:
            errors.append((relpath, f"YAML parse error: {exc}"))
            continue
        if not isinstance(data, dict):
            errors.append((relpath, "file does not contain a mapping"))
            continue
        records.append(SourceRecord(path=path, relpath=relpath, data=data))
    return records, errors


def load_reference(
    path: Path, errors: list[tuple[str, str]] | None = None
) -> dict[str, dict[str, Any]]:
    """Load a reference list (countries, categories, langs) keyed by stripped id.

    A repeated id keeps its first entry and is reported in ``errors``.
    """
    entries = _load_yaml_file(path) or []
    out: dict[str, dict[str, Any]] = {}
    for entry in entries:
        key = str(entry["id"]).strip()
        if key in out:
            if errors is not None:
                errors.append((path.name, f"duplicate id '{key}'"))
            continue
        out[key] = {**entry, "id": key}
    return out


def load_sources(data_dir: Path) -> RegistrySources:
    data_dir = Path(data_dir)
    sources = RegistrySources(data_dir=data_dir)
    sources.countries = load_reference(data_dir / "countries.yaml", sources.load_errors)
    sources.categories = load_reference(data_dir / "categories.yaml", sources.load_errors)
    sources.langs = load_reference(data_dir / "langs.yaml", sources.load_errors)
    sources.datatypes, errors = load_yaml_dir(data_dir / "datatypes", data_dir)
    sources.load_errors.extend(errors)
    sources.tools, errors = load_yaml_dir(data_dir / "tools", data_dir)
    sources.load_errors.extend(errors)
    return sources
