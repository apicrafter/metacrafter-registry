from __future__ import annotations

from conftest import write_record

from metacrafter_registry.loader import load_sources
from metacrafter_registry.validate import validate


def messages(data_dir, level="error"):
    result = validate(load_sources(data_dir))
    issues = result.errors if level == "error" else result.warnings
    return [f"{i.id}: {i.message}" for i in issues]


def test_repository_data_has_no_errors(repo_sources):
    result = validate(repo_sources)
    assert result.errors == [], "\n".join(map(str, result.errors))


def test_mini_registry_is_valid(mini_data):
    assert messages(mini_data) == []


def test_regexp_must_compile(mini_data):
    write_record(
        mini_data / "datatypes/any/pii/bad.yaml",
        "id: bad\nname: Bad\ndoc: Bad regexp\nlangs: [en]\nis_pii: 'False'\nregexp: '(ab'\n",
    )
    assert any("bad: regexp does not compile" in m for m in messages(mini_data))


def test_possessive_quantifier_is_rejected(mini_data):
    write_record(
        mini_data / "datatypes/any/pii/num.yaml",
        "id: num\nname: Num\ndoc: Number\nlangs: [en]\nis_pii: 'False'\nregexp: '^\\d{1,4}+$'\n",
    )
    errors = messages(mini_data)
    # Python 3.11+ reports the portability error; 3.10 cannot compile it at all.
    assert any(
        m.startswith("num: regexp uses possessive") or m.startswith("num: regexp does not compile")
        for m in errors
    ), errors


def test_example_must_match_regexp(mini_data):
    write_record(
        mini_data / "datatypes/any/pii/code.yaml",
        """
        id: code
        name: Code
        doc: Four digit code
        langs: [en]
        is_pii: 'False'
        regexp: '^\\d{4}$'
        examples:
        - value: '12345'
        """,
    )
    assert any("example '12345' does not match" in m for m in messages(mini_data))


def test_negative_example_must_not_match(mini_data):
    write_record(
        mini_data / "datatypes/any/pii/code.yaml",
        """
        id: code
        name: Code
        doc: Four digit code
        langs: [en]
        is_pii: 'False'
        regexp: '^\\d{4}$'
        examples:
        - value: '1234'
          valid: false
        """,
    )
    assert any("negative example '1234' matches" in m for m in messages(mini_data))


def test_directory_country_mismatch(mini_data):
    write_record(
        mini_data / "datatypes/US/pii/usthing.yaml",
        "id: usthing\nname: X\ndoc: Thing\nlangs: [en]\ncountry: [RU]\nis_pii: 'False'\n",
    )
    errors = messages(mini_data)
    assert any("usthing: record in datatypes/US/ must list 'US'" in m for m in errors)
    assert any("unknown country id 'RU'" in m for m in errors)


def test_single_country_in_any_dir(mini_data):
    write_record(
        mini_data / "datatypes/any/pii/local.yaml",
        "id: local\nname: X\ndoc: Thing\nlangs: [en]\ncountry: [US]\nis_pii: 'False'\n",
    )
    assert any("local: record in any/ has a single country" in m for m in messages(mini_data))


def test_duplicate_ids(mini_data):
    write_record(
        mini_data / "datatypes/any/pii/email_copy.yaml",
        "id: email\nname: Copy\ndoc: Copy\nlangs: [en]\nis_pii: 'True'\n",
    )
    assert any("email: duplicate id" in m for m in messages(mini_data))


def test_unresolved_references(mini_data):
    write_record(
        mini_data / "datatypes/any/pii/orphan.yaml",
        "id: orphan\nname: X\ndoc: X\nlangs: [xx]\nsemantic_type: nothing\n",
    )
    errors = messages(mini_data)
    assert any("unknown semantic_type 'nothing'" in m for m in errors)
    assert any("unknown langs id 'xx'" in m for m in errors)


def test_filename_mismatch_is_a_warning(mini_data):
    write_record(
        mini_data / "datatypes/any/pii/other_name.yaml",
        "id: realname\nname: X\ndoc: X\nlangs: [en]\nis_pii: 'False'\n",
    )
    assert messages(mini_data) == []
    assert any("file name should be 'realname.yaml'" in m for m in messages(mini_data, "warning"))
