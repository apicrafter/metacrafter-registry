## Purpose

This capability defines the public static website on GitHub Pages. It lets
people browse, search and evaluate semantic data types. It also keeps every
URL that metacrafter and downstream catalogs already store.

## ADDED Requirements

### Requirement: Legacy URL contract
The site SHALL keep serving these URLs with HTTP 200 on the production domain:

- `/datatype/<id>`, with no extension and no trailing slash, for every datatype and pattern
- `/tool/<id>` for every tool
- `/tool`, either directly or through a redirect to `/tool/`
- `/`

#### Scenario: metacrafter link
- **WHEN** a client requests `https://registry.apicrafter.io/datatype/email`
- **THEN** the response is 200 and contains the HTML page for datatype `email`

### Requirement: Alias redirects
For every alias, the site SHALL serve `/datatype/<alias>`. That page SHALL redirect to the canonical datatype page and declare the canonical URL.

#### Scenario: Merged ID
- **WHEN** a client requests `/datatype/ssn` after `ssn` became an alias of `usssn`
- **THEN** the page redirects to `/datatype/usssn` and contains `<link rel="canonical">` pointing to it

### Requirement: Entity page content
Each datatype or pattern page SHALL show these fields:

- name, ID, status and quality score
- doc
- PII flag and categories
- countries and languages
- regexp and checksum, when present
- examples, labelled as positive or negative
- parent and children
- patterns
- mappings, links and translations
- detection coverage: metacrafter rules and other tools
- provenance dates

Each page SHALL link to its JSON and Markdown representations and to the source file on GitHub for editing.

#### Scenario: Draft record
- **WHEN** a page renders a record with `status: draft`
- **THEN** a visible draft badge explains that the record needs review and links to the contribution guide

### Requirement: Browse and filter
The site SHALL provide these list pages:

- all datatypes, filterable by category, country, PII flag, status and detection coverage
- each category
- each country or region
- all tools

#### Scenario: Filter by country and PII
- **WHEN** a user selects country `RU` and PII on the datatype list
- **THEN** only datatypes with `RU` in `country` and `is_pii: true` are shown

### Requirement: Client-side search
The site SHALL provide full-text search over IDs, names, aliases, docs and translated names. Search SHALL run entirely in the browser and SHALL NOT send queries to third parties.

#### Scenario: Search by Russian name
- **WHEN** a user searches for "почта"
- **THEN** the results include `email`, whose Russian translation name is "Электронная почта (email)"

### Requirement: Value identification playground
The site SHALL provide a page where a user pastes sample values and optionally a field name. The page SHALL show candidate datatypes, ranked by regexp match rate and by checksum results.

Pasted values SHALL NOT leave the browser. Each regexp SHALL run with a time limit, so that a pathological pattern cannot freeze the page.

#### Scenario: Identify IBAN values
- **WHEN** a user pastes three valid IBANs
- **THEN** the IBAN datatype is ranked first, and the page shows that the checksum passed for all three

#### Scenario: Privacy
- **WHEN** values are submitted on the playground
- **THEN** no network request containing those values is made

### Requirement: Quality and contribution pages
The site SHALL publish these pages:

- a quality page with honest coverage statistics and the list of `draft` records
- a changelog page that shows the changes in each release
- a contribution guide that explains how to propose or edit a datatype, by hand or with an AI agent

#### Scenario: Contributor queue
- **WHEN** a user opens the quality page
- **THEN** draft records are listed with their missing quality elements and links to edit them

### Requirement: Discoverability
The site SHALL publish `sitemap.xml`, `robots.txt` and a 404 page.

Each entity page SHALL include a canonical URL, OpenGraph metadata and embedded schema.org JSON-LD that describes the record as a `DefinedTerm`.

#### Scenario: Structured data
- **WHEN** a crawler fetches `/datatype/email`
- **THEN** the HTML contains a JSON-LD `DefinedTerm` with `termCode` `email` and a `sameAs` link for each mapping

### Requirement: Accessible, dependency-light pages
Pages SHALL render their core content without JavaScript. Pages SHALL support light and dark colour schemes and SHALL load no third-party scripts at runtime.

#### Scenario: JavaScript disabled
- **WHEN** a datatype page is loaded with JavaScript disabled
- **THEN** all record fields are readable
