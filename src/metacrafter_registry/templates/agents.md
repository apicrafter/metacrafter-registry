# Metacrafter Registry for AI agents

Use the registry to answer "what is in this column?", "is this field personal data?" or "which Presidio entity is this?", and to link the answer to a stable URL (`{{ site_url }}/datatype/<id>`). Everything is free, read-only and needs no key.

Each record has a `status`. Draft records have not been reviewed yet and may be incomplete or wrong; do not treat them as authoritative for legal or compliance decisions. Filter on `status: stable` when that matters.

## Read the registry

- Index: {{ site_url }}/llms.txt; every record in one file: {{ site_url }}/llms-full.txt
- Markdown twin of any record: append `.md`, e.g. {{ site_url }}/datatype/email.md
- JSON API (OpenAPI 3.1): {{ site_url }}/api/v1/openapi.json
- One record: {{ site_url }}/api/v1/datatypes/<id>.json; former ids: {{ site_url }}/api/v1/aliases.json
- RAG corpus: {{ site_url }}/api/v1/rag/corpus.jsonl

## MCP server (local, offline)

Tools: `identify_values(values, field_name?, country?)`, `search_datatypes(query, category?, country?, is_pii?, status?)`, `get_datatype(id)`, `crosswalk(system, external_id)`, `list_categories()`, `list_countries()`. Resources: `registry://datatype/{id}` (Markdown). Sample values passed to `identify_values` never leave the machine.

Claude Code:

```
claude mcp add metacrafter-registry -- uvx --from "metacrafter-registry[mcp] @ git+https://github.com/apicrafter/metacrafter-registry" metacrafter-registry mcp
```

Other clients:

```json
{"mcpServers": {"metacrafter-registry": {"command": "uvx", "args": ["--from", "metacrafter-registry[mcp] @ git+https://github.com/apicrafter/metacrafter-registry", "metacrafter-registry", "mcp"]}}}
```

The package is installed from GitHub and is not published on PyPI. Add `@v1.3.0` to the URL to pin a release. Installed from the source, the package has no bundled snapshot: the server downloads the published data once and caches it. For offline use, install the wheel attached to a GitHub Release (https://github.com/apicrafter/metacrafter-registry/releases), which bundles the data.

## Python

```python
from metacrafter_registry import Registry

reg = Registry.fetch()  # published data, cached locally
reg.get("ssn")["id"]  # 'usssn': former ids resolve
reg.identify(["7707083893"], field_name="inn")[0]["id"]  # 'inn'
reg.url_for("email")
```

## Skills

- registry-lookup: https://github.com/apicrafter/metacrafter-registry/blob/main/skills/registry-lookup/SKILL.md
- registry-contributor: https://github.com/apicrafter/metacrafter-registry/blob/main/skills/registry-contributor/SKILL.md
