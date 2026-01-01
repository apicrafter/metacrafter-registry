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
├── src/                    # Server code
│   ├── registry.py         # Web server for registry
│   └── templates/          # HTML templates
│       ├── base.tmpl
│       ├── datatype.tmpl
│       ├── datatype_list.tmpl
│       ├── tool.tmpl
│       └── tool_list.tmpl
├── scripts/                # Build and utility scripts
│   ├── builder.py          # Main build script (598 lines)
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

### Builder Script (`scripts/builder.py`)

The builder processes YAML source files and generates JSON/JSONL outputs:

**Key Functions:**
- `datatypes_yaml_to_jsonl()` - Converts datatype YAMLs to JSON/JSONL
- `tools_yaml_to_jsonl()` - Converts tool YAMLs to JSON/JSONL
- `update_by_dict()` - Maps IDs to names using reference dictionaries
- `load_path()` - Recursively loads YAML files from directory

**Build Process:**
1. Loads reference data (countries, categories, langs)
2. Scans `data/datatypes/` directory recursively
3. Separates datatypes from patterns (patterns have `semantic_type` field)
4. Links patterns to parent datatypes
5. Resolves category/country/language IDs to names
6. Outputs to `datatypes_latest.json` and `datatypes_latest.jsonl`
7. Repeats for tools

**Running the Builder:**
```bash
python scripts/builder.py
```

### Export Script (`scripts/export.py`)

Utilities for exporting registry data in various formats.

## Web Server (`src/registry.py`)

Minimal web server for browsing registry:

**Features:**
- HTML pages for browsing datatypes and tools
- API endpoints for programmatic access
- Uses built JSONL files (`datatypes_latest.jsonl`, `tools_latest.jsonl`)

**Running the Server:**
```bash
cd src
python registry.py
# Server available at http://127.0.0.1:8089
```

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
   country: [us]  # Optional
   is_pii: False
   regexp: "^pattern$"  # Optional
   examples:
     - value: "example"
       description: "Example value"
   ```

3. **Rebuild:**
   ```bash
   python scripts/builder.py
   ```

4. **Test:**
   ```bash
   cd src
   python registry.py
   # Browse to http://127.0.0.1:8089/datatype/new_datatype
   ```

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
2. Run builder: `python scripts/builder.py`
3. Commit changes

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

- `scripts/builder.py` - Main build script (598 lines)
- `scripts/export.py` - Export utilities (196 lines)
- `src/registry.py` - Web server
- `data/schemes/datatype.json` - Datatype schema
- `data/schemes/tool.json` - Tool schema

## Dependencies

Key dependencies:
- `PyYAML` - YAML parsing
- `Flask` (or similar) - Web server (in `src/registry.py`)
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

