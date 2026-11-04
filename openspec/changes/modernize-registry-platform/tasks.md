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

- [ ] 8.1 Add `ecosystem.lock`, pinning the metacrafter-rules ref. CI checks out metacrafter-rules at that ref.
- [ ] 8.2 Build `detected_by.metacrafter_rules`, `/api/v1/coverage.json` and the generated `metacrafter` tool `supported_types`.
- [ ] 8.3 Report orphans on PRs. Add the `weekly.yml` drift job, which opens or updates a tracking issue, and an external link check.
- [ ] 8.4 Add the `/identify` playground: a Web Worker, `regexp_js`, per-pattern time limits and JS checksum ports. Add a test that the page makes no network requests.
- [ ] 8.5 Add starter crosswalk mappings for the Presidio, Google DLP and Purview entities. Wire them into the `crosswalk` tool.
- [ ] 8.6 Add the `/quality` and `/changes` pages. Add a changelog generator that diffs against the previous release's assets.
- [ ] 8.7 File the follow-up OpenSpec changes in the sibling repos:
  - metacrafter: honour `METACRAFTER_REGISTRY_URL` in `processor.py`, and optionally use the package.
  - metacrafter-llm: load the corpus by URL or package, and rebuild on a hash change.
  - metacrafter-rules: fix or alias the 39 orphan keys.

## 9. Release 2.0.0

- [ ] 9.1 Declare the data license chosen by the owner in `index.json`, on `/about` and in `LICENSE-DATA`. Add attribution for text copied from Wikipedia.
- [ ] 9.2 Run the full contract test, check reproducibility, and check that `openspec validate --strict` passes.
- [ ] 9.3 Tag `v2.0.0`. Verify the GitHub Release assets, the PyPI package and the production site.
