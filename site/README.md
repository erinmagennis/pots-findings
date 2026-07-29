# POTS & Dysautonomia Findings Browser — Tier 1 MVP

A static, no-backend browser over **36,459 machine-extracted findings** from
**3,121 POTS and dysautonomia papers**. No build step, no server code, and no API key required for
anything except the optional chat panel.

    cd site && python -m http.server 8000    # then open http://localhost:8000

Opening `index.html` directly from the filesystem will NOT work: the pages are ES modules and same-origin
rules block `file://` module and `fetch` loads. Any static host works (GitHub Pages, S3, nginx).

## Read this first — the three things that will mislead you

**1. Scope.** Tier 1 extracted the **POTS/dysautonomia literature only** — 76 of
286 corpus chunks, i.e. 3,121 of roughly 14,263 papers.
Seven related conditions appear in the data **only as incidental mentions inside POTS/dysautonomia papers**:
ME_CFS, fibromyalgia, EDS_hypermobility, MCAS, IBS_gut, migraine, autism. Their own literatures are **not extracted** (Tiers 2-4). A row labelled
`ME_CFS` is ME/CFS *as discussed in a POTS paper*, not the ME/CFS literature. Every page states this in a
banner; every CSV export carries it in a header comment.

**2. Not medical advice.** These are automated summaries of research papers. No diagnosis, no dosing, no
treatment recommendations. Extraction errors exist. Individual studies do not generalize to individual people.
Personal health questions belong with a qualified clinician.

**3. Attribution.** The research is other people's work. Every finding carries authors, journal, year, PMID and
DOI links. Quotes are truncated to 200 characters and always shown beside the full
citation. Read the original paper before citing anything.

## Entity coverage — two different numbers

| Field | Rows | % of 36,459 | What it means |
|---|---|---|---|
| `entity` | 19,307 | 53.0% | the **original** extracted string |
| `canonical_entity` | 10,858 | 29.8% | **canonicalized** — what entity pages/filters/charts use |
| gap | 8,449 | — | names an entity that received **no** canonical mapping |

Entity-based views therefore cover about **29.8% of findings**
(spanning 2,185 of 3,121 papers) — **not half the corpus**. The
remaining ~47% of findings name no entity at all (symptom/phenotype findings, expected by design).

Of 9,582 distinct entity strings, **1,977 resolve to a canonical entity and
7,605 do not** (1,977 + 7,605 =
9,582). Canonicalization deliberately covered the **head** of the distribution; the long tail
of one-off strings was left alone because mapping it costs far more than it changes any count. Unmapped rows
are excluded from entity roll-ups but remain **fully findable by keyword search on their original string**, and
the UI shows that string tagged *not canonicalized* so they never silently vanish.

Separately, the entity **vocabulary** holds 2,019 entries (1,803 direct +
216 compound strings split into components), collapsing to 863 canonical
entities, 368 with an ontology ID — **189 ChEBI** (via OLS4), **144 HGNC** and **1 NCBIGene** (via MyGene),
**34 MeSH** (via NLM). HGNC and NCBIGene are distinct source databases and are counted separately here rather
than pooled as "genes". Note 1,803 is a *vocabulary* count and 1,977 is a count of *distinct
strings observed in the findings* — different denominators, reported separately rather than mixed.

## Counting rules

- **Papers are counted on `canonical_pmid`**, after validated duplicate merging.
- **Total vs direct.** Entity pages report *papers* (all rows) and *papers (direct)* — excluding
  `split_derived` rows produced by splitting a compound entity string — separately. norepinephrine is
  **194** papers on canonical_pmid / **176** direct (195 / 177 on raw pmid); ELP1 is **53** / **52** direct
  (58 / 57 on raw pmid). Mixing bases is the easiest way to get a wrong number here.
- 36,459 findings come from 36,067 pre-split rows; the growth is
  compound-entity splitting only (216 strings split), and the
  36,032 distinct finding texts are unchanged by it.

## Duplicate-paper handling — validated, not applied blindly

**9 duplicate-title groups were examined** (18 pmids,
179 findings). **8 groups were merged**
(8 pmids folded into canonical records, 53 findings
reattributed via `canonical_pmid`; no findings deleted, fully reversible): 5 preprint->published pairs, 1
guideline co-published in two journals, 1 single-page companion/correction, 1 erratum stub.

**1 group was deliberately NOT merged.** "Post-COVID-19 Postural Orthostatic
Tachycardia Syndrome" is a generic title shared by two genuinely distinct papers with fully disjoint author
lists (author overlap 0.0): pmid 34053992 (Ishibashi et al., *Internal Medicine*, 2021) and pmid 35470419
(Savytskyi et al., *Cardiology Journal*, 2022). Merging them would have destroyed a real independent
replication.

So: **9 groups examined, 8 merged,
1 retained as genuinely distinct papers** — 3,129 pmids ->
3,121 distinct canonical papers. Title-only matching would have been wrong here. The
`pmid_dedup_map` artifact records all 9 groups with a `merge_applied` flag for audit.

## Pages

| Page | What it does |
|---|---|
| `index.html` | Search — keyword (instant, default) or semantic; 14 filters; deep links `?q= ?e= ?c= ?null=1` |
| `entities.html` / `entity.html` | 863 canonical entities; per-entity direction/tier charts and a panel listing every original string folded in |
| `conditions.html` / `condition.html` | Condition breakdown, with in-scope vs incidental-only stated per row |
| `papers.html` / `paper.html` | 3,121 papers; all findings per paper |
| `discover.html` | Five discovery views (below), each with a CSV download |
| `charts.html` | Five preset charts, PNG + CSV export |
| `builder.html` | No-code chart builder: pick axis/metric/series, filter, export |
| `chat.html` | Optional BYO-key Q&A over retrieved findings |
| `about.html` | Full scope, limitations and data dictionary |

## The five discovery views

1. **Associations** (555 rows) — entity co-occurrence. Co-occurrence is **not causation**; 101 are cross-kind and non-trivial, 456 significant at FDR 0.05. Reporting-convention pairs are labelled and hidden by default.
2. **Under-studied signals** (329 rows) — few papers, high agreement. Defaults to the 198-row headline-eligible bar; the >=2-independent-last-authors and not-case-report-only bar is 297 rows. **Thin evidence looks identical to a spurious finding.**
3. **Contradictions** (532 rows) — both sides shown side by side with tier and certainty profiles and their supporting quotes. 268 are hard direction flips, 264 null-vs-positive; 127 have a visible moderator; **376 sit under umbrella condition labels** and may reflect pooled distinct diseases rather than replication failure.
4. **Null / failed results** (5,324 rows) — absence of evidence is **not** evidence of absence; 315 are treatment failures at RCT/meta-analysis tier.
5. **Convergence** (308 rows) — entities concordant across conditions. **Most likely view to be misread**: it is scoped to Tier 1, so cross-condition support comes from incidental mentions. 106 pass the non-POTS bar, 45 are headline-eligible.

## How search works

**Keyword (default)** — substring/token matching over finding text, canonical entity, original entity string
and condition. Instant, zero dependencies, works offline and before any model loads.

**Semantic** — the 36,459 findings were embedded with `all-MiniLM-L6-v2`
(384 dims), quantized to int8 (14.0 MB across 7 lazy shards;
dequantization fidelity mean cosine 0.99997). Your query is embedded **in your browser** with
`Xenova/all-MiniLM-L6-v2` — the ONNX export of that same checkpoint — via transformers.js in a Web Worker
(~23 MB on first use, then cached in IndexedDB). Because query and document vectors
come from the same model, cosine ranking is **exact, not an approximation**.

Verified: browser-side query vectors reproduce Python `sentence-transformers` vectors to cosine **1.000000**
(max abs difference 0.00000) on five test queries, and end-to-end ranking against the shipped int8 shards
matches the Python reference at **10/10 top-10 overlap** on all five.

**If the model cannot load** — offline, blocked CDN, or no WASM — the page says semantic search is unavailable
and keyword search keeps working. A failed model load never breaks the site.

## Chat panel and your API key

Optional. Retrieval happens locally; only the retrieved findings plus your question are sent to the provider
you choose (Anthropic or OpenAI), using a key **you** paste. The key is stored in your browser's
`localStorage` and sent only to that provider's HTTPS endpoint — **this site has no backend**, no key is
bundled in the code, and a "clear key" button removes it. The system prompt requires per-claim citations,
forbids outside knowledge, and forbids medical advice. Everything else on the site works with no key.

## Layout

    site/
      *.html                 12 pages
      css/app.css
      js/                    data.js (loader/filters) search.js embed-worker.js ui.js page-*.js
      vendor/chart.umd.js    Chart.js 4.4.1, vendored — no CDN dependency for charts
      data/
        meta.json            all counts, scope, model block
        findings_facets.json 2.72 MB — facet columns for all 36,459 rows (eager)
        text_NN.json         7 shards — finding text (lazy)
        detail_NN.json       7 shards — quotes and detail fields (lazy)
        papers.json          3,121 canonical papers
        entities.json        863 canonical entities
        autocomplete.json    plain strings for filter dropdowns (no vectors)
        emb/                 7 int8 shards (14.0 MB) + manifest + quant params
        associations.json understudied.json contradictions.json null_results.json convergence.json

Initial page weight is the facets file plus papers/entities/meta; text, detail and embedding shards load on
demand. Serve with gzip enabled — the facet layer compresses to about 0.57 MB.

## Known data quirks

- **1 finding** (1 row) had an empty extracted summary sentence; it renders as
  `[no summary sentence extracted]` followed by its relation triple, rather than as a blank card.
- `contradictions.json` and `convergence.json` store list/dict columns as strings (comma-joined pmids, JSON
  text for evidence and tier/certainty profiles). `page-discover.js` normalizes these on read; if you consume
  those files directly, parse accordingly.

## Provenance

Generated 2026-07-29 06:29 UTC from the Tier-1 canonicalized findings parquet and its companion artifacts
(entity vocabulary, paper metadata, pmid dedup map, five discovery tables, int8 embeddings + manifest +
quant params). Counts in this README and everywhere in the UI are read from `data/meta.json`, which was
derived from those parquets rather than transcribed by hand.
