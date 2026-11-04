## 1. Agree the seed packs

Nothing in this group changes the build or `main`.

- [ ] 1.1 Agree the seed packs with the maintainer, with a purpose and a membership rule for each. Candidates: `ru_pii` and `checksum_verified` (design.md, Open Questions). Record the decision in design.md.
- [ ] 1.2 Write the seed pack files by hand and list their members with a throwaway script. Check that every member fits the stated purpose. Adjust `select`, `datatypes` and `exclude` until it does.

## 2. Source records and validation (no new output yet)

- [ ] 2.1 Add `schema/pack.schema.json` (design.md D1) and publish it with the other schemas under `/schema/`.
- [ ] 2.2 Load `data/packs/*.yaml` in `loader.py`, in sorted order.
- [ ] 2.3 Resolve membership in `model.py` (D2): `datatypes`, `select`, `exclude`, patterns through `semantic_type`, sorted output.
- [ ] 2.4 Add the gates and warnings of D3 to `validate.py`.
- [ ] 2.5 Add `tests/test_packs.py` with fixture packs. It covers each `select` key, the default `status`, `country: any`, patterns, `exclude`, and every gate and warning.
- [ ] 2.6 Commit the seed packs from 1.2 as `status: draft`. Run `metacrafter-registry validate` and `pytest -q`.

## 3. API files and pages

- [ ] 3.1 Write `/api/v1/packs.json` and `/api/v1/packs/<id>.json` (D4), with `rules` from the coverage file and `rules_ref` from `ecosystem.lock`. Add both to the manifest and to `openapi.py`.
- [ ] 3.2 Add the `packs` field to records in `/api/v1/`. Check with a test that the legacy files do not change.
- [ ] 3.3 Add the `/pack/` and `/pack/<id>` templates, the Markdown twin, the "In packs" line on record pages, the navigation link, the sitemap and `llms.txt` (D5).
- [ ] 3.4 Report pack changes in `changes.py`: added, deprecated, and datatypes that joined or left.
- [ ] 3.5 Add `/pack/`, `/api/v1/packs.json` and one seed pack to `contract.py`.
- [ ] 3.6 Run `metacrafter-registry validate`, `build`, `check-links`, `check-contract` against `serve`, and `pytest -q`. Commit the regenerated `data/*_latest.json(l)` if they changed.

## 4. Client, MCP and documentation

- [ ] 4.1 Add `Registry.pack()` and `Registry.packs()` to `client.py`, with tests.
- [ ] 4.2 Optional: add the `list_packs` MCP tool and a `pack` filter to `search_datatypes`.
- [ ] 4.3 Document packs in the README URL table, `AGENTS.md`, `CONTRIBUTING.md` (how to propose a pack) and the about page.
- [ ] 4.4 Open an issue in `apicrafter/metacrafter` for a `--pack <id>` option that reads `/api/v1/packs/<id>.json` and runs only the listed rules.
