## Why

Issue #9 asked how the registry relates to the Egeria glossary. The research
in `devdocs/RESEARCH_EGERIA_2026-11.md` (pull request #61) found that a
registry datatype corresponds to an Egeria `DataClass` (type model 0541), not
to a `GlossaryTerm`. It also found that no Egeria content pack ships
`DataClass` instances, so every Egeria user must write data classes by hand.

The registry already has about 600 tested value types with regexps, sample
values, translations and links. If we publish them in a form that Egeria
loads, Egeria users get a ready catalog of data classes, and each data class
links back to its registry URL. This is recommendation R3 of the research.

## What Changes

- **New build output: an Egeria Open Metadata Archive.**
  - `metacrafter-registry build` writes `dist/registry.omarchive.json`. It is
    served at `/registry.omarchive.json`, next to the SKOS export
    `/registry.ttl`.
  - The file is an Open Metadata Archive of type `CONTENT_PACK`, in the JSON
    form of the archives that Egeria ships. It declares no new types. It
    depends only on the Egeria Open Metadata Types archive.
  - The target is Egeria V6.0 and later. Earlier releases do not have the
    `DataValueSpecification` and `DataValueHierarchy` types.
- **One `DataClass` per datatype and per pattern.**
  - A pattern is a child `DataClass` of its datatype through
    `DataValueHierarchy`. `parent` also becomes `DataValueHierarchy`.
  - `status` becomes `contentStatus`. The regexp becomes `dataPatterns`, and
    the positive examples become `sampleValues`.
  - `translations` become `TranslationDetail` entities with `TranslationLink`.
  - `links` become shared `ExternalReference` entities with
    `ExternalReferenceLink`.
  - `country`, `langs`, `categories`, `is_pii`, `classification`, `checksum`,
    `aliases`, `replaced_by` and `mappings` go to `additionalProperties`.
  - Negative examples are not exported.
  - Each former id (alias) becomes a deprecated `DataClass` that names its
    replacement.
- **Stable identity.** Each `qualifiedName` is built from the canonical
  registry URL, for example
  `DataClass::https://registry.apicrafter.io/datatype/inn`. GUIDs are
  derived from the `qualifiedName`, so loading a newer archive updates the
  same Egeria elements instead of creating copies.
- **Checks.**
  - Unit tests check every type and attribute name against a pinned extract
    of the Egeria V6.2 type definitions.
  - A manual workflow loads the archive into an Egeria V6.2 platform.
- **Distribution.**
  - The manifest `/api/v1/index.json` lists the archive with its size and
    SHA-256.
  - `llms.txt`, the README and the about page link to it, with loading
    instructions.
  - Each GitHub Release attaches it as an asset.
  - The public URL contract check also covers the new URL.
- **Not in this change:** a loader built on `pyegeria` or the Data Designer
  API. Users load the archive with Egeria's own archive loading, which
  `pyegeria` already wraps. See design.md D1.

Nothing here is BREAKING. The change adds one file and one manifest entry. No
existing URL, JSON shape or YAML field changes.

## Capabilities

### New Capabilities
- `egeria-export`: the Open Metadata Archive that the build publishes for
  Egeria. It covers the file and where it is published, the mapping of
  registry records to Egeria elements, `qualifiedName` and GUID identity,
  determinism, checks against the Egeria type definitions, and distribution.

### Modified Capabilities
- None. `openspec/specs/` does not exist yet. The capabilities of
  `modernize-registry-platform` are not archived, so this change cannot
  write deltas against them. It states its distribution requirements
  (manifest, release asset, URL contract check) in `egeria-export`.

## Impact

- **Code:**
  - A new module `src/metacrafter_registry/egeria.py` with the archive
    emitter.
  - A pinned extract of the Egeria type definitions, used by the emitter and
    the tests.
  - Hooks in `build.py` (output file and manifest), `agents.py` (`llms.txt`
    link) and `contract.py` (the new URL), and the about page template.
- **CI and release:**
  - `release.yml` copies the archive into the release assets.
  - A new manual workflow, `egeria.yml`, runs the load test.
- **Size:** about 620 records, 140 translations and 470 links. A mock with
  the real counts gives about 8.5 MB of compact JSON, and about 0.2 MB
  compressed. It is served as `application/json`, which GitHub Pages
  compresses.
- **Dependencies:** none for the build. The manual load test uses the
  `odpi/egeria-platform:6.2` container image.
- **Downstream:** none. metacrafter, metacrafter-rules and metacrafter-llm do
  not read this file.
- **Docs:** README API table, about page, `llms.txt`, and a short loading
  guide.
