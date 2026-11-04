## Why

Issue #41 asked what the registry can learn from the Semgrep Registry. The
review in `devdocs/SEMGREP_REVIEW.md` found that Semgrep users rarely pick
single rules. They pick a curated ruleset by name, such as `p/ci` (few false
positives) or `p/secrets`, and the scanner downloads it. A ruleset serves a
purpose. Neither the language nor the directory decides alone what it
contains.

The registry has no such unit. Categories and countries say what a value
is, not what a user wants to scan for. A user who wants "Russian personal
data" or "types that a checksum makes reliable" must filter the full list
and keep the result up to date. metacrafter can filter rules only by
metacrafter-rules context and language. This is recommendation R1 of the
review.

## What Changes

- **New source records: packs.** One YAML file per pack in
  `data/packs/<id>.yaml`, validated by a new `schema/pack.schema.json`.
  - A pack has an `id`, a `name`, a `doc` and a `status`.
  - Its members are an explicit list of datatype ids, a `select` filter over
    existing record fields, or both. An `exclude` list removes members.
  - A pattern is a member when its datatype is a member.
- **Validation.** The build fails on an unknown or retired id in a pack, on a
  pack without members, and on a duplicate pack id. It warns when a pack
  lists a draft or deprecated datatype by hand.
- **New API files.**
  - `/api/v1/packs.json`: every pack with its counts.
  - `/api/v1/packs/<id>.json`: one pack with its resolved datatypes,
    patterns and the metacrafter-rules rules that detect them.
  - The manifest, the OpenAPI description and the URL contract check cover
    both.
  - Each record in `/api/v1/` gets a `packs` list with the ids of the packs
    it belongs to.
- **New pages.** `/pack/` lists the packs. `/pack/<id>` shows one pack, with
  a Markdown twin at `/pack/<id>.md`. Record pages link to their packs.
  `llms.txt` and the sitemap list the packs.
- **Seed packs.** The first packs are chosen with the maintainer (tasks.md,
  group 1).
- **Not in this change:**
  - A `--pack` option in metacrafter. It is a separate change in the
    metacrafter repository that reads `/api/v1/packs/<id>.json`.
  - The `secrets` category and credential datatypes (review R4). A secrets
    pack can follow them.
  - Community packs outside the review process. Packs are records, and they
    are changed by pull request like any other record.

Nothing here is BREAKING. The change adds source files, API files, pages
and one field in `/api/v1/` records. The legacy files (`/registry.json`,
`/datatype/<id>.json`, `/tools.json`, `/tool/<id>.json`) do not change.

## Capabilities

### New Capabilities

- `datatype-packs`: pack source records, membership, validation, API files
  and pages.

### Modified Capabilities

None. The additions to `/api/v1/` are new files and one new field, which the
versioned API allows.

## Impact

- Data: new directory `data/packs/` and `schema/pack.schema.json`.
- Code: `loader.py` (load packs), `validate.py` (gates), `model.py`
  (membership and the `packs` field), `build.py` and templates (pages, API
  files, manifest), `openapi.py`, `agents.py` (`llms.txt`, Markdown twin),
  `contract.py`, `client.py` (`Registry.pack()`), and optionally the MCP
  server (a `list_packs` tool).
- Docs: README URL table, `AGENTS.md`, `CONTRIBUTING.md`, the about page.
- Consumers: metacrafter can adopt packs later. Nothing changes for
  existing consumers.
