## Purpose

This capability defines the files that let a client narrow the registry before
it downloads records: a compact index of all records, and slices by category
and by country.

## ADDED Requirements

### Requirement: Compact index
The build SHALL write `/api/v1/datatypes-index.json`: a JSON array with one object for each datatype and pattern, in id order. Each object SHALL have `id`, `name`, `kind`, `status`, `is_pii`, `categories`, `country`, `quality`, `has_regexp`, `has_rules` and `doc`. `categories` and `country` SHALL be arrays and SHALL be empty when the record has none. `doc` SHALL be cut to 160 characters. An object SHALL have `names`, an array of the record's aliases and translated names, when the record has any.

The manifest `/api/v1/index.json` SHALL list the index with its size and SHA-256.

#### Scenario: One entry per record
- **WHEN** the registry has 3,002 datatypes and patterns
- **THEN** `/api/v1/datatypes-index.json` has 3,002 objects, and each `id` is in `/api/v1/datatypes.json`

#### Scenario: Record without a country
- **WHEN** record `email` has no `country`
- **THEN** its index entry has `"country": []`

### Requirement: Slices by category and country
The build SHALL write `/api/v1/categories/<id>.json` for each category that has records and `/api/v1/countries/<CC>.json` for each country or region that has records. Each file SHALL be a JSON array of the normalized records, with the same shape as in `/api/v1/datatypes.json`, in id order. A record with several categories or countries SHALL be in the slice of each.

#### Scenario: Country slice
- **WHEN** a client reads `/api/v1/countries/RU.json`
- **THEN** it gets exactly the records of `/api/v1/datatypes.json` whose `country` contains `RU`

#### Scenario: Record with two countries
- **WHEN** a record has `country: [GB, IE]`
- **THEN** the record is in `/api/v1/countries/GB.json` and in `/api/v1/countries/IE.json`

### Requirement: Country Markdown twins
The build SHALL write `/country/<CC>.md` for each country or region that has records, in the format of the category Markdown twins: the name, the number of records, and one link to the Markdown twin of each record. `/llms.txt` SHALL link to these files. Each country page SHALL declare its twin with `<link rel="alternate" type="text/markdown">`.

#### Scenario: llms.txt links to Markdown
- **WHEN** an agent reads `/llms.txt`
- **THEN** each country link ends with `.md` and resolves

### Requirement: Described and stable
The OpenAPI document SHALL describe the index and both slice URL templates. `/search-index.json` SHALL stay published with its current shape, and the OpenAPI document SHALL mark it deprecated.

#### Scenario: OpenAPI
- **WHEN** a client reads `/api/v1/openapi.json`
- **THEN** `paths` contains `/api/v1/datatypes-index.json`, `/api/v1/categories/{id}.json` and `/api/v1/countries/{id}.json`
