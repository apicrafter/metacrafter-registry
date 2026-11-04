# metacrafter-registry
Registry of metadata identifier entities like UUID, GUID, person fullname, address and so on. Linked with other sources and to be converted to ontology in the future.

It's created from list of identifiers in [Metacrafter](https://github.com/apicrafter/metacrafter) tool  and list of data classes in [Datacrafter](https://data.apicrafter.ru/class) data catalog.

# Data

The registry contains the following data structures:

* `data/datatypes/` - list of all known semantic data types as separate YAML files, organized by country/language
* `data/tools/` - list of tools and software libraries that support semantic data types
* `data/categories.yaml` - list of all data contexts. Categories are used by Metacrafter tool to filter rules for certain situations/data/contexts set by user
* `data/countries.yaml` - list of all countries with available rules
* `data/langs.yaml` - list of all languages with available rules
* `data/schemes/` - JSON schema definitions for validating datatype and tool structures

## Semantic data type

Semantic data type is a primary data class with description of unique type of the data which is somehow defined identifier or commonly used data type.

Each semantic data type YAML file contains objects with the following structure:

- **id** (required) - unique identifier of the entity
- **name** (required) - name of the entity
- **doc** (required) - English documentation/short description of this entity
- **langs** (required) - list of languages (ISO 639-1 codes)
- **categories** (optional) - list of contexts associated with entity (e.g., "pii", "finance", "geo")
- **country** (optional) - list of countries where this identifier is used (ISO 3166-1 alpha-2 codes)
- **is_pii** (optional) - boolean indicating if this data is Personal Identifiable Information. PII can also be detected from categories
- **regexp** (optional) - regular expression that matches this data type
- **wikidata_property** (optional) - Wikidata property ID (not URL) if applicable
- **links** (optional) - list of associated links with **type** (wikipedia, wikidata, schema.org, datadrivendiscovery, other) and **url**
- **examples** (optional) - list of examples, each with **value** and **description**
- **parent** (optional) - parent semantic type reference
- **semantic_type** (optional) - semantic type classification
- **patterns** (optional) - list of pattern IDs associated with this datatype
- **translations** (optional) - dictionary with language codes as keys, containing translated **name** and **doc** for each language
- **classification** (optional) - additional classification metadata

See `data/schemes/datatype.json` for the complete JSON schema definition.  

## Pattern

Patterns are extensions, additional helpers to identify certain ways to represent semantinc data types. They could be different by usage type, country, language and so on.
Patterns have no category since they inherit category from semantic data type

Each pattern YAML file contains objects with the following structure:

- **id** (required) - unique identifier of the entity
- **name** (required) - name of the entity
- **doc** (required) - English documentation/short description of this entity
- **country** (optional) - list of countries where this pattern is used (ISO 3166-1 alpha-2 codes)
- **langs** (optional) - list of languages (ISO 639-1 codes)
- **links** (optional) - list of associated links with **type** (wikipedia, other) and **url**
- **regexp** (optional) - regular expression that matches this pattern
- **wikidata_property** (optional) - Wikidata property ID if applicable
- **examples** (optional) - list of examples, each with **value** and **description**

Note: Patterns inherit categories from their associated semantic data types.

## Tool

Tools are software libraries, open source or proprietary software with support of semantic data types.
Each tool YAML file contains objects with the following structure:

- **id** (required) - unique identifier of the entity
- **name** (required) - name of the tool/software library
- **category** (required) - category of the tool. Must be one of: `detector`, `pii`, `etl`, `other`
- **doc** (required) - English documentation/short description of this entity
- **website** (optional) - URL of the primary web resource about this tool
- **supported_types** (optional) - array of strings with IDs of datatypes or patterns that this tool supports

See `data/schemes/tool.json` for the complete JSON schema definition.


# Metadata sources

Metadata for this registry collected and interlinked with multiple metadata sources.
Source link defined in property `link` sub-property `type` and it could be one of:
- `wikipedia` - wikipedia page url
- `wikidata` - Wikidata property url, also should be defined as id only, not url, in `wikidata_property` property
- `schema.org` - URL to Schema.org property, like https://schema.org/boolean
- `datadrivendiscovery` - D3M metadata registry https://metadata.datadrivendiscovery.org
- `doc` - URL to external documentation or standard
- `dublincore` - Dublin Core metadata term URL
- `bioschemas` - Bioschemas profile/type URL
- `other` - any other url

The set of allowed `type` values is enforced by the datatype schema
(`data/schemes/datatype.json`).

## ID naming convention

Every datatype, pattern, and tool has a unique `id`. Conventions:

- IDs are lowercase, use `[a-z0-9_]`, and avoid spaces or punctuation.
- Country/language-specific datatypes are prefixed with the lowercase country
  or language code (e.g. `ru_inn`, `us_ssn`, `gb_nino`). Older entries may use a
  concatenated form (e.g. `runpa`, `uscity`); prefer the prefixed form for new
  additions.
- The source file **should** be named `<id>.yaml`. Filename/ID mismatches are
  tracked for migration and new files must match.
- Pattern `semantic_type` and tool `supported_types` must reference existing
  datatype IDs; this is enforced by `builder.py validate`
  (cross-reference check) and by the build's uniqueness check.


## Identification rules

**Under development**

Identification rules are regex, other pattern matching algorithms and code that help to identify certain semantic data type directly or by pattern.

# Code

* `src/metacrafter_registry/` - Python package with the `metacrafter-registry` CLI:
  validation, build of the static site and JSON files, local preview server,
  public URL contract check
* `tests/` - pytest suite (validation gates, legacy JSON shape, build, URL contract)
* `scripts/` - helper scripts; `scripts/builder.py` keeps `stats` and `report` and
  delegates `build` and `validate` to the package
* `src/registry.py` - legacy Flask server, deprecated (replaced by the static site)
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

`python scripts/builder.py build|validate|stats|report` still works.

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

| Path | Description |
|---|---|
| `/` | HTML list of datatypes |
| `/datatype/<id>` | HTML page for one datatype or pattern |
| `/datatype/<id>.json` | Single datatype as JSON |
| `/registry.json` | All datatypes and patterns as JSON, keyed by id |
| `/datatypes.jsonl` | All datatypes and patterns as JSON Lines |
| `/tool` | HTML list of tools |
| `/tool/<id>` | HTML page for one tool |
| `/tool/<id>.json` | Single tool as JSON |
| `/tools.json` | All tools as JSON, keyed by id |
| `/api/v1/index.json` | Manifest: version, git SHA, counts, file hashes, datatype URL template |

The static site has no server-side search: the `?q=` filter and `/health`
endpoint of the old Flask server are not available.

## Identification rules

Detection rules that map real data to these datatypes live in the companion
[metacrafter-rules](https://github.com/apicrafter/metacrafter-rules) repository.
Rule `key` values are aligned with datatype `id`s here; alignment is checked by
`metacrafter/scripts/ecosystem_check.py`.

# Contacts

Maintainer - Ivan Begtin (ivan@begtin.tech)
