# Egeria glossary terms and registry semantic types (2026-11-04)

Research for issue
[#9 "Review Egeria glossary terms"](https://github.com/apicrafter/metacrafter-registry/issues/9).
The issue asks how the Egeria glossary (type area 3) compares with the
registry's semantic types, and what the key differences are.

Sources: the Egeria type documentation in
[`odpi/egeria-docs`](https://github.com/odpi/egeria-docs/tree/main/site/docs/types)
(`main` on 2026-11-04, Egeria release V6.2), the content packs in
[`odpi/egeria`](https://github.com/odpi/egeria/tree/main/content-packs),
and the registry sources at commit `cc4be37`. Registry numbers come from
`metacrafter-registry stats` and from the YAML files.

## Summary

- **A registry datatype is an Egeria `DataClass`, not a `GlossaryTerm`.**
  - A glossary term records what a word means to one organization. Subject
    matter experts write it, and stewards approve it.
  - A data class records what the values of a field look like. It holds
    regular expressions, sample values and a match threshold, and discovery
    engines run it against data. That is what a registry record does.
  - The issue's premise ("the glossary is similar to semantic types") is
    only partly true. The glossary is the closest match by name. The data
    class is the closest match by function.
- **Egeria splits what the registry keeps in one record.** It has three
  layers:
  - meaning: `GlossaryTerm` (area 3);
  - value specification: `DataClass` (area 5, model 0541);
  - storage structure: `SchemaType` and `DataField` (area 5).

  A registry record combines the first two. It does not describe storage.
- **Egeria ships the container, not the content.** The two largest content
  packs have no `DataClass` instances: `CoreContentPack` (45 MB) and
  `CocoComboArchive` (22 MB). The Coco Pharmaceuticals sample contains
  glossary terms of a fictional company. No standard catalog of reusable data
  classes exists for Egeria. The registry could fill that gap (see R3).
- **Egeria models how a type is assigned to a field. The registry does
  not.** `SemanticAssignment` and `DataValueAssignment` carry a status
  (`DISCOVERED`, `PROPOSED`, `VALIDATED`, ...), a confidence of 0 to 100
  and a steward. In our ecosystem, metacrafter produces this when it scans
  data. It does not belong in the registry.
- **Each side has things the other lacks.**
  - Only the registry has country scope, a PII flag, checksums, negative
    examples and typed crosswalk mappings.
  - Only Egeria has storage data type, units, value ranges, composition of
    one class from others, data grain and detection thresholds.

## 1. Egeria in brief

[Egeria](https://egeria-project.org) is an open source (Apache-2.0)
framework for open metadata and governance under LF AI & Data. It defines a
type system for metadata, APIs to manage it, and connectors that exchange
metadata between catalogs and tools. The type system is split into areas
0 to 7. Area 3 is "Glossary and Semantics". Area 5 is "Models and Schemas".

The model has changed since the issue was filed in February 2022:

- Glossary categories were removed in 2025: the primary category
  (model 0335) in April and the category hierarchy (model 0320) in August.
  Glossaries are now organized with generic folders (collections,
  model 0021).
- Spine objects (model 0380) were removed in July 2025.
- The `Translation` and `ValidValue` term-to-term relationships are gone
  from model 0350. Translations now use the generic `TranslationDetail`
  entity (model 0022).
- In 2026 `DataClass` got a new supertype, `DataValueSpecification`
  (model 0540). Its relationships were renamed: `DataClassHierarchy` became
  `DataValueHierarchy`, and `DataClassAssignment` became
  `DataValueAssignment`. A second subtype, `DataGrain`, describes the
  granularity of data.

The core idea is stable. In 2022 the data class already described the
expected values of a logical type for discovery engines, with hierarchy and
assignment relationships. The 2025 documentation lists `dataPatterns`,
`sampleValues` and `matchThreshold`.

## 2. The Area 3 glossary

| Model | Content |
|---|---|
| 0310 Glossary | `Glossary` entity with `language` and `usage`. Classifications: `Taxonomy` (terms sit in one folder of a strict hierarchy) and `CanonicalVocabulary` (term names are unique, and the glossary describes the meaning of data fields). |
| 0330 Terms | `GlossaryTerm`: `displayName`, `description`, `qualifiedName` (inherited), `contentStatus`, `aliases`, `summary`, `examples`, `abbreviation`, `usage`. |
| 0340 Dictionary | Term classifications: `ActivityDescription`, `AbstractConcept`, `DataValueMeaning` (the term names a valid value), `Question`. |
| 0350 Related Terms | Term-to-term relationships: `RelatedTerm` ("see also"), `Synonym`, `Antonym`, `PreferredTerm`, `ReplacementTerm`, `ISARelationship`. Each has a `confidence`, a `steward`, a `source` and a `termRelationshipStatus` (`DRAFT`, `ACTIVE`, `DEPRECATED`, `OBSOLETE`, `OTHER`). |
| 0360 Contexts | `ContextDefinition` classification and `UsedInContext` relationship: a term is valid only in a context. |
| 0370 Semantic Assignment | `SemanticAssignment` links a term to any element, typically a column, to state what its data means. It has `termAssignmentStatus` (`DISCOVERED`, `PROPOSED`, `IMPORTED`, `VALIDATED`, `DEPRECATED`, `OBSOLETE`, `OTHER`), `confidence` and `steward`. `SemanticDefinition` links a term to a data field in a data dictionary. |
| 0385 Controlled Glossary Development | Editing, scoping and staging collections. Changes are made to copies of the live terms, reviewed, and then merged back. |
| 0390 Glossary Projects | A project that maintains a glossary. |
| 0395 Supplementary Properties | A term that adds descriptions to read-only technical metadata. |

Authored elements share the `ContentStatus` lifecycle: `DRAFT`, `PREPARED`,
`PROPOSED`, `APPROVED`, `REJECTED`, `ACTIVE`, `DEPRECATED`, `OBSOLETE`,
`OTHER`.

The glossary is about business vocabulary. A term like "client" may need two
records, one per meaning, separated by context. Glossary terms have no
regular expressions and no way to test values. Their `examples` attribute
holds examples of the word in use, not sample data values.

## 3. Area 5 data classes

`DataValueSpecification` (model 0540) has these attributes:

- `specification` and `specificationDetails`: a rule, stated or named;
- `matchPropertyNames`;
- `matchThreshold`: the percentage of values that must match;
- `dataType`: storage type, such as string or int;
- `units`, `absoluteUncertainty`, `relativeUncertainty`;
- `namespacePath`.

`DataClass` (model 0541) adds:

- `dataPatterns`: a list of regular expressions;
- `sampleValues`;
- `valueList`, `valueRangeFrom`, `valueRangeTo`, `averageValue`;
- `allowsDuplicateValues`, `isNullable`, `defaultValue`, `isCaseSensitive`.

Relationships:

| Relationship | Meaning | Registry counterpart |
|---|---|---|
| `DataValueHierarchy` | General to specific, for example date, then date of birth. Discovery goes down to the most specific class. Code generators go up to a class the target language supports. | `parent` (27 records) and `semantic_type` (58 patterns) |
| `DataClassComposition` | A class built from other classes, for example an address from its parts | none |
| `DataValueDefinition` | Attaches a class to a `DataField` or `DataStructure` in a data specification | none (out of scope) |
| `DataValueAssignment` | Confirms that a field holds values of the class. It has `method`, `assignmentStatus`, `threshold`, `confidence` and `steward`. | none: this is metacrafter's scan output |
| `ValidValuesAssignment` (model 0545) | Links a class or field to a set of valid values (reference data) | none: categorical types do not reference their code lists |

Discovery results are stored as `DataClassAnnotation` (model 0625) with
`candidateDataClassGUIDs`. Stewards then confirm them through
`DataValueAssignment`. Data classes can also link to glossary terms, which
shows how data of a given meaning is implemented.

## 4. Field-by-field crosswalk

How each registry field would be represented in Egeria.

| Registry field | Egeria `DataClass` | Egeria `GlossaryTerm` | Fit |
|---|---|---|---|
| `id` | `qualifiedName` | `qualifiedName` | Good. The `qualifiedName` must be unique in the repository, so it needs a namespace (see R3). |
| `name` | `displayName` | `displayName` | Good |
| `doc` | `description` | `description`, `summary` | Good |
| `status` | `contentStatus` | `contentStatus` | Good: `draft` = `DRAFT`, `stable` = `ACTIVE`, `deprecated` = `DEPRECATED` |
| `parent` | `DataValueHierarchy` | `ISARelationship` | Good |
| `semantic_type` (pattern) | a child class through `DataValueHierarchy`, or one more item in the datatype's `dataPatterns` | `Synonym` or `ISARelationship` | Partial. Egeria has no "representation of" link. |
| `aliases` | none | `aliases` | Mismatch. Registry aliases are former ids. Egeria aliases are natural-language synonyms. |
| `replaced_by` | none | `ReplacementTerm` | Partial |
| `categories` | folder membership (collections) | folder membership | Partial. Egeria has no category list on the element. |
| `country` | none (`namespacePath` at best) | `ContextDefinition` term and `UsedInContext` | Gap |
| `langs` | none | none (`Glossary.language` is the language of the glossary text) | Gap |
| `is_pii` | none | none | Gap. Egeria expresses sensitivity with the governance classification `Confidentiality` (model 0422) on assets and terms, as a level, not a boolean. |
| `classification` | `allowsDuplicateValues: false` for identifiers; `valueList` or `ValidValuesAssignment` for categorical types | `ObjectIdentifier` classification on a `DataField` (model 0580) | Partial |
| `regexp` | `dataPatterns` | none | Good |
| `checksum` | `specification` (a rule name) | none | Partial |
| `examples` (valid) | `sampleValues` | none (`examples` means usage examples) | Good for data classes |
| `examples` with `valid: false` | none | none | Gap |
| `mappings` | `ExternalReference` and `ExternalReferenceLink` (model 0014), or `additionalProperties` | same | Partial. Egeria has no typed crosswalk. |
| `links` | `ExternalReference` and `ExternalReferenceLink`, or `MoreInformation` | same | Good |
| `translations` | `TranslationDetail` with `TranslationLink` (model 0022): `languageCode`, `displayName`, `description` | same | Good |
| none | `dataType`, `units`, `valueRangeFrom`, `valueRangeTo`, `isNullable`, `isCaseSensitive`, `matchThreshold`, `DataClassComposition`, `DataGrain` | `abbreviation`, `usage`, `Antonym`, contexts | Egeria only |

## 5. Key differences

1. **Purpose.**
   - Egeria manages one organization's metadata: its assets, its glossary
     and how they are governed.
   - The registry is a public reference list of value types that are the
     same everywhere. An INN is an INN in every company.
2. **Meaning versus form.**
   - Egeria keeps business meaning (glossary term) apart from value form
     (data class). One term, such as "customer tax id", can be implemented
     by several data classes. One data class can serve many terms.
   - The registry ties one meaning to one or more forms (patterns). It has
     no layer for business meaning.
3. **Identity.**
   - In Egeria, each element has a GUID and a `qualifiedName` that is
     unique within its metadata repository and cohort.
   - Registry ids are global, never removed, and resolve at public URLs that
     metacrafter and stored catalog metadata depend on.
4. **Lifecycle.**
   - Egeria has a controlled development process: editing collections,
     review and merge.
   - The registry does the same with git: a pull request, CI gates and the
     `draft`/`stable`/`deprecated` statuses. Egeria's lifecycle has more
     states, but the registry's three map onto it without loss.
5. **Provenance of assignments.**
   - Egeria records who or what assigned a term or class to a field, with
     what confidence, and whether a steward validated it.
   - The registry defines types only. Assignment is metacrafter's job.
6. **Jurisdiction and privacy.**
   - The registry makes country, language and PII first-class fields,
     because detection depends on them.
   - Egeria leaves jurisdiction to namespaces or contexts. It handles
     privacy with governance classifications that carry levels and are
     owned by the organization.
7. **Testability.**
   - Registry records can be tested: CI checks that positive examples match
     the regexp and that negative examples do not, and it can verify
     checksums.
   - Egeria data classes carry patterns and sample values. The type model
     has no negative samples and no check-digit algorithm.
8. **Structure of values.**
   - Egeria can describe composite values (`DataClassComposition`), storage
     types, units, ranges and grain.
   - The registry describes a value as a single string pattern.

## 6. Recommendations

- **R1. Keep the registry model. Do not adopt the glossary model.**
  Business glossaries belong to organizations. A public registry of value
  types should stay at the value level.
- **R2. Use "data class" as the Egeria term when we describe the
  registry.**
  - Say that a registry datatype corresponds to an Egeria `DataClass`, a
    schema.org `DefinedTerm` and a SKOS `Concept`.
  - Say that a glossary term in a customer's catalog is what a datatype
    gets linked to, not what it is.
- **R3. Follow-up: an Egeria export.** It needs an OpenSpec change, because
  it adds a build output.
  - Generate an Open Metadata Archive, or a loader built on `pyegeria` and
    the Data Designer API. Either one creates:
    - one `DataClass` per datatype;
    - `DataValueHierarchy` from `parent` and `semantic_type`;
    - `TranslationDetail` from `translations`;
    - `ExternalReference` from `links`.
  - This fills the content gap in section 1. Egeria users would get several
    hundred tested data classes, and each would link back to its registry
    URL.
  - Decisions the change has to make:
    - the `qualifiedName` scheme, for example one built from the registry
      URL;
    - whether a pattern becomes a child class or an item in `dataPatterns`;
    - how country, PII and negative examples travel: `additionalProperties`,
      governance classifications, or not at all.
- **R4. Fields worth considering later.** Add each one only when a consumer
  needs it, and through OpenSpec, because the data model is a contract.
  - `data_type`: the usual storage type, for example `string` for INN even
    though it is all digits. Code generators and schema checks need it.
  - `components`: the parts of composite identifiers, for example IBAN =
    country code + check digits + BBAN. This mirrors
    `DataClassComposition`.
  - A link from categorical types to their code lists (ISO 3166, ISO 4217,
    and so on). This mirrors `ValidValuesAssignment`.
  - `units`: only if the registry adds measurement types.
- **R5. Do not add these.**
  - `matchThreshold`: the threshold depends on the detection method, so it
    belongs in metacrafter-rules.
  - Assignment status, confidence or steward fields: these belong to
    metacrafter output and to catalogs.
  - An `egeria` key in `mappings`: Egeria publishes no standard data class
    ids to map to. Revisit this if a standard Egeria content pack ships data
    classes.
  - An Egeria tool record: tool records list `supported_types`, and Egeria
    detects no registry types out of the box.

## 7. Related issues

- #7 (closed) added subtyping through `parent`. Egeria's
  `DataValueHierarchy` confirms this design. Egeria uses the hierarchy in
  both directions: discovery goes down to the most specific class, and code
  generation goes up to a supported one.
- #15 (reading list): add the Egeria area 3 and area 5 documentation.
- #49 (RDF/OWL): the planned SKOS export (task 7.3 of
  `modernize-registry-platform`) is the natural bridge to glossary tools.
  `ISARelationship` corresponds to `skos:broader`, and `RelatedTerm` to
  `skos:related`.

## Sources

- Egeria Area 3, glossary and semantics:
  <https://egeria-project.org/types/3/>
- Model 0330, glossary terms: <https://egeria-project.org/types/3/0330-Terms/>
- Model 0350, related terms:
  <https://egeria-project.org/types/3/0350-Related-Terms/>
- Model 0370, semantic assignment:
  <https://egeria-project.org/types/3/0370-Semantic-Assignment/>
- Model 0540, data value specifications:
  <https://egeria-project.org/types/5/0540-Data-Value-Specifications/>
- Model 0541, data classes and data grains:
  <https://egeria-project.org/types/5/0541-Data-Classes-and-Data-Grains/>
- Model 0545, reference data:
  <https://egeria-project.org/types/5/0545-Reference-Data/>
- Data class concept: <https://egeria-project.org/concepts/data-class/>
- Egeria content packs:
  <https://github.com/odpi/egeria/tree/main/content-packs>
- History of the type documentation: the commit log of
  <https://github.com/odpi/egeria-docs>, for paths under `site/docs/types/3`
  and `site/docs/types/5`.
