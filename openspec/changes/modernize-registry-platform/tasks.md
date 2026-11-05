## 1. Phase 0: Foundation and Pages spike

- [x] 1.1 Add `pyproject.toml`:
  - src-layout package `metacrafter_registry`
  - Python 3.10+
  - ruff and pytest configuration
  - `metacrafter-registry` console script
- [x] 1.2 Port loading, reference lists and the legacy JSON emitter from `scripts/builder.py` into the package. Add snapshot tests: the legacy `datatypes_latest.json` must equal the current committed file.
  - Done as a freshness test. The diff against release 1.02 was reviewed by hand: every difference is either a data fix or one of two old-builder bugs that are now fixed. The bugs: patterns embedded unresolved in the JSONL, and pattern `is_pii` depending on file order (9 patterns, including the passport patterns, were wrongly `false`).
- [x] 1.3 Add the `build` command. It writes `dist/` with the legacy files, `datatype/<id>.html`, `tool/<id>.html`, `tool/index.html` and `index.html`. It reuses the existing templates, minimally.
  - It also writes a minimal `api/v1/index.json` manifest (version, git SHA, counts, file hashes, `datatype_url_template`), which the deploy check uses.
- [x] 1.4 Add the `pages.yml` workflow, which deploys `dist/` with `upload-pages-artifact` and `deploy-pages`.
  - [x] Enable Pages (source: GitHub Actions) in the repository settings. Done on 2026-11-04.
- [x] 1.5 Write the URL contract test, a script run against a deployed base URL. The following must return 200 with the expected content type:
  - `/datatype/email`
  - `/datatype/email.json`
  - `/registry.json`
  - `/tools.json`
  - `/tool/presidio`
  - `/tool`

  Run it on `apicrafter.github.io/metacrafter-registry/`. If extensionless URLs fail, switch to the fallback in design.md (D3 risk).
  - Implemented as `metacrafter-registry check-contract <base-url>`. CI runs it on every PR against a local server that applies the GitHub Pages URL rules (`metacrafter-registry serve`). `pages.yml` runs it against the live site after each deploy, with `--expect-sha`.
  - [x] Confirm the result on the real GitHub Pages after the first deploy. On 2026-11-04, 14/14 checks passed on `apicrafter.github.io/metacrafter-registry`, and `/datatype/email` was served without a redirect.
- [x] 1.6 Add the `ci.yml` workflow. On every PR it runs lint, tests, `validate` and `build`, and checks that the committed `data/*_latest.*` files are fresh.
- [x] 1.7 Remove `.idea/`, `.DS_Store` and `metacrafter.code-workspace`, and extend `.gitignore` with `dist/`.

## 2. Phase 0: Data defects (audit §3)

- [x] 2.1 Fix the `unlocode` regexp so that it compiles, and add examples.
- [x] 2.2 Fix the `country` field in `us_bankaccount.yaml` (→ `US`). Move or fix `jobtitle` (remove `RU`).
- [x] 2.3 Fix the `ipv6subnet` name. Fix the `isbn13` links and examples.
- [x] 2.4 Fix the 26 examples or regexps that disagree, in 15 records (audit §2). The two empty examples on `inn` were also fixed:
  - `ensoc`
  - `chahv`, `chiban`, `chbankaccount`, `chuid`
  - `rusecreg`
  - `ianatimezoneid`
  - `isni`
  - `asn`
  - `isbn13`
  - `cficode`
  - `uprn`
  - `icd10code`
  - `idnpwp`
  - `ccamcode`
- [x] 2.5 In `langs.yaml`, replace `se` (Swedish) with `sv` and update the records that reference it.
- [x] 2.6 Replace the generic "Armenia" Wikipedia links on `am_ssn`, `am_tin` and `am_org_tin` with authoritative sources, or remove them.
  - Removed. Adding authoritative sources is part of the curation work in group 6.
- [x] 2.7 ~~Move `icd10code` out of `DE/`~~. Decision: keep it in `DE/`.
  - The record is the German ICD-10-GM variant, generated from the DE rules. The international code is already covered by `any/medical/icd10.yaml`.
  - Only its double-escaped regexp was fixed. Whether to make it a pattern of `icd10` is part of the 6.8 duplicate review.

## 3. Phase 0: Restore the production domain

- [ ] 3.1 **Owner action.** Point `registry.apicrafter.io` at `apicrafter.github.io`:
  1. Create a Cloudflare CNAME record, DNS-only.
  2. Set the custom domain in the Pages settings.
  3. Enforce HTTPS.
- [x] 3.2 Make the build use the production base URL.
  - The default base URL is `https://registry.apicrafter.io`.
  - `pages.yml` takes the base URL from `actions/configure-pages`, so the site follows the custom domain once it is set.
  - No `CNAME` file is needed: Actions-based Pages deployments ignore it, and the domain is set in the Pages settings.
- [ ] 3.3 Run the URL contract test against production. Record the result in the PR.

## 4. Phase 1: Site

- [x] 4.1 Create the template set: base layout with light and dark themes, home, datatype list, entity page, category, country, tool list, tool, about and 404.
  - The templates live in `src/metacrafter_registry/templates/` (package data), with CSS and JS in `static/`. There are no third-party assets.
  - A search page was added as well.
- [x] 4.2 Build the entity page with every field required by the `registry-site` spec. It includes "Edit on GitHub", JSON and Markdown alternate links, and the canonical link.
  - The page shows every field the data has today, plus the tools that list the type.
  - Status, quality score, metacrafter rule coverage and provenance dates are added when the data model provides them (6.6, 6.7, 8.2).
  - The Markdown alternate is added with the Markdown twins (7.1).
- [x] 4.3 Add client-side filters on the datatype list: category, country, PII, status and coverage.
  - Done: text, category, country (including "global"), kind and PII. The filter state is kept in the URL.
  - Status and coverage filters follow when those fields exist (6.7, 8.2).
- [x] 4.4 Add search: build `search-index.json` ~~and use vendored MiniSearch~~. Index IDs, names, aliases, docs and translated names.
  - Implemented as about 60 lines of plain JS ranking over `search-index.json`. There is no vendored library, and nothing leaves the browser.
  - Aliases are indexed once they exist (6.8).
- [x] 4.5 Add `sitemap.xml`, `robots.txt`, OpenGraph tags and JSON-LD `DefinedTerm` blocks.
- [x] 4.6 Add an accessibility pass (check that pages work without JavaScript, check contrast), plus an internal link checker in CI.
  - Pages include a skip link, labelled inputs and `aria-current` navigation.
  - The filter form is hidden until JS loads, so the full table always renders.
  - Colour tokens are set for light and dark themes.
  - `metacrafter-registry check-links` runs in CI and in tests: 21k+ internal links, 0 broken.

## 5. Phase 1: API v1 and releases

- [x] 5.1 Write the normalised record emitter:
  - `/api/v1/datatypes/<id>.json`, `/api/v1/tools/<id>.json`
  - collection files in JSON and JSONL, and CSV
  - reference lists
- [x] 5.2 Write the `index.json` manifest: version, `git_sha`, commit-time `generated_at`, license, counts, file hashes and `datatype_url_template`.
  - `license` reports the repository license (`Apache-2.0`) until the owner chooses a data license (9.1).
- [x] 5.3 Write the OpenAPI 3.1 document for the static endpoints. Validate it in CI.
  - The tests validate the document and validate every published record against its component schema.
- [x] 5.4 Add a reproducibility test: build twice and compare tree hashes.
- [x] 5.5 Add the `release.yml` workflow. On a `v*` tag it attaches the bulk assets to a GitHub Release. Document the SemVer policy in `CONTRIBUTING.md`.

## 6. Phase 2: Data model v2 and migration

- [x] 6.1 Write the JSON Schemas (`schema/datatype|pattern|tool.schema.json`) per the `registry-data-model` spec. Publish them under `/schema/`.
  - Validation uses `jsonschema` (Draft 2020-12). Empty values are rejected through `minLength`, `minItems` and `minProperties`.
- [x] 6.2 Implement the semantic validator:
  - uniqueness, including aliases
  - references
  - regexp compilation
  - examples, positive and negative
  - directory and country agreement
  - file name and ID agreement
  - warnings: unanchored regexps, regexps with no ECMAScript form, placeholder-like examples
  - Also checked: `replaced_by` must resolve. Possessive quantifiers and atomic groups are errors on every Python version.
- [x] 6.3 Implement `migrate`. Prove it is idempotent with `--check`.
  - A test checks that the repository is fully migrated: `migrate --check` reports 0 changes.
- [x] 6.4 Migration PR, with no content changes:
  - Run `migrate`.
  - `git mv` the 180 files to `<id>.yaml`.
  - Attach a before and after stats report.
  - Done in commit "feat: migrate registry sources to the v2 record contract": 644 files rewritten, 181 renamed (180 datatypes and 1 tool). The normalized `/api/v1/` output was compared before and after: apart from the new fields and source paths, the only differences were trimmed whitespace, the order of inherited pattern categories, and deduplicated `supported_types`.
- [x] 6.5 Add `kind` to the reference lists (`EU` → region, `common` → special).
- [x] 6.6 Implement the quality-score rubric. Fix the `stats` and `report` commands to count only non-empty values.
  - `stats` and `report` are package commands, and `scripts/builder.py` delegates to them.
  - The detector-coverage element counts tool records until rule coverage exists (8.2).
- [x] 6.7 Apply `status: draft` per the stub criteria. Review the list by hand before merging.
  - 238 records are draft and 392 stable. The list is `metacrafter-registry report --status draft`. **Review it in the PR.**
- [x] 6.8 Merge the duplicates: `ssn` into `usssn`, and `ninumber` into `uknino`. Review the 13 duplicate-doc pairs, and merge or differentiate each. Add aliases and redirect pages.
  - `guid` → `uuid` and `eui48` → `mac_address` were merged as well.
  - 11 look-alike groups were differentiated with new descriptions; see the commit "data: merge duplicate records and differentiate look-alikes".
  - Retired ids stay in `registry.json` and the JSONL as alias entries (`alias_of`).
- [x] 6.9 Remove the hand-maintained `patterns:` lists, and redundant pattern `categories`.
- [x] 6.10 Update `generate_missing_entries.py`, or its successor, so that it emits `status: draft`. Move the other one-off scripts, `_original/` and `analysis/` to `archive/`.
  - The generator no longer invents regexps or links. It writes v2 drafts with only the facts taken from the rules.
- [x] 6.11 Remove the Cerberus schemas, `src/registry.py` and the Flask dependency. Update README and `AGENTS.md`.

## 7. Phase 3: Agent integration

- [x] 7.1 Add the Markdown twin emitter (`<page>.md`, with front matter).
  - Twins exist for datatypes, tools and categories.
- [x] 7.2 Add `llms.txt` and `llms-full.txt`.
- [x] 7.3 Add the SKOS Turtle export (`/registry.ttl`). Validate that it parses.
  - The export is written without a runtime dependency. Tests parse it with `rdflib`.
- [x] 7.4 Add the RAG corpus emitter. Put the template version in the manifest.
- [x] 7.5 Add the package runtime API:
  - `Registry.load`, `fetch`, `get` (alias-aware), `search`, `url_for`, `match`
  - checksum validators: `luhn`, `iban_mod97`, `isbn10`, `isbn13`, `gtin`, `ru_inn`, `ru_snils`, `ru_ogrn`
  - Added on top: `identify` (ranking by regexp hit rate × specificity, check digits and field-name similarity) and `crosswalk`.
  - `identify` also counts a value written with spaces or hyphens as a hit when it matches without them, unless the regexp of another record that is at least as specific matches the value as written. So an ISO date is not an eight-digit `okpo` or `oktmo` hit when a date regexp matches it. `match` keeps every compact-form match. The `/identify` page (`identify-core.js`) uses the same rule and gives the same scores.
  - In the `identify` score a compact-form hit counts half a hit as written, unless the record's check digit passes on the value. So a draft date pattern outranks stable eight-digit codes for ISO dates even when its regexp is broader than theirs, and spaced card numbers keep their `bankcard` hit. `regexp_hit_rate` stays the unweighted share of hits. `identify-core.js` applies the same weight.
  - `fetch` verifies SHA-256 against the manifest and caches the data.
  - `checksum` is now set on 12 records. Validation checks examples against the check digit.
  - `iban` and `email` gained regexps and examples.
- [x] 7.6 Add the MCP server (`metacrafter-registry mcp`): the tools and resources from the `agent-integration` spec, an offline snapshot and `--refresh`. Add tests with an MCP client.
  - Uses `mcp>=2,<3` (`MCPServer`).
  - Tests run in memory, plus an end-to-end test over stdio through the real CLI.
- [x] 7.7 Add PyPI trusted publishing to `release.yml`. The data snapshot is bundled from the build output.
  - [ ] **Owner action:** register the trusted publisher on pypi.org (repository `apicrafter/metacrafter-registry`, workflow `release.yml`, environment `pypi`).
- [x] 7.8 Write the skills `skills/registry-lookup/SKILL.md` and `skills/registry-contributor/SKILL.md`, and point to them from `AGENTS.md`.
- [x] 7.9 Add the site pages `/developers` and `/agents`: API, package, MCP configuration snippets, `llms.txt` and the safety note about drafts.
  - `/agents` has a Markdown twin, `/agents.md`.
  - The developer API reference stays on `/about`, so no separate `/developers` page was added.

## 8. Phase 4: Ecosystem alignment

- [x] 8.1 Add `ecosystem.lock`, pinning the metacrafter-rules ref. CI checks out metacrafter-rules at that ref.
  - The build reads a committed summary, `data/coverage/metacrafter-rules.json`, so local builds and CI agree without network access.
  - `coverage update` regenerates the summary. In CI, `coverage check` verifies it against the pinned checkout.
  - The ref is validated as a full SHA before use.
- [x] 8.2 Build `detected_by.metacrafter_rules`, `/api/v1/coverage.json` and the generated `metacrafter` tool `supported_types`.
  - At commit `1982330`: 1,267 rules and 544 keys. 498 records have rules, 123 do not, and 39 rule keys have no registry record.
  - The `metacrafter` tool now lists 498 types, up from 47 typed by hand.
  - The quality rubric counts rules as detector coverage.
- [x] 8.3 Report orphans on PRs. Add the `weekly.yml` drift job, which opens or updates a tracking issue, and an external link check.
  - Orphans appear as `::warning` annotations in CI.
  - `weekly.yml` checks drift against the latest rules and checks links with lychee. Each check keeps one tracking issue up to date.
- [x] 8.4 Add the `/identify` playground: a Web Worker, `regexp_js`, per-pattern time limits and JS checksum ports. Add a test that the page makes no network requests.
  - The JS scorer gives the same top results as `Registry.identify`. A test runs it in node when node is available.
  - Every pattern has a 250 ms watchdog: a slow pattern is skipped and reported.
  - A static test checks that the only network request is the index download. A browser check confirmed it.
- [x] 8.5 Add starter crosswalk mappings for the Presidio, Google DLP and Purview entities. Wire them into the `crosswalk` tool.
  - 148 mappings on 73 records.
  - Names are copied verbatim from the three official lists, retrieved on 2026-11-04. Only exact concept matches are mapped.
- [x] 8.6 Add the `/quality` and `/changes` pages. Add a changelog generator that diffs against the previous release's assets.
  - The `changes` command produces the diff.
  - `release.yml` writes the release notes from it.
  - `pages.yml` downloads every release's `changes.json` and builds `/changes` from them.
- [ ] 8.7 File the follow-up OpenSpec changes in the sibling repos:
  - metacrafter: honour `METACRAFTER_REGISTRY_URL` in `processor.py`, and optionally use the package.
  - metacrafter-llm: load the corpus by URL or package, and rebuild on a hash change.
  - metacrafter-rules: fix or alias the 39 orphan keys.
- [x] 8.8 Review the Microsoft Common Data Model (issue #14). Add the `cdm` crosswalk key, which holds CDM trait names.
  - 44 CDM traits are mapped to 43 records, exact concept matches only, at CDM commit `dd21d71`.
  - CDM entities (Account, Lead, ...) are business objects, not value types. They are not imported. The review is `devdocs/CDM_REVIEW.md`.
- [x] 8.9 Review the D3M Metadata semantic types (issue #45). The `d3m` crosswalk key now holds D3M semantic type URIs.
  - 13 of D3M's 90 types are mapped to 12 records, exact concept matches only, at d3m commit `244d552`.
  - New draft pattern `nanpphone` (North American phone number) for D3M's `AmericanPhoneNumber`.
  - Column roles, dataset structure and hyper-parameter types are not value types. They are not imported. The review is `devdocs/D3M_REVIEW.md`.
- [x] 8.10 Review the FTA (Fast Text Analysis) semantic types (issue #38). Add the `fta` crosswalk key and the `fta` tool.
  - 254 of FTA's 258 types are mapped to 180 records at FTA commit `51b3dd0`. `IDENTITY.VAT_<COUNTRY>` is mapped through its eight bound names.
  - 73 new draft records: 21 value types, 18 postal code patterns and 34 administrative divisions. New countries: TZ, UY.
  - `CHECKDIGIT.LUHN`, `FREE_TEXT` and the two North American union types are not mapped. The review is `devdocs/FTA_REVIEW.md`.
- [x] 8.11 Review the Sherlock semantic types (issue #37). `mappings.sherlock` now holds Sherlock type labels, checked against the list of 78 labels in the schema.
  - 32 of Sherlock's 78 types are mapped to 30 records, same-meaning matches only, at sherlock-project commit `f194013`.
  - 6 new draft records: `birthplace`, `brand`, `religion`, `weight`, `elevation` and `species`. `industry` and `language` came from the FTA review (8.10) and now carry the Sherlock mapping too.
  - New tool `sherlock` (detector). A test checks that its `supported_types` are the records that carry `mappings.sherlock`.
  - Generic header words (`code`, `type`, `rank`, ...) and roles over names (`director`, `owner`, ...) are not imported. The review is `devdocs/SHERLOCK_REVIEW.md`.
- [x] 8.12 Review the AutoType benchmark of Microsoft Research (issue #39). Add the `autotype` crosswalk key, which holds benchmark test case names.
  - 119 of the 142 test cases are mapped to 83 records, at AutoType commit `600df80`.
  - 18 new draft records for benchmark types the registry lacked, such as `bibcode`, `iswc`, `uniprot_id`, `ensembl_id`, `icd9`, `asin` and `ca_fsa`. `ca_postalcode` (a metacrafter-rules key) becomes an alias of `ca_postcode`.
  - Message formats (SWIFT MT, FIX, NOTAM, NMEA), free-text types and mislabelled test cases are not mapped. The review is `devdocs/AUTOTYPE_REVIEW.md`.
- [x] 8.13 Review the Sato semantic types (issue #33). Sato's published model predicts the same 78 types as Sherlock, in camelCase, at megagonlabs/sato commit `c19ace3`.
  - No new mapping key: Sato labels resolve through `mappings.sherlock`, and `crosswalk("sato", ...)` is the same lookup as `crosswalk("sherlock", ...)`.
  - New tool `sato` (detector). A test checks that its `supported_types` are the records that carry `mappings.sherlock`.
  - The 46 unmapped types were checked again against the records added since 8.11; none has a same-meaning record yet. The review is `devdocs/SATO_REVIEW.md`.
- [x] 8.14 Review the GS1 Application Identifiers (issue #20). Add the `gs1_ai` crosswalk key and the `gs1_mod10` and `gs1_checkpair` check-digit algorithms.
  - Source: the GS1 AI vocabulary version 1.2 (541 AIs, 2026-01-26), checked against the GS1 Barcode Syntax Dictionary.
  - The 26 identification-key AIs and 8 of the 9 GS1 Digital Link key qualifiers have one record per AI, holding the element string: 31 new `gs1_ai_<AI>` records, plus the mapping on `sssc`, `gtin` and `gtin02`. AIs 8007, 8040, 8041 and 716 map to `iban`, `imei` and `it_aic`.
  - 11 new draft records for bare GS1 keys (`gdti`, `gcn`, `ginc`, `gsin`, `grai`, `giai`, `gsrn`, `cpid`, `gmn`, `hidri`, `itip`); the element strings of these keys and of `gln` are their patterns.
  - Fixed: the `sssc` regexp (`d{18}`) and description, the unanchored `gln` regexp.
  - Dates, measures, amounts, addresses and other data attributes (503 AIs) are not imported. The review is `devdocs/GS1_AI_REVIEW.md`.
- [x] 8.15 Review the ORG-ID.guide register of organization identifier lists (issue #17). Add the `orgid` crosswalk key, which holds ORG-ID.guide list codes.
  - New draft records `org_id` (an identifier in the ORG-ID.guide form, `GB-COH-09506232`) and `org_id_scheme` (a list code, `GB-COH`).
  - 69 of the 569 list codes are mapped to 61 existing records. 182 lists get 175 new draft records; lists that use the same identifier share one record. New countries: 57. New languages: 22.
  - `crosswalk("orgid", ...)` accepts a list code in any case, its org-id.guide URL or a whole identifier. A test checks that each code maps to at most one record.
  - Not imported: 250 generated Chart of Accounts lists, 52 lists without an example identifier and 16 deprecated lists. The review is `devdocs/ORGID_REVIEW.md`.
- [x] 8.16 Add the date patterns of qddate as registry types (issue #12). Add the `qddate` crosswalk key, which holds qddate pattern keys, and the `qddate` tool.
  - All 151 base patterns of qddate 1.1.0 (commit `ec1f57a`) are mapped to 35 records. 33 are new draft patterns: 28 of `date` and 5 of `monthday`. YYYY-MM-DD maps to `date` itself, and DD.MM.YYYY maps to the existing pattern `date_dmy`.
  - There are 13 numeric notations (`date_dmy`, `date_mdy_slash`, `date_ymd_compact`, ...), one record per language for dates with a month name (15 languages), and Chinese/Japanese and Korean dates with units.
  - `crosswalk("qddate", ...)` resolves generated variants with a time or trailing text to their base pattern, so the `format` that metacrafter reports for a date column finds its notation.
  - Every regexp and example was checked against the qddate grammars: each example is read by qddate with a mapped key, and each month name form of qddate matches the language record. The review is `devdocs/QDDATE_REVIEW.md`.
- Data fixes found during this phase:
  - 9 regexps that matched the empty string were fixed, and the validator now rejects such regexps.
  - The `what3words` regexp had been copied from `geonamesid`.
- [x] 8.17 Add the external sources found in `devdocs/SOURCES_GAP_2026-11.md`. Add the `bioregistry`, `stdnum` and `fhir` crosswalk keys.
  - Crosswalks: `bioregistry` on 130 records, `stdnum` on 259, `fhir` on 78; the existing `dpv` and `schema_org` keys now cover 264 and 241 records.
  - 220 new draft records: 101 postal code patterns (Google address metadata), 40 Bioregistry identifiers, 25 secret token types (Gitleaks, TruffleHog), 15 security identifiers (CVE, CWE, CAPEC, CPE 2.3, ATT&CK, GHSA, OSV, JA3/JA4), 21 classifications, geo grids and SDMX formats, 16 python-stdnum and French csv-detective identifiers, DICOM UID and HL7 v2 identifier types.
  - New tools: `csvdetective`, `awsglue`, `oracledatasafe`; `gitleaks` and `trufflehog` list the new secret types.

## 9. Release 2.0.0

- [ ] 9.1 Declare the data license chosen by the owner in `index.json`, on `/about` and in `LICENSE-DATA`. Add attribution for text copied from Wikipedia.
- [ ] 9.2 Run the full contract test, check reproducibility, and check that `openspec validate --strict` passes.
- [ ] 9.3 Tag `v2.0.0`. Verify the GitHub Release assets, the PyPI package and the production site.
