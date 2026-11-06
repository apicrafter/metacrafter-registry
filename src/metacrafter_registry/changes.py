"""Changelog between two published data versions (normalized /api/v1/ records)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Fields that change with every build or are derived from other fields.
VOLATILE = {"quality", "source", "urls", "detected_by", "children", "patterns"}


def read_records(path: Path | str) -> list[dict[str, Any]]:
    """Records from datatypes.jsonl, datatypes.json, or a directory holding one."""
    path = Path(path)
    if path.is_dir():
        for name in ("datatypes.jsonl", "api/v1/datatypes.jsonl"):
            if (path / name).exists():
                return read_records(path / name)
        raise FileNotFoundError(f"no datatypes.jsonl in {path}")
    text = path.read_text("utf-8")
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    data = json.loads(text)
    return list(data.values()) if isinstance(data, dict) else data


def diff_records(
    old: list[dict[str, Any]], new: list[dict[str, Any]], old_version: str, new_version: str
) -> dict[str, Any]:
    old_by = {r["id"]: r for r in old}
    new_by = {r["id"]: r for r in new}
    aliases = {alias: r["id"] for r in new for alias in r.get("aliases", [])}

    gone = sorted(set(old_by) - set(new_by))
    merged = {rid: aliases[rid] for rid in gone if rid in aliases}
    status_changes, changed = [], []
    for rid in sorted(set(old_by) & set(new_by)):
        a, b = old_by[rid], new_by[rid]
        if a.get("status") and a.get("status") != b.get("status"):
            status_changes.append({"id": rid, "from": a.get("status"), "to": b.get("status")})
        fields = sorted(
            k for k in (set(a) | set(b)) - VOLATILE - {"status"} if a.get(k) != b.get(k)
        )
        if fields:
            changed.append({"id": rid, "fields": fields})
    return {
        "from": old_version,
        "to": new_version,
        "added": sorted(set(new_by) - set(old_by)),
        "removed": [rid for rid in gone if rid not in merged],
        "merged": merged,
        "status_changed": status_changes,
        "changed": changed,
    }


def changes_markdown(diff: dict[str, Any], site_url: str) -> str:
    def link(rid: str) -> str:
        return f"[`{rid}`]({site_url}/datatype/{rid})"

    lines = [f"## Data changes {diff['from']} → {diff['to']}", ""]
    if diff["added"]:
        lines += [f"**Added ({len(diff['added'])}):** " + ", ".join(map(link, diff["added"])), ""]
    if diff["merged"]:
        merged = ", ".join(f"`{old}` → {link(new)}" for old, new in diff["merged"].items())
        lines += [f"**Merged into another record ({len(diff['merged'])}):** {merged}", ""]
    if diff["removed"]:
        lines += [f"**Removed ({len(diff['removed'])}):** " + ", ".join(diff["removed"]), ""]
    became_stable = [s["id"] for s in diff["status_changed"] if s["to"] == "stable"]
    if became_stable:
        lines += [
            f"**Reviewed, now stable ({len(became_stable)}):** "
            + ", ".join(map(link, became_stable)),
            "",
        ]
    other = [s for s in diff["status_changed"] if s["to"] != "stable"]
    if other:
        lines += [
            "**Other status changes:** "
            + ", ".join(f"{link(s['id'])} {s['from']} → {s['to']}" for s in other),
            "",
        ]
    if diff["changed"]:
        lines += [f"**Updated ({len(diff['changed'])}):**", ""]
        lines += [f"- {link(c['id'])}: {', '.join(c['fields'])}" for c in diff["changed"]]
        lines.append("")
    if len(lines) == 2:
        lines += ["No changes to records.", ""]
    return "\n".join(lines)


def load_release_changes(directory: Path | str | None) -> list[dict[str, Any]]:
    """changes.json files of published releases (one per release), newest first."""
    if not directory or not Path(directory).is_dir():
        return []
    entries = []
    for path in sorted(Path(directory).rglob("changes.json")):
        data = json.loads(path.read_text("utf-8"))
        if isinstance(data, dict):  # a release's diff; skip anything else
            entries.append(data)

    def version_key(entry: dict[str, Any]) -> tuple:
        parts = str(entry.get("to", "")).lstrip("v").split(".")
        return tuple(int(p) if p.isdigit() else 0 for p in parts)

    return sorted(entries, key=version_key, reverse=True)
