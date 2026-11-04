"""Command line interface: ``metacrafter-registry <command>``."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import DEFAULT_BASE_URL, __version__
from .loader import find_data_dir, load_sources
from .validate import ValidationResult, validate


def _data_dir(args: argparse.Namespace) -> Path:
    return Path(args.data_dir) if args.data_dir else find_data_dir()


def _print_result(result: ValidationResult, show_warnings: bool) -> None:
    for issue in result.errors:
        print(issue)
    if show_warnings:
        for issue in result.warnings:
            print(issue)
    print(f"{len(result.errors)} error(s), {len(result.warnings)} warning(s)")


def cmd_validate(args: argparse.Namespace) -> int:
    sources = load_sources(_data_dir(args))
    result = validate(sources)
    print(f"Loaded {len(sources.datatypes)} datatypes/patterns and {len(sources.tools)} tools")
    _print_result(result, args.warnings)
    return 0 if result.ok else 1


def cmd_build(args: argparse.Namespace) -> int:
    from .build import BuildError, build

    data_dir = _data_dir(args)
    out_dir = Path(args.out) if args.out else data_dir.parent / "dist"
    try:
        result = build(
            data_dir,
            out_dir,
            base_url=args.base_url,
            update_data_files=not args.no_data_files,
        )
    except BuildError as exc:
        _print_result(exc.result, show_warnings=False)
        print("Build aborted: fix the errors above. Nothing was written.")
        return 1
    print(f"Built {out_dir} ({len(result.warnings)} warning(s); run 'validate -w' to list)")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    from .serve import serve

    directory = Path(args.dir) if args.dir else find_data_dir().parent / "dist"
    if not directory.is_dir():
        print(f"{directory} does not exist; run 'metacrafter-registry build' first")
        return 1
    if not (directory / "index.html").is_file():
        print(f"Warning: {directory} has no index.html at its root")
    serve(directory, args.host, args.port)
    return 0


def cmd_check_contract(args: argparse.Namespace) -> int:
    from .contract import check_contract

    results = check_contract(args.base_url, expect_sha=args.expect_sha, retries=args.retries)
    for result in results:
        print(result)
    failed = [r for r in results if not r.ok]
    print(f"{len(results) - len(failed)}/{len(results)} checks passed")
    return 1 if failed else 0


def _registry(args: argparse.Namespace):
    from .model import build_registry

    return build_registry(load_sources(_data_dir(args)), DEFAULT_BASE_URL)


def cmd_stats(args: argparse.Namespace) -> int:
    from .stats import stats_lines

    print("\n".join(stats_lines(_registry(args))))
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    import json

    from .stats import report_rows

    rows = report_rows(_registry(args), status=args.status, below=args.below)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    for row in rows[: args.limit or None]:
        print(f"{row['score']:3d}  {row['status']:<10} {row['id']:<28} {row['path']}")
        if row["missing"]:
            print(f"{'':16}missing: {', '.join(row['missing'])}")
    print(f"{len(rows)} record(s)")
    return 0


def cmd_migrate(args: argparse.Namespace) -> int:
    from .migrate import apply_migration, plan_migration, plan_reference_lists

    data_dir = _data_dir(args)
    plan = plan_migration(data_dir)
    refs = plan_reference_lists(data_dir)
    root = data_dir.parent
    for old, new in sorted(plan.renames.items()):
        print(f"rename {old.relative_to(root)} -> {new.name}")
    print(f"{len(plan.writes) + len(refs)} file(s) to rewrite, {len(plan.renames)} to rename")
    if args.check:
        return 1 if (plan.changed or refs) else 0
    apply_migration(data_dir, plan, refs)
    print("Migration applied. Run 'metacrafter-registry build' to refresh outputs.")
    return 0


def cmd_check_links(args: argparse.Namespace) -> int:
    from .linkcheck import check_links

    directory = Path(args.dir) if args.dir else find_data_dir().parent / "dist"
    checked, broken = check_links(directory, args.base_path)
    for link in broken:
        print(f"BROKEN {link}")
    print(f"{checked} internal links checked, {len(broken)} broken")
    return 1 if broken else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="metacrafter-registry", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--data-dir", help="registry data directory (default: auto-detect)")
    parser.add_argument("-v", "--verbose", action="store_true", help="log loader warnings")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate", help="validate YAML sources")
    p.add_argument("-w", "--warnings", action="store_true", help="also list warnings")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("build", help="validate and build the static site into dist/")
    p.add_argument("--out", help="output directory (default: <repo>/dist)")
    p.add_argument("--base-url", default=DEFAULT_BASE_URL, help="public base URL of the site")
    p.add_argument(
        "--no-data-files",
        action="store_true",
        help="do not rewrite the committed data/*_latest.json(l) files",
    )
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("serve", help="serve dist/ locally with GitHub Pages URL rules")
    p.add_argument("--dir", help="directory to serve (default: <repo>/dist)")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8089)
    p.set_defaults(func=cmd_serve)

    p = sub.add_parser("check-contract", help="check public URLs on a deployed site")
    p.add_argument("base_url", help="e.g. https://registry.apicrafter.io")
    p.add_argument("--expect-sha", help="fail unless the deployed manifest has this git SHA")
    p.add_argument("--retries", type=int, default=0, help="retry rounds (10 s apart)")
    p.set_defaults(func=cmd_check_contract)

    p = sub.add_parser("stats", help="honest completeness and quality statistics")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("report", help="records ordered by quality score, with missing elements")
    p.add_argument("--status", choices=["draft", "stable", "deprecated"])
    p.add_argument("--below", type=int, help="only records with a score below this value")
    p.add_argument("--limit", type=int, default=0, help="print at most N records (0 = all)")
    p.add_argument("--json", action="store_true", help="print JSON")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("migrate", help="migrate YAML sources to the v2 record contract")
    p.add_argument(
        "--check", action="store_true", help="only report; exit 1 if anything would change"
    )
    p.set_defaults(func=cmd_migrate)

    p = sub.add_parser("check-links", help="check internal links in a built site")
    p.add_argument("--dir", help="built site directory (default: <repo>/dist)")
    p.add_argument(
        "--base-path",
        default="",
        help="path prefix the site was built for, e.g. /metacrafter-registry",
    )
    p.set_defaults(func=cmd_check_links)

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.ERROR, format="%(levelname)s %(message)s"
    )
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
