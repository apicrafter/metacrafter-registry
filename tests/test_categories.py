"""Category reference records: kinds, descriptions and aliases of retired ids."""

from __future__ import annotations

import json

from metacrafter_registry import Registry
from metacrafter_registry.build import build
from metacrafter_registry.linkcheck import check_links
from metacrafter_registry.loader import load_sources
from metacrafter_registry.validate import validate

PII = "- id: pii\n  name: PII\n  kind: sensitivity\n  description: Personal data\n"
PII_WITH_ALIAS = PII + "  aliases: [personal]\n"


def messages(data_dir):
    return [f"{i.id}: {i.message}" for i in validate(load_sources(data_dir)).errors]


def test_repository_categories_have_kind_and_description(repo_sources):
    for cid, entry in repo_sources.categories.items():
        assert entry.get("kind") in ("topic", "form", "sensitivity", "standard"), cid
        assert entry.get("description"), cid


def test_category_needs_a_kind(mini_data):
    (mini_data / "categories.yaml").write_text("- id: pii\n  name: PII\n  description: Personal\n")
    assert any(m.startswith("pii: schema:") and "kind" in m for m in messages(mini_data))


def test_unknown_kind_and_unknown_field_are_errors(mini_data):
    (mini_data / "categories.yaml").write_text(
        "- id: pii\n  name: PII\n  kind: subject\n  description: Personal\n  colour: red\n"
    )
    found = messages(mini_data)
    assert any("kind" in m and "subject" in m for m in found)
    assert any("colour" in m for m in found)


def test_used_category_needs_a_description(mini_data):
    (mini_data / "categories.yaml").write_text(
        "- id: pii\n  name: PII\n  kind: sensitivity\n- id: unused\n  name: Unused\n  kind: topic\n"
    )
    found = messages(mini_data)
    assert "pii: a category that has records needs a description" in found
    assert not any(m.startswith("unused:") for m in found)


def test_alias_must_not_equal_another_category(mini_data):
    (mini_data / "categories.yaml").write_text(
        PII + "  aliases: [geo]\n- id: geo\n  name: Geo\n  kind: topic\n"
    )
    assert any("'geo' is used by ['pii', 'geo']" in m for m in messages(mini_data))


def test_alias_must_not_repeat_in_two_categories(mini_data):
    (mini_data / "categories.yaml").write_text(
        PII_WITH_ALIAS + "- id: geo\n  name: Geo\n  kind: topic\n  aliases: [personal]\n"
    )
    assert any("'personal' is used by" in m for m in messages(mini_data))


def test_source_record_must_not_list_a_retired_category(mini_data):
    (mini_data / "categories.yaml").write_text(PII_WITH_ALIAS)
    path = mini_data / "datatypes/any/pii/email.yaml"
    path.write_text(path.read_text().replace("categories: [pii]", "categories: [personal]"))
    assert "email: category 'personal' is retired: use 'pii'" in messages(mini_data)


def test_search_resolves_a_retired_category(mini_data):
    (mini_data / "categories.yaml").write_text(PII_WITH_ALIAS)
    reg = Registry.from_sources(mini_data)
    assert reg.category_aliases == {"personal": "pii"}
    current = [r["id"] for r in reg.search(category="pii")]
    assert current
    assert [r["id"] for r in reg.search(category="personal")] == current


def test_retired_category_keeps_its_pages(mini_data, tmp_path):
    (mini_data / "categories.yaml").write_text(PII_WITH_ALIAS)
    out = tmp_path / "dist"
    build(mini_data, out, update_data_files=False)

    entry = json.loads((out / "api/v1/categories.json").read_text())[0]
    assert entry["kind"] == "sensitivity"
    assert entry["description"] == "Personal data"
    assert entry["aliases"] == ["personal"]

    page = (out / "category/personal.html").read_text()
    assert 'http-equiv="refresh"' in page and "/category/pii" in page
    assert "/category/pii.md" in (out / "category/personal.md").read_text()
    assert (out / "api/v1/categories/personal.json").read_text() == (
        out / "api/v1/categories/pii.json"
    ).read_text()

    # records list the current id only, and the alias page is not in the sitemap
    assert json.loads((out / "api/v1/datatypes/email.json").read_text())["categories"] == ["pii"]
    assert "category/personal" not in (out / "sitemap.xml").read_text()
    assert check_links(out)[1] == []


def test_category_pages_show_kind_and_description(built_site, repo_sources):
    listing = (built_site / "category/index.html").read_text()
    assert "<h2>Topics</h2>" in listing and "<h2>Standards</h2>" in listing
    description = " ".join(repo_sources.categories["gs1"]["description"].split())
    assert description in listing
    assert description in (built_site / "category/gs1.html").read_text()
    assert description in (built_site / "category/gs1.md").read_text()
    assert description in (built_site / "llms.txt").read_text()
