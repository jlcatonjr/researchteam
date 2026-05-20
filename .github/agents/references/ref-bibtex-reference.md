# BibTeX Reference — ResearchTeam

> Quick-reference for **BibTeX ** (library) in ResearchTeam.
> This is a lightweight reference file, not a full agent. For tool-specific operations, consult the relevant specialist agent or escalate to `@orchestrator`.

---

## Version

`BibTeX` ``

## Configuration

**Config files:** `N/A`

## Official Documentation

https://www.bibtex.org/ and https://tug.org/bibtex/

## Key API Surface

BibTeX entries are plain-text records in `references/bibliography.bib`. Each entry has the form:

```bibtex
@article{AuthorYear,
  author  = {Last, First},
  title   = {Title of Article},
  journal = {Journal Name},
  year    = {2024},
  volume  = {10},
  number  = {2},
  pages   = {100--120},
  doi     = {10.xxxx/xxxxxx}
}
```

**Common entry types:** `@article`, `@book`, `@incollection`, `@inproceedings`, `@unpublished`, `@misc`
**Citation key convention:** `AuthorYear` (e.g., `Smith2023`)

## Common Patterns & Pitfalls

- Always verify DOIs resolve before adding an entry; use the CrossRef API or DOI.org.
- Use braces `{}` around proper nouns in titles to preserve capitalisation: `{Chicago}`.
- Deduplicate by checking for existing keys with the same author-year before inserting.
- Never invent page numbers, volumes, or DOIs — leave fields absent rather than guessed.
- For online sources, use `@misc` with `url` and `urldate` fields.
- Run `@conflict-auditor` after any addition or update to `bibliography.bib`.

## Key Conventions

- Follow project style rules when using BibTeX
- Refer to authority sources for API contract accuracy
- Validate changes against existing tests before committing

## Related Agents

- `@technical-validator` — verify technical accuracy of BibTeX usage
- `@primary-producer` — implements code that depends on BibTeX
