## Context

See proposal.md (Why) and `devdocs/SEMGREP_REVIEW.md`, sections 4 and 8.

Current state:

- Records are grouped only by `categories` and `country`. The site has
  `/category/<id>` and `/country/<CC>` pages, and `/api/v1/` has reference
  lists with record counts.
- `data/coverage/metacrafter-rules.json` lists every metacrafter-rules rule
  with its `key`, `type`, `context`, `lang` and `country_code`. The build
  already joins it to records as `detected_by`.
- metacrafter selects rules with `--contexts` and `--langs`. These values
  follow the files of metacrafter-rules, not a user's purpose.
- Global records have no `country` field. 28 records have a `checksum`.

## Goals / Non-Goals

**Goals:**

- A pack is reviewed like any record, and its membership can be read from
  its source file and from its API file.
- A consumer gets everything it needs for one pack from one file: datatype
  ids, pattern ids and rule names.
- A pack that is defined by a filter stays current without hand edits.

**Non-Goals:**

- Ranking or scoring inside a pack. Packs are sets.
- Packs of tools or of metacrafter-rules rules that have no registry key.
- Changes to metacrafter or metacrafter-rules.

## Decisions

### D1. One YAML file per pack in `data/packs/`

```yaml
# Illustrative: the members show the format, not an agreed pack.
id: ru_pii
name: Russian personal data
status: draft
doc: >-
  Identifiers and fields that hold personal data of individuals in Russia.
select:
  country: [RU]
  is_pii: true
datatypes: [inn]   # added by hand: an individual's INN identifies a person
```

The fields are:

- `id`: `[a-z0-9_]`, the same rule as record ids. The file is named
  `<id>.yaml`.
- `name`, `doc`: required, as for records.
- `status`: `draft`, `stable` or `deprecated`, as for records. A
  deprecated pack can name `replaced_by`.
- `translations`: optional, in the same form as for records.
- `datatypes`, `select` and `exclude`: see D2. At least one of `datatypes`
  and `select` is required.

The schema is `schema/pack.schema.json`. As for records, it has
`additionalProperties: false`, and empty values are not allowed.

*Alternatives:*

- A single `data/packs.yaml` file. One file per pack gives each pack its own
  history, its own "edit on GitHub" link and its own review, as for records.
- A `packs: [...]` field on each record. Then a pack has no single place to
  review, and its description has no home.

### D2. Membership: explicit list, filter, exclusions

Members = (`datatypes` ∪ records that match `select`) − `exclude`.

- `datatypes` and `exclude` hold datatype ids. Pattern ids are not allowed
  there. A pattern is a member when the datatype in its `semantic_type` is a
  member.
- `select` keys are combined with AND. The values of one key are combined
  with OR:
  - `categories`: the record has at least one of the listed categories;
  - `country`: the record lists at least one of the countries. The value
    `any` matches records without a country;
  - `langs`: the record lists at least one of the languages;
  - `is_pii`: `true` or `false`;
  - `classification`: `identifier` or `categorical`;
  - `checksum`: `true` means the record has a `checksum`;
  - `status`: the statuses to match. The default is `[stable]`, so a new
    draft does not join a pack until someone reviews it. `deprecated` is
    never matched.
- `select` works on datatypes only. It uses the values that patterns
  inherit, so a datatype matches on its own fields.
- The order of output lists is sorted by id, so builds stay reproducible.

*Alternatives:*

- Lists only, like Semgrep rulesets. A pack such as "Russian personal data"
  would then need an edit for every new record. It would drift from the
  records without anyone noticing.
- Filters only. A curated pack, such as special categories of personal
  data, cannot be written as a filter over the current fields.
- A query language with OR across keys and NOT. It is harder to review, and
  `exclude` covers the cases found so far.

### D3. Validation gates

The build fails on:

- a schema error in a pack file, or a file name that differs from the id;
- a duplicate pack id;
- an id in `datatypes` or `exclude` that is unknown, an alias or a pattern.
  The error names the canonical id for an alias;
- a `select` value that is not a known category, country, language or
  classification;
- a pack with no members after resolution;
- an unresolved `replaced_by`.

It warns when:

- `datatypes` lists a `draft` or `deprecated` record;
- an `exclude` id would not be a member anyway;
- a `stable` pack has a member without metacrafter-rules rules.

### D4. API files

`/api/v1/packs.json` (the counts are illustrative):

```json
{"packs": [{"id": "ru_pii", "name": "...", "status": "draft",
            "counts": {"datatypes": 41, "patterns": 3, "rules": 57},
            "url": "https://registry.apicrafter.io/pack/ru_pii",
            "json_url": "https://registry.apicrafter.io/api/v1/packs/ru_pii.json"}]}
```

`/api/v1/packs/<id>.json` holds the pack's source fields and these resolved
fields:

- `datatypes`: member datatype ids;
- `patterns`: pattern ids;
- `rules`: one entry per metacrafter-rules rule whose `key` is a member or
  one of its aliases. The fields are copied from the coverage file: `rule`,
  `key`, `type`, `context`, `lang`, `country_code` and `file`;
- `without_rules`: member ids that no rule detects;
- `rules_ref`: the metacrafter-rules commit pinned in `ecosystem.lock`;
- `url`, `json_url` and `md_url`.

Each record in `/api/v1/datatypes/<id>.json` and in the bulk files gets
`packs`: the sorted ids of the packs it belongs to. The field is omitted
when the list is empty, as other empty values are.

The manifest lists both files with size and SHA-256. The OpenAPI
description gets the two paths and a `Pack` schema.

*Alternative:* serve a YAML config for metacrafter, like
`semgrep.dev/c/p/<id>`. metacrafter-rules rules are not in this repository,
so the registry cannot serve them. A list of rule names plus the pinned
commit lets metacrafter select rules from its own checkout.

### D5. Pages

- `/pack/` lists the packs with name, status and counts.
- `/pack/<id>` shows the description, how membership is defined (the
  `select` filter in words, the hand-picked ids and the exclusions), the
  member table (the same table macro as category pages) and the
  rule-coverage numbers.
- `/pack/<id>.md` is the Markdown twin. `llms.txt`, the sitemap and the
  site navigation link the packs.
- A record page shows "In packs:" with links when `packs` is not empty.

### D6. Client and MCP

- `Registry.pack(id)` returns the resolved pack, and `Registry.packs()`
  lists them.
- The MCP server gets a `list_packs` tool, and `search_datatypes` gets a
  `pack` filter. This is optional, in task group 4.

## Risks / Trade-offs

- [A `select` pack changes when records change, without a pack edit.] →
  The `/changes` page and `changes.json` report pack membership changes
  between releases. `select` matches `stable` records by default.
- [Pack ids become part of the URL contract.] → A pack is never deleted. It
  is deprecated with `replaced_by`, as records are. Retired pack ids keep
  their files.
- [Rule lists go stale when metacrafter-rules moves on.] → The rules come
  from the pinned coverage file, and `rules_ref` names its commit. They
  update with `coverage update`.
- [Too many packs that differ little from category pages.] → A pack needs a
  purpose that categories and countries do not cover. Contributors state
  the purpose in `doc`, and reviewers check it.

## Migration Plan

Additive. Deploy with the next minor release. Rollback is to revert the
change: no existing file or URL changes.

## Open Questions

- Which packs to seed. Candidates from the review: `ru_pii` (country RU and
  personal data), `checksum_verified` (records with a check-digit
  algorithm), and `secrets` once the `secrets` category exists. The
  maintainer decides in task 1.1.
