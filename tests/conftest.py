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


# An ISO 8601 calendar date. Its hyphens are part of the format: without them
# "2025-05-15" is eight digits, which okpo and oktmo accept.
ISO_DATE = r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$"
ISO_DATES = ["2025-05-15", "1990-01-31", "2001-12-02"]


@pytest.fixture(scope="session")
def reg_with_date(repo_sources):
    """The registry of data/, with ISO_DATE on the `date` record if it has no regexp."""
    from metacrafter_registry import Registry

    base = Registry.from_sources(DATA)
    records = [dict(r) for r in base.datatypes.values()]
    for record in records:
        if record["id"] == "date":
            record.setdefault("regexp", ISO_DATE)
    return Registry(records, aliases=base.aliases, manifest=base.manifest)


# Hexadecimal values that several records accept: only the field name tells
# them apart. The key identifier and the serial number are from the public
# e-trust register of Russian certification authorities.
HEX40 = ["E0986CEDDC7945B1D58115A79A1C75D86601A609", "DA39A3EE5E6B4B0D3255BFEF95601890AFD80709"]


@pytest.fixture(scope="session")
def reg_pki():
    """Records whose regexps accept the same hexadecimal values, with Russian names."""
    from metacrafter_registry import Registry

    def record(rid, name, regexp, example, ru=None):
        out = {
            "id": rid,
            "name": name,
            "kind": "datatype",
            "status": "stable",
            "is_pii": False,
            "regexp": regexp,
            "examples": [{"value": example}],
        }
        if ru:
            out["translations"] = {"ru": {"name": ru}}
        return out

    hex40 = r"^[0-9A-Fa-f]{40}$"
    return Registry(
        [
            record("sha1hash", "SHA-1 hash", hex40, HEX40[1], "Хеш SHA-1"),
            record(
                "x509_key_identifier",
                "X.509 key identifier (SKI, AKI)",
                hex40,
                HEX40[0],
                "Идентификатор ключа X.509 (SKI, AKI)",
            ),
            record(
                "x509_certificate_thumbprint",
                "X.509 certificate thumbprint (compact hex)",
                hex40,
                HEX40[1],
                "Отпечаток сертификата X.509",
            ),
            record(
                "x509_serial_number",
                "X.509 certificate serial number",
                r"^(?:[0-9A-Fa-f]{2}){1,20}$",
                "00A94CF4CA0000000005A1",
                "Серийный номер сертификата X.509",
            ),
        ]
    )


@pytest.fixture(scope="session")
def built_site(tmp_path_factory, repo_sources):
    out = tmp_path_factory.mktemp("site") / "dist"
    build(DATA, out, update_data_files=False, sources=repo_sources)
    return out


@pytest.fixture
def mini_data(tmp_path) -> Path:
    """A tiny valid registry: one datatype, one pattern, one tool."""
    data = tmp_path / "data"
    data.mkdir(parents=True)
    shutil.copytree(REPO / "schema", tmp_path / "schema")
    (data / "countries.yaml").write_text("- id: US\n  name: United States\n")
    (data / "categories.yaml").write_text("- id: pii\n  name: PII\n")
    (data / "langs.yaml").write_text("- id: en\n  name: English\n- id: common\n  name: Common\n")
    write_record(
        data / "datatypes/any/pii/email.yaml",
        """
        id: email
        name: Email
        status: stable
        doc: Electronic mail address
        langs: [common]
        categories: [pii]
        is_pii: true
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
        status: draft
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
