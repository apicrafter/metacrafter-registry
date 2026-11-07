## Why

The registry is the reference catalog that metacrafter links every detected
type to. That link target, `registry.apicrafter.io`, is offline today, so
every `datatype_url` printed by metacrafter is dead.

The data itself has problems:

- About a third of the records are generated stubs.
- The builder's completeness statistics are overstated: for example, 85.7%
  of records are reported as having a regexp, but the real figure is 46.7%.
- Nothing is offered to the AI agents that now do much of the data
  classification work.

See `devdocs/AUDIT_2026-11.md` for the evidence.

We want to turn the repository into a self-publishing, versioned registry: a
static site on GitHub Pages, built and validated in CI. It will serve humans,
metacrafter, and AI agents from the same YAML sources.

## What Changes

- **Static site on GitHub Pages.** It replaces the Flask server, keeps the
  `registry.apicrafter.io` domain and URL scheme, and deploys from CI on every
  merge to `main`.
- **Static JSON API.**
  - New: versioned `/api/v1/` endpoints, bulk downloads (JSON, JSONL, CSV),
    an `index.json` manifest with version and hashes, and an OpenAPI
    description.
  - Kept: the legacy `/registry.json`, `/datatype/<id>.json` and `/tools.json`
    files, frozen in their current shape.
- **Agent surfaces.**
  - `llms.txt` and `llms-full.txt`.
  - A Markdown twin of every entity page.
  - schema.org JSON-LD embedded in pages, and a SKOS (RDF) export.
  - An MCP server that agents run locally.
  - Agent skills for using the registry and for contributing to it.
- **Python package `metacrafter-registry`.** It bundles a data snapshot and
  provides lookup, URL-building and value-matching helpers, so metacrafter and
  metacrafter-llm can work offline. Each GitHub Release attaches its wheel. It
  is not published to PyPI, because the registry is used through its site and API.
- **Data model v2.**
  - JSON Schema (2020-12) replaces the Cerberus rule files, and the schema is
    published for editors and agents.
  - New fields: `status` (draft/stable/deprecated), `aliases`, `replaced_by`,
    `checksum`, typed `mappings` (Wikidata, schema.org, W3C DPV, Presidio,
    Google DLP, Microsoft Purview) and negative examples.
  - `is_pii` becomes a boolean, `parent` becomes an ID string, and empty
    values must be omitted.
  - **BREAKING** for YAML authors only. A migration script converts all
    records. Legacy JSON outputs keep their current shape.
- **Quality gates in CI.** Every pull request must pass these checks, or CI
  fails:
  - schema validity
  - unique IDs and aliases
  - resolvable references
  - every regexp compiles
  - positive examples match their regexp and negative examples do not
  - directory and country agree
  - the file name equals the ID

  Each record gets a quality score. The site shows the score, and the API
  exposes it.
- **Data curation.**
  - Fix the defects listed in the audit.
  - Merge duplicate concepts.
  - Mark generated stubs as `draft`.
  - Rename files to match their IDs.
  - Change an ID only when duplicates merge. The old ID keeps a permanent
    alias and a redirect page.
  - Fix language codes (`se` → `sv`).
- **Ecosystem alignment.**
  - The build reads metacrafter-rules and shows, for each datatype, the rules
    that detect it.
  - The `metacrafter` tool record is generated automatically.
  - CI reports orphans in both directions.
- **Releases.**
  - Data is versioned with SemVer.
  - Each release gets a git tag and a GitHub Release with the bulk assets and
    the Python package.
  - Release notes list the added, changed and deprecated IDs.
- **Repository hygiene.**
  - Add `pyproject.toml`, tests and a single CLI (`build`, `validate`,
    `stats`, `serve`, `migrate`).
  - Remove IDE files.
  - Archive one-off generator scripts, `_original/` and `analysis/`.
  - Add CONTRIBUTING and a "propose a datatype" issue form.
- **Removed:** `src/registry.py` and the Flask dependency.
  - The server-side `?q=` filter on `/registry.json` is dropped.
  - Replacements: search on the site, the MCP tools and the Python package.

## Capabilities

### New Capabilities
- `registry-data-model`: the YAML record contract for datatypes, patterns and
  tools. It covers the published JSON Schema, statuses, aliases, mappings,
  examples and reference lists.
- `registry-build`: a reproducible build and validation pipeline. It covers
  quality gates, quality scoring, honest statistics, versioning, releases and
  the changelog.
- `registry-site`: the static website on GitHub Pages. It covers entity,
  category, country and tool pages, search, the value-identification
  playground, redirects and the legacy URL contract.
- `registry-api`: static machine-readable outputs. It covers legacy JSON
  files, the `/api/v1/` endpoints, bulk downloads, the manifest, OpenAPI and
  linked data (JSON-LD, SKOS).
- `agent-integration`: surfaces for AI agents. It covers `llms.txt`, Markdown
  twins, the MCP server, agent skills and the RAG corpus.
- `ecosystem-alignment`: the contract with metacrafter and metacrafter-rules.
  It covers rule coverage, orphan reporting, the Python package for offline
  use and generated tool records.

### Modified Capabilities
- None. `openspec/specs/` does not exist yet, so all capabilities are new.

## Impact

- **Code:**
  - `scripts/builder.py` and the helper scripts are replaced by a package
    with a CLI.
  - `src/` (Flask) is removed.
  - New `.github/workflows/` and `site/` templates.
  - Schemas move to `schema/*.schema.json`.
- **Data:**
  - The migration script rewrites all 630 datatype YAML files and 12 tool
    YAML files once.
  - 180 files are renamed to `<id>.yaml`.
  - IDs change only for merged duplicates, and each keeps an alias.
- **Public URLs:** `registry.apicrafter.io` must point to GitHub Pages. This
  is a DNS change by the owner. The existing paths keep working.
- **Downstream (follow-up changes in other repos, not part of this change):**
  - metacrafter: honour `METACRAFTER_REGISTRY_URL` in
    `classify/processor.py`, and optionally depend on the package.
  - metacrafter-llm: load the JSONL from a URL or the package, and rebuild the
    index when the manifest hash changes.
  - metacrafter-rules: fix or alias the 39 orphan keys.
- **Dependencies:**
  - Added: `jsonschema` and `jinja2` (build).
  - Added, optional: `mcp` (the MCP server extra).
  - Dropped: `flask` and `cerberus`.
- **License:** the data license must be declared, and text copied from
  Wikipedia must be attributed or rewritten. See the open question in
  design.md.
