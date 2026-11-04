# metacrafter-registry
Registry of metadata identifier entities like UUID, GUID, person fullname, address and so on. Linked with other sources and to be converted to ontology in the future.

It's created from list of identifiers in [Metacrafter](https://github.com/apicrafter/metacrafter) tool  and list of data classes in [Datacrafter](https://data.apicrafter.ru/class) data catalog.

# Data

The registry contains the following data structures:

* `data/datatypes/` - one YAML file per semantic datatype or pattern, organized
  as `<COUNTRY|any>/<category>/<id>.yaml`
* `data/tools/` - one YAML file per tool that supports semantic datatypes
* `data/categories.yaml` - contexts of use. Metacrafter uses them to choose the
  rules for a dataset
* `data/countries.yaml` - countries and regions (`kind: country` or `region`)
* `data/langs.yaml` - languages (`kind: language`; `common` has `kind: special`
  and means language-independent)
* `schema/` - JSON Schemas (draft 2020-12) of datatype, pattern and tool
  records, also published at `https://registry.apicrafter.io/schema/`

## Semantic datatype

A semantic datatype is a kind of value with a meaning: an identifier, a code, a
personal attribute or a commonly used data class. Fields (see
`schema/datatype.schema.json`; empty values are not allowed, omit the field):

| Field | Required | Description |
|---|---|---|
| `id` | yes | Unique id, `[a-z0-9_]`; the file must be named `<id>.yaml` |
| `name` | yes | English name |
| `status` | yes | `draft` (not reviewed yet), `stable` or `deprecated` |
| `doc` | yes | English description |
| `langs` | yes | ISO 639-1 codes; `common` for language-independent values |
| `is_pii` | yes | `true` if the value is personal data |
| `categories` | | Category ids from `data/categories.yaml` |
| `country` | | Uppercase ISO 3166-1 alpha-2 codes; must include the directory's country |
| `parent` | | Id of a broader datatype |
| `aliases` | | Former ids of this record; they keep resolving everywhere |
| `replaced_by` | | For `deprecated` records: the id to use instead |
| `classification` | | `identifier` or `categorical` |
| `regexp` | | Python `re` pattern, anchored with `^...$`; every example must match it |
| `checksum` | | Name of the check-digit algorithm, e.g. `luhn` |
| `examples` | | List of `{value, description, valid}`; `valid: false` marks a negative example |
| `mappings` | | Ids in other vocabularies: `wikidata` (e.g. `P968`), `fibo` (FIBO class IRI without `https://spec.edmcouncil.org/fibo/ontology/`), `schema_org`, `dpv`, `presidio`, `google_dlp`, `purview`, `d3m` (D3M semantic type URI, e.g. `http://schema.org/email`), `sherlock`, `cdm` (Microsoft Common Data Model trait, e.g. `means.identity.service.email`), `autotype` (AutoType benchmark test case, e.g. `isbn` or `date-chinese`) |
| `links` | | List of `{type, url}`; `type` is one of `wikipedia`, `wikidata`, `schema.org`, `doc`, `dublincore`, `bioschemas`, `datadrivendiscovery`, `other` |
| `translations` | | `{<lang>: {name, doc}}` |

## Pattern

A pattern is one representation of a datatype, for example a national passport
number format. It sets `semantic_type: <datatype id>` and follows
`schema/pattern.schema.json`. A pattern inherits `categories`, `is_pii` and
`classification` from its datatype unless it declares them.

## Tool

A tool is software that supports semantic datatypes (`schema/tool.schema.json`):
`id`, `name`, `category` (`detector`, `pii`, `etl`, `catalogs` or `other`),
`doc`, optional `website` and `supported_types` (datatype ids).

## Status and quality

Records generated from rule keys, or with no real description and no evidence
(regexp, examples or links), have `status: draft`. The site marks them and the
API exposes `status`, so agents can skip unreviewed records. Every record also
gets a quality score from 0 to 100 with the list of missing elements; see
`metacrafter-registry stats` and `metacrafter-registry report`.

## ID naming convention

- IDs are lowercase `[a-z0-9_]`.
- New country-specific IDs start with the lowercase country code and an
  underscore (`ru_inn`). Older IDs use a concatenated form (`usssn`,
  `rusfirstname`); they are kept, because metacrafter rules and stored URLs
  use them.
- An ID changes only when duplicates are merged. The old ID then becomes an
  alias of the surviving record and keeps resolving.

## Identification rules

Detection rules that map real data to these datatypes live in the companion
[metacrafter-rules](https://github.com/apicrafter/metacrafter-rules) repository.

# Code

* `src/metacrafter_registry/` - Python package with the `metacrafter-registry` CLI:
  validation, build of the static site and JSON files, local preview server,
  public URL contract check
* `tests/` - pytest suite (validation gates, legacy JSON shape, build, URL contract)
* `scripts/` - helper scripts; `scripts/builder.py` keeps `stats` and `report` and
  delegates `build` and `validate` to the package
* `schema/` - JSON Schemas of the source records
* `archive/` - historical material (original CSV, research notes, one-off scripts)
* `.github/workflows/` - CI (`ci.yml`) and GitHub Pages deployment (`pages.yml`)

# Build registry

The YAML files in `data/` are the source of truth. One command validates them and
builds everything that gets published.

1. Install the package (once):
   ```bash
   python -m venv .venv && . .venv/bin/activate
   pip install -e ".[dev]"
   ```
2. Edit YAML files in `data/`.
3. Validate (add `-w` to list warnings):
   ```bash
   metacrafter-registry validate
   ```
4. Build:
   ```bash
   metacrafter-registry build
   ```
   This writes:
   - `dist/` - the static site and JSON files deployed to GitHub Pages
     (not committed)
   - `data/datatypes_latest.json`, `data/datatypes_latest.jsonl`,
     `data/tools_latest.json`, `data/tools_latest.jsonl` - transitional files
     still read from a checkout by metacrafter tools. Commit them; CI fails if
     they are stale.

   The build fails, and writes nothing, if any record has a validation error:
   schema, unknown reference, duplicate id, regexp that does not compile,
   example that does not match its regexp, or a directory/country mismatch.
5. Preview locally with the same URL rules as GitHub Pages:
   ```bash
   metacrafter-registry serve        # http://127.0.0.1:8089
   ```
6. Run the tests and commit:
   ```bash
   pytest -q
   ```

`python scripts/builder.py <command>` still works and delegates to the same CLI.

# Python package and MCP server

```python
from metacrafter_registry import Registry

reg = Registry.load()  # bundled snapshot (wheel) or the YAML of this checkout
reg = Registry.fetch()  # published data, cached in ~/.cache, verified by SHA-256
reg.get("ssn")["id"]  # 'usssn': former ids (aliases) resolve
reg.identify(["7707083893", "7728168971"], field_name="inn")[0]["id"]  # 'inn'
reg.search("passport", country="GB")
reg.url_for("email")  # https://registry.apicrafter.io/datatype/email
```

`identify` ranks datatypes for sample values of one column. It combines:
- the regexp hit rate, weighted by how specific the regexp is;
- check digits: Luhn, IBAN mod-97, GTIN, ISBN, Russian INN, SNILS and OGRN;
- similarity to the field name.

The MCP server exposes the same functions to AI agents and runs locally:

```bash
pip install "metacrafter-registry[mcp]"
metacrafter-registry mcp            # stdio; add --refresh to download newer data
```

See https://registry.apicrafter.io/agents for client configuration, and
`skills/` for agent skills.

# metacrafter-rules coverage

`ecosystem.lock` pins a commit of
[metacrafter-rules](https://github.com/apicrafter/metacrafter-rules), and
`data/coverage/metacrafter-rules.json` summarizes every rule at that commit.
The build uses this summary for three things:
- the rules that detect each datatype (`detected_by.metacrafter_rules`);
- the `metacrafter` tool's supported types;
- `/api/v1/coverage.json`, which lists the rule keys with no registry record
  and the records with no rule.

To adopt newer rules:

```bash
git clone https://github.com/apicrafter/metacrafter-rules /tmp/metacrafter-rules
metacrafter-registry coverage update --rules-dir /tmp/metacrafter-rules/rules
metacrafter-registry build
```

CI checks the summary against the pinned commit. A weekly workflow
(`weekly.yml`) does two more checks: it compares coverage with the latest
rules, and it checks external links. It reports both in tracking issues.

# FIBO mappings

`mappings.fibo` links a record to a class of
[FIBO](https://github.com/edmcouncil/fibo), the Financial Industry Business
Ontology. Glossaries that use FIBO terms, such as a DataHub business glossary,
can then reach the registry's regexps and examples. The value is the class IRI
without `https://spec.edmcouncil.org/fibo/ontology/`:

```yaml
mappings:
  fibo: FBC/ProductsAndServices/ClientsAndAccounts/InternationalBankAccountIdentifier
```

The FIBO server answers any path, so links cannot catch a typo. Instead,
`data/vocabularies/fibo.json` pins the label, definition and maturity of every
mapped class at one FIBO commit, and `validate` rejects classes that it does not
list. After adding or changing a mapping:

```bash
git clone --depth 1 https://github.com/edmcouncil/fibo /tmp/fibo
metacrafter-registry fibo search bank account identifier --fibo-dir /tmp/fibo
metacrafter-registry fibo update --fibo-dir /tmp/fibo
metacrafter-registry build
```

Map only exact concept matches. The FIBO IRIs appear in `/registry.ttl`
(`skos:exactMatch`), in the pages' JSON-LD (`sameAs`), and in
`crosswalk("fibo", ...)`. See `devdocs/FIBO_ANALYSIS.md` for the analysis.

# Publishing

Every merge to `main` builds the site and deploys it to GitHub Pages
(`.github/workflows/pages.yml`). After deploying, the workflow checks the public
URL contract on the live site:

```bash
metacrafter-registry check-contract https://registry.apicrafter.io
```

## Public URLs

These URLs are a contract: metacrafter links every detected type to
`https://registry.apicrafter.io/datatype/<id>`, and its `RegistryClient` reads the
JSON files.

Site pages:

| Path | Description |
|---|---|
| `/` | Home: search, statistics, categories, countries |
| `/datatype/` | All datatypes and patterns, with filters (category, country, kind, PII) |
| `/datatype/<id>` | Page for one datatype or pattern (with schema.org JSON-LD) |
| `/category/`, `/category/<id>` | Categories and their datatypes |
| `/country/`, `/country/<CC>` | Countries and their datatypes |
| `/tool/`, `/tool/<id>` | Tools and the types they support (`/tool` redirects to `/tool/`) |
| `/search?q=` | Client-side search (runs in the browser) |
| `/about` | About, API reference, license, contributing |
| `/identify` | Paste column values to find their datatype (runs in the browser) |
| `/quality` | Completeness, metacrafter-rules coverage, drafts to review |
| `/changes` | Changes in each data release |
| `/agents` | MCP server, Python package, skills, llms.txt |
| `/sitemap.xml`, `/robots.txt` | For crawlers |

JSON API (static files, described in `/api/v1/openapi.json`):

| Path | Description |
|---|---|
| `/api/v1/index.json` | Manifest: version, git SHA, license, counts, file sizes and SHA-256, URL templates |
| `/api/v1/datatypes/<id>.json` | One datatype or pattern, normalized (references are id strings) |
| `/api/v1/datatypes.json`, `.jsonl`, `.csv` | All datatypes and patterns |
| `/api/v1/tools/<id>.json`, `/api/v1/tools.json`, `.jsonl` | Tools |
| `/api/v1/categories.json`, `countries.json`, `languages.json` | Reference lists with record counts |
| `/api/v1/openapi.json` | OpenAPI 3.1 description |
| `/api/v1/rag/corpus.jsonl` | One embedding text per record (template version in the manifest) |
| `/llms.txt`, `/llms-full.txt` | Index and full text for LLMs ([llmstxt.org](https://llmstxt.org)) |
| `/datatype/<id>.md`, `/tool/<id>.md`, `/category/<id>.md` | Markdown twins of the pages |
| `/registry.ttl` | SKOS concept scheme (Turtle) |
| `/api/v1/aliases.json` | Retired ids and the record each one resolves to |
| `/api/v1/coverage.json` | metacrafter-rules coverage: orphan rule keys, records without rules |
| `/api/v1/changes.json` | Changes per data release |
| `/schema/*.schema.json` | JSON Schemas of the source records |
| `/registry.json` | Legacy: all records keyed by id (release 1.02 shape) |
| `/datatype/<id>.json` | Legacy: one record (release 1.02 shape) |
| `/datatypes.jsonl`, `/tools.json`, `/tool/<id>.json` | Legacy bulk and tool files |

The legacy files keep the release 1.02 shape: fields may be added, never removed
or retyped. The static site has no server-side search: the `?q=` filter and the
`/health` endpoint of the old Flask server are not available.

Releases are published by pushing a `v*` tag (see `CONTRIBUTING.md`).

# Contacts

Maintainer - Ivan Begtin (ivan@begtin.tech)
