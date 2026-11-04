"""Build the publishable tree (static site + JSON) from registry sources."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from jinja2 import Environment, PackageLoader, select_autoescape

from . import DEFAULT_BASE_URL, __version__, legacy
from .loader import RegistrySources, load_sources
from .validate import ValidationResult, validate


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
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch:
        generated_at = datetime.fromtimestamp(int(epoch), tz=timezone.utc).isoformat()
    else:
        commit_time = _git(["log", "-1", "--format=%cI"], repo_dir)
        if commit_time:
            generated_at = datetime.fromisoformat(commit_time).astimezone(timezone.utc).isoformat()
    return BuildInfo(version=__version__, git_sha=sha, generated_at=generated_at)


def _dump(obj: Any, *, indent: int | None = None) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=indent, default=str)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_legacy_data_files(data_dir: Path, datatypes: dict, tools: dict) -> list[Path]:
    """Write the transitional committed files ``data/*_latest.json(l)``."""
    files = {
        data_dir / "datatypes_latest.json": _dump(datatypes),
        data_dir / "datatypes_latest.jsonl": "".join(_dump(r) + "\n" for r in datatypes.values()),
        data_dir / "tools_latest.json": _dump(tools),
        data_dir / "tools_latest.jsonl": "".join(_dump(r) + "\n" for r in tools.values()),
    }
    for path, text in files.items():
        _write(path, text)
    return list(files)


def _render_site(
    out: Path,
    datatypes: dict,
    tools: dict,
    base_url: str,
    info: BuildInfo,
) -> None:
    env = Environment(
        loader=PackageLoader("metacrafter_registry", "templates"),
        autoescape=select_autoescape(["html"]),
        keep_trailing_newline=True,
    )
    site_url = base_url.rstrip("/")
    context = {
        "base": urlparse(site_url).path.rstrip("/"),
        "site_url": site_url,
        "version": info.version,
        "git_sha": info.git_sha,
    }

    def render(template: str, target: str, **kwargs: Any) -> None:
        _write(out / target, env.get_template(template).render(**context, **kwargs))

    render("datatype_list.html", "index.html", objects=list(datatypes.values()))
    for rid, record in datatypes.items():
        render("datatype.html", f"datatype/{rid}.html", object=record)
        _write(out / "datatype" / f"{rid}.json", _dump(record, indent=2))
    render("tool_list.html", "tool/index.html", objects=list(tools.values()))
    for rid, record in tools.items():
        render("tool.html", f"tool/{rid}.html", object=record)
        _write(out / "tool" / f"{rid}.json", _dump(record, indent=2))
    render("404.html", "404.html")


def build(
    data_dir: Path,
    out_dir: Path,
    *,
    base_url: str = DEFAULT_BASE_URL,
    update_data_files: bool = True,
    sources: RegistrySources | None = None,
) -> ValidationResult:
    """Validate sources and write the publishable tree to ``out_dir``.

    Raises :class:`BuildError` before writing anything if validation fails.
    The output directory is replaced atomically only after a complete build.
    """
    data_dir = Path(data_dir)
    out_dir = Path(out_dir)
    sources = sources or load_sources(data_dir)
    result = validate(sources)
    if not result.ok:
        raise BuildError(result)

    datatypes = legacy.build_datatypes(sources)
    tools = legacy.build_tools(sources)
    info = build_info(data_dir)

    out_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".build-", dir=out_dir.parent))
    try:
        _render_site(staging, datatypes, tools, base_url, info)
        _write(staging / "registry.json", _dump(datatypes))
        _write(staging / "tools.json", _dump(tools))
        _write(staging / "datatypes.jsonl", "".join(_dump(r) + "\n" for r in datatypes.values()))
        _write(staging / ".nojekyll", "")

        bulk = ["registry.json", "tools.json", "datatypes.jsonl"]
        manifest = {
            "name": "metacrafter-registry",
            "version": info.version,
            "git_sha": info.git_sha,
            "generated_at": info.generated_at,
            "base_url": base_url.rstrip("/"),
            "datatype_url_template": base_url.rstrip("/") + "/datatype/{id}",
            "counts": {
                "datatypes": sum(1 for r in datatypes.values() if r["type"] == "datatype"),
                "patterns": sum(1 for r in datatypes.values() if r["type"] == "pattern"),
                "tools": len(tools),
            },
            "files": {
                name: {
                    "path": "/" + name,
                    "bytes": (staging / name).stat().st_size,
                    "sha256": _sha256(staging / name),
                }
                for name in bulk
            },
        }
        _write(staging / "api" / "v1" / "index.json", _dump(manifest, indent=2))

        if out_dir.exists():
            shutil.rmtree(out_dir)
        staging.rename(out_dir)
    finally:
        if staging.exists():
            shutil.rmtree(staging)

    if update_data_files:
        write_legacy_data_files(data_dir, datatypes, tools)
    return result
