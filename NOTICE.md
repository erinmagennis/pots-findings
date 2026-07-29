# Notice

The license itself is [`LICENSE`](LICENSE): the full text of Creative Commons Attribution 4.0
International (CC BY 4.0). This file explains what that license covers here, what it does not
cover, and the exact credit line to use.

## Two different things are in this repository

### 1. Derived structured data — CC BY 4.0

Everything this project produced — the extracted structured fields, canonical entity
vocabulary, entity/ontology mappings, the association, under-studied, contradiction, null-result
and convergence tables, the embeddings, and all documentation and notebooks — is released under
the **Creative Commons Attribution 4.0 International License (CC BY 4.0)**.

Full text: https://creativecommons.org/licenses/by/4.0/legalcode

**You must attribute.** Any use, redistribution, or derivative work — including a fork, a
republished copy, a paper, a product, or a model trained on this data — must credit:

> Magennis, E. (2026). POTS/Dysautonomia Literature Findings, Tier 1 v1.
> https://pots.erinmagennis.com · https://github.com/erinmagennis/pots-findings
> Licensed CC BY 4.0.

The credit must appear wherever the work is normally credited, and must not be removed from
redistributed copies. If you modify the data, say so, and do not imply that the modified version
is endorsed by the author.

**And you should credit the underlying researchers.** The scientific content summarized here is
the work of the ~3,121 papers' authors. Every row carries `citation_short`, `authors`,
`journal`, `doi_url` and `pubmed_url`. If a finding matters to your work, cite the original
paper. Attributing this database is not a substitute for that.

### 2. Verbatim quoted text — NOT licensed by us

The `provenance_quote_trunc` column contains **short verbatim excerpts from the source
publications**. This text is the **copyright of the respective publishers and authors**. It is
not ours to license, and CC BY 4.0 does **not** apply to it.

These excerpts are included for a single purpose: letting a reader **identify and verify** that
an extracted finding actually appears in the cited paper. To keep that use narrow:

- excerpts are truncated to **≤200 characters**;
- every excerpt is stored adjacent to the full citation and a link to the source;
- **no bulk quote export is provided**, and the project does not publish one.

If you redistribute this data, keep those constraints. Do not extract the quote column into a
standalone corpus, do not reconstruct article text from it, and do not present the excerpts
without their citations. If you are a publisher or author and want an excerpt removed, that is a
reasonable request and it will be honored.

## No warranty

The data is machine-extracted and contains errors. It is provided as-is, with no warranty of
accuracy, completeness or fitness for any purpose. It is **not medical advice** and must not be
used for diagnosis or treatment decisions.
