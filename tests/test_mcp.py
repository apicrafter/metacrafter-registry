from __future__ import annotations

import sys

import anyio
import pytest

pytest.importorskip("mcp")

from mcp.client import Client  # noqa: E402

from metacrafter_registry import Registry  # noqa: E402
from metacrafter_registry.mcp_server import create_server  # noqa: E402


@pytest.fixture(scope="module")
def server():
    from conftest import DATA

    return create_server(Registry.from_sources(DATA))


def run(coro_fn):
    return anyio.run(coro_fn)


def test_tools_are_listed_and_read_only(server):
    async def main():
        async with Client(server) as client:
            return (await client.list_tools()).tools

    tools = {t.name: t for t in run(main)}
    assert set(tools) == {
        "identify_values",
        "search_datatypes",
        "get_datatype",
        "crosswalk",
        "list_categories",
        "list_countries",
    }
    assert all(t.annotations.read_only_hint for t in tools.values())


def test_identify_values_tool(server):
    async def main():
        async with Client(server) as client:
            return await client.call_tool(
                "identify_values",
                {"values": ["7707083893", "7728168971"], "field_name": "inn"},
            )

    result = run(main)
    assert not result.is_error
    top = result.structured_content["candidates"][0]
    assert top["id"] == "inn" and top["checksum"]["pass_rate"] == 1.0
    assert top["url"].endswith("/datatype/inn")


def test_get_datatype_resolves_alias_and_reports_unknown(server):
    async def main():
        async with Client(server) as client:
            alias = await client.call_tool("get_datatype", {"id": "ssn"})
            missing = await client.call_tool("get_datatype", {"id": "no_such_type"})
            return alias, missing

    alias, missing = run(main)
    assert alias.structured_content["id"] == "usssn"
    assert alias.structured_content["resolved_from_alias"] == "ssn"
    assert missing.is_error and "No datatype 'no_such_type'" in missing.content[0].text


def test_search_filters_drafts(server):
    async def main():
        async with Client(server) as client:
            return await client.call_tool(
                "search_datatypes", {"query": "hash", "status": "stable", "limit": 50}
            )

    hits = run(main).structured_content["result"]
    assert hits and all(h["status"] == "stable" for h in hits)


def test_datatype_resource_is_markdown(server):
    async def main():
        async with Client(server) as client:
            return await client.read_resource("registry://datatype/email")

    text = run(main).contents[0].text
    assert text.startswith('---\nid: "email"') and "# Email" in text


def test_stdio_server_end_to_end():
    """The real CLI over stdio: no stray stdout output may break the protocol."""
    from conftest import DATA
    from mcp.client.stdio import StdioServerParameters

    params = StdioServerParameters(
        command=sys.executable,
        args=[
            "-m",
            "metacrafter_registry.cli",
            "--data-dir",
            str(DATA),
            "mcp",
            "--data",
            str(DATA),
        ],
    )

    async def main():
        async with Client(params) as client:
            result = await client.call_tool("get_datatype", {"id": "email"})
            return result.structured_content["id"]

    assert run(main) == "email"


def test_explicit_missing_path_is_an_error(tmp_path, monkeypatch):
    from metacrafter_registry import mcp_server

    def no_network(*args, **kwargs):
        raise AssertionError("must not download")

    monkeypatch.setattr(Registry, "fetch", no_network)
    with pytest.raises(FileNotFoundError):
        mcp_server.load_registry(str(tmp_path / "missing"))


def test_refresh_falls_back_on_a_bad_download(monkeypatch):
    from conftest import DATA

    from metacrafter_registry import mcp_server

    def bad_download(*args, **kwargs):
        raise ValueError("datatypes.jsonl: SHA-256 does not match the manifest")

    monkeypatch.setattr(Registry, "fetch", bad_download)
    assert len(mcp_server.load_registry(str(DATA), refresh=True)) > 0
