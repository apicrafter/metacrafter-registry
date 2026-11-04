## 1. Spike: confirm Egeria behaviour

Nothing in this group changes the build or `main`.

- [ ] 1.1 Hand-write a minimal archive in the layout of design.md D3 to D7. It has:
  - three data classes: `email`, `passport` and one passport pattern;
  - one `ru` translation and one link;
  - the `MetadataCollection` entity.

  Copy the instance headers and the `Anchors` classifications from Egeria's `SimpleCatalog.omarchive`.
- [ ] 1.2 Start `odpi/egeria-platform:6.2` with a metadata store server. Write down the minimal setup.
- [ ] 1.3 Load the archive with `pyegeria`'s `add_archive_content`. Then read the `email` data class with the Data Designer API, by `qualifiedName`. Check:
  - its data patterns, sample values and `contentStatus`;
  - the `DataValueHierarchy` to the pattern;
  - the translation and the external reference.
- [ ] 1.4 Load a second copy of the archive in which the `email` description changed and every `version` is higher. Confirm that the element was updated, not duplicated. Also try a copy with the same `version`, and write down what happens.
- [ ] 1.5 Answer the open question in design.md: which `Anchors` values, if any, `DataClass` and `TranslationDetail` need. Also write down whether loaded elements can be edited in Egeria.
- [ ] 1.6 Update design.md D3, D5 and Risks with the results. If reload does not update elements, rewrite the "Reload of a later build" scenario and the loading docs before group 2 starts.

## 2. Emitter and tests (not yet in `dist/`)

- [ ] 2.1 Add `scripts/extract_egeria_types.py`. It writes `src/metacrafter_registry/egeria_types.json` from an `OpenMetadataTypes.omarchive`. Generate the file from the V6.2 archive, with its source and release recorded in it (design.md D9).
- [ ] 2.2 Add `src/metacrafter_registry/egeria.py` with the archive envelope (D3), identity and GUIDs (D4, D5), and the property-value builders. It takes type GUIDs and enum ordinals only from the extract.
- [ ] 2.3 Map records to `DataClass` entities: the attributes, `contentStatus`, `dataPatterns`, `sampleValues` and `additionalProperties` (D7). The build fails if a list item contains a comma.
- [ ] 2.4 Add `DataValueHierarchy` for `semantic_type` (label `pattern`) and `parent` (label `subtype`). Print a warning when a pattern has both fields (D6).
- [ ] 2.5 Add `TranslationDetail` and `TranslationLink` for every translation, including `en`, and shared `ExternalReference` entities with `ExternalReferenceLink` (D7).
- [ ] 2.6 Add the deprecated data classes for aliases (D8).
- [ ] 2.7 Add `tests/test_egeria.py`. It covers:
  - the envelope and the fixed `archiveGUID`;
  - type and attribute conformance against the extract;
  - unique GUIDs;
  - every relationship end resolves;
  - the counts;
  - the mapping on fixture records, including drafts, patterns, negative examples, translations, shared links and aliases;
  - identical bytes across two builds;
  - identities that do not change with `--base-url`.

## 3. Publish the archive

- [ ] 3.1 Make `build` write `dist/registry.omarchive.json`, and add the file to the manifest's `files`.
- [ ] 3.2 Add `/registry.omarchive.json` to the URL contract check, with the media type `application/json`.
- [ ] 3.3 Link the archive from `llms.txt`, the README API table and the about page. Add a short loading guide (Egeria archive loading and `pyegeria`). It lists the `additionalProperties` keys, names the regexp dialect, and states the supported Egeria versions.
- [ ] 3.4 Run `metacrafter-registry validate`, `build`, `check-links` and `check-contract` against `serve`, and `pytest -q`. Commit the regenerated `data/*_latest.json(l)` if they changed.

## 4. Release and load test

- [ ] 4.1 Copy `registry.omarchive.json` into the release assets in `release.yml`, so that it is included in `SHA256SUMS`.
- [ ] 4.2 Add the manual workflow `.github/workflows/egeria.yml` (`workflow_dispatch`). It builds the registry and loads the archive into `odpi/egeria-platform:6.2`, using the setup from 1.2. It then runs the checks of 1.3 and 1.4: it loads the archive of a second build with a changed description and a higher `version`.
- [ ] 4.3 Run the workflow once on `main` and link the run from the pull request. Mention the archive in the next release notes.
