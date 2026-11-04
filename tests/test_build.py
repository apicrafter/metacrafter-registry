from __future__ import annotations

import hashlib
import json
import urllib.request

import pytest
from conftest import write_record

from metacrafter_registry.build import BuildError, build
from metacrafter_registry.contract import check_contract
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
    ):
        assert (built_site / rel).is_file(), rel


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
        "id: bad\nname: Bad\ndoc: Bad\nlangs: [en]\nis_pii: 'False'\nregexp: '(ab'\n",
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
    html = (out / "index.html").read_text("utf-8")
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
