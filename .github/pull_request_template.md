## Summary

<!-- What changes and why. Link the issue, for example "Closes #123". -->

## Checklist

For changes under `data/`:

- [ ] `metacrafter-registry validate` passes.
- [ ] I ran `metacrafter-registry build` and committed the regenerated `data/*_latest.json(l)` files.
- [ ] New or unreviewed records have `status: draft`.
- [ ] Regexps, examples and links are checked against an authoritative source. Nothing is guessed.
- [ ] Descriptions are in my own words.
- [ ] Examples contain no data of real people and no real secrets.
- [ ] No published id is removed or renamed. A merged duplicate keeps its id in `aliases`.

For code changes:

- [ ] `pytest -q` passes.
- [ ] Changes to the data model, the URL contract or the build have an OpenSpec change in `openspec/changes/`.
