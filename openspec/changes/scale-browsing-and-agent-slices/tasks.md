## 1. Index and slices

- [x] 1.1 Write `/api/v1/datatypes-index.json` from the normalized records. Add it to the manifest.
  - 1.2 MB, 254 KB compressed.
- [x] 1.2 Write `/api/v1/categories/<id>.json` and `/api/v1/countries/<CC>.json` for each category and country that has records.
- [x] 1.3 Write `/country/<CC>.md`. Link the country Markdown twins from `llms.txt`, and add `<link rel="alternate" type="text/markdown">` to the country pages.
- [x] 1.4 Describe the new files in OpenAPI and mark `/search-index.json` deprecated. Add one slice and the index to the URL contract check.
- [x] 1.5 Tests: the index has one entry per record; each slice equals the filtered bulk file; a record with two countries is in both slices.

## 2. List page

- [x] 2.1 Render the first 100 records in `/datatype/` and add the no-JavaScript note with links to the category and country pages.
- [x] 2.2 Load the index in `site.js`; filter, sort and page in memory, 100 rows at a time. Keep the query parameters.
- [x] 2.3 Move the search page to the new index.
- [x] 2.4 Tests: `/datatype/index.html` is under 150 KB; the link check still reaches every record page.
  - 101 KB, down from 2.6 MB.
- [ ] 2.5 Check in a browser at 375px and on a throttled connection: the filters work before the index arrives for the first 100 rows, and for all rows after.
  - Checked on a local build: filters, paging and sorting over all rows. Not checked: the state before the index arrives, which a local server passes too fast to see.

## 3. Record page

- [x] 3.1 Add the "Test a value" field for records with a convertible pattern or a check-digit algorithm; load `identify-core.js` only there.
- [x] 3.2 Show the names in the record's own languages under the title.
- [x] 3.3 Tests: the field is absent when the pattern cannot be converted; the native-language name has a `lang` attribute.

## 4. Documentation

- [x] 4.1 Document the new URLs in `README.md`, `about.html`, `agents.html`, `agents.md` and the "How to find a datatype" section of `llms.txt`.
