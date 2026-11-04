from __future__ import annotations

import shutil
import textwrap
from pathlib import Path

import pytest

from metacrafter_registry.build import build
from metacrafter_registry.loader import load_sources

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"


@pytest.fixture(scope="session")
def repo_sources():
    return load_sources(DATA)


@pytest.fixture(scope="session")
def built_site(tmp_path_factory, repo_sources):
    out = tmp_path_factory.mktemp("site") / "dist"
    build(DATA, out, update_data_files=False, sources=repo_sources)
    return out


@pytest.fixture
def mini_data(tmp_path) -> Path:
    """A tiny valid registry: one datatype, one pattern, one tool."""
    data = tmp_path / "data"
    shutil.copytree(DATA / "schemes", data / "schemes")
    (data / "countries.yaml").write_text("- id: US\n  name: United States\n")
    (data / "categories.yaml").write_text("- id: pii\n  name: PII\n")
    (data / "langs.yaml").write_text("- id: en\n  name: English\n- id: common\n  name: Common\n")
    write_record(
        data / "datatypes/any/pii/email.yaml",
        """
        id: email
        name: Email
        doc: Electronic mail address
        langs: [common]
        categories: [pii]
        is_pii: 'True'
        regexp: '^[^@ ]+@[^@ ]+$'
        examples:
        - value: user@example.com
          description: plain address
        """,
    )
    write_record(
        data / "datatypes/US/pii/usemail.yaml",
        """
        id: usemail
        name: US email
        doc: Email address used in the US
        langs: [en]
        country: [US]
        categories: [pii]
        semantic_type: email
        """,
    )
    write_record(
        data / "tools/other/sometool.yaml",
        """
        id: sometool
        name: Some tool
        category: other
        doc: A tool
        supported_types: [email]
        """,
    )
    return data


def write_record(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")
