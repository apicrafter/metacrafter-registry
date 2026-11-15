## Why

The registry has 36 categories for 2408 datatypes (and 583 patterns, which
inherit). The sizes run from 16 records (`dublincore`) to 409 (`geo`). A
review on 2026-11-16 found that size is a symptom. The cause is that one flat
list mixes four different questions:

- the topic of a value (`finances`, `medical`, `transport`)
- its sensitivity (`pii`)
- its technical form (`identifiers`, `objectids`, `values`, `common`)
- the standard it comes from (`gs1`, `dublincore`)

The effects, counted on datatypes:

- **Large categories hold unrelated groups.** The subgroup sizes are keyword
  estimates and overlap.
  - `geo` (409): about 280 administrative and statistical units, 50
    addresses and postal codes, 40 coordinates and geometries, and cadastral
    numbers.
  - `government` (327): 134 records are the same administrative units as in
    `geo`. About 55 are budget and procurement codes and 35 are legal acts.
    Only 58 records have `government` as their only category.
  - `finances` (297): about 130 tax numbers, 100 bank and payment
    identifiers, 30 budget codes and 25 securities identifiers.
  - `science` (185): about 90 life-science identifiers, 40 bibliometric
    identifiers and 30 environmental measurements.
- **`pii` repeats the `is_pii` field, and the two disagree.** 93 datatypes
  have `is_pii: true` and no `pii` category. 216 of the 241 `persons`
  records also have `pii`.
- **Some categories have no definition.** `common` (69) holds `okved`,
  `latitude`, `email`, `curp` and `password`. `identifiers` (65) and
  `objectids` (47) have no stated border, and `isni` is in both.
- **Some categories are small and adjacent:** `useraccounts` (20),
  `ecommerce` (19), `shipping` (30).
- **The directory does not always follow the categories.** 19 records are in
  a directory that is not one of their categories, and the directory `files`
  is not a category.

`companies` (280) is large but uniform: one registration number per country.
The country filter already divides it. `telecom` (28), `energy` (26) and
`cryptocurrency` (31) are small but uniform. These four stay.

Categories are used outside the site. metacrafter filters scan results by
category, metacrafter-llm filters its retrieval, and the DataHub glossary
uses the first category of a record as its node. A category that mixes
groups makes each of these less useful.

## What Changes

- **Category reference records get three new fields** in
  `data/categories.yaml`:
  - `description`: what belongs in the category and what does not.
  - `kind`: `topic`, `form`, `sensitivity` or `standard`.
  - `aliases`: former category ids, which keep resolving.
- **`pii` becomes a derived category.** Source records do not list it. The
  build adds `pii` to the `categories` of every record whose `is_pii` is
  true. This closes the gap of 93 records.
- **A primary category.** The first category of a datatype is its primary
  category. Its kind is `topic` or `form`, and it is the name of the
  directory of the file. A record has at most three source categories.
- **Five new categories** split the large ones (sizes are estimates):
  - `territories` (about 280): administrative and statistical units, from
    `geo` and `government`.
  - `addresses` (about 50): addresses, streets and postal codes, from `geo`.
  - `publicfinance` (about 80): budget classifications, procurement and
    grants, from `government` and `finances`.
  - `taxes` (about 130): tax and VAT numbers, from `finances`.
  - `lifesciences` (about 90): biology, genomics and taxonomy, from
    `science`.
- **Five categories are retired** and become aliases:
  - `objectids` into `identifiers`. `identifiers` then holds only general
    identifier formats (UUID, ULID). Subject identifiers move to their topic.
  - `common` into `values`. Most of its records already have a topic.
  - `useraccounts` into `internet`.
  - `ecommerce` and `shipping` into a new `commerce` category.
- **Moves between existing categories:** cadastral numbers to `realestate`,
  legal acts to `legal`, bibliometric identifiers to `publishing`.
- **Category aliases resolve everywhere a category id is accepted:**
  `/category/<alias>` and `/category/<alias>.md` redirect, `Registry.search`
  and the MCP `search_datatypes` tool accept an alias, and
  `/api/v1/categories.json` lists the aliases of each category.
- **BREAKING (values, not shape):** the values of `categories` change in
  `/registry.json`, `/datatype/<id>.json`, `/api/v1/` and the JSONL files. No
  field is added to, removed from or retyped in the legacy shape. A consumer
  that compares a record's categories with a retired id (`objectids`,
  `common`, `useraccounts`, `ecommerce`, `shipping`) gets no match until it
  resolves aliases from `/api/v1/categories.json`. metacrafter and
  metacrafter-llm are such consumers.
- **Not in this change:**
  - New ids, renamed ids or removed datatypes. Only `categories` and file
    paths change.
  - A hierarchy of categories. The list stays flat.
  - A split of `companies`.
  - Changes to tool categories (`detector`, `pii`, `etl`, `catalogs`,
    `other`). They are a separate list.

The result is 37 categories (36, plus six new, minus five retired). The
count does not fall. The gain is that no large category mixes unrelated
groups: the two largest, `territories` and `companies`, are each one kind
of record.

## Capabilities

### New Capabilities

- `category-taxonomy`: category reference records, kinds, aliases, the
  derived `pii` category, the primary category and its directory, and the
  validation gates for them.

### Modified Capabilities

None as a delta. `registry-data-model` (in `modernize-registry-platform`)
says that records are stored under
`data/datatypes/<COUNTRY|any>/<category>/` and that `categories` holds ids
from the reference list. Both stay true. This change makes them stricter.

## Impact

- Data: `data/categories.yaml`; `categories` in about 700 to 800 datatype
  files; file moves between category directories (`git mv`, ids do not
  change); regenerated `data/*_latest.json(l)`.
- Schema: a new `schema/category.schema.json` for the reference list.
- Code: `loader.py` (reference fields), `validate.py` (gates), `model.py`
  and `legacy.py` (derived `pii`, alias resolution), `build.py` and
  templates (category list grouped by kind, descriptions, redirects),
  `agents.py` (`llms.txt`, category Markdown, SKOS), `client.py` and
  `mcp_server.py` (alias in filters), `openapi.py`, `contract.py`,
  `datahub.py` (node names follow the new primary categories), `changes.py`
  (category changes in the changelog).
- Docs: `AGENTS.md`, `CONTRIBUTING.md`, `skills/registry-contributor`, the
  issue forms.
- Consumers: metacrafter (`scan_service.py`, category filter) and
  metacrafter-llm (retriever filter) need alias resolution. The `source`
  path of moved records changes in `/api/v1/`. DataHub glossary nodes change
  for records whose primary category changes.
