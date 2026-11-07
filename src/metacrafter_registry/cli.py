"""Command line interface: ``metacrafter-registry <command>``."""

from __future__ import annotations

import argparse
import json
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
            changes_dir=Path(args.changes_dir) if args.changes_dir else None,
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


def cmd_changes(args: argparse.Namespace) -> int:
    """Changelog between two data versions (e.g. the previous release and this build)."""
    from .changes import changes_markdown, diff_records, read_records

    diff = diff_records(
        read_records(args.old), read_records(args.new), args.old_version, args.new_version
    )
    if args.json:
        Path(args.json).write_text(json.dumps(diff, ensure_ascii=False, indent=2), "utf-8")
    markdown = changes_markdown(diff, args.base_url.rstrip("/"))
    if args.markdown:
        Path(args.markdown).write_text(markdown, "utf-8")
    else:
        print(markdown)
    return 0


def cmd_coverage(args: argparse.Namespace) -> int:
    """Rule coverage from metacrafter-rules: update the pinned summary, check it, report."""
    from .coverage import (
        build_coverage,
        coverage_path,
        coverage_report,
        dump_coverage,
        git_ref,
        load_coverage,
        read_lock,
        source_aliases,
        write_lock,
    )

    data_dir = _data_dir(args)
    sources = load_sources(data_dir)
    ids = {rec.id for rec in sources.datatypes}
    aliases = source_aliases(sources)

    if args.action in ("update", "check"):
        if not args.rules_dir:
            print("--rules-dir is required (the rules/ directory of a metacrafter-rules checkout)")
            return 2
        rules_dir = Path(args.rules_dir)
        ref = args.ref or git_ref(rules_dir) or "unknown"
        if args.action == "update" and ref == "unknown":
            print(f"Cannot read the commit of {rules_dir}; pass --ref <full commit SHA>")
            return 2
        fresh = build_coverage(rules_dir, ref)
        if args.action == "update":
            path = coverage_path(data_dir)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(dump_coverage(fresh), encoding="utf-8")
            write_lock(data_dir, ref)
            print(f"Wrote {path} ({len(fresh['rules'])} rules at {ref[:12]}) and ecosystem.lock")
            return 0
        committed = load_coverage(data_dir)
        locked = read_lock(data_dir).get("metacrafter-rules", {}).get("ref")
        if committed != fresh or locked != ref:
            print(
                f"Coverage is stale for metacrafter-rules {ref[:12]} (lock: {str(locked)[:12]}). "
                "Run: metacrafter-registry coverage update --rules-dir <checkout>/rules"
            )
            return 1
        print(f"Coverage matches metacrafter-rules {ref[:12]} ({len(fresh['rules'])} rules)")
        return 0

    if args.rules_dir:  # report against another checkout, e.g. the latest rules
        rules_dir = Path(args.rules_dir)
        coverage = build_coverage(rules_dir, args.ref or git_ref(rules_dir) or "unknown")
    else:
        coverage = load_coverage(data_dir)
    report = coverage_report(coverage, ids, aliases)
    orphans = report["orphan_rule_keys"]
    if args.github_annotations:
        for key, refs in orphans.items():
            print(
                "::warning title=Rule key without registry record::"
                f"{key} used by {', '.join(refs[:3])}"
            )
    if args.markdown:
        lines = [
            "## metacrafter-rules coverage",
            "",
            f"Rules: {report['rules']} ({report['rule_keys']} keys) at "
            f"`{(report['source'] or {}).get('ref', 'unknown')}`.",
            f"Datatypes with rules: {report['datatypes_with_rules']}; "
            f"without rules: {len(report['datatypes_without_rules'])}.",
            "",
            f"### Rule keys without a registry record ({len(orphans)})",
            "",
        ]
        lines += [f"- `{key}`: {', '.join(refs)}" for key, refs in orphans.items()] or ["None."]
        Path(args.markdown).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"{report['rules']} rules, {report['rule_keys']} keys; "
        f"{report['datatypes_with_rules']} datatypes with rules, "
        f"{len(report['datatypes_without_rules'])} without; {len(orphans)} orphan rule keys"
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def cmd_fibo(args: argparse.Namespace) -> int:
    """FIBO mappings: update the committed term list, check it, or search a checkout."""
    from .coverage import git_ref
    from .fibo import (
        build_vocabulary,
        dump_vocabulary,
        load_vocabulary,
        mapped_paths,
        scan_classes,
        search,
        vocabulary_path,
    )

    fibo_dir = Path(args.fibo_dir)
    if not fibo_dir.is_dir():
        print(
            f"--fibo-dir {fibo_dir} is not a directory (clone https://github.com/edmcouncil/fibo)"
        )
        return 2
    classes = scan_classes(fibo_dir)
    if args.action == "search":
        if not args.query:
            print("search needs a query, e.g.: fibo search 'bank account' --fibo-dir <checkout>")
            return 2
        for path, term in search(classes, " ".join(args.query), args.limit):
            abbreviations = (
                f" ({', '.join(term['abbreviations'])})" if term.get("abbreviations") else ""
            )
            print(f"{path}\n    {term['label']}{abbreviations} [{term.get('maturity', '?')}]")
            if term.get("definition"):
                print(f"    {term['definition']}")
        return 0

    data_dir = _data_dir(args)
    used = mapped_paths(rec.data for rec in load_sources(data_dir).datatypes)
    ref = args.ref or git_ref(fibo_dir) or "unknown"
    if args.action == "update" and ref == "unknown":
        print(f"Cannot read the commit of {fibo_dir}; pass --ref <full commit SHA>")
        return 2
    fresh, missing = build_vocabulary(classes, used, ref)
    for path in missing:
        print(f"Not a labelled FIBO class at {ref[:12]}: {path} (used by {', '.join(used[path])})")
    if args.action == "update":
        if missing:
            return 1
        path = vocabulary_path(data_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dump_vocabulary(fresh), encoding="utf-8")
        print(f"Wrote {path} ({len(fresh['terms'])} FIBO classes at {ref[:12]})")
        return 0
    committed = load_vocabulary(data_dir) or {}
    if missing or committed.get("terms") != fresh["terms"]:
        print(
            f"FIBO term list differs from FIBO {ref[:12]} "
            f"(committed: {str((committed.get('source') or {}).get('ref'))[:12]}). "
            "Review the changes, then run: metacrafter-registry fibo update --fibo-dir <checkout>"
        )
        return 1
    print(f"FIBO term list matches FIBO {ref[:12]} ({len(fresh['terms'])} classes)")
    return 0


def cmd_snapshot(args: argparse.Namespace) -> int:
    """Copy published data files into the package so wheels work offline."""
    import shutil

    from .client import SNAPSHOT_DIR, SNAPSHOT_FILES

    source = Path(args.dist) / "api" / "v1"
    target = Path(args.out) if args.out else SNAPSHOT_DIR
    missing = [name for name in SNAPSHOT_FILES if not (source / name).is_file()]
    if missing:
        print(f"{source} lacks {', '.join(missing)}; run 'metacrafter-registry build' first")
        return 1
    target.mkdir(parents=True, exist_ok=True)
    for name in SNAPSHOT_FILES:
        shutil.copyfile(source / name, target / name)
    print(f"Snapshot of {len(SNAPSHOT_FILES)} files written to {target}")
    return 0


def cmd_mcp(args: argparse.Namespace) -> int:
    try:
        from .mcp_server import serve
    except ImportError:  # pragma: no cover - depends on the optional extra
        print(
            "The MCP server needs the extra: pip install -e '.[mcp]' in a checkout, or\n"
            "pip install 'metacrafter-registry[mcp] @ "
            "git+https://github.com/apicrafter/metacrafter-registry'",
            file=sys.stderr,
        )
        return 1
    kwargs = {}
    if args.transport != "stdio":
        kwargs = {"host": args.host, "port": args.port}
    serve(
        args.data,
        refresh=args.refresh,
        base_url=args.base_url,
        transport=args.transport,
        **kwargs,
    )
    return 0


def cmd_check_links(args: argparse.Namespace) -> int:
    from .linkcheck import check_links

    directory = Path(args.dir) if args.dir else find_data_dir().parent / "dist"
    if not directory.is_dir():
        print(f"{directory} is not a directory; run `metacrafter-registry build` first")
        return 2
    checked, broken = check_links(directory, args.base_path)
    for link in broken:
        print(f"BROKEN {link}")
    print(f"{checked} internal links checked, {len(broken)} broken")
    if not checked:
        print(f"No internal links found in {directory}: is it a built site?")
        return 1
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
    p.add_argument("--changes-dir", help="directory with changes.json files of past releases")
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

    p = sub.add_parser("changes", help="changelog between two data versions")
    p.add_argument("--old", required=True, help="previous datatypes.jsonl (or its directory)")
    p.add_argument("--new", default="dist", help="new datatypes.jsonl or built site (default dist)")
    p.add_argument("--old-version", default="previous")
    p.add_argument("--new-version", default="current")
    p.add_argument("--base-url", default=DEFAULT_BASE_URL)
    p.add_argument("--json", help="write the changes as JSON")
    p.add_argument("--markdown", help="write release notes as Markdown (default: print)")
    p.set_defaults(func=cmd_changes)

    p = sub.add_parser("coverage", help="metacrafter-rules coverage: update, check, report")
    p.add_argument("action", choices=["update", "check", "report"])
    p.add_argument("--rules-dir", help="rules/ directory of a metacrafter-rules checkout")
    p.add_argument("--ref", help="git ref of that checkout (default: its HEAD)")
    p.add_argument("--github-annotations", action="store_true", help="print ::warning lines")
    p.add_argument("--markdown", help="write a Markdown report to this file")
    p.add_argument("--json", action="store_true", help="print the full report as JSON")
    p.set_defaults(func=cmd_coverage)

    p = sub.add_parser("fibo", help="FIBO mappings: update or check the term list, search FIBO")
    p.add_argument("action", choices=["update", "check", "search"])
    p.add_argument("query", nargs="*", help="search: words to find in class names and labels")
    p.add_argument("--fibo-dir", required=True, help="a checkout of github.com/edmcouncil/fibo")
    p.add_argument("--ref", help="git ref of that checkout (default: its HEAD)")
    p.add_argument("--limit", type=int, default=20, help="search: most classes to print")
    p.set_defaults(func=cmd_fibo)

    p = sub.add_parser("snapshot", help="bundle published data files into the package")
    p.add_argument("--dist", default="dist", help="built site directory (default: dist)")
    p.add_argument("--out", help="target directory (default: the package snapshot/ folder)")
    p.set_defaults(func=cmd_snapshot)

    p = sub.add_parser("mcp", help="run the MCP server (needs the [mcp] extra)")
    p.add_argument("--data", help="snapshot or data/ directory (default: bundled or checkout)")
    p.add_argument("--refresh", action="store_true", help="download newer published data")
    p.add_argument("--base-url", default=None, help="site to download data from")
    p.add_argument(
        "--transport", choices=["stdio", "streamable-http"], default="stdio", help="MCP transport"
    )
    p.add_argument("--host", default="127.0.0.1", help="host for streamable-http")
    p.add_argument("--port", type=int, default=8000, help="port for streamable-http")
    p.set_defaults(func=cmd_mcp)

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
