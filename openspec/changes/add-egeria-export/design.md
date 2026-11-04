## Context

The motivation is in `proposal.md` (Why). The research behind it is
`devdocs/RESEARCH_EGERIA_2026-11.md` (pull request #61): sections 3 and 4,
and recommendation R3.

Every Egeria name in this document was checked against these sources on
2026-11-04:

- the type documentation in `odpi/egeria-docs` at commit `254700b`:
  - `site/docs/types/0/`: `0010-Base-Model.md`, `0014-External-References.md`,
    `0017-External-Identifiers.md`, `0019-More-Information.md` and
    `0022-Translations.md`;
  - `site/docs/types/4/0422-Governed-Data-Classifications.md`;
  - `site/docs/types/5/`: `0540-Data-Value-Specifications.md` and
    `0541-Data-Classes-and-Data-Grains.md`;
- `content-packs/OpenMetadataTypes.omarchive` in `odpi/egeria`, at tags
  `V6.0` and `V6.2` and on `main` (`3627a6f`, archive version 6.3-SNAPSHOT);
- the content packs `SimpleCatalog.omarchive` and
  `OrganizationInsightContentPack.omarchive` on `main`, used as samples of
  the archive JSON;
- `pyegeria` 6.2.20 (`odpi/egeria-python`, commit `52ff46a`).

What the sources show:

- **The types are stable across Egeria 6.x.** The following types have the
  same GUIDs and the same attribute lists in V6.0, V6.2 and `main`:
  - `Referenceable`, `AuthoredReferenceable`, `DataValueSpecification` and
    `DataClass`;
  - `DataValueHierarchy`;
  - `TranslationDetail` and `TranslationLink`;
  - `ExternalReference` and `ExternalReferenceLink`.

  Only the end names of `ExternalReferenceLink` changed between V6.0 and
  V6.2. Archive instances do not contain end names. Egeria 5.x has the older
  `DataClassHierarchy` instead, so V6.0 is the oldest release we can support.
- **The attributes we use:**

  | Type | Attributes |
  |---|---|
  | `Referenceable` | `qualifiedName`, `identifier`, `displayName`, `description`, `versionIdentifier`, `category`, `url`, `additionalProperties` (map of strings) |
  | `AuthoredReferenceable` | `contentStatus` (enum `ContentStatus`), `userDefinedContentStatus`, `authors` |
  | `DataValueSpecification` | `namespacePath`, `matchPropertyNames`, `matchThreshold`, `specification`, `specificationDetails`, `dataType`, `units`, `absoluteUncertainty`, `relativeUncertainty` |
  | `DataClass` | `allowsDuplicateValues`, `isNullable`, `isCaseSensitive`, `defaultValue`, `averageValue`, `valueList`, `valueRangeFrom`, `valueRangeTo`, `sampleValues`, `dataPatterns` |
  | `TranslationDetail` | `language`, `languageCode`, `locale`, `displayName`, `description`, `additionalTranslations` |
  | `ExternalReference` | `referenceTitle`, `referenceAbstract`, `authors`, `sources`, `organization`, `license`, `copyright`, `attribution` |
  | `LabeledRelationship` | `label`, `description` |

  `ExternalReference` inherits `url` and `displayName` from `Referenceable`.
  `TranslationDetail` inherits from `OpenMetadataRoot`, not from
  `Referenceable`, so it has no `qualifiedName`.
- **The relationships we use:**
  - `DataValueHierarchy` is a `LabeledRelationship`. End 1 is the more
    abstract specification (`superDataValueSpecification`, at most one). End
    2 is the more specialized one (`subDataValueSpecifications`, any number).
  - `TranslationLink`: end 1 is the translated element (at most one). End 2
    is the `TranslationDetail`.
  - `ExternalReferenceLink` is a multi-link `LabeledRelationship`. End 1 is
    a `Referenceable`, and end 2 is an `ExternalReference`.
- **`ContentStatus` values:** `DRAFT`, `PREPARED`, `PROPOSED`, `APPROVED`,
  `REJECTED`, `ACTIVE`, `DEPRECATED`, `OBSOLETE` and `OTHER`.
- **The archive JSON.**
  - The top level is `class: OpenMetadataArchive`, with `archiveProperties`
    and `archiveInstanceStore`.
  - `archiveProperties` has `archiveGUID`, `archiveName`,
    `archiveDescription`, `archiveType` (`CONTENT_PACK`), `archiveVersion`,
    `creationDate`, `dependsOnArchives`, `originatorName` and
    `originatorLicense`.
  - `archiveInstanceStore` has `entities` (`EntityDetail`) and
    `relationships` (`Relationship`, with `entityOneProxy` and
    `entityTwoProxy`).
  - Property values are `PrimitivePropertyValue`, `ArrayPropertyValue`,
    `MapPropertyValue` or `EnumPropertyValue` objects.
  - Each instance carries `instanceProvenanceType: CONTENT_PACK`, a
    `metadataCollectionId` equal to the `archiveGUID`, and a `version`.
  - Both sample packs also contain a `MetadataCollection` entity that
    describes the pack. Its GUID is the `archiveGUID`, and its
    `qualifiedName` has the form `MetadataCollection::Content Pack::<archiveName>`.
  - The Open Metadata Types archive has the GUID
    `bce3b0a0-662a-4f87-b8dc-844078a11a6e` in every release checked. Content
    packs list it in `dependsOnArchives`.
- **How users load an archive:**
  - Egeria loads archives at server start-up, or into a running server.
  - `pyegeria` wraps this as `add_archive_file`, for a path on the server's
    file system, and `add_archive_content`, which posts the archive as a
    request body.
  - The Data Designer API (`pyegeria.omvs.data_designer`) creates data
    classes one at a time, through `data-value-specifications` endpoints.
    The endpoint names follow the 2026 type changes.
- **`pyegeria` needs Python 3.12 or later.** The registry supports Python
  3.10 and later.

Registry facts that shape the mapping (data at `4041c22`):

- 621 records: 563 datatypes and 58 patterns.
- Statuses: 416 `stable` and 205 `draft`.
- 27 datatypes have a `parent`. No pattern has a `parent`.
- 466 links point to 408 distinct URLs.
- 143 translations in 9 languages, including 12 in `en`. Some records have a
  name that is not in English, for example `bsn`.
- 448 positive examples. 14 records have negative examples.
- 12 records have a `checksum`.
- 9 aliases, and no `replaced_by`.
- 4 records have more than one `country`.
- The build's canonical base URL is `DEFAULT_BASE_URL`
  (`https://registry.apicrafter.io`). `--base-url` changes it for preview
  and fallback deployments.

## Goals / Non-Goals

**Goals:**
- An Egeria V6.x user loads one file and gets every registry datatype and
  pattern as a `DataClass`, with hierarchy, translations and links. Each
  element points back to the registry.
- Loading the archive of a later release updates the same elements. It does
  not duplicate them.
- The build stays offline, deterministic and free of new dependencies.
- No Egeria attribute or type name is used that the pinned Egeria type
  definitions do not declare.

**Non-Goals:**
- A loader that calls Egeria APIs (`pyegeria`, Data Designer). See D1.
- Egeria releases before V6.0.
- Glossary terms. Research R1: the registry stays at the value level.
- `Collection` elements for categories. Categories go to
  `additionalProperties`. A later change can add folders if Egeria users ask
  for them.
- Tools, rule coverage (`detected_by`) and quality scores. They describe the
  registry and metacrafter, not the values.
- Importing from Egeria into the registry.
- Values for Egeria-only attributes that the registry has no data for:
  `matchThreshold`, `dataType`, `units`, value ranges, `isNullable`,
  `isCaseSensitive`, `DataClassComposition`. Research R4 and R5 cover them.

## Decisions

### D1. Output form: an Open Metadata Archive file, not an API loader

The build writes a static archive file. This change ships no `pyegeria` or
Data Designer loader.

- **Why:**
  - Archives are how Egeria distributes standard content. Content packs are
    archives, and users already know how to load them.
  - A static file fits the platform: GitHub Pages, an offline deterministic
    build, and a checksum in the manifest. The SKOS export works the same
    way.
  - Archive elements carry the archive's metadata collection id and the
    `CONTENT_PACK` provenance. They stay identifiable as registry content,
    and a reload replaces them as a set. An API loader would create elements
    in the user's own collection. Those would drift from the registry, and
    the loader would need update and delete logic.
  - Python users already have a loader: `pyegeria`'s `add_archive_content`
    and `add_archive_file`. The docs show a short snippet instead.
  - A `pyegeria` dependency would need Python 3.12 or later, but the
    registry supports 3.10. The Data Designer API changes with the type
    model, so a loader would also need regular maintenance.
- **Alternatives:**
  - Loader only: needs a running Egeria server and credentials. It cannot
    run in the Pages build. It writes elements that the user's server owns.
  - Both: twice the maintenance, and nothing that the archive with a
    `pyegeria` snippet does not already give. A later change can add a
    loader if users need upsert into their own collections.
- **Cost:** the archive JSON is verbose and close to Egeria's internal
  instance model. D9 and D10 control that risk.

### D2. File, location and media type

- The path is `dist/registry.omarchive.json`, served at
  `/registry.omarchive.json`. It sits next to `/registry.ttl`: both files
  export the whole registry.
- The `.json` extension makes GitHub Pages serve the file as
  `application/json`, which Pages compresses. Egeria does not depend on the
  file extension.
- The JSON is compact (no indentation) and UTF-8. Our estimate, from a mock
  with the real record counts: about 8.5 MB, and about 0.2 MB compressed.
- The same file is a GitHub Release asset under the same name.
- **Alternatives:**
  - `.omarchive`, the extension Egeria uses: Pages serves unknown
    extensions as `application/octet-stream`, and we cannot rely on it
    compressing that type. The download could be up to about 40 times
    larger.
  - A path under `/api/v1/`: that tree holds the registry's own versioned
    JSON shapes. The archive follows Egeria's format and versioning.

### D3. Archive envelope

`archiveProperties`:

| Property | Value |
|---|---|
| `archiveGUID` | A fixed UUID, chosen once in the implementation and never changed |
| `archiveName` | `MetacrafterRegistry` |
| `archiveDescription` | One sentence: what the archive holds, the registry URL, and the supported Egeria versions |
| `archiveType` | `CONTENT_PACK` |
| `archiveVersion` | The data version from the manifest |
| `creationDate` | The commit time (`SOURCE_DATE_EPOCH`, else the last commit), in milliseconds |
| `dependsOnArchives` | `["bce3b0a0-662a-4f87-b8dc-844078a11a6e"]`, the Open Metadata Types archive |
| `originatorName` | `Metacrafter Registry` |
| `originatorLicense` | The manifest license (`Apache-2.0`) |

- No `archiveTypeStore`, because the archive declares no types.
- Instances use `instanceProvenanceType: CONTENT_PACK`. Their
  `metadataCollectionId` is the `archiveGUID`, and their
  `metadataCollectionName` is the `archiveName`.
- The archive includes a `MetadataCollection` entity that describes it, as
  Egeria's own packs do. Its GUID is the `archiveGUID`, and its
  `qualifiedName` is `MetadataCollection::Content Pack::MetacrafterRegistry`.
- Instance headers, classifications (including `Anchors`) and property value
  objects follow the layout of the Egeria-built sample packs. Task 1 checks
  the result by loading it into a real server.

### D4. `qualifiedName`: the type name plus the canonical registry URL

| Element | `qualifiedName` |
|---|---|
| Datatype or pattern | `DataClass::https://registry.apicrafter.io/datatype/<id>` |
| Former id (D8) | `DataClass::https://registry.apicrafter.io/datatype/<alias>` |
| Link target | `ExternalReference::<link url>` |
| The archive itself | `MetadataCollection::Content Pack::MetacrafterRegistry` |

- **Why:**
  - It follows Egeria's convention `<TypeName>::<name>`, which `pyegeria`'s
    `__create_qualified_name__` and the content packs use.
  - The URL is globally unique. It cannot collide with an organization's own
    data classes, and it is unique within its type, as `Referenceable`
    requires.
  - Removing the `DataClass::` prefix gives the registry URL. That URL
    already resolves for every id and every alias, forever (URL contract).
  - It contains the same URL that metacrafter writes into catalogs as
    `datatype_url`.
- The base of the `qualifiedName` is always `DEFAULT_BASE_URL`, never
  `--base-url`. A preview or `github.io` build must produce the same
  identities, or a user who loads both gets duplicates.
- Other identity attributes:
  - `identifier` holds the registry id. `Referenceable` describes this
    attribute as an identifier used outside open metadata.
  - `url` holds the page URL built from the build's base URL, as the other
    outputs do.
- **Alternatives:**
  - The bare id (`inn`): not unique across sources.
  - The bare URL: unique, but it breaks the `<TypeName>::` convention that
    Egeria's own tools and packs follow.
  - `MetacrafterRegistry::DataClass::inn` (pyegeria's local-qualifier
    form): unique, but it does not resolve, and it adds a namespace token
    that exists nowhere else.

### D5. GUIDs, versions and determinism

- **GUIDs.** The `MetadataCollection` entity uses the `archiveGUID` (D3).
  Every other GUID is a UUIDv5 value. The namespace is the `archiveGUID`,
  and the name is:
  - the `qualifiedName`, for `Referenceable` elements;
  - `<DataClass qualifiedName>::TranslationDetail::<language>`, for
    translations;
  - `<relationship type>::<end 1 GUID>::<end 2 GUID>[::<label>]`, for
    relationships. The label makes multi-link `ExternalReferenceLink`
    instances unique.
- **`version`** of every instance is the commit time in Unix seconds.
  **`createTime` and `updateTime`** are the commit time in milliseconds. On
  `main` these values increase with each merge. Our understanding is that
  Egeria updates a stored instance only when the incoming `version` is
  higher. Task 1 verifies this.
- **Order:** entities are sorted by type name, then `qualifiedName` or GUID.
  Relationships are sorted by GUID. Array values keep source order.
- **Determinism:** two builds of the same commit produce identical bytes.
  The build reads no wall clock and no random state.

### D6. Patterns and `parent`: `DataValueHierarchy`, not `dataPatterns`

- A pattern becomes its own `DataClass`. A `DataValueHierarchy` links it to
  the `DataClass` of its `semantic_type`: the datatype is end 1 (super), and
  the pattern is end 2 (sub). The label is `pattern`.
- A `parent` also becomes a `DataValueHierarchy`: the parent is end 1, and
  the record is end 2. The label is `subtype`.
- A datatype's `dataPatterns` holds only its own regexp. The regexps of its
  patterns are not copied into it.
- **Why:**
  - Patterns have their own id, URL, status, examples, links and often
    country. 40 of the 58 patterns are metacrafter-rules keys, so
    metacrafter links to their URLs. As items in `dataPatterns`, all of that
    would be lost.
  - Egeria says discovery goes down `DataValueHierarchy` to the most
    specific class. A value that matches a pattern also matches its
    datatype, which is the meaning of the hierarchy.
  - The two labels keep the registry's distinction between a representation
    (`semantic_type`) and a broader type (`parent`). Egeria has no
    "representation of" relationship.
- **Constraint:** end 1 of `DataValueHierarchy` allows at most one super, so
  a record can have only one. Today no pattern has a `parent`. If a pattern
  ever has both fields, the export uses `semantic_type` and the build prints
  a warning.
- **Alternative:** copying the pattern regexps into the datatype's
  `dataPatterns` as well. This duplicates data and makes a datatype match
  values that only one regional pattern defines. Rejected.

### D7. Field mapping

A `DataClass` is built from the normalized `/api/v1` record. Patterns
therefore carry the `categories`, `is_pii` and `classification` they inherit.

| Registry field | Egeria | Reason |
|---|---|---|
| `id` | `identifier`; part of `qualifiedName` and `url` | D4 |
| `name` | `displayName` | Same meaning |
| `doc` | `description` | Same meaning |
| `status` | `contentStatus`: `draft` = `DRAFT`, `stable` = `ACTIVE`, `deprecated` = `DEPRECATED` | Egeria defines `ACTIVE` as approved and in use, which is what a published stable record is. `APPROVED` only says that the content is approved. |
| `regexp` | `dataPatterns` (one item) | Same meaning |
| `examples` with `valid` not `false` | `sampleValues`, in source order | Same meaning. Example descriptions are dropped. |
| `examples` with `valid: false` | dropped | See below |
| `parent`, `semantic_type` | `DataValueHierarchy` | D6 |
| `translations` | `TranslationDetail` and `TranslationLink` | See below |
| `links` | `ExternalReference` and `ExternalReferenceLink` | See below |
| `mappings` | `additionalProperties`, keys `mappings.<vocabulary>` | See below |
| `country`, `langs`, `categories` | `additionalProperties` | See below |
| `is_pii` | `additionalProperties` | See below |
| `classification` | `additionalProperties` | See below |
| `checksum` | `additionalProperties` | See below |
| `aliases`, `replaced_by` | `additionalProperties` (and D8) | Egeria has no former-id or replacement relationship for data classes. `ReplacementTerm` connects glossary terms only. |
| data version | `versionIdentifier` | `Referenceable`'s user-managed version |
| `quality`, `detected_by`, `provenance` | dropped | Non-goals |

Details:

- **`additionalProperties` encoding.**
  - The keys are the registry field names, so the mapping documents itself:
    `country`, `langs`, `categories`, `is_pii`, `classification`,
    `checksum`, `aliases`, `replaced_by` and `mappings.<vocabulary>`.
  - A list becomes one string joined with commas. Registry ids and ISO
    codes contain no commas, and no current mapping value does. The build
    fails if an item ever contains one.
  - Booleans become `true` or `false`.
  - An absent field gives no key.
- **Translations.**
  - Each language becomes one `TranslationDetail`, with these attributes:
    - `languageCode`: the ISO 639-1 key;
    - `language`: the English name from `data/langs.yaml`;
    - `displayName`: the translated `name`;
    - `description`: the translated `doc`.
  - `locale` and `additionalTranslations` are not set.
  - `en` is exported like any other language. Some base texts are not
    English (`bsn` is Dutch), so the base text is not assumed to be
    English.
  - `TranslationLink` connects the `DataClass` (end 1) to each translation
    (end 2).
- **Links.**
  - Each distinct URL becomes one `ExternalReference`, with `url` and
    `displayName` both set to the URL. The registry stores no link titles,
    so `referenceTitle` is not set.
  - Each link becomes one `ExternalReferenceLink`, with `label` set to the
    link `type` (`wikipedia`, `wikidata`, `schema.org`, ...).
  - About 408 shared elements serve 466 links.
  - Rejected alternatives:
    - `MoreInformation`: it still needs a `Referenceable` at the far end.
      It means "describes", not "cites".
    - `ExternalId`: it correlates elements of catalogued third-party
      metadata systems.
- **Mappings** go to `additionalProperties`, not `ExternalId` and
  `ExternalIdLink`.
  - `ExternalId` exists to synchronize metadata with a third-party system
    that is catalogued in Egeria. It needs that system as a `ScopedBy`
    element, and it carries synchronization attributes
    (`permittedSynchronization`, `lastSynchronized`). For Presidio, Google
    DLP or Purview, we would have to invent the system elements, and the
    synchronization attributes would mean nothing.
  - `ExternalReference` describes documents. Most Wikidata and schema.org
    mappings already have a matching entry in `links`.
- **`is_pii`** goes to `additionalProperties`, not the `Confidentiality`
  classification (model 0422).
  - `confidentialityLevel` is an integer on a scale that each organization
    defines with valid metadata values. A boolean cannot choose a level for
    every organization. Setting one would invent a fact.
  - A classification describes the element it is attached to. On a
    `DataClass`, it would label the definition as confidential, not the data
    that the definition describes.
  - Organizations attach governance classifications to their own assets and
    terms.
- **`country`** goes to `additionalProperties`.
  - It does not go to `namespacePath`, which holds one value. Four records
    have several countries, and the attribute has no agreed meaning for
    jurisdiction.
  - It does not become `Location` elements (model 0025). An Egeria location
    says where an asset or its data is, for data sovereignty. The registry's
    `country` says which jurisdiction defines or issues the value. A
    `KnownLocation` from a data class to a country would claim that the
    class is located there. It would also mean inventing about 60 country
    elements.
- **`checksum`** goes to `additionalProperties`, not `specification`.
  - `specification` holds a complete matching rule, in the rule language of
    each organization.
  - A bare algorithm name such as `luhn` would look like the whole rule, and
    it would hide the fact that the regexp also applies.
  - The record's `url` documents the algorithm.
- **`classification`** goes to `additionalProperties`. It does not set
  `allowsDuplicateValues: false`.
  - This corrects the research crosswalk.
  - `identifier` means that a value identifies something. It does not mean
    that the values in a column are unique: a transactions table repeats the
    counterparty INN.
  - `allowsDuplicateValues` describes a field's values, so setting it would
    be wrong for most real columns.
- **Negative examples are dropped.**
  - `DataClass` has no attribute for values that must not match.
  - They are test fixtures for the registry's CI, and the record's `url`
    leads to them.
  - Putting them in `additionalProperties` would need a list encoding for
    free text that can contain commas.
- **Attributes not set:**
  - `matchThreshold` (research R5);
  - `dataType`, `units`, ranges, `isNullable`, `isCaseSensitive`,
    `defaultValue`, `averageValue` and `valueList`: the registry has no data
    for them;
  - `namespacePath`, `specification` and `category`: see above;
  - `authors`: records have no authors.

### D8. Former ids become deprecated `DataClass` elements

- For each alias, the archive contains a `DataClass` with these values:
  - `qualifiedName` and `url` built from the alias;
  - `identifier`: the alias;
  - `displayName`: the canonical record's name;
  - `description`: a generated sentence naming the canonical id;
  - `contentStatus`: `DEPRECATED`;
  - `additionalProperties.replaced_by`: the canonical id.

  It has no patterns, samples, links or hierarchy.
- **Why:**
  - Registry ids are permanent, and aliases keep resolving.
  - An Egeria repository that loaded an archive before a merge still holds
    the old element.
  - Loading a later archive now updates that element to `DEPRECATED`, with a
    pointer, instead of leaving it looking current. The site's alias
    redirect pages do the same for people.
- **Alternative:** emitting nothing for aliases. The stale elements would
  stay `ACTIVE` in users' repositories forever.

### D9. Pinned Egeria type extract

- The package includes `egeria_types.json`, an extract of the V6.2
  `OpenMetadataTypes.omarchive`. It contains:
  - for each type we emit, and for its supertypes: the name, GUID, version
    and category;
  - the declared attributes and their types;
  - the `ContentStatus` ordinals;
  - the GUIDs of the property types `string`, `array<string>` and
    `map<string,string>`.

  A script in `scripts/` regenerates it from a types archive. Egeria is
  Apache-2.0, like this repository. The file names its source and release.
- The emitter reads type GUIDs and enum ordinals from the extract. It never
  uses literal GUIDs.
- A unit test fails if an emitted entity, relationship or classification
  uses a type name that is not in the extract, or a property that its type
  and supertypes do not declare. This enforces "do not invent attributes" in
  code.

### D10. Checks

- **Unit tests (every PR, through `pytest`):**
  - the envelope is correct;
  - names and properties are declared (D9);
  - GUIDs are unique;
  - every relationship end points to an entity in the archive, except the
    types archive, which is never referenced;
  - the counts match the registry;
  - the mapping is correct on fixture records;
  - the bytes are identical across two builds.
- **Load test (manual workflow `egeria.yml`, `workflow_dispatch`):** runs
  against the `odpi/egeria-platform:6.2` container with a metadata store
  server. It does three things:
  - loads the built archive;
  - finds a `DataClass` by `qualifiedName` and checks its patterns, samples,
    hierarchy and translations;
  - loads the archive of a second build with a higher `version`, and checks
    that the element was updated and not duplicated.

  It is not part of PR CI: an Egeria platform takes minutes to start and
  configure, and a third-party image should not block contributors. Run it before a release
  that changes the emitter or the pinned Egeria version.

## Risks / Trade-offs

- **[Egeria renames or reshapes the types again, as in 2026]** → The
  archive targets V6.0 and later. The pinned extract (D9) and the manual
  load test catch drift when the extract is updated. The archive
  description and the docs state the supported range.
- **[Reload semantics differ from our understanding]** If Egeria ignores
  instances whose GUID already exists, or does not compare `version` → Task
  1 verifies this before any other work. If an update by reload does not
  work, the docs tell users to remove the archive's elements and load the
  new one. D5 stays, because deterministic GUIDs are still needed to avoid
  duplicates.
- **[A changed `archiveGUID` orphans every loaded element]** It would move
  them to a different home metadata collection → The value is a constant,
  and a test pins it.
- **[Regexp dialect]** Registry regexps use Python `re`. Egeria tools are
  usually Java → The registry's portability gate already rejects possessive
  quantifiers and atomic groups, and warns on Python-only syntax. Today one
  regexp gets that warning (`sgnric`, `(?i)`), and Java supports that
  syntax too. Regexps are exported as they are. The docs name the dialect.
- **[Users edit the loaded elements, and a reload overwrites the edits]** →
  The docs say to link organization terms and fields to registry classes,
  not to edit the classes. Task 1 records how Egeria V6.2 treats archive
  elements: as read-only copies, or as elements that users can edit.
- **[About 200 draft records reach Egeria]** → They keep `DRAFT`, so users
  can filter on `contentStatus`. Leaving them out would make the archive
  disagree with every other output.
- **[Large JSON]** About 8.5 MB → Compact JSON, served compressed. Its size
  and SHA-256 are in the manifest.
- **[`additionalProperties` is untyped]** → The keys are the registry field
  names, and the docs list them. Typed Egeria representations can replace
  keys in a later change, if Egeria users need them.

## Migration Plan

- The change is purely additive. No data, YAML field or existing URL
  changes.
- Rollout follows the task groups. Each group leaves `main` deployable:
  1. spike;
  2. emitter and tests, with the file not yet written to `dist/`;
  3. wire the file into the build, manifest, contract check and docs;
  4. release asset and load-test workflow.
- Rollback: remove the archive from the build. Nothing depends on it inside
  the ecosystem. Users who loaded it keep their reference copies, and they
  can remove them with Egeria's archive tooling.

## Open Questions

- Does Egeria V6.2 need the `Anchors` classification on `DataClass` and
  `TranslationDetail` elements that come from an archive? And if it does,
  with which anchor values? The spike copies what Egeria's own packs do.
  This changes only the emitted instance layout, not the specs or the
  tasks.
