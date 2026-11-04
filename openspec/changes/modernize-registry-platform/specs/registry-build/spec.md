## Purpose

This capability defines a single reproducible build that validates the YAML
sources and produces every published artifact. It also covers honest quality
statistics, data versioning, releases and the changelog.

## ADDED Requirements

### Requirement: Single build command
One command SHALL validate the sources and write the complete publishable tree to an output directory: site, API, agent files, linked-data exports and legacy files.

The build SHALL write nothing to the output directory if validation fails.

#### Scenario: Invalid source blocks build
- **WHEN** any record fails schema or semantic validation
- **THEN** the build exits non-zero, lists every error with file path and field, and leaves the previous output untouched

#### Scenario: Successful build
- **WHEN** all records are valid
- **THEN** the output directory contains the site, `/api/v1/`, legacy JSON files, `llms.txt` and the SKOS export

### Requirement: Reproducible output
Given the same commit, two builds SHALL produce byte-identical output. Generated timestamps SHALL be derived from the commit time.

#### Scenario: Rebuild
- **WHEN** the build runs twice on the same commit
- **THEN** the two output trees have identical checksums

### Requirement: Semantic validation gates
Beyond schema validation, the build SHALL fail on any of these:

- duplicate IDs or aliases
- an unresolved `parent`, `semantic_type`, `replaced_by`, tool `supported_types`, or reference-list ID
- a regexp that does not compile
- an example that violates its regexp
- a mismatch between directory and country
- a file name that differs from its ID

The build SHALL emit warnings, without failing, for:

- regexps that are not anchored
- regexps that cannot be translated to ECMAScript
- placeholder-like examples
- orphan rule keys

#### Scenario: Invalid regexp
- **WHEN** record `unlocode` has a regexp with an unbalanced parenthesis
- **THEN** the build fails and names `unlocode` and the compile error

#### Scenario: Unanchored regexp
- **WHEN** a regexp lacks `^` and `$` anchors
- **THEN** the build succeeds and emits a warning for that record

### Requirement: Honest completeness statistics
Statistics and reports SHALL count a field as present only when it holds a non-empty value.

#### Scenario: Empty regexp
- **WHEN** a record has no regexp, or an empty one
- **THEN** the record is not counted in "with regexp"

### Requirement: Quality score per record
The build SHALL compute a quality score from 0 to 100 for every datatype and pattern, using a documented rubric. The build SHALL publish the score together with the list of missing quality elements.

#### Scenario: Stub record
- **WHEN** a record has a doc equal to its name, no regexp, no examples and no links
- **THEN** its quality score is below 40 and the missing elements are listed

### Requirement: Transitional legacy data files
Until a major release removes them, the repository SHALL keep `data/datatypes_latest.json`, `data/datatypes_latest.jsonl`, `data/tools_latest.json` and `data/tools_latest.jsonl`. They SHALL be in the legacy shape and match the sources.

CI SHALL fail if these files are stale.

#### Scenario: Stale committed file
- **WHEN** a pull request changes a YAML record but not `data/datatypes_latest.jsonl`
- **THEN** CI fails with instructions to run the build

### Requirement: Continuous validation and deployment
Every pull request SHALL run lint, tests, validation and a full build.

Every merge to the default branch SHALL deploy the build output to GitHub Pages without committing generated files to any branch.

#### Scenario: Merge to main
- **WHEN** a pull request is merged into `main`
- **THEN** the site is rebuilt and deployed to GitHub Pages, and the deployed `index.json` reports the merge commit SHA

### Requirement: Versioned releases with changelog
The data SHALL be versioned with SemVer:

- **MAJOR:** an ID is removed without an alias, or a published shape changes incompatibly.
- **MINOR:** records or fields are added.
- **PATCH:** values are corrected.

Each release SHALL create a git tag and a GitHub Release. The release SHALL attach the bulk files and carry a changelog that lists added, deprecated, merged and changed IDs, computed against the previous release.

#### Scenario: Release
- **WHEN** a maintainer pushes tag `v2.1.0`
- **THEN** a GitHub Release `v2.1.0` is published with bulk JSON, JSONL and CSV assets and a changelog grouped by change type

### Requirement: Migration tool
A migration command SHALL convert records from the v1 YAML conventions to the v2 contract. It SHALL:

- convert string booleans;
- convert dict-shaped `parent`;
- move `wikidata_property` into `mappings`;
- drop empty fields;
- normalise translations;
- convert language `se` to `sv`;
- rename files to match their IDs;
- set `status: draft` on stub records.

The command SHALL be idempotent.

#### Scenario: Idempotent migration
- **WHEN** the migration runs on already-migrated sources
- **THEN** no file changes
