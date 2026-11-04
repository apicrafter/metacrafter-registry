#!/usr/bin/env python
"""
Utility to enrich all datatype definitions in the registry with
optional metadata fields if they are missing:

- links
- examples
- wikidata_property
- translations
- regexp

The script is intentionally conservative: it only adds fields that are
absent, and it does NOT overwrite any existing values.

Usage:

  python scripts/enrich_datatypes.py

By default it processes all ``data/datatypes/**/*.yaml`` files.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict

try:
    import yaml
except ImportError:  # pragma: no cover - runtime environment issue
    print("This script requires PyYAML. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


REPO_ROOT = Path(__file__).resolve().parents[1]
DATATYPES_ROOT = REPO_ROOT / "data" / "datatypes"


def enrich_record(data: Dict[str, Any]) -> bool:
    """
    Ensure that the optional fields exist on a datatype record.

    Returns True if the record was modified, False otherwise.
    """
    changed = False

    # We only touch top-level mappings that look like datatype records.
    if not isinstance(data, dict) or "id" not in data:
        return False

    # Do not overwrite anything that already exists.
    if "links" not in data:
        data["links"] = []
        changed = True

    if "examples" not in data:
        data["examples"] = []
        changed = True

    if "wikidata_property" not in data:
        # Empty string is treated as "no value" in templates/Jinja.
        data["wikidata_property"] = ""
        changed = True

    if "translations" not in data:
        data["translations"] = {}
        changed = True

    if "regexp" not in data:
        data["regexp"] = ""
        changed = True

    return changed


def process_file(path: Path, dry_run: bool = False, verbose: bool = False) -> bool:
    """
    Load a YAML file, enrich its top-level document if needed, and write back.

    Returns True if the file was modified.
    """
    with path.open("r", encoding="utf-8") as f:
        try:
            # Most registry files are a single mapping document.
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:  # pragma: no cover - defensive
            print(f"Failed to parse YAML: {path}: {e}", file=sys.stderr)
            return False

    if data is None:
        return False

    modified = False

    if isinstance(data, list):
        # Some files might in theory contain a list of records.
        for idx, item in enumerate(data):
            if isinstance(item, dict):
                if enrich_record(item):
                    modified = True
                    data[idx] = item
    elif isinstance(data, dict):
        if enrich_record(data):
            modified = True
    else:
        # Unsupported structure – leave untouched.
        return False

    if not modified:
        return False

    if verbose:
        print(f"Enriched: {path.relative_to(REPO_ROOT)}")

    if dry_run:
        return False

    with path.open("w", encoding="utf-8") as f:
        # Use safe_dump with explicit settings to keep output readable.
        yaml.safe_dump(
            data,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Enrich all datatype YAMLs with optional metadata fields."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only report which files would be changed, do not write anything.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print each file as it is processed.",
    )

    args = parser.parse_args(argv)

    if not DATATYPES_ROOT.exists():
        print(f"Datatypes directory not found: {DATATYPES_ROOT}", file=sys.stderr)
        return 1

    changed_files = 0
    for path in DATATYPES_ROOT.rglob("*.yaml"):
        if process_file(path, dry_run=args.dry_run, verbose=args.verbose):
            changed_files += 1

    if args.dry_run:
        print(f"[dry-run] Files that would be modified: {changed_files}")
    else:
        print(f"Files modified: {changed_files}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


