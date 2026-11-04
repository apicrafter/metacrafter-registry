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

This document provides guidance for AI agents working with the Metacrafter Registry codebase.

## Overview

Metacrafter Registry is a comprehensive registry of metadata identifier entities (semantic data types) used for data classification and labeling. It contains structured metadata about data types, patterns, tools, categories, countries, and languages. The registry links to external sources like Wikipedia, Wikidata, Schema.org, and DataDrivenDiscovery.

## Repository Structure

```
metacrafter-registry/
├── data/                    # Registry data (YAML source files)
│   ├── datatypes/          # Semantic data types organized by country/language
│   │   ├── any/            # Language-agnostic datatypes (221 files)
│   │   │   ├── medical/    # Medical identifiers
│   │   │   ├── finance/    # Financial identifiers
│   │   │   └── ...
│   │   ├── US/             # US-specific datatypes
│   │   ├── RU/             # Russian-specific datatypes (69 files)
│   │   ├── DE/             # German-specific datatypes
│   │   ├── FR/             # French-specific datatypes
│   │   ├── CA/             # Canadian datatypes
│   │   └── [other countries]/
│   ├── tools/              # Tools and software libraries
│   │   ├── detectors/      # Detection tools
│   │   ├── pii/            # PII detection tools
│   │   ├── etl/            # ETL tools
│   │   └── other/          # Other tools
│   ├── categories.yaml     # Data contexts/categories
│   ├── countries.yaml      # Country metadata
│   ├── langs.yaml          # Language metadata
│   ├── schemes/            # JSON schemas
│   │   ├── datatype.json   # Datatype schema
│   │   └── tool.json       # Tool schema
│   ├── datatypes_latest.json   # Built JSON (all datatypes)
│   ├── datatypes_latest.jsonl  # Built JSONL (one per line)
│   ├── tools_latest.json       # Built JSON (all tools)
│   └── tools_latest.jsonl      # Built JSONL (one per line)
├── src/
│   ├── metacrafter_registry/  # Package + CLI: validate, build, serve, check-contract
│   │   └── templates/         # Jinja2 templates of the static site
│   ├── registry.py         # Legacy Flask server (deprecated)
│   └── templates/          # Templates of the legacy Flask server
├── tests/                  # pytest suite
├── .github/workflows/      # ci.yml, pages.yml (GitHub Pages deploy)
├── openspec/               # OpenSpec config and change proposals
├── devdocs/                # Audit and analysis notes
├── scripts/                # Build and utility scripts
│   ├── builder.py          # Legacy entry point (stats, report; delegates build/validate)
│   ├── export.py           # Export utilities
│   ├── enrich_datatypes.py # Data enrichment
│   └── analyze_missing_rules.py  # Analysis tools
├── _original/              # Original source data (CSV format)
└── analysis/               # Analysis and research
```

## Key Components

### 1. Data Types (`data/datatypes/`)

Semantic data types are the core entities. Each datatype is a YAML file containing:

```yaml
id: email                    # Unique identifier
name: Email Address          # Human-readable name
doc: Electronic mail address # Description
langs: [en]                 # Language codes (ISO 639-1)
categories: [pii, internet] # Context categories
country: [us, gb]           # Country codes (ISO 3166-1 alpha-2)
is_pii: True               # PII flag
regexp: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
wikidata_property: P968     # Wikidata property ID
links:
  - type: wikipedia
    url: https://en.wikipedia.org/wiki/Email_address
examples:
  - value: "user@example.com"
    description: "Standard email format"
parent: identifier          # Parent datatype reference
semantic_type: email        # Semantic classification
patterns: [email_standard]  # Associated pattern IDs
translations:
  ru:
    name: "Адрес электронной почты"
    doc: "Адрес электронной почты"
```

### 2. Patterns

Patterns are variations/implementations of semantic data types. They inherit categories from their parent datatype and may have country/language-specific variations.

### 3. Tools (`data/tools/`)

Tools are software libraries or applications that support semantic data types:

```yaml
id: metacrafter
name: Metacrafter
category: detector          # detector, pii, etl, other
doc: Data classification tool
website: https://github.com/apicrafter/metacrafter
supported_types: [email, phone, ssn, ...]
```

### 4. Categories (`data/categories.yaml`)

Context categories used to filter rules (e.g., "pii", "finance", "geo", "medical").

### 5. Countries (`data/countries.yaml`)

Country metadata with ISO 3166-1 alpha-2 codes.

### 6. Languages (`data/langs.yaml`)

Language metadata with ISO 639-1 codes.

## Build System

### Package and CLI (`src/metacrafter_registry/`)

Install once with `pip install -e ".[dev]"`. Then:

```bash
metacrafter-registry validate      # schema + semantic checks; -w lists warnings
metacrafter-registry build         # dist/ (site + JSON) and data/*_latest.json(l)
metacrafter-registry serve         # preview dist/ with GitHub Pages URL rules
metacrafter-registry check-contract <base-url>   # verify public URLs
pytest -q
```

Modules:
- `loader.py` - deterministic loading of YAML sources and reference lists
- `validate.py` - validation gates (see below)
- `legacy.py` - the release 1.02 JSON shape. This shape is a public contract:
  do not remove or retype fields
- `build.py` - renders `dist/`, writes the manifest `api/v1/index.json` and the
  transitional `data/*_latest.*` files
- `serve.py`, `contract.py` - local Pages-like server and URL contract check
- `templates/` - Jinja2 templates of the site

**Validation gates.** The build fails, and writes nothing, on any of these:
- schema error
- unknown category, country or language id
- duplicate id
- unresolved `semantic_type`, `parent` or tool `supported_types`
- regexp that does not compile
- example that does not match its regexp
- record under `datatypes/<CC>/` without `<CC>` in `country`
- record under `datatypes/any/` with exactly one country

Warnings, which do not fail the build: file name differs from id, unanchored
regexp, Python-only regexp syntax.

**Committed outputs.** `data/datatypes_latest.json(l)` and
`data/tools_latest.json(l)` are still committed, because metacrafter tools read
them from a checkout. Always run `metacrafter-registry build` and commit them
together with YAML changes; CI fails if they are stale.

`scripts/builder.py build|validate|stats|report` still works. Its `build` and
`validate` commands delegate to the package.

### Publishing

`.github/workflows/pages.yml` deploys `dist/` to GitHub Pages on every push to
`main`, then runs `check-contract` against the live site.
`.github/workflows/ci.yml` runs lint, tests, validation, build, the
freshness check and the URL contract on every PR.

### Legacy Flask server (`src/registry.py`)

Deprecated. Use `metacrafter-registry serve` instead. It will be removed with
the schema v2 migration.

## Common Tasks

### Adding a New Datatype

1. **Choose location:**
   - Language-agnostic: `data/datatypes/any/{category}/`
   - Country-specific: `data/datatypes/{COUNTRY_CODE}/{category}/`

2. **Create YAML file:**
   ```yaml
   id: new_datatype
   name: New Data Type
   doc: Description of the data type
   langs: [en]
   categories: [category1, category2]
   country: [US]  # Optional; uppercase ISO 3166-1 alpha-2, must match the directory
   is_pii: 'False'  # quoted string until the schema v2 migration
   regexp: '^pattern$'  # Optional; anchored; every example must match it
   examples:
     - value: "example"
       description: "Example value"
   ```

3. **Validate and rebuild:**
   ```bash
   metacrafter-registry validate
   metacrafter-registry build
   ```

4. **Preview:**
   ```bash
   metacrafter-registry serve
   # Browse to http://127.0.0.1:8089/datatype/new_datatype
   ```

5. **Commit** the YAML file together with the regenerated `data/*_latest.*` files.

### Adding a Pattern

Patterns are variations of datatypes:

```yaml
id: email_standard
name: Standard Email Format
doc: Standard email address format
semantic_type: email  # Links to parent datatype
regexp: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
country: [us, gb]
examples:
  - value: "user@example.com"
    description: "Standard format"
```

### Adding a Tool

1. **Choose category directory:**
   - `data/tools/detectors/` - Detection tools
   - `data/tools/pii/` - PII detection tools
   - `data/tools/etl/` - ETL tools
   - `data/tools/other/` - Other tools

2. **Create YAML file:**
   ```yaml
   id: tool_name
   name: Tool Name
   category: detector
   doc: Description of the tool
   website: https://example.com
   supported_types: [email, phone, ssn]
   ```

3. **Rebuild and test**

### Updating Metadata

1. Edit the YAML file directly
2. Run `metacrafter-registry validate` and `metacrafter-registry build`
3. Commit the YAML change and the regenerated `data/*_latest.*` files

### Linking to External Sources

Add links in the `links` array:

```yaml
links:
  - type: wikipedia
    url: https://en.wikipedia.org/wiki/Email
  - type: wikidata
    url: https://www.wikidata.org/wiki/Q968
  - type: schema.org
    url: https://schema.org/email
  - type: datadrivendiscovery
    url: https://metadata.datadrivendiscovery.org/types/...
  - type: other
    url: https://example.com
```

For Wikidata, also set `wikidata_property: P968` (property ID only, not URL).

## Data Organization

### Directory Structure

- **`any/`**: Language-agnostic datatypes (221 files)
  - Organized by category subdirectories
- **Country codes**: `US/`, `RU/`, `DE/`, etc.
  - Organized by category subdirectories
  - Examples: `US/finances/`, `RU/geo/`

### Naming Conventions

- **File names**: `{datatype_id}.yaml` (e.g., `email.yaml`, `us_ssn.yaml`)
- **IDs**: lowercase with underscores (e.g., `email`, `us_ssn`, `ru_inn`)
- **Country codes**: Uppercase ISO 3166-1 alpha-2 (e.g., `US`, `RU`, `DE`)

## Schema Validation

JSON schemas in `data/schemes/`:
- `datatype.json` - Validates datatype structure
- `tool.json` - Validates tool structure

Use these schemas to validate YAML files before building.

## Integration with Metacrafter

The registry is used by Metacrafter to:
- Provide datatype URLs in scan output
- Link detected datatypes to registry entries
- Fetch rule metadata
- Display rich metadata about detected types

Registry URL: `https://registry.apicrafter.io` (default)

## Data Sources

Metadata is collected from:
- **Wikipedia** - General information
- **Wikidata** - Structured data properties
- **Schema.org** - Semantic web schemas
- **DataDrivenDiscovery** - D3M metadata registry
- **Other sources** - Various documentation and standards

## Common Workflows

### Adding Country-Specific Datatype

1. Create directory: `data/datatypes/{COUNTRY_CODE}/{category}/`
2. Create YAML file with country code in `country` field
3. Add appropriate language codes
4. Link to parent datatype if applicable
5. Build and test

### Enriching Existing Datatype

1. Locate YAML file
2. Add missing fields:
   - `regexp` pattern
   - `examples`
   - `links` to external sources
   - `wikidata_property`
   - `translations`
3. Rebuild

### Analyzing Missing Rules

Use `scripts/analyze_missing_rules.py` to identify:
- Datatypes without corresponding rules in Metacrafter
- Rules without corresponding datatypes in registry

## Important Files

- `src/metacrafter_registry/` - build, validation and site generation (CLI `metacrafter-registry`)
- `scripts/builder.py` - legacy entry point (`stats`, `report`)
- `scripts/export.py` - Export utilities
- `src/registry.py` - legacy Flask server (deprecated)
- `data/schemes/datatype.json` - Datatype schema
- `data/schemes/tool.json` - Tool schema

## Dependencies

Key dependencies:
- `PyYAML` - YAML parsing
- `Jinja2` - static site templates
- `cerberus` - schema validation (until the JSON Schema migration)
- `Flask` - legacy server only (`src/registry.py`)
- Standard library: `json`, `os`, `logging`, `csv`

## Contributing Guidelines

1. **Follow schema:** Ensure YAML files match JSON schemas
2. **Use consistent IDs:** Follow naming conventions
3. **Add examples:** Include example values when possible
4. **Link sources:** Add links to Wikipedia, Wikidata, etc.
5. **Rebuild after changes:** Always run builder before committing
6. **Test locally:** Use web server to verify changes
7. **Update related data:** If adding new category/country/language, update reference files

## Relationship to Other Repositories

- **metacrafter**: Consumes registry data, provides datatype URLs
- **metacrafter-rules**: Rules may reference registry datatypes

When adding datatypes:
1. Consider if corresponding rules exist in metacrafter-rules
2. Ensure datatype IDs match rule keys where applicable
3. Update registry if rule changes affect datatype definitions

## Data Quality

### Validation Checklist

- [ ] ID is unique and follows naming conventions
- [ ] Name and doc are clear and descriptive
- [ ] Language codes are valid ISO 639-1
- [ ] Country codes are valid ISO 3166-1 alpha-2
- [ ] Categories exist in `categories.yaml`
- [ ] Regexp patterns are valid (if provided)
- [ ] Examples are accurate
- [ ] Links are valid URLs
- [ ] Wikidata property IDs are correct (if provided)
- [ ] File matches JSON schema

### Enrichment Opportunities

- Add regexp patterns for better matching
- Add more examples
- Link to Wikipedia/Wikidata
- Add translations for non-English names/docs
- Link related datatypes via `parent` field
- Add semantic type classifications

