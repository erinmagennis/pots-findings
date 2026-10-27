# How often are model-emitted ontology identifiers right?, a full-population benchmark from pots-findings v1.1 (2026-10-21)

**Setting.** The first two POTS packages (t1, t2) let the extraction model write ontology identifiers directly (HGNC, ChEBI, MeSH). Later packages replaced this with authority resolution and the v1.1 release flagged the model-written ids `unverified_model_emitted` (16,662 rows; 6,120 distinct name × id pairs). Every one of those ids was looked up **by id** at its minting authority and the authority's label and full synonym list compared with the entity name; the name was also resolved forward to obtain the correct id where one exists. No model was involved.

| outcome (share of rows) | % |
|---|---:|
| id denotes the entity — exact label | 37.6 |
| id denotes the entity — authority synonym | 12.8 |
| id denotes the entity — case/plural/Greek/punctuation variant | 11.0 |
| id denotes one of several entities in a compound name | 3.9 |
| **id exists but denotes a different entity** | **34.7** |
| id does not exist | 0.0 |

**Headline.** 99.98% of model-emitted ids exist; 65.3% denote the entity; **34.7% exist but point at something else**. The failure mode is not fabrication but near-miss assignment: a neighbouring gene (SCN9A given SCN8A's id; TGFBR2 given TGFBR1's; MRGPRX2 given MRGPRD's), a related compound (naltrexone → naloxone; levodopa → an unrelated alkaloid), a sibling concept (orthostatic hypotension → "pure autonomic failure"). Of the wrong HGNC ids whose true id is known, 270 of 631 lie within ±50 of it and 196 within ±5 — the model is interpolating in id space. An existence check catches none of this; only label correspondence does.

By authority (% of rows wrong): ChEBI 37.2 · HGNC 31.4 · MeSH 44.0.

**What it means for the corpus.** Nulling the flagged ids wholesale would have discarded ~10,800 usable identifiers. v1.2 instead: **keep** 10,879 rows as authority-verified (retrospectively, with match mode recorded); **replace** 3,176 rows whose name resolves to a different id; **null** 2,607 rows. Every action is in `pots_model_id_benchmark.parquet`, one row per name × id pair.

**What it means for the field.** Any pipeline that lets a language model emit ontology identifiers and validates them by existence will carry roughly one wrong-but-plausible id in three. The remedy is cheap and mechanical: resolve names against the authority and accept only exact-label or authority-synonym agreement.

Caveats: compound-name matches are partial credit; MeSH supplementary concepts have sparse synonym lists so MeSH "wrong" may be slightly overstated; relaxed matching never uses string similarity for acceptance.
