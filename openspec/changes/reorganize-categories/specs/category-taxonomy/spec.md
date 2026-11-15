## Purpose

This capability defines the categories of the registry: what a category
record contains, how a record is assigned to categories, and how a retired
category id keeps resolving.

## ADDED Requirements

### Requirement: Category reference records
Each entry of `data/categories.yaml` SHALL be valid against `schema/category.schema.json`. An entry SHALL have `id`, `name` and `kind`. An entry that has records SHALL have a `description` that says what belongs in the category. An entry MAY have `aliases`, a list of former category ids.

- `kind` SHALL be `topic`, `form`, `sensitivity` or `standard`.
- An id SHALL be unique among all category ids and aliases.
- Empty values SHALL NOT be allowed, and unknown fields SHALL be rejected.

#### Scenario: Category without a kind
- **WHEN** an entry of `data/categories.yaml` has `id` and `name` and no `kind`
- **THEN** `metacrafter-registry validate` fails and names the category

#### Scenario: Alias equals another id
- **WHEN** the category `identifiers` has `aliases: [values]` and a category `values` exists
- **THEN** validation fails and names both categories

#### Scenario: Used category without a description
- **WHEN** a datatype lists a category that has no `description`
- **THEN** validation fails and names the category

### Requirement: Derived pii category
A source record SHALL NOT list the category `pii`. The build SHALL add `pii` as the last category of every datatype and pattern whose resolved `is_pii` is true, in every output that carries `categories`.

#### Scenario: PII record gains the category
- **WHEN** a datatype has `is_pii: true` and `categories: [taxes]`
- **THEN** its records in `/registry.json`, `/datatype/<id>.json` and `/api/v1/` have the categories `taxes` and `pii`, in this order

#### Scenario: Pattern inherits is_pii
- **WHEN** a pattern declares neither `is_pii` nor `categories`, and its datatype has `is_pii: true`
- **THEN** the output categories of the pattern end with `pii`

#### Scenario: pii written in a source record
- **WHEN** a source record has `categories: [persons, pii]`
- **THEN** validation fails and tells the contributor to set `is_pii` instead

### Requirement: Primary category
The first source category of a datatype SHALL be its primary category, and the kind of that category SHALL be `topic` or `form`. A record SHALL have at most three source categories.

#### Scenario: Standard as the first category
- **WHEN** a datatype has `categories: [gs1, commerce]`
- **THEN** validation fails and says that the first category must be a topic or a form

#### Scenario: Too many categories
- **WHEN** a datatype lists four categories
- **THEN** validation fails and names the record

### Requirement: Directory follows the primary category
The category part of a record's path, `data/datatypes/<COUNTRY|any>/<category>/<id>.yaml`, SHALL equal the primary category of the record. For a pattern that declares no categories, it SHALL equal the primary category of the datatype named by `semantic_type`.

#### Scenario: Record in another directory
- **WHEN** `data/datatypes/any/geo/postindex.yaml` has `categories: [addresses]`
- **THEN** validation fails and names the file, its directory and the expected directory

#### Scenario: Pattern beside its datatype's category
- **WHEN** a pattern without `categories` has `semantic_type: phone`, `phone` has the primary category `telecom`, and the pattern file is in a `telecom` directory
- **THEN** validation reports no error for the pattern

### Requirement: Category aliases
A category id that is retired SHALL be kept in `aliases` of the category that replaces it. An alias SHALL resolve wherever a category id is accepted as input. Output records SHALL list only current category ids.

- `/category/<alias>` and `/category/<alias>.md` SHALL redirect to the pages of the current category.
- `/api/v1/categories.json` SHALL list `kind`, `description` and, when present, `aliases` for each category.
- `Registry.search` and the MCP tool `search_datatypes` SHALL resolve an alias to its category before they filter.
- A source record that lists an alias SHALL fail validation, and the message SHALL name the current id.

#### Scenario: Old category page
- **WHEN** `objectids` is an alias of `identifiers` and a user opens `/category/objectids`
- **THEN** the user is redirected to `/category/identifiers`

#### Scenario: Search by a retired id
- **WHEN** a client calls `Registry.search(category="objectids")`
- **THEN** it gets the same records as for `category="identifiers"`

#### Scenario: Alias in a source record
- **WHEN** a datatype has `categories: [objectids]`
- **THEN** validation fails and says to use `identifiers`

#### Scenario: Consumer reads the aliases
- **WHEN** a consumer reads `/api/v1/categories.json`
- **THEN** the entry `identifiers` has `"aliases": ["objectids"]`

### Requirement: Category list by kind
The page `/category/` SHALL group the categories by kind and SHALL show the description and the record count of each. The category section of `llms.txt` SHALL give the description of each category.

#### Scenario: Reader looks for a topic
- **WHEN** a user opens `/category/`
- **THEN** topics, forms, sensitivity and standards are separate groups, and each category shows its description

### Requirement: Category changes in the changelog
`metacrafter-registry changes` SHALL report categories that were added or retired between two data versions, and SHALL report a record whose categories changed.

#### Scenario: Category retired between versions
- **WHEN** the old version has the category `objectids` and the new version has it as an alias of `identifiers`
- **THEN** the changelog says that `objectids` was merged into `identifiers`

### Requirement: Stable identifiers during reorganization
A change of categories SHALL NOT change the `id` of a datatype or pattern, and SHALL NOT add, remove or retype a field of the legacy JSON shape.

#### Scenario: Record moves to a new category
- **WHEN** `ru_inn` moves from the directory `finances` to the directory `taxes`
- **THEN** `/datatype/ru_inn` and `/datatype/ru_inn.json` still resolve, and the legacy record has the same fields as before
