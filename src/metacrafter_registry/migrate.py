"""Migrate registry YAML sources to the v2 record contract.

The migration is mechanical and idempotent. It changes representation, never
meaning:

* ``is_pii`` strings become booleans; patterns drop ``is_pii``,
  ``categories`` and ``classification`` when they equal their datatype's
  (they inherit them);
* ``parent: {type: x}`` becomes ``parent: x``;
* ``wikidata_property`` moves to ``mappings.wikidata``;
* empty values (``''``, ``[]``, ``{}``) are removed;
* string translations become ``{name: ...}``; example values become strings;
* hand-maintained ``patterns`` lists are removed (they are derived);
* duplicate ``supported_types`` entries of tools are removed;
* ``status`` is set: ``draft`` for stub records, ``stable`` otherwise;
* keys are written in a canonical order and files are renamed to ``<id>.yaml``.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .loader import SafeLoader

DATATYPE_KEY_ORDER = [
    "id",
    "name",
    "status",
    "doc",
    "semantic_type",
    "parent",
    "aliases",
    "replaced_by",
    "categories",
    "country",
    "langs",
    "is_pii",
    "classification",
    "regexp",
    "checksum",
    "examples",
    "mappings",
    "links",
    "translations",
]
TOOL_KEY_ORDER = ["id", "name", "category", "doc", "website", "supported_types"]
EXAMPLE_KEY_ORDER = ["value", "valid", "description"]
LINK_KEY_ORDER = ["type", "url"]

STUB_DOC_MIN = 25


class _Dumper(yaml.SafeDumper):
    """Block-style YAML with readable unicode."""


def dump_yaml(data: dict[str, Any]) -> str:
    return yaml.dump(
        data,
        Dumper=_Dumper,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=100,
    )


def _empty(value: Any) -> bool:
    return (
        value is None
        or (isinstance(value, (str, list, dict)) and len(value) == 0)
        or (isinstance(value, str) and not value.strip())
    )


def _as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    return str(value).strip() == "True"


def _ordered(data: dict[str, Any], order: list[str]) -> dict[str, Any]:
    out = {key: data[key] for key in order if key in data}
    out.update({key: value for key, value in data.items() if key not in out})
    return out


def is_stub(record: dict[str, Any]) -> bool:
    """A record that only names a type: no real description and no evidence."""
    name = str(record.get("name", "")).strip().lower()
    doc = str(record.get("doc", "")).strip()
    if doc.lower() == name or len(doc) < STUB_DOC_MIN:
        return True
    return not (record.get("regexp") or record.get("examples") or record.get("links"))


def migrate_datatype(data: dict[str, Any], parent: dict[str, Any] | None) -> dict[str, Any]:
    """Return the v2 form of one datatype or pattern record.

    ``parent`` is the v1 or v2 record of the pattern's ``semantic_type`` (for patterns).
    """
    out: dict[str, Any] = {}
    for key, value in data.items():
        if key == "patterns":
            continue  # derived from semantic_type
        if key == "is_pii":
            value = _as_bool(value)
        elif key == "parent" and isinstance(value, dict):
            value = value.get("type")
        elif key == "wikidata_property":
            if not _empty(value):
                out.setdefault("mappings", {})["wikidata"] = str(value).strip()
            continue
        elif key == "mappings" and isinstance(value, dict):
            value = {**value, **out.get("mappings", {})}
        elif key == "translations" and isinstance(value, dict):
            translations = {}
            for lang, entry in value.items():
                if isinstance(entry, str):
                    entry = {"name": entry}
                if isinstance(entry, dict):
                    entry = {
                        k: str(v).strip()
                        for k, v in entry.items()
                        if k in ("name", "doc") and not _empty(v)
                    }
                    if entry:
                        translations[str(lang)] = _ordered(entry, ["name", "doc"])
            value = translations
        elif key == "examples" and isinstance(value, list):
            examples = []
            for example in value:
                if not isinstance(example, dict) or _empty(example.get("value")):
                    continue
                item = {"value": str(example["value"])}
                if example.get("valid") is False:
                    item["valid"] = False
                if not _empty(example.get("description")):
                    item["description"] = str(example["description"]).strip()
                examples.append(_ordered(item, EXAMPLE_KEY_ORDER))
            value = examples
        elif key == "links" and isinstance(value, list):
            links = []
            for link in value:
                if isinstance(link, dict) and not _empty(link.get("url")):
                    links.append(
                        _ordered(
                            {"type": link.get("type") or "other", "url": str(link["url"])},
                            LINK_KEY_ORDER,
                        )
                    )
            value = links
        elif isinstance(value, str):
            value = value.strip()
        if _empty(value):
            continue
        out[key] = value

    if out.get("semantic_type") and parent is not None:
        parent_pii = _as_bool(parent.get("is_pii"))
        if "is_pii" in out and out["is_pii"] == parent_pii:
            del out["is_pii"]
        if "categories" in out and sorted(out["categories"]) == sorted(
            parent.get("categories") or []
        ):
            del out["categories"]
        if "classification" in out and out["classification"] == parent.get("classification"):
            del out["classification"]

    if "status" not in out:
        out["status"] = "draft" if is_stub(out) else "stable"
    return _ordered(out, DATATYPE_KEY_ORDER)


def migrate_tool(data: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in data.items():
        if key == "supported_types" and isinstance(value, list):
            seen: list[str] = []
            for item in value:
                if str(item) not in seen:
                    seen.append(str(item))
            value = seen
        elif isinstance(value, str):
            value = value.strip()
        if not _empty(value):
            out[key] = value
    return _ordered(out, TOOL_KEY_ORDER)


@dataclass
class MigrationPlan:
    writes: dict[Path, str] = field(default_factory=dict)  # target path -> new text
    renames: dict[Path, Path] = field(default_factory=dict)  # old path -> new path

    @property
    def changed(self) -> list[Path]:
        return sorted(set(self.writes) | set(self.renames))


def _load(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        return yaml.load(handle, Loader=SafeLoader)


def _yaml_files(directory: Path) -> list[Path]:
    paths = []
    for root, dirs, files in os.walk(directory):
        dirs.sort()
        paths += [Path(root) / f for f in files if f.endswith(".yaml")]
    return sorted(paths)


def plan_migration(data_dir: Path) -> MigrationPlan:
    data_dir = Path(data_dir)
    plan = MigrationPlan()
    raw = {path: _load(path) for path in _yaml_files(data_dir / "datatypes")}
    by_id = {str(d["id"]): d for d in raw.values()}
    for path, data in raw.items():
        parent = by_id.get(str(data.get("semantic_type"))) if data.get("semantic_type") else None
        new = migrate_datatype(data, parent)
        _plan_file(plan, path, new)
    for path in _yaml_files(data_dir / "tools"):
        _plan_file(plan, path, migrate_tool(_load(path)))
    return plan


def _plan_file(plan: MigrationPlan, path: Path, record: dict[str, Any]) -> None:
    text = dump_yaml(record)
    if yaml.load(text, Loader=SafeLoader) != record:  # pragma: no cover - safety net
        raise RuntimeError(f"YAML round-trip changed {path}")
    target = path.with_name(f"{record['id']}.yaml")
    if target != path:
        if target.exists():
            raise RuntimeError(f"cannot rename {path} to {target}: target exists")
        plan.renames[path] = target
    if path.read_text(encoding="utf-8") != text:
        plan.writes[target] = text


def _add_kind(path: Path, special: dict[str, str], default: str) -> str | None:
    """Add a ``kind`` line to every entry of a reference list, keeping comments."""
    raw = path.read_bytes().decode("utf-8")
    newline = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    current: str | None = None
    has_kind = False

    def flush() -> None:
        if current is not None and not has_kind:
            out.append(f"  kind: {special.get(current, default)}")

    for line in lines:
        match = re.match(r"^- id:\s*(\S+)", line)
        if match:
            flush()
            current, has_kind = match.group(1), False
        elif re.match(r"^\s+kind:", line):
            has_kind = True
        elif current is not None and not line.startswith("  "):
            flush()
            current, has_kind = None, True
        out.append(line)
    flush()
    text = newline.join(out)
    if not text.endswith(newline):
        text += newline
    return None if text == raw else text


def plan_reference_lists(data_dir: Path) -> dict[Path, str]:
    writes = {}
    for name, special, default in (
        ("countries.yaml", {"EU": "region"}, "country"),
        ("langs.yaml", {"common": "special"}, "language"),
    ):
        path = Path(data_dir) / name
        text = _add_kind(path, special, default)
        if text is not None:
            writes[path] = text
    return writes


def apply_migration(data_dir: Path, plan: MigrationPlan, refs: dict[Path, str]) -> None:
    repo = Path(data_dir).resolve().parent
    for old, new in plan.renames.items():
        moved = subprocess.run(
            ["git", "mv", str(old), str(new)], cwd=repo, capture_output=True, text=True
        )
        if moved.returncode != 0:  # not a git checkout: plain rename
            old.rename(new)
    for path, text in {**plan.writes, **refs}.items():
        path.write_bytes(text.encode("utf-8"))
