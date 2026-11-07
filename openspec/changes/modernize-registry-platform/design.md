## Context

The motivation is in `proposal.md` (Why) and the evidence in
`devdocs/AUDIT_2026-11.md`. The constraints that shape the design are:

- **A URL contract that is already in the wild.**
  - metacrafter hardcodes `https://registry.apicrafter.io/datatype/{id}`
    (`metacrafter/classify/processor.py:221`). Those URLs are stored in
    DataHub, OpenMetadata and Atlas metadata that metacrafter has written.
  - `RegistryClient` reads `/registry.json`, a dict keyed by ID, and
    `/datatype/{id}.json`.
- **Consumers that read local files.**
  - The metacrafter LLM mode, metacrafter-llm and
    `metacrafter/scripts/ecosystem_check.py` read
    `data/datatypes_latest.jsonl` from a sibling checkout.
- **Static hosting only.** GitHub Pages serves files, so there is no server
  code, no query strings and no MCP endpoint on Pages itself.
- **DNS.** `registry.apicrafter.io` is on Cloudflare, and its origin is dead.
  Repointing it needs a DNS change by the owner.
- **Size.** About 630 entities and 12 tools, growing slowly, with roughly 3–5
  contributors. The whole dataset is about 0.5 MB of JSON, so there is no
  need for a database or a backend.
- **Clean YAML sources.** No YAML file contains comments, so a mechanical
  rewrite by a migration script loses nothing.
- **Shared rule source.** metacrafter-rules is not on PyPI, so CI must check
  out the repository at a pinned ref.

## Goals / Non-Goals

**Goals:**
- One command (`metacrafter-registry build`) turns `data/` into a complete
  `dist/` tree: site, API, agent files and RDF. The output is deterministic
  for a given commit.
- Every public URL that exists today keeps resolving with the same response
  shape.
- An agent can find, read and use the registry with no human help, through
  any of:
  - `llms.txt`
  - OpenAPI
  - MCP
  - the Python package
- Quality is measured honestly and enforced on change. Weak records are
  labelled, not hidden.

**Non-Goals:**
- A hosted (remote) MCP endpoint. A Cloudflare Worker could provide one
  later. Agents use the local MCP server or the static JSON.
- A graph database, or OWL reasoning (#49). This change publishes SKOS. OWL
  can come later.
- Fixing metacrafter, metacrafter-rules or metacrafter-llm code. These get
  follow-up changes in those repositories. This change only publishes what
  they need.
- Full UI localisation. The site UI is English. Translated names and docs are
  shown on entity pages.
- Bulk data enrichment, such as Wikidata, Presidio or DLP crosswalks for every
  record. This change provides the fields, tooling and gates. Content is
  filled in incrementally.

## Decisions

### D1. YAML-per-entity in git stays the source of truth

- **Why:** Diffs are reviewable, contributors can edit through GitHub's UI,
  agents can edit files directly, and history is already in place.
- **Alternatives:**
  - Graph DB or Wikibase: too much operational cost for about 600 records.
  - Single JSON or CSV file: merge conflicts, and poor review.

### D2. A custom Python + Jinja2 static generator, not a docs framework

- The generator reuses the data model that the API, Markdown, `llms.txt` and
  RDF emitters also use, all in one process. The repository keeps a single
  toolchain (Python, the same as metacrafter).
- It gives exact control over URLs. For example, `/datatype/email` with no
  trailing slash must keep working.
- **Alternatives:**
  - Docusaurus, which the metacrafter docs use: it needs Node and MDX
    generation for 600+ pages, and fighting its routes to keep extensionless
    URLs. The registry site links to the metacrafter docs instead.
  - MkDocs Material: data-driven faceted pages are awkward, and
    directory-style URLs break the contract.
  - Astro: a strong second choice if richer interactivity is needed later.
    It adds a Node toolchain.
- **Client-side pieces:**
  - Search is a small plain-JS ranking over `search-index.json`: exact id,
    id prefix, name, translated names, categories, then doc. At about 630
    records it needs no library. MiniSearch remains an option if fuzzy
    matching becomes necessary.
  - Plain JavaScript and no CSS framework. Light and dark themes come from
    CSS variables.
  - No third-party requests at runtime: no CDN and no analytics by default.

### D3. Hosting: GitHub Pages via an Actions artifact, under the existing domain

- **Workflow:** `actions/upload-pages-artifact` → `actions/deploy-pages`.
  There is no `gh-pages` branch, and nothing in the build is committed.
- **Domain:** `registry.apicrafter.io` is set as the custom domain in the Pages settings. Actions-based deployments ignore a `CNAME` file. The build takes its base URL from `actions/configure-pages`.
- **Cloudflare:** the record changes to `CNAME → apicrafter.github.io`. It
  should be DNS-only until GitHub issues the TLS certificate. After that it
  may be proxied with "Full (strict)" SSL.
- **Entity pages:**
  - Each entity page is written as `datatype/<id>.html`. GitHub Pages serves
    `/datatype/<id>` from that file.
  - `datatype/<id>.json` and `datatype/<id>.md` sit next to it.
  - Lists are written as `datatype/index.html` and `tool/index.html`. The
    legacy `/tool` URL is redirected to `/tool/` by Pages.
  - The first task (spike) verifies this behaviour before anything else
    depends on it.
- **Base URL:** a `--base-url` build option keeps a project-path deployment
  working (`apicrafter.github.io/metacrafter-registry/`) as a fallback, and
  for PR previews.

### D4. Two API layers: frozen legacy files plus a versioned `/api/v1/`

- **Legacy layer.** These files keep exactly the current shape, produced by a
  compatibility emitter from the new model:
  - `/registry.json`
  - `/datatype/<id>.json`
  - `/tools.json`
  - `/tool/<id>.json`

  Current shape means:
  - categories, countries and languages as `{id, name}` objects;
  - `is_pii` as a boolean;
  - `type` set to `datatype` or `pattern`;
  - embedded pattern objects;
  - `wikidata_property`.
- **Versioned layer.** `/api/v1/` is normalised:
  - references are plain ID strings, resolved through `categories.json` and
    the other reference lists;
  - each record adds `status`, `aliases`, `quality`, `detected_by`,
    `mappings`, `provenance` and absolute URLs.

  Breaking changes will go to `/api/v2/`.
- **Alternative rejected:** changing the legacy shape in place. It would break
  `RegistryClient` and everything stored downstream.
- **Transitional files.** `data/datatypes_latest.json(l)` and
  `data/tools_latest.json(l)` stay committed, in the legacy shape. CI fails if
  they are stale. They are removed in a later major release, once metacrafter
  and metacrafter-llm switch to the package or URL.

### D5. JSON Schema 2020-12 replaces Cerberus

- The schema files are `schema/datatype.schema.json`,
  `schema/pattern.schema.json` and `schema/tool.schema.json`. They are
  validated with `jsonschema` and published at `/schema/...`.
- Editors get autocompletion through yaml-language-server. Agents get a
  machine-readable contract.
- Checks that JSON Schema cannot express run as a separate semantic
  validation pass in Python:
  - cross-references
  - uniqueness
  - regexp compilation
  - examples against their regexp
  - directory and country agreement
  - file name and ID agreement

### D6. Data model v2: minimal churn, explicit semantics

Field names stay where possible, so diffs stay small. Here is a v2 record.
The values are illustrative: the `parent` and the mapping identifiers must be
verified when the record is curated.

```yaml
id: usssn                 # unchanged; file renamed to usssn.yaml
name: US Social Security Number
status: stable            # draft | stable | deprecated
doc: Nine-digit number issued by the US Social Security Administration ...
aliases: [ssn]            # former IDs merged into this one; redirects generated
parent: nationalid        # was {type: nationalid}
categories: [pii, persons, government]
country: [US]
langs: [en]
is_pii: true              # was 'True'
classification: identifier
regexp: '^(?!000|666|9\d\d)\d{3}-?(?!00)\d{2}-?(?!0000)\d{4}$'
checksum: null            # named algorithm: luhn, iban_mod97, isbn10, isbn13, gtin, ru_inn, ...
examples:
  - {value: '078-05-1120', valid: true, description: Famous invalidated SSN (format-valid)}
  - {value: '000-12-3456', valid: false, description: Area 000 never issued}
mappings:
  wikidata: P...          # replaces wikidata_property
  schema_org: null
  dpv: dpv-pd:SocialSecurityNumber   # if applicable
  presidio: US_SSN
  google_dlp: US_SOCIAL_SECURITY_NUMBER
  purview: U.S. Social Security Number (SSN)
links:
  - {type: wikipedia, url: https://en.wikipedia.org/wiki/Social_Security_number}
translations:
  ru: {name: Номер социального страхования США, doc: ...}
```

- **Patterns** keep `semantic_type`. They inherit `categories` and `is_pii`
  unless they override them, and the override must be explicit.
- **Derived at build time, never stored in YAML:**
  - the `patterns` lists;
  - `provenance.added` and `provenance.updated`, from git history;
  - `detected_by`, from metacrafter-rules and the tool records;
  - `quality`.
- **Reference lists** gain a `kind` field:
  - `countries.yaml`: `kind: region` for `EU`.
  - `langs.yaml`: `kind: special` for `common`, which means
    "language-independent".
  - The language `se` becomes `sv`.

### D7. Mark weak records instead of deleting them

- **Draft rule.** The migration sets `status: draft` on any record that meets
  any of these:
  - `doc` equals `name`;
  - `doc` is shorter than 25 characters;
  - it has no regexp, no examples and no links.

  The audit counts about 238 such records.
- **Quality score.** Each record gets a 0–100 score from a published rubric:

  | Element | Points |
  |---|---|
  | Doc | 20 |
  | Valid, anchored regexp | 20 |
  | ≥2 matching positive examples | 15 |
  | A negative example | 5 |
  | An authoritative link | 15 |
  | A mapping | 10 |
  | A translation | 5 |
  | Rule coverage | 10 |

- **Where drafts show up:**
  - The site shows a badge on each draft.
  - A `/quality` page lists drafts as a contributor queue.
  - Agents can filter on `status`.
- **Stub creation.** Generator scripts may still create stubs, but only as
  `draft`.
- **Alternatives rejected:**
  - Deleting stubs: that would break the rule-key alignment.
  - Leaving them unmarked: agents would treat them as authoritative.

### D8. IDs: rename files, not IDs

- 180 file names are changed to `<id>.yaml` with `git mv`. This has no effect
  on consumers.
- An ID changes only when duplicates merge, for example `ssn` → `usssn` and
  `ninumber` → `uknino`. The loser's ID goes into `aliases`. The build then
  emits:
  - a redirect page at `/datatype/<old>`;
  - a JSON file at `/datatype/<old>.json` that contains the canonical record
    plus `"alias_of"`;
  - an entry in `/api/v1/aliases.json`.
- The `cc_` prefix convention applies to new IDs only.
- **Alternative rejected:** a mass rename of the 127 concatenated and `rus*`
  IDs to `cc_` IDs. It would break the matching metacrafter-rules keys and
  every stored URL, for cosmetic gain.

### D9. Regex flavour

- Python `re` syntax stays canonical, because metacrafter is the main
  consumer.
- The build derives `regexp_js`. It translates `(?P<name>` to `(?<name>`, and
  sets `null` when it meets a construct it cannot translate (`\Z`, inline
  flags in the middle of a pattern, …).
- The `/identify` playground uses only `regexp_js`.
- All regexps run in a Web Worker, with a time budget for each pattern and an
  input length cap. A catastrophic-backtracking pattern cannot hang the page.

### D10. Agent surfaces

**Discovery**

- `/llms.txt` follows the llmstxt.org layout: a summary, then links to the
  Markdown docs, the API, the categories and the downloads.
- `/llms-full.txt` holds every datatype in compact Markdown (estimated at
  under 1 MB).
- Each entity page has `<link rel="alternate">` tags pointing to its `.json`
  and `.md` twins.

**Contract**

- `/api/v1/openapi.json` (OpenAPI 3.1) describes the static GET endpoints.
  Agent frameworks that support OpenAPI tools, and custom GPT actions, can use
  it as is.

**Linked data**

- Each page embeds schema.org `DefinedTerm` JSON-LD, inside a
  `DefinedTermSet`.
- `/registry.ttl` is a SKOS export, built with `rdflib` (a build-time
  dependency only):
  - `skos:Concept` with `prefLabel` and `altLabel` in each translated
    language;
  - `definition`;
  - `broader`, from `parent` and from `semantic_type`;
  - `exactMatch`, from the mappings;
  - `notation`, from the ID;
  - each category becomes a `skos:Collection`.

**MCP server**

- It ships in the Python package as `metacrafter-registry mcp`, over stdio,
  with an optional `--http` for self-hosting.
- Tools:
  - `search_datatypes(query, category?, country?, is_pii?, status?, limit?)`
  - `get_datatype(id)`, which resolves aliases
  - `identify_values(values[], field_name?, country?)`, which ranks
    candidates by regexp hit rate, checksum results, and similarity between
    the field name and the names, aliases and metacrafter field rules
  - `crosswalk(system, external_id)`, for example Presidio `US_SSN` →
    `usssn`
  - `list_categories()`
  - `list_countries()`
- Resources: `registry://datatype/{id}`, which returns Markdown.
- Data comes from the bundled snapshot. `--refresh` pulls a newer snapshot
  when the hash in `index.json` changes.

**Skills**

- `skills/registry-lookup/SKILL.md` tells an agent how to use the registry to
  label columns.
- `skills/registry-contributor/SKILL.md` tells an agent how to add or fix a
  datatype: where the file goes, the schema, `validate`, and the `draft`
  status.
- `AGENTS.md` is rewritten to point to both skills.

**RAG corpus**

- `/api/v1/rag/corpus.jsonl` has `{id, text, metadata}` per datatype.
- The `text` template is owned by the registry and versioned in
  `index.json`, so metacrafter-llm and the registry stop drifting.
- The corpus contains no precomputed embeddings, because they are tied to a
  model and would need secrets in CI.

### D11. Python package `metacrafter-registry`

- **Layout:** the source is `src/metacrafter_registry/`. It replaces the
  Flask `src/registry.py`.
- **API:**
  - `Registry.load()` loads the bundled snapshot.
  - `Registry.fetch(base_url)` loads the latest data and caches it.
  - `.get(id)` is alias-aware.
  - Other methods: `.search(...)`, `.url_for(id)`, `.match(value)`,
    `.version`.
- **CLI subcommands:** `build`, `validate`, `stats`, `report`, `migrate`,
  `serve` (which serves `dist/` locally), `mcp` and `lookup`.
- **Release:** a GitHub Release on tag, with the wheel and its data snapshot.
  The package is not published on PyPI (owner decision, 2026-11-07): the
  registry is used through its site and API.
- **Rationale:** this mirrors how metacrafter-rules bundles its rules.
  metacrafter can enrich scan output offline, which is the open item "Wire
  RegistryClient into scan output" in its ROADMAP.

### D12. Versioning and releases

- **Data uses SemVer.**
  - MAJOR: an ID is removed without an alias, or a legacy or `v1` shape
    changes.
  - MINOR: new records or new fields.
  - PATCH: corrections.
- **First release:** the first release under this design is `2.0.0`, because
  the YAML schema changes. The legacy JSON shape is unchanged.
- **Changelog:** the build diffs the current `datatypes.jsonl` against the
  previous release's file, taken from the GitHub Release assets. It emits:
  - `/api/v1/changes.json`
  - a `/changes` page
  - the release notes

  The changes are listed as added, deprecated, merged and changed IDs.
- **Manifest:** `index.json` records:
  - `version`
  - `git_sha`
  - `generated_at`, taken from the commit time so builds are reproducible
  - `license`
  - counts
  - the `sha256` of every bulk file

### D13. Ecosystem alignment in CI

- CI checks out `apicrafter/metacrafter-rules` at a pinned ref, set in
  `ecosystem.lock`.
- The build reads every rule's `key`, `type`, `match` and file. It uses them
  to:
  - fill `detected_by.metacrafter_rules`;
  - generate `supported_types` for the `metacrafter` tool record, replacing
    the hand-written list;
  - emit `/api/v1/coverage.json`.
- Orphans in both directions are reported as warnings on PRs.
- A weekly job runs against the latest metacrafter-rules `main` and opens or
  updates an issue with the drift.

### D14. Repository layout after the change

```
data/                     YAML sources (location unchanged)
schema/                   JSON Schemas (published at /schema/)
src/metacrafter_registry/ package: model, load, validate, quality, emit/*, client, match, mcp, cli
src/metacrafter_registry/templates/, .../static/   Jinja2 templates, CSS, JS (vendored MiniSearch); package data
skills/                   agent skills
tests/                    pytest (model, validation, emitters, URL contract snapshot)
.github/workflows/        ci.yml, pages.yml, release.yml, weekly.yml
archive/                  _original/, analysis/, one-off generator scripts (read-only)
openspec/, devdocs/
```

## Risks / Trade-offs

- **Pages may not serve `/datatype/<id>` from `datatype/<id>.html` as
  expected** (for example, a redirect to `.html` or to a trailing slash).
  → A spike deploy goes first, and a contract test runs `curl` on the
  deployed preview. The fallback is a 404.html JS router that rewrites
  `/datatype/<id>` to `/datatype/<id>/`, with pages written to
  `datatype/<id>/index.html`.
- **The DNS change is outside our control and delays the domain going
  live.**
  → The site deploys first on `apicrafter.github.io/metacrafter-registry/`.
  Once DNS is updated, the `CNAME` file is added and the base URL flips.
  metacrafter users can set `METACRAFTER_REGISTRY_URL` in the meantime, after
  the processor fix in metacrafter.
- **Marking about 238 records as `draft` looks like regression.**
  → The site frames them as a contribution queue. Counts appear on `/quality`.
  Drafts stay in every output.
- **A YAML rewrite by the migration script produces a huge diff.**
  → The migration is its own PR with no content changes. It is reproducible
  (`metacrafter-registry migrate --check` is idempotent) and reviewed with
  stats, not line by line.
- **Text copied from Wikipedia under CC BY-SA.**
  → A `provenance.source` and attribution field is added. The `/about` page
  states the licensing. Copied ledes are rewritten over time, tracked as a
  quality item. The data license is the owner's choice (see Open Questions).
- **Pasted PII in the `/identify` playground.**
  → Matching runs only in the browser. The page has no network calls and no
  analytics, and the page says so.
- **Pinning metacrafter-rules lags behind rule changes.**
  → The weekly drift job keeps the lag visible. Bumping `ecosystem.lock` is
  a one-line PR.
- **Pages limits** (1 GB site, a soft 100 GB/month bandwidth, 10 builds an
  hour).
  → The estimated `dist/` is under 30 MB. Builds run per merge only.

## Migration Plan

1. **Phase 0, restore (days).**
   - Package skeleton and CI validation.
   - P0 data fixes (audit §3).
   - A legacy-compatible static export deployed to Pages.
   - Contract test.
   - DNS switch.

   Exit: `https://registry.apicrafter.io/datatype/email` and `/registry.json`
   respond 200 with the legacy shape.
2. **Phase 1, site and API.**
   - Entity, category, country and tool pages; search; `/api/v1/`; manifest;
     OpenAPI; sitemap; release workflow.
3. **Phase 2, data model v2.**
   - JSON Schema, a migration PR, statuses, aliases and merges, quality
     scoring, real stats, file renames.
4. **Phase 3, agents.**
   - `llms.txt` and `llms-full.txt`, Markdown twins, JSON-LD and SKOS, the
     Python package with the MCP server, skills, and the RAG corpus.
5. **Phase 4, ecosystem.**
   - Rules coverage and the generated tool record, the weekly drift job, the
     `/identify` playground, and starter crosswalks (Presidio, Google DLP,
     Purview, DPV).
   - File follow-up changes in the metacrafter, metacrafter-rules and
     metacrafter-llm repositories.

**Rollback:**
- Pages deployment: re-run `pages.yml` on the previous commit. Each deploy is
  an immutable artifact.
- DNS: revert the CNAME.
- Migration: a single revertable PR.
- Legacy files are generated from the same model and covered by a snapshot
  test, so a regression is caught before deploy.

## Open Questions

- **Data license.** CC BY 4.0 is suggested for compatibility with attribution
  sources; CC0 is the alternative. The owner decides. The specs require only
  that a license is declared and published.
- **Remote MCP endpoint.** A Cloudflare Worker over the static JSON is the
  candidate. It can be added later without changing any spec in this change.
- **Russian UI.** A Russian locale for the UI could follow, once more than
  50% of records have `ru` translations. Today 18% do.
