## Purpose

This capability keeps the registry aligned with metacrafter and
metacrafter-rules. It covers rule coverage, orphan reporting, generated tool
records, and a Python package for offline lookups and URL building.

## ADDED Requirements

### Requirement: Rule coverage from metacrafter-rules
The build SHALL read the metacrafter-rules repository at a pinned reference recorded in the registry repository.

For every datatype, the build SHALL publish the rules whose `key` equals the datatype ID or one of its aliases. Each rule entry SHALL include the rule key, the rule type (field or data), the match type and the source file.

#### Scenario: Coverage on record
- **WHEN** metacrafter-rules contains a data rule with `key: email`
- **THEN** the published `email` record lists that rule under `detected_by.metacrafter_rules`

### Requirement: Orphan reporting
The build SHALL report two lists:

- rule keys that resolve to no registry ID or alias;
- registry IDs that have no rule.

On pull requests, orphans SHALL be warnings. A scheduled job SHALL run against the latest metacrafter-rules and SHALL open or update a tracking issue when the orphan sets change.

#### Scenario: Orphan rule key
- **WHEN** metacrafter-rules uses `key: email_person` and the registry has no such ID or alias
- **THEN** the coverage report lists `email_person` with the rule files that use it

### Requirement: Generated detector tool records
The `supported_types` list of the `metacrafter` tool record SHALL be generated from rule coverage. It SHALL NOT be maintained by hand.

#### Scenario: New rule
- **WHEN** the pinned metacrafter-rules reference is bumped to a version with a rule for a new key
- **THEN** the next build lists that key in the `metacrafter` tool's supported types

### Requirement: Stable datatype URL builder
The registry SHALL document the canonical datatype URL template, `https://registry.apicrafter.io/datatype/{id}`, and SHALL publish it in the manifest. Consumers can then build links without hardcoding the template.

#### Scenario: Manifest template
- **WHEN** a consumer reads `/api/v1/index.json`
- **THEN** it finds `datatype_url_template` with the value `https://registry.apicrafter.io/datatype/{id}`

### Requirement: Python package for offline use
The registry SHALL be published to PyPI as `metacrafter-registry`, with a data snapshot for each release. The package SHALL provide:

- loading of the bundled snapshot;
- optional fetching of the latest published data, with caching;
- alias-aware lookup;
- search;
- datatype URL building;
- value matching using regexps and checksums.

#### Scenario: Offline enrichment in metacrafter
- **WHEN** metacrafter has the package installed and detects key `email`
- **THEN** it can obtain the name, categories, `is_pii` and URL of `email` without any network access

#### Scenario: Version pinning
- **WHEN** a consumer pins `metacrafter-registry==2.1.0`
- **THEN** the bundled snapshot equals the data in GitHub Release `v2.1.0`
