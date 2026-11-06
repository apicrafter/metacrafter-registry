<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Check `openspec/` (run `openspec list`) when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Project context and rules are in `openspec/config.yaml`. The active change is
`openspec/changes/modernize-registry-platform/` (proposal, design, specs,
tasks). The audit behind it is `devdocs/AUDIT_2026-11.md`.
Use `openspec instructions <artifact> --change <id>` for artifact formats.

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# AGENTS.md - Metacrafter Registry

Guidance for AI agents working in this repository.

## Overview

The Metacrafter Registry is a catalog of semantic datatypes: what a value
means (an email address, a Russian INN, an IBAN), with regular expressions,
examples, links to Wikipedia, Wikidata and Schema.org, and translations.
[Metacrafter](https://github.com/apicrafter/metacrafter) links every detected
type to `https://registry.apicrafter.io/datatype/<id>`, and the rule `key`s in
[metacrafter-rules](https://github.com/apicrafter/metacrafter-rules) are
registry ids.

The YAML files in `data/` are the source of truth. A build turns them into a
static site and JSON API that GitHub Pages serves at
https://registry.apicrafter.io. The old address
https://apicrafter.github.io/metacrafter-registry/ redirects there.

## Repository structure

```
data/
  datatypes/<COUNTRY|any>/<category>/<id>.yaml   one datatype or pattern per file
  tools/<category>/<id>.yaml                      one tool per file
  categories.yaml, countries.yaml, langs.yaml     reference lists
  datatypes_latest.json(l), tools_latest.json(l)  generated legacy files (committed)
schema/                     JSON Schemas of datatype, pattern and tool records
src/metacrafter_registry/   package and CLI `metacrafter-registry`
  templates/, static/       site templates, CSS and JS
tests/                      pytest suite
scripts/                    builder.py (wrapper), generate_missing_entries.py, check_qddate.py,
                            wikidata_properties.py (compare with Wikidata identifier properties)
.github/workflows/          ci.yml, pages.yml (deploy), release.yml (tags),
                            weekly.yml (rules drift and external links)
.github/ISSUE_TEMPLATE/     issue forms: propose a datatype, fix a datatype
openspec/                   OpenSpec config and change proposals
devdocs/                    audit and analysis notes
archive/                    historical material; not maintained, not built
```

## Commands

Install once with `pip install -e ".[dev]"`. Then:

```bash
metacrafter-registry validate        # schema + semantic checks; -w lists warnings
metacrafter-registry build           # dist/ (site + JSON) and data/*_latest.json(l)
metacrafter-registry serve           # preview dist/ at http://127.0.0.1:8089
metacrafter-registry stats           # honest completeness and quality statistics
metacrafter-registry report --status draft --limit 20   # records that need work
metacrafter-registry migrate --check # sources are in canonical v2 form
metacrafter-registry check-links     # internal links of dist/ resolve
metacrafter-registry check-contract <base-url>   # public URLs work
metacrafter-registry coverage report # metacrafter-rules coverage and orphan rule keys
metacrafter-registry coverage update --rules-dir <metacrafter-rules>/rules   # bump the pinned rules
metacrafter-registry coverage check --rules-dir <metacrafter-rules>/rules    # summary matches the checkout
metacrafter-registry fibo search <words> --fibo-dir <fibo checkout>   # find a FIBO class
metacrafter-registry fibo update --fibo-dir <fibo checkout>   # pin the FIBO classes that records map to
metacrafter-registry fibo check --fibo-dir <fibo checkout>    # pinned list matches the checkout
metacrafter-registry changes --old <prev datatypes.jsonl>   # changelog between versions
metacrafter-registry mcp             # MCP server over stdio (needs the [mcp] extra)
metacrafter-registry snapshot        # bundle dist/ data into the package (release only)
pytest -q
```

## Agent skills

- `skills/registry-lookup/SKILL.md` - label dataset columns with registry
  types (MCP tools, Python package or HTTP).
- `skills/registry-contributor/SKILL.md` - add or improve records so that they
  pass validation. Follow it when you edit `data/`.

## Record format (v2)

Full contract: `schema/datatype.schema.json`, `schema/pattern.schema.json`,
`schema/tool.schema.json`. Empty values are not allowed: omit the field.

```yaml
# Illustrative record: field values show the format, not verified facts.
id: ru_inn                  # [a-z0-9_]; the file must be named ru_inn.yaml
name: Russian taxpayer number (INN)
status: stable              # draft (not reviewed) | stable | deprecated
doc: Taxpayer identification number issued by the Russian tax service ...
categories: [finances, pii]  # ids from data/categories.yaml
country: [RU]               # uppercase ISO 3166-1 alpha-2; must include the directory's country
langs: [ru]                 # ISO 639-1, or common for language-independent values
is_pii: true                # boolean
classification: identifier  # identifier | categorical
regexp: '^(?:\d{10}|\d{12})$'   # Python re, anchored, no possessive quantifiers
checksum: ru_inn            # optional check-digit algorithm name
examples:
- value: '7707083893'       # always a string; never a real person's data
  description: Organization INN
- value: '1234567890'
  valid: false              # negative example: must not match the regexp
mappings:                   # ids in other vocabularies; only ones you verified
  wikidata: P968            # an id, never a URL (P968 is shown for illustration)
  fibo: FBC/...             # FIBO class IRI without https://spec.edmcouncil.org/fibo/ontology/
links:
- type: wikipedia           # wikipedia | wikidata | schema.org | doc | dublincore | bioschemas | datadrivendiscovery | other
  url: https://en.wikipedia.org/wiki/Taxpayer_Identification_Number
translations:
  ru: {name: ИНН, doc: Идентификационный номер налогоплательщика}
```

Other fields: `parent` (id of a broader datatype), `aliases` (former ids),
`replaced_by` (for deprecated records).

**Patterns** are one representation of a datatype: they set
`semantic_type: <datatype id>` and inherit `categories`, `is_pii` and
`classification` unless they declare them.

**Tools**: `id`, `name`, `category` (detector, pii, etl, catalogs, other),
`doc`, `website`, `supported_types` (datatype ids).

## Rules for changes

- Run `metacrafter-registry validate` and `metacrafter-registry build`, then
  commit the YAML change **together with** the regenerated
  `data/*_latest.json(l)`. CI fails if they are stale.
- A new or unreviewed record is `status: draft`. Mark a record `stable` only
  when it has a real description and evidence (regexp, examples or an
  authoritative link) that you checked.
- Never invent facts: no made-up regexps, placeholder examples
  (`1234567890`), generic links (the country's Wikipedia page) or real
  people's personal data. Leave a field out instead.
- Write descriptions in your own words. Do not paste Wikipedia text.
- Never remove or rename a published id. To merge duplicates, keep one record
  and add the other id to its `aliases`; the old id keeps resolving in
  `/datatype/<id>`, `/datatype/<id>.json`, `registry.json` and the JSONL.
- The public URLs (`/datatype/<id>`, `/datatype/<id>.json`, `/registry.json`,
  `/tools.json`, `/tool/<id>`, `/api/v1/...`) are a contract used by
  metacrafter and stored catalog metadata. Do not break them.
- Larger changes (data model, URL contract, build) go through OpenSpec (see
  the managed block above).

## What the build checks

The build fails, and writes nothing, on:
- schema errors
- unknown categories, countries or languages
- duplicate ids or aliases
- an unresolved `semantic_type`, `parent`, `replaced_by` or tool
  `supported_types`
- a file name that differs from the id
- a regexp that does not compile or uses non-portable syntax
- an example that does not match its whole regexp, or a negative example that
  matches it
- a directory that does not match the record's country
- a `mappings.fibo` class missing from `data/vocabularies/fibo.json`

Warnings: unanchored regexps, Python-only regexp syntax, placeholder-like
examples.

## Package modules (`src/metacrafter_registry/`)

- `loader.py`: loads the YAML sources and reference lists deterministically.
- `validate.py`: validates against the JSON Schema and runs the semantic
  gates.
- `migrate.py`: converts v1 records to the v2 contract. It is idempotent and
  defines the canonical YAML form.
- `model.py`: builds the normalized records for `/api/v1/` and the site.
- `quality.py`: scores each record from 0 to 100 and lists missing elements.
- `stats.py`: the `stats` and `report` commands.
- `legacy.py`: the release 1.02 JSON shape, which is a public contract.
  Fields may be added, never removed or retyped.
- `build.py`: renders `dist/` and writes the manifest.
- `openapi.py`: the OpenAPI 3.1 description.
- `client.py`: the public `Registry` API: `load`, `fetch`, `get`, `search`,
  `identify`, `match`, `crosswalk`, `url_for`.
- `checksums.py`: the check-digit algorithms named by the `checksum` field.
- `agents.py`: Markdown twins, `llms.txt`, `llms-full.txt`, the RAG corpus and
  the SKOS export.
- `coverage.py`: metacrafter-rules coverage. `ecosystem.lock` pins the
  rules commit, and `data/coverage/metacrafter-rules.json` is its committed
  summary, so builds need no network. The list of the `metacrafter` tool's
  `supported_types` is generated from it; do not edit it by hand.
- `fibo.py`: FIBO mappings. `data/vocabularies/fibo.json` pins the label,
  definition and maturity of each mapped FIBO class at one FIBO commit, so
  validation needs no network. Regenerate it with `fibo update`; do not edit it
  by hand.
- `datahub.py`: the DataHub business glossary, `/datahub-glossary.yml`. Term ids
  are registry ids, the URNs that metacrafter's DataHub export attaches.
- `changes.py`: the changelog between two data versions, used for release
  notes and the `/changes` page.
- `mcp_server.py`: the MCP server: tools `identify_values`,
  `search_datatypes`, `get_datatype`, `crosswalk`, `list_categories`,
  `list_countries`, and the resource `registry://datatype/{id}`.
- `serve.py`, `contract.py`, `linkcheck.py`: the local Pages-like server, the
  URL contract check and the link checker.

## Publishing

- **CI** (`ci.yml`) runs on every pull request. It runs:
  - lint and tests on Python 3.10 and 3.13
  - validate
  - build
  - the freshness check of `data/*_latest.*`
  - the link check
  - the URL contract against a local server
- **Deploy** (`pages.yml`) runs on every push to `main`. It deploys `dist/` to
  GitHub Pages, then checks the live site.
- **Releases** (`release.yml`) run when a `v*` tag is pushed. They publish the
  bulk files as a GitHub Release. The versioning policy is in
  `CONTRIBUTING.md`.

## Relationship to other repositories

- **metacrafter** builds `https://registry.apicrafter.io/datatype/<id>`
  links. Its `RegistryClient` reads `/registry.json` and
  `/datatype/<id>.json`. Its LLM mode reads `data/datatypes_latest.jsonl`
  from a checkout.
- **metacrafter-rules**: every rule `key` should be a registry id or alias.
  `scripts/generate_missing_entries.py` creates draft records for missing
  keys.
