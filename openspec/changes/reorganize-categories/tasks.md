## 1. Agree the target list

Nothing in this group changes the build or `main`.

- [ ] 1.1 Agree the names and the answers to the Open Questions of design.md with the maintainer. Record the decisions in design.md.
- [ ] 1.2 Write a `description` for each of the target categories (design.md D6) and check each against ten of its records.
- [ ] 1.3 Open issues in `apicrafter/metacrafter` and `apicrafter/metacrafter-llm`: resolve category aliases from `/api/v1/categories.json` in the category filter. Link them from design.md.

## 2. Reference records: description, kind, aliases (no record changes)

- [ ] 2.1 Add `schema/category.schema.json` (D1) and publish it under `/schema/`.
- [ ] 2.2 Add `kind` and `description` to every entry of `data/categories.yaml`. No category is added or retired yet.
- [ ] 2.3 Read the new fields in `loader.py`. Add the gates of the requirement "Category reference records" to `validate.py`.
- [ ] 2.4 Resolve aliases (D5): `model.py`, `client.py` (`Registry.search`), `mcp_server.py` (`search_datatypes`), redirect pages in `build.py`, the alias gate for source records in `validate.py`.
- [ ] 2.5 Add `kind`, `description` and `aliases` to `/api/v1/categories.json` and to `openapi.py`.
- [ ] 2.6 Group `/category/` by kind and show descriptions. Add descriptions to the category section of `llms.txt` and to `category_markdown`.
- [ ] 2.7 Add tests with a fixture alias: reference gates, redirect pages, search by alias. Run `validate`, `build`, `check-links`, `pytest -q`.

## 3. Derived `pii`

- [ ] 3.1 Add `pii` to output categories from `is_pii` in `model.py` and `legacy.py` (D3). Test datatypes, patterns that inherit, and the order.
- [ ] 3.2 Remove `pii` from the `categories` of all source records with `scripts/recategorize.py` (D7). Move the one record in a `pii` directory.
- [ ] 3.3 Add the gate that rejects `pii` in a source record.
- [ ] 3.4 Check with a test that the 265 records that had `pii` still have it in output, and list the 93 that gain it in the pull request.
- [ ] 3.5 Run `validate`, `build`, `pytest -q`. Commit the regenerated `data/*_latest.json(l)`.

## 4. Primary category and directory

- [ ] 4.1 Fix the 19 records whose directory is not one of their categories, and the 3 records in `files`.
- [ ] 4.2 Reduce the 4 records that have four categories to three.
- [ ] 4.3 Reorder `categories` where the first one has the kind `standard`, and give a topic to records that have only a `standard` category (design.md, Open Questions).
- [ ] 4.4 Move every record whose directory differs from its first category, with `scripts/recategorize.py`.
- [ ] 4.5 Add the gates of the requirements "Primary category" and "Directory follows the primary category" to `validate.py`, with tests.
- [ ] 4.6 Run `validate`, `build`, `check-links`, `pytest -q`. Commit the regenerated files.

## 5. Splits (one pull request per item)

For each item: propose the mapping, review every row, commit it as `devdocs/categories/<group>.csv`, apply it, run `validate`, `build`, `check-links`, `pytest -q`, and commit the regenerated files.

- [ ] 5.1 `territories`: administrative and statistical units from `geo` and `government`.
- [ ] 5.2 `addresses`: addresses, streets and postal codes from `geo`. Cadastral numbers from `geo` to `realestate`.
- [ ] 5.3 `publicfinance`: budget, procurement and grants from `government` and `finances`. Legal acts from `government` to `legal`.
- [ ] 5.4 `taxes`: tax and VAT numbers from `finances`.
- [ ] 5.5 `lifesciences`: biology, genomics and taxonomy from `science`. Bibliometric identifiers from `science` to `publishing`.
- [ ] 5.6 Narrow the descriptions of `geo`, `government`, `finances` and `science` to what remains, and check that no remaining record contradicts them.

## 6. Merges (after the consumer issues of 1.3 are closed or accepted)

Each item retires a category id into `aliases` and follows the steps of group 5.

- [ ] 6.1 `objectids` into `identifiers`. Move subject identifiers out of `identifiers` to their topics.
- [ ] 6.2 `common` into `values`. Give every former `common` record a topic or `values`.
- [ ] 6.3 `useraccounts` into `internet`.
- [ ] 6.4 `ecommerce` and `shipping` into the new `commerce`.

## 7. Changelog, contract and documentation

- [ ] 7.1 Report category changes in `changes.py` (D8), with tests.
- [ ] 7.2 Add `/category/` and one category alias to `contract.py`.
- [ ] 7.3 Check `datahub.py` output: no duplicate term names inside a node after the moves.
- [ ] 7.4 Update `AGENTS.md`, `CONTRIBUTING.md`, `skills/registry-contributor/SKILL.md` and the issue forms: how to choose the primary category, `is_pii` instead of `pii`, the three-category limit.
- [ ] 7.5 Write the release notes: new categories, retired ids and their replacements, and the filters that return fewer records (`geo`, `government`, `finances`, `science`).
