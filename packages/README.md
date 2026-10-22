# POTS / Dysautonomia Cross-Condition Literature Findings

**148,186 machine-extracted structured findings from 11,519 papers** across the POTS,
dysautonomia and comorbid-condition literature — including ME/CFS, Ehlers-Danlos and
hypermobility, MCAS, fibromyalgia, IBS, small-fiber neuropathy, long COVID, autism, migraine,
Sjögren's and PANS/PANDAS.

Each finding carries the verbatim source span it was drawn from, its source paper's PMID and
DOI, and explicit provenance for every ontology identifier — so a reader can check it.

> **Read this first: scientific fidelity is unmeasured.**
> Every quality check in this repository verifies *well-formedness* — that a quote is real text
> from the right paper, that identifiers carry authority provenance, that counts are conserved.
> **Nothing verifies that a finding correctly interprets its source.** That requires a human
> reader. Treat every row as a pointer to a paper worth reading, not as a fact to cite.
>
> **Not medical advice.** No diagnostic or treatment guidance. Machine-extracted research
> information only.

## The five packages

Five blocks of one corpus. **Zero papers are shared between any two** — verified by PMID set
intersection across all ten pairs. Each folder stands alone: data, docs, QA evidence, pinned
code, and a verifier that re-derives every documented number from the shipped data.

| package | findings | papers | topic | identifiers | quotes verifiable, shipped source | after re-fetch (v1.1) |
|---|---:|---:|---|---|---:|---:|
| [`dysautonomia-core-findings/`](dysautonomia-core-findings/) | 36,067 | 3,129 | POTS, dysautonomia core | model-emitted | 18.12% | 99.67% |
| [`comorbid-conditions-findings-a/`](comorbid-conditions-findings-a/) | 36,611 | 3,123 | comorbid conditions, wave 1 | model-emitted | 21.07% | 99.83% |
| [`comorbid-conditions-findings-b/`](comorbid-conditions-findings-b/) | 33,830 | 2,589 | comorbid conditions, wave 2 | model-emitted | 19.39% | 99.85% |
| [`postviral-autism-findings/`](postviral-autism-findings/) | 26,032 | 1,587 | long COVID, post-viral, autism | authority-derived | 12.22% | 99.96% |
| [`migraine-hypermobility-findings/`](migraine-hypermobility-findings/) | 15,646 | 1,091 | migraine, hypermobility, Sjögren's, PANS/PANDAS | authority-derived | 100.0% | 100.0% (retained) |
| **total** | **148,186** | **11,519** | | | **26.75%** | **99.8%** |

"Shipped source" counts a quote as verifiable only if the text it was drawn from ships with the package
(Tier 4's retained archive, or an abstract). "After re-fetch" is the v1.1 retrofit: every Tier 1–3 quote
re-checked against Europe PMC's *current* text — a weaker guarantee than a retained archive, and not the
bytes the model read. See "will mislead you" item 2.

Start with any folder's `README.md`. [`OVERVIEW.md`](OVERVIEW.md) compares all five;
[`COMPARABILITY.md`](COMPARABILITY.md) is the one document to read before pooling any of them.

## Downloading one tier at a time

Every folder is self-contained — its own data, docs, QA evidence and code. You never need more
than one.

**Easiest: download a single package archive.** From the
[Releases](../../releases) page, take just the tier you want:

```bash
tar -xzf migraine-hypermobility-findings-v1.2.tar.gz
cd migraine-hypermobility-findings-v1.2
shasum -a 256 -c CHECKSUMS.sha256          # confirm the download is intact
python code/verify_package.py --self-test  # confirm the data matches the docs
```

That's 10 MB compressed for Tier 4, and nothing from the other four tiers is involved. No Git
needed.

**From Git, one folder only.** A plain `git clone` fetches all five (~114 MB working tree). To
get a single tier, use a sparse checkout:

```bash
git clone --filter=blob:none --no-checkout https://github.com/erinmagennis/pots-findings.git
cd pots-findings
git sparse-checkout init --cone
git sparse-checkout set migraine-hypermobility-findings
git checkout
```

You end up with `migraine-hypermobility-findings/` plus the top-level docs, and none of the other package folders. Add
another later with `git sparse-checkout add postviral-autism-findings`.

**Single file, no clone at all.** Every file has a direct URL, which is useful for a script
that only wants the table. Fetch the bytes, then read them:

```python
import io, urllib.request
import pandas as pd

url = ("https://raw.githubusercontent.com/erinmagennis/pots-findings/main/"
       "migraine-hypermobility-findings/data/tier4_findings.parquet")
df = pd.read_parquet(io.BytesIO(urllib.request.urlopen(url).read()))
```

Passing the URL straight to `pd.read_parquet(url)` also works, but only if `fsspec` and
`requests` are installed — they are not part of a default pandas install, so the two-step
version above is the portable one.

Files over 100 MB will not serve
from `raw.githubusercontent.com`; nothing here approaches that (largest file: 18 MB).

**Package sizes**, compressed / on disk:

| package | archive | extracted | findings |
|---|---:|---:|---:|
| dysautonomia-core-findings | 32 MB | 34 MB | 36,067 |
| comorbid-conditions-findings-a | 22 MB | 24 MB | 36,611 |
| comorbid-conditions-findings-b | 20 MB | 21 MB | 33,830 |
| postviral-autism-findings | 16 MB | 18 MB | 26,032 |
| migraine-hypermobility-findings | 10 MB | 12 MB | 15,646 |

Each folder repeats the shared files — the 39,128-row entity vocabulary, the chunk map, the
invariant modules — which is why the five sum to slightly more than the corpus. That redundancy
is deliberate: it is what lets any one folder work alone.

The whole repository is **301 files / 113.6 MB** (55 + 58 + 58 + 62 + 60 across the five tier
folders, plus 8 at the root). The largest single file is the 18 MB Tier 1 CSV, so **no Git LFS
is required** — GitHub warns at 50 MB and blocks at 100 MB per file.

**If you want all five**, pool them freely for row counts, paper metadata and quote presence —
but read [`COMPARABILITY.md`](COMPARABILITY.md) first. Eleven metrics are not comparable across
packages, and three columns will actively mislead you.

## Four things that will mislead you

These are the errors most likely to be made by someone using this data, in the order they are
likely to be made.

### 1. The metric that looks like grounding quality ranks the packages backwards

`id_resolved_frac` — the share of rows carrying an ontology identifier — measures **coverage**,
not **correctness**:

| package | identifier coverage | identifier correctness |
|---|---:|---:|
| Tier 1 | 12.1% | 0.578 |
| Tier 2 (A+B) | 17.5% | 0.708 |
| Tier 3 | 15.8% | **0.986** |
| Tier 4 | 10.3% | **0.998** |

Tier 2 has the most identifiers and nearly the worst; Tier 4 the fewest and the best. The
reason is architectural: in Tiers 1–2 the extraction model *emitted* identifiers from memory
(there is no reasoning path from a name to an arbitrary integer — only recall). In Tiers 3–4 the
model emitted names only and a resolver looked identifiers up afterwards.

**Always stratify on `ontology_id_verification`. Never pool `id_resolved_frac`.**

### 2. Only one package ships the text its quotes came from

Only Tier 4 retained body text after extraction. In the other four, **108,549 of
148,186 rows have no shipped source** — a *retention* failure, not an extraction failure.

v1.1 re-fetched the source for every Tier 1–3 paper from Europe PMC and re-checked every quote
(`annotations/quote_retrofit_<pkg>.parquet`): **147,941 of 148,186 rows
(99.8%) now have a checkable source**, full-text quotes trace at 97.92%, and
wrong-paper false positives are 0/400 in every stratum. What that does *not* give you: the retrofit
checks Europe PMC's text *today*, not the bytes the model read, and the fetched text is not shipped
(LICENSE). 245 rows have no source anywhere and 1,391 full-text rows could only be
checked against the abstract. Treat Tier 4's retained-archive traceability and the Tier 1–3 retrofit
traceability as two different guarantees; never pool them.

### 3. One column has opposite meanings in different packages

`ontology_id_source == 'unresolved_nulled'` means the identifier was **KEPT** in Tier 2 and
**NULLED** in Tiers 3–4. So the obvious filter silently drops 2,242 Tier-2 rows that do carry
identifiers:

```python
df[df.ontology_id_source != 'unresolved_nulled']   # WRONG - drops valid rows
df[df.ontology_id_verification == 'authority_verified']   # right
```

### 4. `condition` is a population bucket — and the `MCAS` bucket is mostly not MCAS

`condition` means **the patient population the paper studied**, in coarse buckets whose written
definitions (`<pkg>/annotations/CONDITION_BUCKET_DEFINITIONS.md`) were fixed only on 2026-09-16, after
extraction. A stratified census of the 1,083 papers labelled `MCAS` projects that **~69% study mast-cell
biology with no mast-cell-disorder population, ~10% are MCAS as defined, ~5% are mastocytosis** — a distinct
clonal neoplasm. A "markers of MCAS" count taken from the raw bucket is mostly a count of mast-cell markers
in general. The shipped column is unchanged; `annotations/condition_annotations.parquet` (pmid-keyed, in
every package) carries a per-paper verdict — `in_bucket` / `bucket_violation` / `NEEDS_HUMAN` — all
classifier-derived and `human_confirmed == False`. Only the MCAS bucket has been censused.

```python
ann = pd.read_parquet('comorbid-conditions-findings-a/annotations/condition_annotations.parquet')
ok = ann.loc[ann.condition_bucket_verdict == 'in_bucket', 'pmid']
df[df.condition.eq('MCAS') & df.pmid.isin(ok)]   # MCAS population, classifier-verified
```

## What changed in v1.1 — additive annotations, no data changed

No row of any `data/` table was modified between v1 and v1.1. Three things were added, all as separate
files under each package's `annotations/`, covered by its `MANIFEST.json` and `CHECKSUMS.sha256`:

- **Quote source retrofit for Tiers 1–3.** Source text for all 10,428 Tier 1–3 papers was re-fetched
  from Europe PMC (abstract 96.8%, full text 98.4% of the 6,239 full-text papers) and every quote
  re-checked with the shipped comparator. Verifiable rows in Tiers 1–3 went from 23,991 to **132,295 of
  132,540 (18.1% → 99.8%)**; full-text rows trace to re-fetched full text at **97.9%** with 0/400
  wrong-paper false positives in every stratum. Row-level results: `quote_retrofit_<pkg>.parquet`. The
  fetched text is not shipped (see LICENSE). This checks *current* Europe PMC text, not the bytes the
  model read — Tier 4's retained-archive guarantee is not reproduced.
- **Condition bucket annotations** (item 4 above) and the bucket definitions file.
- **Documentation corrections**: `condition` and `provenance_quote` re-described in every data dictionary
  (128 quotes carry raw HTML entity codes, verbatim to model input); `code/README.md` in every package
  explains why a Tier-1 package carries `tier3_*` modules; three boolean columns are now stored as nullable
  `boolean` in the parquet (values unchanged); the Tier-4 "1,960 uncertain rows" figure is corrected to the
  data's 2,257; `PACKAGE_INDEX.csv` file counts now match each `MANIFEST.json`.

## Quickstart

```python
import pandas as pd
df = pd.read_parquet('postviral-autism-findings/data/tier3_findings.parquet')   # 26,032 findings

# identifiers you can trust
grounded = df[df.ontology_id_verification == 'authority_verified']

# findings whose quote can be checked against surviving source text
checkable = df[df.cap_quote_source_retained == True]

# highest-confidence evidence
strong = df[df.evidence_tier.isin(['meta-analysis','RCT'])
            & df.certainty_derived.eq('confirmed')]
```

Each package also ships the same table as `data/<pkg>_findings.csv.gz` for tools without
parquet support, and a 39,128-row entity canonicalization lookup as
`data/entity_vocabulary_crosstier.parquet`.

**Never lowercase entity names to merge them** — `MECP2` and `Mecp2` are the human and mouse
genes. The shipped vocabulary keeps every ortholog pair apart (0 false merges against 25
planted controls).

## Verify any package

Every documented number is re-derivable from the shipped data. Nothing requires the network.

```bash
cd postviral-autism-findings
shasum -a 256 -c CHECKSUMS.sha256          # confirm nothing was corrupted
python code/verify_package.py --self-test  # re-derive every number in the README
```

The verifier exits non-zero if the data disagrees with the documentation. `--self-test` plants
six regressions and asserts each is caught — a checker that only ever passes is untested.

All five packages currently report **19/19 headline numbers re-derived** and **6/6 planted
regressions caught**.

## Known invariant failures — declared, not hidden

A nine-check invariant suite runs on each package. **Tiers 1, 2a and 2b do not fully pass, and
ship that way on purpose:**

| package | passing | what fails |
|---|---:|---|
| dysautonomia-core-findings | 8/9 | `id_provenance` — Tier 1 predates the provenance-tag convention; no row carries a source tag |
| comorbid-conditions-findings-a | 7/9 | `id_provenance`, plus 11 rows from one paper with GO ids written into a free-text prose field |
| comorbid-conditions-findings-b | 7/9 | `id_provenance`, plus 1 such row |
| postviral-autism-findings | 9/9 | — |
| migraine-hypermobility-findings | 9/9 | — |

These are **pre-existing, characterized properties of the earlier extraction passes**, not
damage from packaging. The project rule is to flag and never silently repair: a suite tuned
until it passes is not a suite. Each package's `docs/README.md` explains its own failures.

## Repository layout

```
dysautonomia-core-findings/ comorbid-conditions-findings-a/ comorbid-conditions-findings-b/ postviral-autism-findings/ migraine-hypermobility-findings/    five self-contained packages
  data/     findings table (parquet + csv.gz), entity vocabulary, chunk map
  docs/     README, DATA_DICTIONARY, METHODS, LIMITATIONS, COMPARABILITY,
            WEBSITE_INTEGRATION
  qa/       invariant results, quote census, per-package statistics
  code/     pinned extraction pipeline, prompt, resolver, invariants, verifier
  MANIFEST.json  CHECKSUMS.sha256  LICENSE  CITATION.cff
OVERVIEW.md          all five compared
COMPARABILITY.md     read before pooling packages
PACKAGE_INDEX.csv    the comparison as a table
```

Each folder duplicates the shared files (entity vocabulary, chunk map, invariant modules) so
that any single folder can be copied out and still work unaided.

## Citing

Each package has a `CITATION.cff` with a `PLACEHOLDER-DOI-<pkg>` field, to be filled in by a rebuild once the Zenodo DOIs are reserved.

**Cite the source papers for any finding that matters to
your work** — every row carries `pmid`, `doi`, `title`, `journal` and `year`. Attributing this
database is not a substitute for citing the researchers whose work it summarizes.

## License

Derived structured data: **CC BY 4.0**.

The `provenance_quote` column contains **short verbatim excerpts from the source publications**
— copyright of the respective publishers and authors, and **not** covered by CC BY. They exist
so findings can be verified; median length is 180 characters, typically one sentence. See
[`LICENSE`](LICENSE) for the excerpt policy and the takedown commitment, which will be honored.

