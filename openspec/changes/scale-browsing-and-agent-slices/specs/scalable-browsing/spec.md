## Purpose

This capability defines how the site lists records when the registry is too
large for one HTML table, and what a record page offers beyond the stored
facts: a test of one value and the names in the record's own languages.

## ADDED Requirements

### Requirement: Bounded list page
`/datatype/` SHALL render at most 100 records in its HTML, and its HTML SHALL be smaller than 150 KB whatever the number of records. With JavaScript, the page SHALL load `/api/v1/datatypes-index.json` and SHALL filter, sort and page over all records, 100 rows at a time. The filter form SHALL be usable before the index has loaded.

The page SHALL keep the query parameters `q`, `category`, `country`, `kind`, `status`, `rules` and `pii`.

#### Scenario: Existing link with a filter
- **WHEN** a visitor opens `/datatype/?pii=yes&country=RU`
- **THEN** the page shows only the records that are personal data and have the country `RU`, and states how many there are

#### Scenario: Size does not grow
- **WHEN** the registry grows from 3,002 to 6,000 records
- **THEN** `/datatype/index.html` is still smaller than 150 KB

### Requirement: Every record reachable without JavaScript
Without JavaScript, `/datatype/` SHALL show its first 100 records and a note that links to the category and country lists. Every record page SHALL be linked from at least one category or country page or, for a record with neither, from the sitemap.

#### Scenario: No JavaScript
- **WHEN** a browser without JavaScript opens `/datatype/`
- **THEN** the page shows 100 records and links to `/category/` and `/country/`

### Requirement: Test a value on the record page
A record page SHALL offer a field to test one value when the record has a check-digit algorithm or a regular expression that converts to JavaScript. The test SHALL run in the browser and SHALL NOT send the value anywhere. The result SHALL state separately whether the value matches the regular expression and whether its check digit is valid. When the record has neither, or its regular expression does not convert, the page SHALL NOT show the field.

#### Scenario: Valid value
- **WHEN** a visitor enters `7707083893` on `/datatype/inn`
- **THEN** the page states that the value matches the pattern and that the check digit is valid

#### Scenario: Wrong check digit
- **WHEN** a visitor enters `7707083894` on `/datatype/inn`
- **THEN** the page states that the value matches the pattern and that the check digit is not valid

#### Scenario: No pattern
- **WHEN** a record has no regular expression and no check-digit algorithm
- **THEN** its page has no test field

### Requirement: Names in the record's languages
A record page SHALL show, under the title, the translated name for each language in the record's `langs` that has a translation, marked with the `lang` attribute of that language.

#### Scenario: Russian name
- **WHEN** record `bik` has `langs: [ru]` and a Russian translation with the name «Банковский идентификационный код»
- **THEN** its page shows «Банковский идентификационный код» under the title, in an element with `lang="ru"`

#### Scenario: No translation
- **WHEN** a record has no translation for any of its `langs`
- **THEN** its page shows no extra name under the title
