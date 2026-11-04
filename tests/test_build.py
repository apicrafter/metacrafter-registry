from __future__ import annotations

import hashlib
import json
import urllib.request

import pytest
from conftest import write_record

from metacrafter_registry.build import BuildError, build
from metacrafter_registry.contract import check_contract
from metacrafter_registry.linkcheck import check_links
from metacrafter_registry.serve import running_server


def tree_hash(root):
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def test_site_layout(built_site):
    for rel in (
        "index.html",
        "404.html",
        ".nojekyll",
        "registry.json",
        "tools.json",
        "datatypes.jsonl",
        "api/v1/index.json",
        "datatype/email.html",
        "datatype/email.json",
        "tool/index.html",
        "tool/presidio.html",
        "tool/presidio.json",
        "datatype/index.html",
        "category/index.html",
        "category/pii.html",
        "country/index.html",
        "country/RU.html",
        "about.html",
        "search.html",
        "search-index.json",
        "sitemap.xml",
        "robots.txt",
        "assets/site.css",
        "assets/site.js",
        "api/v1/datatypes/email.json",
        "api/v1/datatypes.json",
        "api/v1/datatypes.jsonl",
        "api/v1/datatypes.csv",
        "api/v1/tools/presidio.json",
        "api/v1/tools.json",
        "api/v1/categories.json",
        "api/v1/countries.json",
        "api/v1/languages.json",
        "api/v1/openapi.json",
    ):
        assert (built_site / rel).is_file(), rel


def test_no_third_party_assets(built_site):
    for page in ("index.html", "datatype/email.html", "datatype/index.html"):
        html = (built_site / page).read_text("utf-8")
        assert '<script src="http' not in html and 'stylesheet" href="http' not in html


def test_internal_links_resolve(built_site):
    checked, broken = check_links(built_site)
    assert checked > 10000
    assert [str(b) for b in broken] == []


def test_internal_links_with_project_base_path(mini_data, tmp_path):
    out = tmp_path / "dist"
    build(
        mini_data,
        out,
        base_url="https://apicrafter.github.io/metacrafter-registry",
        update_data_files=False,
    )
    checked, broken = check_links(out, "/metacrafter-registry")
    assert checked > 0
    assert [str(b) for b in broken] == []


def test_build_info_uses_commit_time(monkeypatch, tmp_path):
    from metacrafter_registry import build as build_module

    # A GitHub merge commit; its ISO date ends in "Z", which Python 3.10 cannot parse.
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    monkeypatch.setattr(
        build_module, "_git", lambda args, cwd: "1793797539" if "--format=%ct" in args else "abc"
    )
    info = build_module.build_info(tmp_path)
    assert info.generated_at == "2026-11-04T13:05:39+00:00"

    monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")
    assert build_module.build_info(tmp_path).generated_at == "1970-01-01T00:00:00+00:00"


def test_full_site_build_is_reproducible(repo_sources, tmp_path):
    from conftest import DATA

    build(DATA, tmp_path / "a", update_data_files=False, sources=repo_sources)
    build(DATA, tmp_path / "b", update_data_files=False, sources=repo_sources)
    assert tree_hash(tmp_path / "a") == tree_hash(tmp_path / "b")


def test_manifest(built_site):
    manifest = json.loads((built_site / "api/v1/index.json").read_text("utf-8"))
    assert manifest["datatype_url_template"] == "https://registry.apicrafter.io/datatype/{id}"
    registry = built_site / "registry.json"
    expected = hashlib.sha256(registry.read_bytes()).hexdigest()
    assert manifest["files"]["registry.json"]["sha256"] == expected


def test_build_is_reproducible(mini_data, tmp_path):
    build(mini_data, tmp_path / "a", update_data_files=False)
    build(mini_data, tmp_path / "b", update_data_files=False)
    assert tree_hash(tmp_path / "a") == tree_hash(tmp_path / "b")


def test_invalid_sources_leave_previous_output(mini_data, tmp_path):
    out = tmp_path / "dist"
    build(mini_data, out, update_data_files=False)
    before = tree_hash(out)
    write_record(
        mini_data / "datatypes/any/pii/bad.yaml",
        "id: bad\nname: Bad\nstatus: stable\ndoc: Bad\nlangs: [en]\nis_pii: false\nregexp: '(ab'\n",
    )
    with pytest.raises(BuildError):
        build(mini_data, out, update_data_files=False)
    assert tree_hash(out) == before


def test_project_path_base_url(mini_data, tmp_path):
    out = tmp_path / "dist"
    build(
        mini_data,
        out,
        base_url="https://apicrafter.github.io/metacrafter-registry",
        update_data_files=False,
    )
    html = (out / "datatype/index.html").read_text("utf-8")
    assert 'href="/metacrafter-registry/datatype/email"' in html
    page = (out / "datatype/email.html").read_text("utf-8")
    assert (
        'rel="canonical" href="https://apicrafter.github.io/metacrafter-registry/datatype/email"'
        in page
    )


def test_pages_like_server(built_site):
    with running_server(built_site) as base:
        with urllib.request.urlopen(base + "/datatype/email") as response:
            assert response.status == 200
            assert "text/html" in response.headers["Content-Type"]
        with urllib.request.urlopen(base + "/tool") as response:  # follows 301 to /tool/
            assert response.geturl().endswith("/tool/")
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(base + "/datatype/does-not-exist")
        assert exc.value.code == 404


def test_url_contract_on_local_build(built_site):
    with running_server(built_site) as base:
        results = check_contract(base)
    failed = [str(r) for r in results if not r.ok]
    assert failed == []
