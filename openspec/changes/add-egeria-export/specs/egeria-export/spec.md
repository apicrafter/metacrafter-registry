## Purpose

This capability publishes the registry as an Egeria Open Metadata Archive.
Egeria users load one file and get every registry datatype and pattern as a
`DataClass`, linked back to its registry URL.

## ADDED Requirements

### Requirement: Archive file
The build SHALL write an Open Metadata Archive to `dist/registry.omarchive.json`. The site SHALL serve it at `/registry.omarchive.json` with the media type `application/json`.

The archive SHALL meet these conditions:

- It is compact UTF-8 JSON, and its top-level `class` is `OpenMetadataArchive`.
- Its `archiveProperties` have `archiveType` `CONTENT_PACK` and a fixed `archiveGUID` that never changes between builds or releases.
- Its `archiveVersion` is the registry data version, and its `originatorLicense` is the data license of the manifest.
- Its `dependsOnArchives` list contains only the Egeria Open Metadata Types archive (`bce3b0a0-662a-4f87-b8dc-844078a11a6e`).
- It declares no types: it has no `archiveTypeStore`.
- Every instance in `archiveInstanceStore` has `instanceProvenanceType` `CONTENT_PACK`, and its `metadataCollectionId` is the `archiveGUID`.

#### Scenario: Build writes the archive
- **WHEN** `metacrafter-registry build` succeeds
- **THEN** `dist/registry.omarchive.json` exists, parses as JSON, and has `archiveType` `CONTENT_PACK`, the fixed `archiveGUID` and the current data version

#### Scenario: Served as JSON
- **WHEN** a client requests `/registry.omarchive.json` from the deployed site
- **THEN** the response is 200 with the media type `application/json`

### Requirement: Egeria type conformance
The archive SHALL use only entity, relationship and classification types, attributes and enumeration values that the Egeria V6.2 Open Metadata Types archive declares. For each type, the allowed attributes SHALL be its own attributes and those of its supertypes. The repository SHALL pin an extract of those type definitions, and a test SHALL fail when the archive uses a name that the extract does not declare. Type GUIDs and enumeration ordinals in the archive SHALL come from the extract.

The documentation SHALL state that the archive supports Egeria V6.0 and later.

#### Scenario: Undeclared attribute
- **WHEN** a change makes the emitter set an attribute that `DataClass` and its supertypes do not declare
- **THEN** the test suite fails, naming the type and the attribute

#### Scenario: Type GUIDs
- **WHEN** the archive contains a `DataClass` entity
- **THEN** its type GUID is `6bc727dc-e855-4979-8736-78ac3cfcd32f`, the value of the pinned V6.2 extract

### Requirement: Data classes for datatypes and patterns
The archive SHALL contain exactly one `DataClass` entity for each datatype and each pattern. Its values SHALL come from the normalized record of `/api/v1`, so a pattern carries the `categories`, `is_pii` and `classification` it inherits. Each `DataClass` SHALL have these attributes:

- `qualifiedName`, as the "Stable identity" requirement defines it;
- `identifier`: the registry id;
- `displayName`: the `name`;
- `description`: the `doc`;
- `url`: the record page URL;
- `versionIdentifier`: the data version;
- `contentStatus`: `DRAFT` for `draft`, `ACTIVE` for `stable`, and `DEPRECATED` for `deprecated`;
- `dataPatterns`: a list with the record's own `regexp`, only when the record has one;
- `sampleValues`: the values of the examples that are not marked `valid: false`, in source order, only when there is at least one.

The archive SHALL NOT set the `DataClass` and `DataValueSpecification` attributes that the registry has no data for. These include `matchThreshold`, `dataType`, `units`, `allowsDuplicateValues`, `isNullable` and `isCaseSensitive`.

#### Scenario: Stable datatype with regexp and examples
- **WHEN** the registry has a stable datatype with a regexp, two positive examples and one negative example
- **THEN** its `DataClass` has `contentStatus` `ACTIVE`, `dataPatterns` with that one regexp, and `sampleValues` with the two positive values only

#### Scenario: Draft record without regexp
- **WHEN** a draft record has no regexp and no examples
- **THEN** its `DataClass` has `contentStatus` `DRAFT`, and has neither `dataPatterns` nor `sampleValues`

#### Scenario: Counts match the registry
- **WHEN** the registry has N datatypes and M patterns
- **THEN** the archive has N + M `DataClass` entities for records, plus one for each alias (see "Former ids")

### Requirement: Stable identity
Each element SHALL have an identity that does not depend on the build's base URL. The `qualifiedName` values SHALL be:

- `DataClass::https://registry.apicrafter.io/datatype/<id>`, for a datatype, a pattern or an alias;
- `ExternalReference::<link url>`, for a link target;
- `MetadataCollection::Content Pack::MetacrafterRegistry`, for the entity that describes the archive.

The GUID of the `MetadataCollection` entity SHALL be the `archiveGUID`. Every other GUID SHALL be a name-based UUID (version 5). Its namespace SHALL be the `archiveGUID`. Its name SHALL be one of these:

- the element's `qualifiedName`;
- for an element without a `qualifiedName`, a fixed key built from the identities of the elements it connects to, plus its language or label.

The `url` attribute SHALL use the build's base URL.

#### Scenario: Preview build keeps identities
- **WHEN** the registry is built twice from the same commit, once with the default base URL and once with `--base-url https://apicrafter.github.io/metacrafter-registry`
- **THEN** both archives have the same `qualifiedName` and GUID for every element, and only the `url` values differ

#### Scenario: Qualified name resolves
- **WHEN** a user removes the `DataClass::` prefix from a data class's `qualifiedName`
- **THEN** the rest is the registry URL of that id, and it resolves under the public URL contract

### Requirement: Value hierarchy
The archive SHALL link data classes with `DataValueHierarchy` relationships. In each relationship, end 1 SHALL be the more general class and end 2 the more specific one:

- For a pattern, end 1 SHALL be the `DataClass` of its `semantic_type`, and `label` SHALL be `pattern`.
- For a record with `parent`, end 1 SHALL be the `DataClass` of the parent, and `label` SHALL be `subtype`.

A record SHALL be end 2 of at most one `DataValueHierarchy`. If a pattern has both `semantic_type` and `parent`, the archive SHALL use `semantic_type`, and the build SHALL print a warning. A datatype's `dataPatterns` SHALL NOT contain the regexps of its patterns.

#### Scenario: Pattern under its datatype
- **WHEN** a pattern has `semantic_type: passport`
- **THEN** a `DataValueHierarchy` with label `pattern` links the `passport` data class (end 1) to the pattern's data class (end 2), and the `passport` data class's `dataPatterns` does not contain the pattern's regexp

#### Scenario: Subtype
- **WHEN** the datatype `birthday` has `parent: date`
- **THEN** a `DataValueHierarchy` with label `subtype` links the `date` data class (end 1) to the `birthday` data class (end 2)

### Requirement: Translations
For each language in a record's `translations`, including `en`, the archive SHALL contain one `TranslationDetail` entity with these attributes:

- `languageCode`: the language code;
- `language`: the English name of the language from the registry's language list;
- `displayName`: the translated name, when there is one;
- `description`: the translated description, when there is one.

A `TranslationLink` SHALL link the record's `DataClass` (end 1) to the `TranslationDetail` (end 2).

#### Scenario: Russian translation
- **WHEN** the record `email` has a `ru` translation with the name `Электронная почта (email)`
- **THEN** its data class has a `TranslationLink` to a `TranslationDetail` with `languageCode` `ru`, `language` `Russian` and `displayName` `Электронная почта (email)`

### Requirement: External references
For each distinct URL in the records' `links`, the archive SHALL contain one `ExternalReference` entity, with `url` and `displayName` set to that URL. For each link, an `ExternalReferenceLink` SHALL connect the record's `DataClass` (end 1) to that `ExternalReference` (end 2), with `label` set to the link `type`.

#### Scenario: Shared link target
- **WHEN** two records each have a `wikipedia` link to the same URL
- **THEN** the archive has one `ExternalReference` for that URL, and two `ExternalReferenceLink` relationships with label `wikipedia`

### Requirement: Registry-only fields
The archive SHALL carry the registry fields that Egeria has no attribute for in the `additionalProperties` of the `DataClass`. The keys SHALL be the registry field names:

- `country`, `langs` and `categories`;
- `is_pii` and `classification`;
- `checksum`;
- `aliases` and `replaced_by`;
- `mappings.<vocabulary>`, one key for each mapping vocabulary.

The values SHALL be encoded as follows:

- A list SHALL be joined with commas. The build SHALL fail if a list item contains a comma.
- A boolean SHALL be `true` or `false`.
- A field that the record does not have SHALL produce no key.

The archive SHALL NOT contain these:

- negative examples, example descriptions, quality scores or rule coverage;
- a `Confidentiality` or any other governance classification;
- `Location` or `ExternalId` elements.

#### Scenario: National identifier
- **WHEN** the record `inn` has `country: [RU]`, `is_pii: false`, `checksum: ru_inn` and a `purview` mapping
- **THEN** its data class's `additionalProperties` has `country` = `RU`, `is_pii` = `false`, `checksum` = `ru_inn`, and `mappings.purview` with the Purview name

#### Scenario: PII without a governance classification
- **WHEN** the record `email` has `is_pii: true`
- **THEN** its data class's `additionalProperties` has `is_pii` = `true`, and the data class has no `Confidentiality` or other governance classification

#### Scenario: Negative example is not exported
- **WHEN** a record has an example with `valid: false`
- **THEN** that value appears nowhere in the archive

### Requirement: Former ids
For each alias, the archive SHALL contain a `DataClass` with these values:

- `qualifiedName` and `url` built from the alias;
- `identifier`: the alias;
- `displayName`: the canonical record's name;
- `description`: a sentence that names the canonical id;
- `contentStatus`: `DEPRECATED`;
- `additionalProperties.replaced_by`: the canonical id.

It SHALL have no data patterns, sample values, translations, links or hierarchy relationships.

#### Scenario: Merged duplicate
- **WHEN** the record `usssn` lists `ssn` in `aliases`
- **THEN** the archive has a data class `DataClass::https://registry.apicrafter.io/datatype/ssn` with `contentStatus` `DEPRECATED` and `replaced_by` `usssn`

### Requirement: Deterministic output
Two builds of the same commit SHALL produce byte-identical archives. The instance `version`, `createTime` and `updateTime` values, and the archive `creationDate`, SHALL come from the commit time, never from the wall clock. Entities and relationships SHALL be written in a fixed sort order.

#### Scenario: Rebuild
- **WHEN** the same commit is built twice, on different days
- **THEN** the two `registry.omarchive.json` files have the same SHA-256

#### Scenario: Later commit
- **WHEN** a later commit on `main` is built
- **THEN** every instance `version` in its archive is greater than in the archive of the earlier commit

### Requirement: Load into Egeria
A load test SHALL show that the archive loads into an Egeria V6.2 metadata store, and that loading the archive of a later build updates the loaded elements instead of creating copies. The repository SHALL provide this test as a manually started workflow. It SHALL NOT be a required check on pull requests.

#### Scenario: First load
- **WHEN** the load test loads the archive into an empty Egeria V6.2 metadata store
- **THEN** a search by `qualifiedName` for the `email` data class returns one `DataClass` with the registry's data patterns, sample values and translations

#### Scenario: Reload of a later build
- **WHEN** the load test then loads the archive of a later build, in which the `email` description changed
- **THEN** the store still holds one `email` data class, and it has the new description

### Requirement: Distribution
The archive SHALL be listed and documented with the registry's other bulk files:

- The manifest `/api/v1/index.json` SHALL list `registry.omarchive.json` in `files`, with its path, size and SHA-256.
- Each GitHub Release SHALL attach the file as an asset, and `SHA256SUMS` SHALL include it.
- `llms.txt`, the README API table and the about page SHALL link to the file. The README and the about page SHALL show how to load it, with Egeria's archive loading and with `pyegeria`.
- The public URL contract check SHALL include `/registry.omarchive.json`.

These additions SHALL NOT change any existing URL or JSON shape.

#### Scenario: Manifest entry
- **WHEN** a client reads `/api/v1/index.json`
- **THEN** `files["registry.omarchive.json"]` gives the path `/registry.omarchive.json`, its size in bytes, and a SHA-256 that matches the served file

#### Scenario: Release asset
- **WHEN** a `v*` tag is pushed
- **THEN** the GitHub Release has a `registry.omarchive.json` asset, and its checksum is in `SHA256SUMS`
