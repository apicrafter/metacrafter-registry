"""MCP server for the registry (``metacrafter-registry mcp``).

Requires the optional dependency: ``pip install "metacrafter-registry[mcp]"``.
The server works offline from local data; sample values given to
``identify_values`` never leave the machine.
"""

from __future__ import annotations

import logging
from typing import Any

from . import __version__
from .agents import DRAFT_NOTE, record_markdown
from .client import Registry

logger = logging.getLogger(__name__)

INSTRUCTIONS = (
    "Metacrafter Registry: a catalog of semantic datatypes (identifiers, personal data, "
    "codes). Use identify_values to label a column from sample values and its field name, "
    "search_datatypes to find types by keyword, get_datatype for full details, and "
    "crosswalk to map ids from other vocabularies (e.g. Wikidata, FIBO). Cite the record url. "
    + DRAFT_NOTE
)


def _summary(registry: Registry, record: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": record["id"],
        "name": record["name"],
        "kind": record["kind"],
        "status": record["status"],
        "is_pii": record["is_pii"],
        "categories": record.get("categories", []),
        "country": record.get("country", []),
        "quality": record["quality"]["score"],
        "url": registry.url_for(record["id"]),
    }


def create_server(registry: Registry):
    """Build the MCP server around a loaded :class:`Registry`."""
    from mcp.server.mcpserver import MCPServer
    from mcp.server.mcpserver.exceptions import ResourceError, ToolError
    from mcp.types import ToolAnnotations

    read_only = ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False)
    server = MCPServer(
        name="metacrafter-registry",
        title="Metacrafter Registry",
        instructions=INSTRUCTIONS,
        website_url="https://registry.apicrafter.io/agents",
        version=__version__,
    )

    @server.tool(annotations=read_only)
    def identify_values(
        values: list[str],
        field_name: str | None = None,
        country: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Rank registry datatypes for sample values of one column.

        Uses regexp hit rate (weighted by how specific the regexp is), check-digit
        algorithms (Luhn, IBAN mod-97, INN, ...) and similarity to the field name.
        country is an ISO 3166-1 alpha-2 code that favours national datatypes.
        """
        candidates = registry.identify(
            values, field_name=field_name, country=country, limit=max(1, min(limit, 50))
        )
        return {"registry_version": registry.version, "candidates": candidates}

    @server.tool(annotations=read_only)
    def search_datatypes(
        query: str = "",
        category: str | None = None,
        country: str | None = None,
        is_pii: bool | None = None,
        status: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search datatypes by keywords in ids, names, translated names and descriptions.

        Filters: category id (see list_categories), country (ISO code), is_pii, and
        status ('stable' excludes unreviewed drafts).
        """
        hits = registry.search(
            query,
            category=category,
            country=country,
            is_pii=is_pii,
            status=status,
            limit=max(1, min(limit, 100)),
        )
        return [_summary(registry, r) for r in hits]

    @server.tool(annotations=read_only)
    def get_datatype(id: str) -> dict[str, Any]:
        """Full record of a datatype or pattern. Former ids (aliases) resolve."""
        record = registry.get(id)
        if record is None:
            raise ToolError(f"No datatype '{id}'. Try search_datatypes.")
        if record["id"] != id:
            return {**record, "resolved_from_alias": id}
        return record

    @server.tool(annotations=read_only)
    def crosswalk(system: str, external_id: str) -> list[dict[str, Any]]:
        """Registry records mapped to an id in another vocabulary.

        system: wikidata, fibo, schema_org, dpv, presidio, google_dlp, purview, d3m,
        sherlock, cdm, fta or gs1_ai. For wikidata, a property id (P968) or its URL. For fibo, a
        FIBO class IRI, e.g. https://spec.edmcouncil.org/fibo/ontology/FBC/
        ProductsAndServices/ClientsAndAccounts/InternationalBankAccountIdentifier,
        or the part after /ontology/. For cdm, a Common Data Model trait name
        (means.identity.service.email). For d3m, a D3M semantic type URI
        (http://schema.org/email) or its bare name (FileName). For purview, a
        Microsoft Purview sensitive information type name; case, periods and
        apostrophes are ignored. For fta, a semantic type as FTA (Fast Text
        Analysis) reports it (POSTAL_CODE.ZIP5_US, MONTH.FULL_fr-FR). For
        sherlock, a Sherlock semantic type label (city, birth Date); case and
        spaces are ignored. For gs1_ai, a GS1 Application Identifier (8003 or
        (8003)) or its https://ref.gs1.org/ai/ IRI.
        """
        return [_summary(registry, r) for r in registry.crosswalk(system, external_id)]

    @server.tool(annotations=read_only)
    def list_categories() -> list[dict[str, Any]]:
        """Categories (contexts of use) with the number of records in each."""
        return [c for c in registry.categories.values() if c.get("count")]

    @server.tool(annotations=read_only)
    def list_countries() -> list[dict[str, Any]]:
        """Countries and regions with the number of country-specific records."""
        return [c for c in registry.countries.values() if c.get("count")]

    @server.resource(
        "registry://datatype/{id}",
        name="datatype",
        description="A registry record as Markdown",
        mime_type="text/markdown",
    )
    def datatype_resource(id: str) -> str:
        record = registry.get(id)
        if record is None:
            raise ResourceError(f"No datatype '{id}'")
        return record_markdown(
            record,
            categories=registry.categories,
            countries=registry.countries,
            langs=registry.languages,
        )

    return server


def load_registry(
    path: str | None = None, *, refresh: bool = False, base_url: str | None = None
) -> Registry:
    """Local data first; download the published data when there is none or on refresh."""
    from . import DEFAULT_BASE_URL

    if refresh:
        try:
            return Registry.fetch(base_url or DEFAULT_BASE_URL)
        except OSError as exc:
            logger.warning("refresh failed (%s); using local data", exc)
    try:
        return Registry.load(path)
    except FileNotFoundError:
        return Registry.fetch(base_url or DEFAULT_BASE_URL)


def serve(
    path: str | None = None,
    *,
    refresh: bool = False,
    base_url: str | None = None,
    transport: str = "stdio",
    **kwargs: Any,
) -> None:
    registry = load_registry(path, refresh=refresh, base_url=base_url)
    logger.info(
        "serving %d records (%s, version %s)", len(registry), registry.source, registry.version
    )
    create_server(registry).run(transport=transport, **kwargs)
