## Purpose

This capability defines the machine-readable static outputs of the registry:
frozen legacy JSON files, a versioned JSON API, bulk downloads, a manifest,
an OpenAPI description and linked-data exports.

## ADDED Requirements

### Requirement: Frozen legacy JSON files
The site SHALL serve `/registry.json`, `/datatype/<id>.json`, `/tools.json` and `/tool/<id>.json` in the shape produced by release 1.02:

- `/registry.json` is an object keyed by ID.
- Categories, countries and languages are `{id, name}` objects.
- `is_pii` is a boolean.
- `type` is `datatype` or `pattern`.
- Pattern objects are embedded in `patterns`.
- `wikidata_property` is present when it is known.

New fields MAY be added to these files. Existing fields SHALL NOT be removed or retyped.

#### Scenario: RegistryClient compatibility
- **WHEN** metacrafter's `RegistryClient` loads `/registry.json` and `/datatype/email.json`
- **THEN** both parse, and the record for `email` has the fields `id`, `name`, `doc`, `categories`, `is_pii` and `type`

#### Scenario: Alias JSON
- **WHEN** a client requests `/datatype/<alias>.json`
- **THEN** the response is the canonical record, with an added `alias_of` field that holds the canonical ID

### Requirement: Versioned API
The site SHALL serve a normalised API under `/api/v1/`. It SHALL contain:

- one JSON file per datatype, pattern and tool
- collection files in JSON and JSONL
- reference lists: categories, countries and languages
- `aliases.json`, which maps each alias to its canonical ID
- `coverage.json`
- `changes.json`

Within `/api/v1/`, references SHALL be ID strings. Each record SHALL include:

- `status`, `aliases` and `quality`
- `detected_by` and `mappings`
- `provenance`
- the absolute URLs of its HTML, JSON and Markdown representations

Incompatible changes SHALL be published under a new version prefix.

#### Scenario: Fetch one datatype
- **WHEN** a client requests `/api/v1/datatypes/usssn.json`
- **THEN** the response contains `"categories": ["pii", ...]` as strings, together with `status`, `quality.score` and `url`

### Requirement: Manifest
`/api/v1/index.json` SHALL report:

- the data version
- the git commit SHA
- the generation time
- the data license
- record counts
- the path, size and SHA-256 of every bulk file
- the RAG corpus template version

#### Scenario: Change detection
- **WHEN** a consumer has a cached copy and compares the `sha256` of `datatypes.jsonl` in the manifest
- **THEN** it can tell whether to re-download, without fetching the bulk file

### Requirement: Bulk downloads
The site SHALL serve all datatypes and patterns as JSON, JSONL and flat CSV. The same files SHALL be attached to each GitHub Release.

#### Scenario: CSV export
- **WHEN** a user downloads `/api/v1/datatypes.csv`
- **THEN** it has one row per datatype or pattern, and list fields are joined with `|`

### Requirement: OpenAPI description
The site SHALL serve an OpenAPI 3.1 document that describes every static GET endpoint and its response schema.

#### Scenario: Tool import
- **WHEN** an agent framework imports `/api/v1/openapi.json`
- **THEN** it obtains operations to list datatypes, get a datatype by ID, list categories and get the manifest

### Requirement: Linked data export
The site SHALL serve a SKOS concept scheme in Turtle at `/registry.ttl`. Each datatype and pattern SHALL be a `skos:Concept` with:

- a `prefLabel` for each available language
- `definition`
- `notation`, set to the ID
- `broader`, from `parent` or `semantic_type`
- `altLabel`, from the aliases
- `exactMatch`, for each mapping that has a resolvable URI

#### Scenario: Pattern hierarchy
- **WHEN** pattern `uspassport` has `semantic_type: passport`
- **THEN** the Turtle export contains the triple `<…/datatype/uspassport> skos:broader <…/datatype/passport>`

### Requirement: Published schemas
The JSON Schemas for source records and for `/api/v1/` responses SHALL be served under `/schema/`.

#### Scenario: Schema URL
- **WHEN** a client requests `/schema/datatype.schema.json`
- **THEN** it receives the JSON Schema that the build used to validate datatype records
