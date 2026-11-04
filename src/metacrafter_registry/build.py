"""Build the publishable tree (static site + JSON) from registry sources."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from xml.sax.saxutils import escape as xml_escape

from jinja2 import Environment, PackageLoader, select_autoescape

from . import DEFAULT_BASE_URL, __version__, agents, legacy
from .loader import RegistrySources, load_sources
from .model import CSV_COLUMNS, RegistryModel, build_registry, csv_row
from .openapi import build_openapi
from .validate import ValidationResult, validate

LICENSE = "Apache-2.0"


class BuildError(Exception):
    """Raised when sources are invalid; nothing is written."""

    def __init__(self, result: ValidationResult):
        super().__init__(f"{len(result.errors)} validation error(s)")
        self.result = result


@dataclass
class BuildInfo:
    version: str
    git_sha: str | None
    generated_at: str | None


def _git(args: list[str], cwd: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    return out or None


def build_info(repo_dir: Path) -> BuildInfo:
    """Version metadata derived from the commit, so rebuilds are reproducible."""
    sha = os.environ.get("GITHUB_SHA") or _git(["rev-parse", "HEAD"], repo_dir)
    generated_at = None
    # Unix seconds, not ISO text: GitHub merge commits print "...Z", which
    # datetime.fromisoformat() rejects before Python 3.11.
    epoch = os.environ.get("SOURCE_DATE_EPOCH") or _git(["log", "-1", "--format=%ct"], repo_dir)
    if epoch and epoch.strip().isdigit():
        generated_at = datetime.fromtimestamp(int(epoch), tz=timezone.utc).isoformat()
    return BuildInfo(version=__version__, git_sha=sha, generated_at=generated_at)


def _dump(obj: Any, *, indent: int | None = None) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=indent, default=str)


def _jsonl(records: Any) -> str:
    return "".join(_dump(r) + "\n" for r in records)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_legacy_data_files(data_dir: Path, datatypes: dict, tools: dict) -> list[Path]:
    """Write the transitional committed files ``data/*_latest.json(l)``."""
    files = {
        data_dir / "datatypes_latest.json": _dump(datatypes),
        data_dir / "datatypes_latest.jsonl": _jsonl(datatypes.values()),
        data_dir / "tools_latest.json": _dump(tools),
        data_dir / "tools_latest.jsonl": _jsonl(tools.values()),
    }
    for path, text in files.items():
        _write(path, text)
    return list(files)


def _write_legacy(out: Path, datatypes: dict, tools: dict) -> None:
    """Release 1.02 files: a public contract used by metacrafter."""
    _write(out / "registry.json", _dump(datatypes))
    _write(out / "tools.json", _dump(tools))
    _write(out / "datatypes.jsonl", _jsonl(datatypes.values()))
    for rid, record in datatypes.items():
        _write(out / "datatype" / f"{rid}.json", _dump(record, indent=2))
    for rid, record in tools.items():
        _write(out / "tool" / f"{rid}.json", _dump(record, indent=2))


def _write_api_v1(out: Path, reg: RegistryModel, site_url: str, info: BuildInfo) -> None:
    api = out / "api" / "v1"
    records = list(reg.datatypes.values())
    for rid, record in reg.datatypes.items():
        _write(api / "datatypes" / f"{rid}.json", _dump(record, indent=2))
    _write(api / "datatypes.json", _dump(records))
    _write(api / "datatypes.jsonl", _jsonl(records))
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(CSV_COLUMNS)
    writer.writerows(csv_row(r) for r in records)
    _write(api / "datatypes.csv", buffer.getvalue())

    tools = list(reg.tools.values())
    for rid, tool in reg.tools.items():
        _write(api / "tools" / f"{rid}.json", _dump(tool, indent=2))
    _write(api / "tools.json", _dump(tools))
    _write(api / "tools.jsonl", _jsonl(tools))

    _write(api / "categories.json", _dump(list(reg.categories.values()), indent=2))
    _write(api / "countries.json", _dump(list(reg.countries.values()), indent=2))
    _write(api / "languages.json", _dump(list(reg.langs.values()), indent=2))
    _write(api / "aliases.json", _dump(reg.aliases, indent=2))
    _write(api / "coverage.json", _dump(reg.coverage, indent=2))
    _write(api / "rag" / "corpus.jsonl", _jsonl(agents.rag_entry(r) for r in records))
    _write(api / "openapi.json", _dump(build_openapi(site_url, info.version), indent=2))


def _write_agent_files(out: Path, reg: RegistryModel, site_url: str, info: BuildInfo) -> None:
    """Markdown twins, llms.txt, llms-full.txt and the SKOS export."""
    refs = {"categories": reg.categories, "countries": reg.countries, "langs": reg.langs}
    for rid, record in reg.datatypes.items():
        _write(out / "datatype" / f"{rid}.md", agents.record_markdown(record, **refs))
    for rid, tool in reg.tools.items():
        _write(out / "tool" / f"{rid}.md", agents.tool_markdown(tool))
    records = list(reg.datatypes.values())
    categories = sorted(
        (c for c in reg.categories.values() if c["count"]), key=lambda c: (-c["count"], c["id"])
    )
    countries = sorted((c for c in reg.countries.values() if c["count"]), key=lambda c: c["name"])
    for category in categories:
        members = [r for r in records if category["id"] in r.get("categories", [])]
        _write(
            out / "category" / f"{category['id']}.md",
            agents.category_markdown(category, members, site_url),
        )
    counts = {"datatypes": reg.kind_count("datatype"), "patterns": reg.kind_count("pattern")}
    from .client import Registry

    runtime = Registry(datatypes=records)
    _write(
        out / "identify-index.json",
        _dump(agents.identify_index(records, runtime._broadness)),
    )
    _write(out / "llms.txt", agents.llms_txt(site_url, counts, categories, countries))
    _write(out / "llms-full.txt", agents.llms_full_txt(records, site_url))
    _write(
        out / "registry.ttl",
        agents.skos_turtle(records, reg.categories.values(), site_url, info.version),
    )


def _search_text(record: dict[str, Any]) -> str:
    names = [t.get("name", "") for t in record.get("translations", {}).values()]
    parts = [record["id"], *record.get("aliases", []), record["name"], *names, record["doc"][:200]]
    return " ".join(p for p in parts if p).lower()


def _search_index(reg: RegistryModel) -> list[dict[str, Any]]:
    index = []
    for record in reg.datatypes.values():
        doc = record["doc"]
        index.append(
            {
                "id": record["id"],
                "n": record["name"],
                "d": doc if len(doc) <= 160 else doc[:157].rstrip() + "…",
                "k": record["kind"],
                "p": record["is_pii"],
                "s": record["status"],
                "c": " ".join(record.get("categories", []) + record.get("country", [])),
                "t": " ".join(
                    [*record.get("aliases", [])]
                    + [t.get("name", "") for t in record.get("translations", {}).values()]
                ),
            }
        )
    return index


def _jsonld(record: dict[str, Any], site_url: str) -> dict[str, Any]:
    same_as = []
    wikidata = record.get("mappings", {}).get("wikidata")
    if wikidata:
        prefix = "Property:" if wikidata.startswith("P") else ""
        same_as.append(f"https://www.wikidata.org/wiki/{prefix}{wikidata}")
    for link in record.get("links", []):
        if link["type"] in ("schema.org", "wikidata") and link["url"] not in same_as:
            same_as.append(link["url"])
    data: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "DefinedTerm",
        "@id": record["urls"]["html"],
        "url": record["urls"]["html"],
        "termCode": record["id"],
        "name": record["name"],
        "description": record["doc"],
        "inDefinedTermSet": {
            "@type": "DefinedTermSet",
            "@id": site_url + "/",
            "name": "Metacrafter Registry",
        },
    }
    if same_as:
        data["sameAs"] = same_as
    return data


def _render_site(
    out: Path,
    reg: RegistryModel,
    site_url: str,
    info: BuildInfo,
    releases: list[dict[str, Any]] | None = None,
) -> list[str]:
    """Render HTML pages; return the list of page paths (for the sitemap)."""
    env = Environment(
        loader=PackageLoader("metacrafter_registry", "templates"),
        autoescape=select_autoescape(["html"]),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    by_count = sorted(
        (c for c in reg.categories.values() if c["count"]), key=lambda c: (-c["count"], c["id"])
    )
    countries = sorted((c for c in reg.countries.values() if c["count"]), key=lambda c: c["name"])
    env.globals.update(
        base=urlparse(site_url).path.rstrip("/"),
        site_url=site_url,
        version=info.version,
        git_sha=info.git_sha,
        generated_at=info.generated_at,
        reg=reg,
        categories=by_count,
        countries=countries,
        search_text={rid: _search_text(r) for rid, r in reg.datatypes.items()},
    )
    pages: list[str] = []

    def render(template: str, target: str, url_path: str | None, **kwargs: Any) -> None:
        context = {"section": "", "canonical": url_path, **kwargs}
        _write(out / target, env.get_template(template).render(**context))
        if url_path is not None:
            pages.append(url_path)

    records = list(reg.datatypes.values())
    render("home.html", "index.html", "/")
    render(
        "datatype_list.html",
        "datatype/index.html",
        "/datatype/",
        section="datatypes",
        records=records,
    )
    for rid, record in reg.datatypes.items():
        render(
            "datatype.html",
            f"datatype/{rid}.html",
            f"/datatype/{rid}",
            section="datatypes",
            object=record,
            patterns=[reg.datatypes[p] for p in record.get("patterns", [])],
            children=[reg.datatypes[c] for c in record.get("children", [])],
            jsonld=_jsonld(record, site_url),
        )

    for alias, canonical in reg.aliases.items():
        render(
            "alias.html",
            f"datatype/{alias}.html",
            None,
            alias=alias,
            object=reg.datatypes[canonical],
            canonical=f"/datatype/{canonical}",
        )

    render("category_list.html", "category/index.html", "/category/", section="categories")
    for category in by_count:
        members = [r for r in records if category["id"] in r.get("categories", [])]
        render(
            "category.html",
            f"category/{category['id']}.html",
            f"/category/{category['id']}",
            section="categories",
            group=category,
            records=members,
        )

    global_count = sum(1 for r in records if not r.get("country"))
    render(
        "country_list.html",
        "country/index.html",
        "/country/",
        section="countries",
        global_count=global_count,
    )
    for country in countries:
        members = [r for r in records if country["id"] in r.get("country", [])]
        render(
            "country.html",
            f"country/{country['id']}.html",
            f"/country/{country['id']}",
            section="countries",
            group=country,
            records=members,
        )

    render(
        "tool_list.html",
        "tool/index.html",
        "/tool/",
        section="tools",
        tools=list(reg.tools.values()),
    )
    for rid, tool in reg.tools.items():
        supported = [reg.datatypes[t] for t in tool["supported_types"] if t in reg.datatypes]
        render(
            "tool.html",
            f"tool/{rid}.html",
            f"/tool/{rid}",
            section="tools",
            object=tool,
            records=supported,
        )

    render("about.html", "about.html", "/about", section="about")
    render("agents.html", "agents.html", "/agents", section="agents")
    render("identify.html", "identify.html", "/identify", section="identify")
    render("changes.html", "changes.html", "/changes", section="", releases=releases)
    from .stats import report_rows

    render(
        "quality.html",
        "quality.html",
        "/quality",
        section="",
        drafts=report_rows(reg, status="draft"),
        records=records,
    )
    _write(out / "agents.md", env.get_template("agents.md").render(**env.globals))
    render("search.html", "search.html", None)
    render("404.html", "404.html", None)
    return pages


def _copy_static(out: Path) -> None:
    static = resources.files("metacrafter_registry") / "static"
    for entry in static.iterdir():
        if entry.is_file():
            target = out / "assets" / entry.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(entry.read_bytes())


def _copy_schemas(out: Path, data_dir: Path) -> None:
    """Publish the source-record JSON Schemas at /schema/ (editors, agents)."""
    from .validate import default_schema_dir

    schema_dir = default_schema_dir(data_dir)
    for path in sorted(schema_dir.glob("*.schema.json")):
        target = out / "schema" / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())


def _write_sitemap(out: Path, pages: list[str], site_url: str, info: BuildInfo) -> None:
    lastmod = f"<lastmod>{info.generated_at[:10]}</lastmod>" if info.generated_at else ""
    urls = "".join(
        f"<url><loc>{xml_escape(site_url + page)}</loc>{lastmod}</url>\n" for page in pages
    )
    _write(
        out / "sitemap.xml",
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}</urlset>\n",
    )
    _write(out / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {site_url}/sitemap.xml\n")


def _write_manifest(
    out: Path, reg: RegistryModel, site_url: str, info: BuildInfo, tool_count: int
) -> None:
    bulk = [
        "registry.json",
        "tools.json",
        "datatypes.jsonl",
        "api/v1/datatypes.json",
        "api/v1/datatypes.jsonl",
        "api/v1/datatypes.csv",
        "api/v1/tools.json",
        "api/v1/tools.jsonl",
        "api/v1/openapi.json",
        "api/v1/aliases.json",
        "api/v1/categories.json",
        "api/v1/countries.json",
        "api/v1/languages.json",
        "api/v1/rag/corpus.jsonl",
        "llms-full.txt",
        "registry.ttl",
    ]
    manifest = {
        "name": "metacrafter-registry",
        "version": info.version,
        "git_sha": info.git_sha,
        "generated_at": info.generated_at,
        "license": LICENSE,
        "base_url": site_url,
        "datatype_url_template": site_url + "/datatype/{id}",
        "api_record_url_template": site_url + "/api/v1/datatypes/{id}.json",
        "openapi": site_url + "/api/v1/openapi.json",
        "llms_txt": site_url + "/llms.txt",
        "rag_template_version": agents.RAG_TEMPLATE_VERSION,
        "counts": {
            "datatypes": reg.kind_count("datatype"),
            "draft": sum(1 for r in reg.datatypes.values() if r["status"] == "draft"),
            "aliases": len(reg.aliases),
            "patterns": reg.kind_count("pattern"),
            "tools": tool_count,
            "categories": sum(1 for c in reg.categories.values() if c["count"]),
            "countries": sum(1 for c in reg.countries.values() if c["count"]),
        },
        "files": {
            name: {
                "path": "/" + name,
                "bytes": (out / name).stat().st_size,
                "sha256": _sha256(out / name),
            }
            for name in bulk
        },
    }
    _write(out / "api" / "v1" / "index.json", _dump(manifest, indent=2))


def build(
    data_dir: Path,
    out_dir: Path,
    *,
    base_url: str = DEFAULT_BASE_URL,
    update_data_files: bool = True,
    sources: RegistrySources | None = None,
    changes_dir: Path | None = None,
) -> ValidationResult:
    """Validate sources and write the publishable tree to ``out_dir``.

    Raises :class:`BuildError` before writing anything if validation fails.
    The output directory is replaced only after a complete build.
    """
    data_dir = Path(data_dir)
    out_dir = Path(out_dir)
    site_url = base_url.rstrip("/")
    sources = sources or load_sources(data_dir)
    result = validate(sources)
    if not result.ok:
        raise BuildError(result)

    legacy_datatypes = legacy.build_datatypes(sources)
    legacy_tools = legacy.build_tools(sources)
    reg = build_registry(sources, site_url)
    info = build_info(data_dir)

    out_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".build-", dir=out_dir.parent))
    try:
        _write_legacy(staging, legacy_datatypes, legacy_tools)
        _write_api_v1(staging, reg, site_url, info)
        from .changes import load_release_changes

        releases = load_release_changes(changes_dir)
        _write(staging / "api" / "v1" / "changes.json", _dump(releases, indent=2))
        pages = _render_site(staging, reg, site_url, info, releases)
        _copy_static(staging)
        _copy_schemas(staging, data_dir)
        _write(staging / "search-index.json", _dump(_search_index(reg)))
        _write_agent_files(staging, reg, site_url, info)
        _write_sitemap(staging, pages, site_url, info)
        _write(staging / ".nojekyll", "")
        _write_manifest(staging, reg, site_url, info, len(legacy_tools))

        if out_dir.exists():
            shutil.rmtree(out_dir)
        staging.rename(out_dir)
    finally:
        if staging.exists():
            shutil.rmtree(staging)

    if update_data_files:
        write_legacy_data_files(data_dir, legacy_datatypes, legacy_tools)
    return result
