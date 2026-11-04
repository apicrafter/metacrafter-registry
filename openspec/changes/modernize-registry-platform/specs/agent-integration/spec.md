## Purpose

This capability defines how AI agents discover, read and use the registry
without human help. It covers llms.txt, Markdown twins, a local MCP server,
agent skills and a RAG corpus.

## ADDED Requirements

### Requirement: llms.txt
The site SHALL serve `/llms.txt` following the llmstxt.org format. It SHALL contain a title, a one-paragraph summary, and link sections for documentation, the API, the categories and the downloads.

The site SHALL also serve `/llms-full.txt`, which contains every datatype and pattern in compact Markdown.

#### Scenario: Agent discovery
- **WHEN** an agent fetches `https://registry.apicrafter.io/llms.txt`
- **THEN** it receives Markdown that links to the OpenAPI document, `index.json`, `llms-full.txt` and the MCP setup guide

### Requirement: Markdown twins
Every datatype, pattern and tool SHALL be available at `<page-url>.md` as Markdown, with the same facts as the HTML page. HTML pages SHALL advertise the Markdown twin with `<link rel="alternate" type="text/markdown">`.

#### Scenario: Read as Markdown
- **WHEN** an agent requests `/datatype/email.md`
- **THEN** it receives Markdown with front matter (`id`, `status`, `is_pii`, `categories`, `country`) and sections for the description, regexp, examples, mappings and detection

### Requirement: Local MCP server
The registry Python package SHALL provide an MCP server that runs locally over stdio. It SHALL expose these tools:

- `search_datatypes`, with filters for category, country, PII and status
- `get_datatype`, which resolves aliases
- `identify_values`, which ranks candidate datatypes for sample values and an optional field name
- `crosswalk`, which maps an identifier from Presidio, Google DLP, Purview, DPV or Wikidata to a registry ID
- `list_categories`
- `list_countries`

It SHALL also expose each datatype as a resource that returns Markdown.

The server SHALL work offline from the bundled data snapshot. It SHALL refresh the snapshot only when asked to, and only when the published manifest hash differs.

#### Scenario: Identify column values
- **WHEN** an agent calls `identify_values` with `["7707083893", "7728168971"]` and `field_name: "inn"`
- **THEN** the top candidate is the Russian INN datatype, and the response gives the regexp hit rate, the checksum result and the registry URL

#### Scenario: Alias resolution
- **WHEN** an agent calls `get_datatype("ssn")` after `ssn` became an alias
- **THEN** the canonical record is returned, with a note naming the alias

#### Scenario: Offline
- **WHEN** the MCP server starts without network access
- **THEN** all tools work from the bundled snapshot and report its version

### Requirement: Agent skills
The repository SHALL ship two agent skills, as `SKILL.md` documents with front-matter descriptions:

- a lookup skill, which explains how to use the registry to label dataset columns;
- a contributor skill, which explains how to add or improve a record. The contributor skill SHALL cover file placement, the schema, the validation command, example rules and when to use `status: draft`.

The repository `AGENTS.md` SHALL point to both skills.

#### Scenario: Agent adds a datatype
- **WHEN** an agent follows the contributor skill to add a new national ID
- **THEN** the resulting file passes `validate` without manual fixes

### Requirement: RAG corpus
The site SHALL serve `/api/v1/rag/corpus.jsonl` with one entry per datatype and pattern. Each entry SHALL contain `id`, `text` and `metadata`.

The `text` SHALL be produced by a template that the registry versions. The template version SHALL be reported in the manifest.

#### Scenario: Index rebuild detection
- **WHEN** metacrafter-llm compares its stored corpus hash and template version with the manifest
- **THEN** it can decide whether to rebuild its vector index

### Requirement: Agent-safe semantics
Every machine-readable representation SHALL carry `status` and `quality.score`.

Documentation for agents SHALL state that `draft` records are unreviewed and that pages must not be treated as authoritative for legal or compliance decisions.

#### Scenario: Filter drafts
- **WHEN** an agent calls `search_datatypes` with `status: stable`
- **THEN** no draft records are returned
