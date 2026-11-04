"""Coverage of registry datatypes by metacrafter-rules.

The rules repository is pinned in ``ecosystem.lock``. ``coverage update`` reads
a checkout of that ref and writes ``data/coverage/metacrafter-rules.json``, a
committed, deterministic summary of every rule. The build only reads that
file, so local builds and CI produce the same output without network access.
"""

from __future__ import annotations

import json
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

from .loader import SafeLoader

LOCK_FILE = "ecosystem.lock"
COVERAGE_FILE = Path("coverage") / "metacrafter-rules.json"
RULES_REPO = "apicrafter/metacrafter-rules"


def lock_path(data_dir: Path) -> Path:
    return Path(data_dir).resolve().parent / LOCK_FILE


def coverage_path(data_dir: Path) -> Path:
    return Path(data_dir) / COVERAGE_FILE


def read_lock(data_dir: Path) -> dict[str, Any]:
    path = lock_path(data_dir)
    if not path.exists():
        return {}
    return yaml.load(path.read_text("utf-8"), Loader=SafeLoader) or {}


def write_lock(data_dir: Path, ref: str) -> None:
    lock_path(data_dir).write_text(
        "# Pinned versions of ecosystem repositories used by the build.\n"
        "# Update with: metacrafter-registry coverage update --rules-dir <checkout>\n"
        f"metacrafter-rules:\n  repo: {RULES_REPO}\n  ref: {ref}\n",
        encoding="utf-8",
    )


def scan_rules(rules_dir: Path) -> list[dict[str, Any]]:
    """Every rule in a metacrafter-rules ``rules/`` directory, in a stable order."""
    rules_dir = Path(rules_dir)
    out = []
    for path in sorted(rules_dir.rglob("*.yaml")):
        data = yaml.load(path.read_text("utf-8"), Loader=SafeLoader) or {}
        if not isinstance(data, dict) or not isinstance(data.get("rules"), dict):
            continue
        for rule_id, rule in sorted(data["rules"].items()):
            if not isinstance(rule, dict) or not rule.get("key"):
                continue
            entry = {
                "rule": str(rule_id),
                "key": str(rule["key"]).strip(),
                "type": str(rule.get("type", "")),
                "match": str(rule.get("match", "")),
                "file": path.relative_to(rules_dir).as_posix(),
            }
            for field in ("context", "lang", "country_code"):
                if data.get(field):
                    entry[field] = str(data[field])
            out.append(entry)
    return out


def git_ref(checkout: Path) -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=checkout, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def build_coverage(rules_dir: Path, ref: str) -> dict[str, Any]:
    return {"source": {"repo": RULES_REPO, "ref": ref}, "rules": scan_rules(rules_dir)}


def dump_coverage(coverage: dict[str, Any]) -> str:
    return json.dumps(coverage, ensure_ascii=False, indent=1) + "\n"


def load_coverage(data_dir: Path) -> dict[str, Any] | None:
    path = coverage_path(data_dir)
    if not path.exists():
        return None
    return json.loads(path.read_text("utf-8"))


def rules_by_datatype(
    coverage: dict[str, Any] | None, ids: set[str], aliases: dict[str, str]
) -> dict[str, list[dict[str, Any]]]:
    """Canonical datatype id -> rules whose key is the id or one of its aliases."""
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rule in (coverage or {}).get("rules", []):
        key = rule["key"]
        canonical = key if key in ids else aliases.get(key)
        if canonical:
            item = {k: rule[k] for k in ("rule", "type", "match", "file")}
            if key != canonical:
                item["key"] = key
            out[canonical].append(item)
    return dict(out)


def coverage_report(
    coverage: dict[str, Any] | None, ids: set[str], aliases: dict[str, str]
) -> dict[str, Any]:
    """Orphans in both directions, for CI warnings and /api/v1/coverage.json."""
    rules = (coverage or {}).get("rules", [])
    orphan_keys: dict[str, list[str]] = defaultdict(list)
    for rule in rules:
        if rule["key"] not in ids and rule["key"] not in aliases:
            orphan_keys[rule["key"]].append(f"{rule['file']}#{rule['rule']}")
    covered = rules_by_datatype(coverage, ids, aliases)
    return {
        "source": (coverage or {}).get("source"),
        "rules": len(rules),
        "rule_keys": len({r["key"] for r in rules}),
        "datatypes_with_rules": len(covered),
        "datatypes_without_rules": sorted(ids - set(covered)),
        "orphan_rule_keys": {key: sorted(refs) for key, refs in sorted(orphan_keys.items())},
    }


GENERATED_TOOL = "metacrafter"


def source_aliases(sources: Any) -> dict[str, str]:
    return {
        str(alias): rec.id for rec in sources.datatypes for alias in rec.data.get("aliases") or []
    }


def effective_supported_types(sources: Any) -> dict[str, list[str]]:
    """Tool id -> supported datatype ids.

    The ``metacrafter`` tool's list is generated from rule coverage (when a
    coverage file exists); every other tool uses its hand-written list.
    """
    coverage = load_coverage(sources.data_dir)
    ids = {rec.id for rec in sources.datatypes}
    out = {}
    for rec in sources.tools:
        types = [str(t) for t in rec.data.get("supported_types") or []]
        if rec.id == GENERATED_TOOL and coverage:
            types = sorted(rules_by_datatype(coverage, ids, source_aliases(sources)))
        out[rec.id] = types
    return out
