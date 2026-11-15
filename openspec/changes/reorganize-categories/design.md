## Context

See proposal.md (Why) for the counts of 2026-11-16.

Current state:

- `data/categories.yaml` is a list of `{id, name}`. `loader.load_reference`
  reads it. Nothing describes what a category contains.
- A datatype lists `categories`. A pattern inherits them through
  `semantic_type` unless it declares its own (`model.py`, `legacy.py`).
- The file path is `data/datatypes/<COUNTRY|any>/<category>/<id>.yaml`. The
  build checks the country part of the path. It does not check the category
  part.
- `/category/<id>` and `/category/<id>.md` exist for every category that has
  records. `/api/v1/categories.json` lists `{id, name, count}`.
- `datahub.py` places a record in the glossary node of its first category.
- metacrafter (`scan_service.py`) keeps a result when its registry record
  shares a category with the `categories` filter. metacrafter-llm filters
  retrieval the same way.

## Goals / Non-Goals

**Goals:**

- Each category answers one question, and its description says which.
- A contributor can choose the directory and the first category of a new
  record without asking.
- No category id that was ever published stops resolving.
- Every task group leaves `main` deployable. The move is done category by
  category, not in one pull request.

**Non-Goals:**

- Equal category sizes. A uniform category may be large.
- A category tree. Kinds group the flat list on the site and nothing more.
- A review of record quality. Records that move stay `draft` or `stable` as
  they are.

## Decisions

### D1. Category reference record

```yaml
- id: territories
  name: Administrative and statistical territories
  kind: topic
  description: >-
    Codes and names of administrative units (regions, municipalities,
    districts) and statistical areas (census tracts, NUTS). Coordinates and
    geometries belong in geo. Addresses belong in addresses.
  aliases: []          # omitted when empty
```

- `kind` is required. `description` is required for every category that has
  records. `aliases` is optional.
- `schema/category.schema.json` validates the list. It is published under
  `/schema/` with the other schemas.
- Alternative considered: a separate file per category. Rejected: 36 short
  records are easier to review in one file, and the loader already reads it.

### D2. Kinds

| Kind | Question | Categories |
|---|---|---|
| `topic` | What subject area is the value from? | all others |
| `form` | What general form does the value have, when it has no subject? | `identifiers`, `values`, `datetime` |
| `sensitivity` | Does the value need protection? | `pii` |
| `standard` | Which standard defines the value? | `gs1`, `dublincore` |

- `secrets` and `cryptography` are topics. A secret is sensitive, but the
  category describes the subject (credentials), and no boolean field repeats
  it.
- `texts` is a topic (texts and articles), not a form.
- The site groups `/category/` by kind. The API adds `kind` to each entry of
  `/api/v1/categories.json`.
- Alternative considered: move `gs1` and `dublincore` out of categories into
  `mappings` or a new `standard` field. Rejected for now: it is a data model
  change with no consumer that asks for it. The kind already separates them.

### D3. `pii` is derived from `is_pii`

- A source record SHALL NOT list `pii`. Validation fails if it does.
- `model.py` and `legacy.py` add `pii` to the output `categories` of every
  record whose resolved `is_pii` is true. It is added last, so it is never
  the primary category.
- Output for the 265 records that have `pii` today does not change, except
  for the position of `pii` in the list. 93 more records gain it.
- Alternative considered: remove `pii` from output and point consumers to
  `is_pii`. Rejected: `categories=pii` is the most likely filter in
  metacrafter, and removing it breaks that filter for no gain.

### D4. Primary category and directory

- The first source category of a datatype is its primary category. Its kind
  SHALL be `topic` or `form`.
- The category part of the file path SHALL equal the primary category. For a
  pattern that declares no categories, it SHALL equal the primary category
  of its datatype.
- A record SHALL have at most three source categories. Four records have
  four today.
- 19 records and the `files` directory do not follow the directory rule
  today. They are fixed before the gate is turned on.
- The 16 records whose only category is `dublincore`, and any record whose
  only category is `gs1`, need a topic. See Open Questions.
- Alternative considered: a separate `primary_category` field. Rejected: the
  order of the list already carries this meaning in `datahub.py`, and a
  second field can disagree with the list.

### D5. Aliases for retired categories

- A retired category id becomes an entry in `aliases` of the category that
  replaces it. An id is unique across all ids and aliases.
- Output records list only current ids.
- `/category/<alias>` and `/category/<alias>.md` are redirect pages, built
  the same way as datatype alias pages.
- `/api/v1/categories.json` adds `aliases` to an entry when it has any.
- `Registry.search(category=...)` and the MCP tool `search_datatypes`
  resolve an alias before they filter.
- A source record that lists an alias fails validation, and the message
  names the current id.
- A category that is split is not retired. `geo`, `government`, `finances`
  and `science` keep their ids with a narrower description. A filter on
  `geo` then returns fewer records. This is the intended effect, and the
  changelog states it.

### D6. Target list

Sizes are estimates from keyword counts. The final membership comes from
the reviewed mapping (D7).

| Category | Today | Target | Change |
|---|---|---|---|
| `geo` | 409 | ~80 | keeps coordinates, geometries, grids, general places |
| `territories` | new | ~280 | from `geo` and `government` |
| `addresses` | new | ~50 | from `geo` |
| `government` | 327 | ~100 | public bodies, registers, official documents |
| `publicfinance` | new | ~80 | from `government` and `finances` |
| `finances` | 297 | ~140 | banking, payments, securities |
| `taxes` | new | ~130 | from `finances` |
| `science` | 185 | ~60 | research organizations, classifications, general science |
| `lifesciences` | new | ~90 | from `science` |
| `publishing` | 76 | ~115 | gains bibliometric identifiers |
| `identifiers` | 65 | ~40 | general identifier formats only; alias `objectids` |
| `values` | 49 | ~60 | alias `common` |
| `internet` | 60 | ~80 | alias `useraccounts` |
| `commerce` | new | ~50 | aliases `ecommerce`, `shipping` |
| `realestate` | 60 | ~100 | gains cadastral numbers |
| `legal` | 55 | ~80 | gains legal acts |

All other categories keep their members. A record that leaves a narrowed
category may keep it as a secondary category when it fits the new
description. For example, a tax number of a company keeps `companies`.

### D7. Migration by reviewed mapping

- One mapping file per task group, `devdocs/categories/<group>.csv`, with
  the columns `id`, `old_categories`, `new_categories`. A throwaway script
  proposes it from the current categories and keywords. A person reviews
  every row before it is applied.
- `scripts/recategorize.py` applies a mapping: it rewrites `categories` in
  canonical YAML form and moves the file with `git mv` when the primary
  category changes. It refuses a row whose `old_categories` differ from the
  file.
- Each task group applies one mapping, regenerates `data/*_latest.json(l)`
  and passes `validate`, `build`, `check-links` and `pytest`.
- The mapping files stay in `devdocs/` as the record of the decision.

### D8. Changelog

`changes.py` reports categories that were added or retired and, for each
record, a change of its categories. The release notes of the release that
contains a split state which filters return fewer records.

## Risks / Trade-offs

- **A consumer filters by a retired id and silently gets nothing.**
  Mitigation: aliases in `/api/v1/categories.json`, issues in metacrafter
  and metacrafter-llm before the first retirement merges (tasks, group 1),
  and the retirements are the last group.
- **Keyword-based mapping puts records in the wrong category.** Mitigation:
  every mapping row is reviewed by a person (D7). The script only proposes.
- **File moves conflict with open pull requests.** Mitigation: one category
  per pull request, merged quickly. `git` follows the renames.
- **DataHub glossary nodes change** for records whose primary category
  changes. Term ids are registry ids and do not change, so attached terms
  keep working. Only the node that shows them moves.
- **A filter on a narrowed category returns fewer records.** This is a
  change of meaning without a change of id. It is stated in the description
  of the category and in the release notes.

## Open Questions

- Names: `territories` or `adminunits`; `publicfinance` or `budget`;
  `lifesciences` or `biology`; `commerce` or `trade`.
- Should securities identifiers (about 25) be a `securities` category, or
  stay in `finances`? Proposed: stay.
- Which topic do the 16 `dublincore`-only records get as primary category?
  Proposed: `publishing`.
- Should `values` be renamed to say that it now holds general values too,
  and does it keep its id? Proposed: keep the id, change the name to
  "General values and measurements".
- Should NGO and charity numbers (74) get a `nonprofits` category, split
  from `companies`? Proposed: no. Rename `companies` to "Companies and
  organizations" and keep the id.
