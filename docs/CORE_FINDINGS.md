# Core Findings — Tier 1 (POTS / dysautonomia)

**A machine-extracted, source-linked map of what the POTS and dysautonomia literature actually reports.**
36,459 structured findings from 3,121 distinct papers. Every finding carries its source paper, authors,
journal, and a link. Every number below is computed from a table you can open and re-check.

---

## Read this before anything else

**This is not medical advice.** Everything here is research information extracted automatically from
published papers. It contains no diagnostic guidance and no treatment recommendations, and nothing in it
is tailored to any individual. Several sections below describe drugs, biomarkers, and test results;
none of that is a reason to start, stop, or change any treatment. Decisions about your own care or a
patient's care belong to a qualified clinician who knows the full clinical picture.

**The credit belongs to the original authors.** Every line in this corpus is an automated summary of
someone else's study. The extraction adds indexing and counting; it adds no new evidence. Where a finding
matters to you, follow the link and read the paper — the summary is a pointer, not a substitute, and the
authors did the work.

**This is machine extraction, and it has errors.** Entity names were normalized by language models and
deterministic rules; 51 of 1,803 mapped entity strings are flagged low confidence and 240 medium
(`map_confidence` column). Direction labels, evidence tiers, and effect descriptions are model
judgments over source text, not adjudicated by a human reviewer for every row. Co-occurrence in this
corpus is not causation: 23,193 of 36,459 findings are explicitly labeled correlational-only and only
4,373 carry a causal claim by the original authors.

---

## 1. What this is, and what it is not

### Scope — the single most important caveat

Tier 1 covers **POTS and dysautonomia only**. It is chunks 0–75 of a 286-chunk, ~14,263-paper corpus:
**~3,121 of ~14,263 papers are covered (about 22%)**.

Other conditions appear in this table, but **only as incidental mentions inside POTS/dysautonomia
papers** — not as their own literature:

| Condition | Tier-1 papers mentioning it | Where its own literature actually lives |
|---|---:|---|
| ME/CFS | 136 | Tier 2 — **not yet extracted** |
| EDS / hypermobility | 146 | Tier 2 — **not yet extracted** |
| fibromyalgia | 103 | Tier 2 — **not yet extracted** |
| MCAS | 90 | Tier 2 — **not yet extracted** |
| IBS / gut | 64 | Tier 2 — **not yet extracted** |
| migraine | 61 | Tier 2 / Tier 4 — **not yet extracted** |
| autism | 18 | Tier 3 — **not yet extracted** |

So: **this is not a cross-condition resource.** A count of "ME/CFS findings" here is a count of what POTS
researchers said about ME/CFS in passing. Tier 2 (7,243 papers: ME/CFS, MCAS, EDS, fibromyalgia, IBS,
small-fiber neuropathy, gastroparesis), Tier 3 (1,754 papers: long COVID, autism, post-viral), and Tier 4
(1,471 papers) are not extracted yet. Any cross-condition claim made from Tier 1 alone is a claim about
POTS papers, and it is labeled as such everywhere in the tables (`scope_warning` column).

> *In plain terms: this covers the POTS and dysautonomia research only — roughly one paper in five of the
> full planned collection. Other conditions show up only when a POTS paper happened to mention them, so
> this cannot yet tell you how POTS compares to ME/CFS or fibromyalgia.*

### Method, in a paragraph

Papers were retrieved and grouped into topic chunks, then each paper's text — full text where available,
abstract otherwise — was read by a language model against a fixed 70-field schema: one row per discrete
finding, with the measured entity, direction of effect, condition, study design tier, participant count,
certainty, and a verbatim supporting quote. 29,531 of 36,459 findings come from retrieved full text,
6,522 from abstract only, 14 from blocked text. **`provenance_quote` coverage is 100%** — no finding
exists without a quoted span from its source. A second pass canonicalized the entity vocabulary: 9,582
distinct entity strings were reduced to **863 canonical entities**, of which **368 carry a real ontology
identifier** (189 ChEBI chemicals, 145 gene identifiers via HGNC/NCBI Gene, 34 MeSH conditions).
216 compound strings ("epinephrine, norepinephrine, dopamine") were split into components.

A duplicate-title pass then ran with author-list validation: **9 duplicate-title groups (18 PMIDs, 179
findings) were examined, 8 were merged, and 1 was retained as genuinely distinct papers.** The 8 merges
folded 8 PMIDs into their canonical record and reattributed **53 findings** via `canonical_pmid` — no
findings deleted, fully reversible — and comprised 5 preprint→published pairs (bioRxiv / Research Square),
1 guideline co-published simultaneously in two journals, 1 single-page companion/correction, and 1 erratum
stub. So **3,129 PMIDs become 3,121 distinct canonical papers**. Details in §8.

### Where it is weakest

- **Entity coverage is partial, and there are two distinct gaps — state both.** First, **17,152 findings
  (47.6% of the 36,067 pre-split rows; 47.0% of 36,459) carry no `entity` at all** — these are symptom and
  phenotype statements naming no discrete analyte. Second, of the rows that *do* name an entity, 8,449
  carry a string that received no canonical mapping (7,605 distinct long-tail strings; only 1,803 of 9,582
  strings were mapped). Net: **`canonical_entity` is populated on 10,858 rows = 29.8% of the table**,
  spanning **2,185 of 3,121 papers**. Every entity-level count in §2 is a count over those 10,858 rows.
  It is never a count over the whole corpus, and the unmapped long tail is searchable but not aggregated.
- **Evidence tier is bottom-heavy.** cohort 8,239 · cross-sectional 7,009 · review/expert-opinion 6,507 ·
  case-report 3,777 · case-series 3,239 · case-control 3,184 · mechanistic/in-vitro 2,787 · **RCT 877** ·
  **meta-analysis 840**. Only 226 papers contribute at least one meta-analysis-tier finding and 189 at
  least one RCT-tier finding. The high-tier layer is thin, and it is the layer to trust.
- **Ontology grounding is an enrichment, not a key.** All 170 physiological-measure canonicals have zero
  ontology IDs by design — HRV indices and orthostatic BP deltas have no genuine ChEBI/HGNC/MeSH
  descriptor, and forcing a match would be worse than leaving them unresolved.

*Source tables: `tier1_findings_canonical.parquet`, `entity_vocabulary.parquet`, `paper_metadata.parquet`,
`pmid_dedup_map.parquet`, `canonicalization_report.md`, `tier1_validation_report.md`, `PRE_TIER2_AUDIT.md`.*

---

## 2. Best-supported signals

### First, a measurement correction that changes the leaderboard

Counting papers by exact entity string — which is what an unnormalized extraction does — **materially
undercounts every HRV metric.** Measured, before → after synonym merge (`canonicalization_report.md` §5):

| Signal | Papers by best single string | Papers after synonym merge | Distinct surface strings merged |
|---|---:|---:|---:|
| **HF power** | **9** | **49** | 25 |
| SDNN | 38 | 80 | 19 |
| RMSSD | 33 | 70 | 18 |
| LF power | 8 | 28 | 16 |
| norepinephrine | 152 | 177 | 16 |

HF power was undercounted **5.4×**. A reviewer looking at the raw extraction would have concluded that
high-frequency HRV was a fringe measure in this literature with 9 papers; it is in 49. The distortion is
larger than the norepinephrine case that motivated the work.

> *In plain terms: the same measurement gets written 25 different ways across papers ("HF power",
> "high-frequency HRV", "HF power (normalized units)"…). Counting the phrases instead of the concept made
> a well-studied measurement look rare. Merging the phrasings fixed it.*

**And type discipline matters as much as merging.** Three different things share the word
"norepinephrine": the catecholamine (`norepinephrine`, molecule, 176 papers), the transporter gene
(`slc6a2`, gene-or-protein, 17 papers), and the antidepressant class (`snri`, drug class, 5 papers).
They are kept as **three separate entities**. A naive substring merge pools all 98 norepinephrine-ish
strings and reports **232 papers** for "norepinephrine" — a number that silently mixes a catecholamine
measurement, a gene variant, and a drug class. That is the wrong answer, and it is the answer a regex
gives you.

### The leaderboard

Recomputed directly from `tier1_findings_canonical.parquet` on `canonical_pmid` (post duplicate-title
collapse). `papers_direct` excludes rows recovered by splitting compound strings; `papers` includes them.
`last_authors` counts distinct last authors across the supporting papers — a rough independence proxy.

| Canonical entity | Kind | papers_direct | papers | findings | distinct last authors | best tier | meta / RCT rows | dominant direction |
|---|---|---:|---:|---:|---:|---|---:|---|
| norepinephrine | molecule | 176 | 194 | 270 | 175 | meta-analysis | 4 / 5 | elevated (135) |
| heart rate variability | physiological | 168 | 170 | 291 | 165 | meta-analysis | 13 / 7 | reduced (152) |
| heart rate | physiological | 168 | 178 | 271 | 149 | meta-analysis | 2 / 8 | elevated (143) |
| orthostatic hypotension | clinical sign | 115 | 115 | 249 | 98 | meta-analysis | 24 / 2 | elevated (120) |
| midodrine | drug | 86 | 95 | 153 | 90 | meta-analysis | 10 / 28 | n/a (treatment) |
| SDNN | physiological | 80 | 94 | 162 | 90 | meta-analysis | 9 / 0 | reduced (95) |
| LF/HF ratio | physiological | 78 | 81 | 117 | 78 | meta-analysis | 12 / 0 | elevated (50) |
| SNCA (α-synuclein) | gene/protein | 77 | 77 | 182 | 69 | meta-analysis | 4 / 0 | elevated (94) |
| RMSSD | physiological | 70 | 84 | 121 | 83 | meta-analysis | 16 / 1 | reduced (67) |
| IV immunoglobulin | drug | 62 | 62 | 84 | 60 | meta-analysis | 1 / 7 | n/a (treatment) |
| ivabradine | drug | 60 | 62 | 125 | 56 | meta-analysis | 9 / 18 | n/a (treatment) |
| systolic blood pressure | physiological | 55 | 62 | 89 | 54 | meta-analysis | 2 / 2 | reduced (32) |
| fludrocortisone | drug | 54 | 61 | 72 | 61 | meta-analysis | 1 / 5 | n/a (treatment) |
| ELP1 | gene/protein | 52 | 53 | 203 | 38 | case-control | 0 / 0 | reduced (61) |
| IL-6 | molecule | 51 | 75 | 92 | 75 | meta-analysis | 3 / 1 | elevated (62) |
| **HF power** | physiological | **49** | 52 | 70 | 48 | meta-analysis | 5 / 0 | reduced (35) |
| baroreflex sensitivity | physiological | 43 | 43 | 75 | 39 | meta-analysis | 2 / 7 | reduced (37) |
| ACE2 | gene/protein | 40 | 41 | 58 | 40 | cohort | 0 / 0 | elevated (16) |
| pyridostigmine | drug | 40 | 42 | 82 | 40 | meta-analysis | 7 / 18 | n/a (treatment) |
| C-reactive protein | molecule | 37 | 46 | 55 | 46 | meta-analysis | 4 / 2 | elevated (38) |
| gAChR autoantibody | molecule | 36 | 36 | 66 | 35 | cohort | 0 / 0 | elevated (35) |
| cortisol | molecule | 36 | 41 | 72 | 40 | meta-analysis | 6 / 0 | elevated (28) |
| TNF-α | molecule | 33 | 54 | 65 | 51 | meta-analysis | 1 / 2 | elevated (41) |

**Counting-basis note, stated because it moves numbers.** The canonicalization report counted raw PMIDs
and reports norepinephrine at 177 papers_direct and ELP1 at 57; recomputing on `canonical_pmid` after the
8 validated duplicate-title merges gives **176** and **52**. Three of the eight merged groups are ELP1
preprint→published pairs, which is why ELP1 moves most. Both numbers are correct for their stated basis;
the table above uses the merged basis throughout, because a preprint and its published version should not
look like two independent studies.

### What the strongest rows actually say

**Reduced heart rate variability is the most replicated physiological signal in the corpus** — 291
findings across 170 papers, 165 distinct last authors, 152 of the direction-labeled findings in the
"reduced" direction, with 13 meta-analysis-tier and 7 RCT-tier rows. It is also the least specific:
the same direction appears in Parkinsonism, COPD, laryngopharyngeal reflux, and depression cohorts in
this very table. Example spans, each ≤200 characters and each with its source:

- "In the time domain parameters, SDNN, reflecting overall HRV, is significantly reduced (p < 0.001)."
  — Bogdan C et al. (2024) *Life (Basel)*, case-control, n=140.
  [PubMed](https://pubmed.ncbi.nlm.nih.gov/39202781/) · [DOI](https://doi.org/10.3390/life14081039)
- "HRV was significantly lower at end of follow-up in the DLB group than in the AD group."
  — Haglund M et al. (2024) *Parkinsonism & Related Disorders*, cohort, n=36.
  [PubMed](https://pubmed.ncbi.nlm.nih.gov/38547558/) · [DOI](https://doi.org/10.1016/j.parkreldis.2024.106947)
- "SDNN (115 [65–226] vs. 131.5 [84–175] ms; P = 0.013)" — Li Z et al. (2025) *Clinical Autonomic
  Research*, case-control, n=103. [PubMed](https://pubmed.ncbi.nlm.nih.gov/40056296/) ·
  [DOI](https://doi.org/10.1007/s10286-025-01112-0)

> *In plain terms: heart rate variability — how much the spacing between heartbeats fluctuates — is
> consistently lower in these patients than in comparison groups, and it is the finding that turns up in
> the most independent papers. But it is also lower in Parkinson's, in COPD, and in depression, so a low
> value points at "something is wrong with autonomic regulation," not at POTS specifically.*

**Elevated norepinephrine is the most-supported molecular signal** — 176 papers by synonym merge, 270
findings, 135 in the elevated direction. Representative span: "Fifteen patients (78.9%) had elevated
upright norepinephrine >600 pg/mL." — Lamotte G et al. (2021) *Hypertension*, cohort.
[PubMed](https://pubmed.ncbi.nlm.nih.gov/34739766/) ·
[DOI](https://doi.org/10.1161/HYPERTENSIONAHA.121.17805). Note the direction is contested at the top of
the contradictions table (§3): 60 papers report elevated, 41 reduced, under a broad `dysautonomia` label.

> *In plain terms: norepinephrine — the "fight or flight" chemical — is reported as elevated on standing
> in many of these studies, more than any other molecule in the corpus. Some studies find it lowered
> instead, and section 3 explains why those two results may not actually disagree.*

**Ganglionic AChR autoantibody is the clearest example of a marker whose literature is genuinely split.**
36 papers, 66 findings, 35 distinct last authors, no meta-analysis or RCT rows. Positive-detection and
no-difference results sit side by side, and the negative ones are large:

- "Fifteen of 217 patients with POTS (7%) had gAChR antibodies (8 very low and 7 low). Six of the 77
  healthy controls (8%) were positive." — Bryarly M et al. (2021) *Neurology Clinical Practice*,
  case-control, n=294. [PubMed](https://pubmed.ncbi.nlm.nih.gov/34484936/) ·
  [DOI](https://doi.org/10.1212/cpj.0000000000001047)
- "In the overall cohort, 77 patients were tested for serum gAChR antibodies. Zero were found to have
  elevated antibody levels." — Zhang R et al. (2022) *Cureus*, cohort, n=356.
  [PubMed](https://pubmed.ncbi.nlm.nih.gov/36349067/) · [DOI](https://doi.org/10.7759/cureus.31021)

> *In plain terms: an antibody that has been proposed as an autoimmune marker for POTS is found at
> nearly the same rate in patients and healthy controls in one study, and in nobody at all in another.
> The corpus records both the positive and the negative reports rather than only the positive ones.*

*Traceable to: `tier1_findings_canonical.parquet` (columns `canonical_entity`, `split_derived`,
`evidence_tier`, `direction`, `provenance_quote`), `paper_metadata.parquet`, `canonicalization_report.md` §4–5.*

---

## 3. Contradictions worth investigating

**532 contradiction records**: 268 hard direction flips (one set of papers says elevated, another says
reduced) and 264 null-vs-positive conflicts (one set finds an effect, another finds none). Ranked by
combined evidence weight, not by count.

### The 127 with a visible moderator are the interesting ones

A "visible moderator" means the two sides of the conflict differ systematically on a recorded covariate —
so the disagreement may be **subtype structure, not noise.** 127 of 532 records carry one.

**Read this first: 61 of those 127 involve `fulltext_status`, which is an extraction artifact, not
biology.** It means one side was read from full text and the other from an abstract only. That is a
property of what the pipeline could retrieve, and it must never be interpreted as a patient difference.
**73 of the 127 have at least one moderator that is not purely `fulltext_status`** — those are the ones
worth a researcher's attention. Moderator frequencies across the 127: `fulltext_status` 61,
`population_age_group` 36, `sex_hormonal` 21, `is_covid_associated` 17, `pots_subtype` 4.

**Candidate subtype structure — highest-weight examples:**

| Entity | Condition | Conflict | Side A | Side B | Moderator split |
|---|---|---|---|---|---|
| midodrine | dysautonomia | hard flip | elevated, 21 papers (meta-analysis) | reduced, 5 papers (RCT) | female-specific vs male-specific |
| mean arterial pressure | dysautonomia | hard flip | elevated, 9 | reduced, 10 | female-specific vs male-specific |
| epinephrine | dysautonomia | hard flip | elevated, 12 | reduced, 8 | hormonal-axis / male-specific vs sex-difference-reported |
| **gAChR autoantibody** | **POTS** | null-vs-positive | effect, 8 papers | no difference, 4 papers | **immune-related vs neurogenic subtype** |
| **midodrine** | **POTS** | null-vs-positive | effect, 7 papers | no difference, 5 papers | **neurogenic vs hyperadrenergic subtype** |
| renin | POTS | null-vs-positive | effect, 11 | no difference, 1 | adult vs pediatric |
| flow-mediated dilation | POTS | hard flip | elevated, 3 | reduced, 2 | pediatric vs adult |
| HF power | POTS | hard flip | elevated, 1 | reduced, 3 | pediatric vs adult |
| SDNN | POTS | hard flip | elevated, 2 | reduced, 2 | pediatric vs adult |
| peak oxygen uptake | POTS | null-vs-positive | effect, 3 | no difference, 1 | mixed/pediatric vs adult |

The two `pots_subtype` rows are the cleanest hypotheses in the whole table: **whether midodrine works and
whether the gAChR autoantibody is detectable both split along recorded POTS subtype boundaries** — the
positive midodrine papers are labeled neurogenic, the null ones hyperadrenergic; the antibody-positive
papers immune-related, the null ones neurogenic. That is a testable prestratification hypothesis for a
trial design, and it is generated here from 12 and 11 papers respectively, not from one lab's opinion.

The pediatric-vs-adult cluster in HRV metrics (HF power, SDNN, flow-mediated dilation, peak oxygen
uptake) is a second coherent pattern: in each case the pediatric papers report the opposite direction from
the adult papers. Paper counts are small (2–5 per side) — this is a signal to check, not a result.

> *In plain terms: sometimes two studies "disagree" because they studied different kinds of patients.
> Here, studies finding that midodrine helps mostly studied one POTS subtype, and studies finding it
> doesn't mostly studied another — and adult and paediatric studies flip direction on several
> heart-rhythm measures. That is a clue about who a treatment works for, not proof that either study
> was wrong.*

### The large caveat on the other 405

**376 of the 532 contradictions sit under an umbrella condition label** (`dysautonomia`, `general`,
`multiple`). Opposing directions there may reflect **pooled distinct diseases rather than a replication
failure** — the corpus's own `heterogeneity_caveat` column says so on every affected row. The top of the
ranked list is dominated by exactly these: heart rate (95 papers), orthostatic hypotension (79),
norepinephrine (94), heart rate variability (114). Those are not scandals; they are the arithmetic
consequence of labeling diabetic autonomic neuropathy, Parkinson's dysautonomia, and POTS with the same
umbrella term. Treat them as a call to stratify, not as evidence of a broken field.

*Traceable to: `contradictions.parquet` (columns `conflict_type`, `has_visible_moderator`,
`moderator_candidates`, `moderator_detail`, `broad_condition_flag`, `heterogeneity_caveat`, `pmids_A/B`).*

---

## 4. Under-studied signals — a hypothesis-generation list, nothing more

329 candidate under-studied signals were scored. This section uses only the **198** that clear two
filters: **≥2 distinct last authors** (so it is not one group citing itself) and **not case-report-only**.
All 198 are `map_confidence='high'`. Median support is **3 papers** (range 2–13) — by construction these
are thin. 30 of the 198 have at least one RCT or meta-analysis-tier paper behind them; the rest are
cohort (94), cross-sectional (26), case-control (24), or mechanistic (21) at best.

**This is a list of things to replicate, not a list of things that are true.** Thin evidence includes
noise, single-lab artifacts, and findings that will not survive a second look. Nothing in it is
actionable for anyone's care.

| Signal | Kind | Condition | Direction | Papers | Distinct last authors | Best tier | Years |
|---|---|---|---|---:|---:|---|---|
| REM sleep behavior disorder | clinical sign | dysautonomia | elevated | 6 | 6 | meta-analysis | 2024–2026 |
| deceleration capacity | physiological | dysautonomia | reduced | 5 | 5 | cohort | 2022–2026 |
| 25-hydroxyvitamin D | molecule | dysautonomia | reduced | 5 | 5 | cohort | 2023–2025 |
| diuretic exposure | drug | dysautonomia | elevated | 4 | 4 | case-control | 2023–2026 |
| syncope | clinical sign | dysautonomia | elevated | 3 | 3 | cohort | 2025–2026 |
| empagliflozin | drug | dysautonomia | elevated | 3 | 3 | RCT | 2022–2025 |
| stroke volume index | physiological | POTS | reduced | 3 | 3 | cohort | 2021–2024 |
| joint hypermobility | clinical sign | EDS/hypermobility | elevated | 3 | 3 | cohort | 2024–2026 |
| systemic immune-inflammation index | physiological | general | elevated | 3 | 3 | cohort | 2024–2026 |
| incobotulinumtoxinA | drug | dysautonomia | reduced | 2 | 2 | RCT | 2023–2024 |
| trimethylamine N-oxide | molecule | general | elevated | 2 | 2 | cohort | 2025–2026 |
| indoxyl sulfate | molecule | general | elevated | 2 | 2 | cohort | 2025–2026 |
| SLC18A3 | gene/protein | dysautonomia | reduced | 2 | 2 | cohort | 2024–2025 |
| L-serine | molecule | small-fiber neuropathy | reduced | 2 | 2 | RCT | 2024–2025 |
| postural sway | physiological | dysautonomia | elevated | 2 | 2 | cohort | 2024–2026 |
| QTc dispersion | physiological | POTS | elevated | 2 | 2 | cohort | 2023–2025 |
| abdominal compression garment | other | POTS | reduced | 2 | 2 | cohort | 2026 |
| LAMP1 | gene/protein | dysautonomia | elevated | 2 | 2 | mechanistic | 2025 |

Composition of the 198: molecule-or-analyte 66, physiological-measure 41, clinical-sign 37, drug 23,
gene/protein 18, other 13.

Three that look most worth a replication attempt, and why:

1. **REM sleep behavior disorder ↔ dysautonomia**, 6 papers from 6 different last authors, meta-analysis
   tier available, all 2024–2026, 100% direction agreement. Six independent groups converging in three
   years on a prodromal-synucleinopathy link is the strongest thin signal in the list. E.g. Meng Y et al.
   (2024) *Medicine* [PubMed](https://pubmed.ncbi.nlm.nih.gov/38728450/) ·
   [DOI](https://doi.org/10.1097/MD.0000000000038169)
2. **Deceleration capacity reduced**, 5 papers, 5 last authors, 2022–2026. An HRV-adjacent metric with
   independent support that almost nobody in the POTS literature uses. E.g. Scala I et al. (2022)
   *J Clin Med* [PubMed](https://pubmed.ncbi.nlm.nih.gov/35807167/) ·
   [DOI](https://doi.org/10.3390/jcm11133883)
3. **Gut-derived metabolites** — trimethylamine N-oxide and indoxyl sulfate, 2 papers each, both
   2025–2026, both elevated. Too thin to believe, recent enough and mechanistically coherent enough to
   test. E.g. Brar AS et al. (2025) *World J Cardiol* [PubMed](https://pubmed.ncbi.nlm.nih.gov/40575430/) ·
   [DOI](https://doi.org/10.4330/wjc.v17.i6.107386)

> *In plain terms: these are measurements that a few separate research groups have found something
> interesting about, but that almost nobody has followed up. They are suggestions for what to study next.
> Two or three papers is not enough to know whether any of them is real, and none of them should change
> anyone's treatment.*

*Traceable to: `understudied_signals.parquet` (columns `n_papers`, `n_distinct_last_authors`,
`case_report_only`, `headline_eligible`, `best_tier`, `direction_agreement`, `supporting_pmids`).*

---

## 5. What has failed — the negative-evidence layer

**5,324 null or failed results across 1,996 papers**: 3,076 biomarker/mechanism nulls, 1,340
treatment/intervention failures, 908 diagnostic nulls. This layer exists because the thing that
publication bias hides is the thing a researcher most needs, and because a patient reading a
promising-sounding marker deserves to see the studies that found nothing.

### Start with the 315 RCT- and meta-analysis-tier treatment failures

**315 treatment-failure findings at RCT or meta-analysis tier, across 129 papers** (234 RCT-tier + 81
meta-analysis-tier). **Negative evidence at this tier is the most reliable content in the entire corpus** —
a well-powered randomized trial that finds nothing is a stronger statement than an observational study
that finds something.

| Intervention | RCT/meta-tier failure findings | Example |
|---|---:|---|
| nirmatrelvir/ritonavir | 11 | meta-analysis, long COVID / dysautonomia outcomes |
| pyridostigmine | 9 | RCT + meta-analysis |
| midodrine | 8 | RCT |
| antihypertensive therapy | 7 | RCT |
| vagus nerve stimulation | 7 | sham-controlled RCT, n=145 |
| IV immunoglobulin | 6 | placebo-controlled RCT in POTS, n=30 |
| fludrocortisone | 4 | RCT / review-level |
| atomoxetine, onabotulinumtoxinA, pregabalin | 4 each | RCT |

Named examples, each quote ≤200 characters with its citation adjacent:

- **IVIG in POTS, randomized, n=30:** "Change in COMPASS-31 did not differ between groups (median change
  [IQR]; IVIG: -5.5 [-23.3, 2.5] versus albumin: -10.6 [-14.1, -4.7]; p-value = 0.629)." — Vernino S et al.
  (2024) *Clinical Autonomic Research*. [PubMed](https://pubmed.ncbi.nlm.nih.gov/38311655/) ·
  [DOI](https://doi.org/10.1007/s10286-024-01020-9)
- **Pyridostigmine added to beta-blockade in POTS:** "adding pyridostigmine to these agents did not
  significantly improve symptom scores" — Pierson BC et al. (2024) *Frontiers in Neurology*, RCT tier.
  [PubMed](https://pubmed.ncbi.nlm.nih.gov/39882369/) ·
  [DOI](https://doi.org/10.3389/fneur.2024.1515486)
- **Vagus nerve stimulation, sham-controlled, n=145:** "None of the changes in secondary outcomes between
  treatment groups were significantly different." — Kufaishi H et al. (2024) *Diabetes Technology &
  Therapeutics*. [PubMed](https://pubmed.ncbi.nlm.nih.gov/39446990/) ·
  [DOI](https://doi.org/10.1089/dia.2024.0175)
- **Midodrine after spinal cord injury, randomized, n=15:** "significant increases in SBP and diastolic
  CBFv without appreciable effects on cognition after 30 days of midodrine administration" — Peters CG
  et al. (2024) *Topics in Spinal Cord Injury Rehabilitation*.
  [PubMed](https://pubmed.ncbi.nlm.nih.gov/39619823/) · [DOI](https://doi.org/10.46292/sci23-00038)
- **Midodrine for post-operative orthostatic intolerance, randomized, n=42:** "There was no statistically
  significant difference in the incidence of orthostatic intolerance between the groups 17.4% vs 31.6%
  (P = 0.45)." — Cammerman AC et al. (2025) *Anaesthesia and Intensive Care*.
  [PubMed](https://pubmed.ncbi.nlm.nih.gov/39921403/) ·
  [DOI](https://doi.org/10.1177/0310057x241290536)
- **Fludrocortisone evidence quality:** "A recent Cochrane review of several RCTs found limited evidence
  on the efficacy of fludrocortisone, with the quality of evidence being low/very low" — Grosu C et al.
  (2025) *J Clin Med*. [PubMed](https://pubmed.ncbi.nlm.nih.gov/39860637/) ·
  [DOI](https://doi.org/10.3390/jcm14020630)

Note carefully what this does **not** say. It does not say these drugs do not work, and it is not a
recommendation to stop any of them. Each row is one outcome in one trial in one population — midodrine
failing to change cognition after spinal cord injury says nothing about midodrine for standing blood
pressure in POTS, and the same drugs appear with positive findings elsewhere in the corpus (midodrine:
86 papers, 28 RCT-tier rows). What the layer gives you is the negative half of the record, at the tier
where negatives are trustworthy, with links.

> *In plain terms: for several treatments used in POTS and dysautonomia, the best-quality trials found
> no benefit on the outcome they measured. That is real information — it is usually much harder to find
> than the positive studies. It is not a reason to change a medication; each trial measured one specific
> thing in one specific group, and only a clinician who knows your situation can weigh it.*

### Biomarker and diagnostic nulls

**3,076 biomarker/mechanism nulls across 1,354 papers.** The most-nulled entities are the same ones that
top the positive leaderboard — heart rate (40 null findings), orthostatic hypotension (35),
norepinephrine (34), heart rate variability (28), LF/HF ratio (22), RMSSD (19). That symmetry is the
point: these measures are studied so much that they generate both the positive and the negative record,
and any honest reading has to include both.

**908 diagnostic nulls across 582 papers**, led by sympathetic skin response (11 findings) and the gAChR
autoantibody (9 findings across 8 papers). Two examples, both drawn from the diagnostic-null subset
(`null_class = 'diagnostic null'`):

- **Sympathetic skin response fails to separate patients from controls:** "SSR latency and amplitude
  values were not significantly different between pSS patients and healthy controls." — Eren Y et al.
  (2026) *Irish Journal of Medical Science*, case-control, n=97.
  [PubMed](https://pubmed.ncbi.nlm.nih.gov/41296195/) ·
  [DOI](https://doi.org/10.1007/s11845-025-04174-1)
- **gAChR antibody specificity does not hold up:** "we found no positivity in a sizeable SLE cohort or in
  heterogenous groups of non-AAG neurological disorders (Figure 3) contrary to other reports (9)."
  — Urriola N et al. (2021) *Frontiers in Immunology*, case-control.
  [PubMed](https://pubmed.ncbi.nlm.nih.gov/34249013/) ·
  [DOI](https://doi.org/10.3389/fimmu.2021.705292)

> *In plain terms: the tests most often proposed for diagnosing autonomic problems also have the most
> studies showing they don't reliably separate patients from non-patients. A test being popular is not
> the same as a test working.*

*Traceable to: `null_results.parquet` (columns `null_class`, `evidence_tier`, `negative_strength`,
`canonical_entity`, `treatment_class`, `provenance_quote_trunc`, `pubmed_url`, `doi_url`).*

---

## 6. Associations — and why the top of the list is boring on purpose

555 entity-pair associations were computed; 547 entered the primary analysis and **456 are significant at
BH-FDR q<0.05**.

**The highest-ranked pairs are reporting convention, not biology.** HF power ↔ LF power (26 shared papers,
lift 41.2, q=9.2e-42) co-occur because both are printed in the same HRV table. Fludrocortisone ↔ midodrine
(35 papers, lift 16.4) co-occur because they are co-prescribed and reviewed together. Diastolic ↔ systolic
BP (29 papers, lift 28.7), RMSSD ↔ SDNN (37 papers, lift 14.4), midodrine ↔ pyridostigmine (23 papers,
lift 14.5) — all the same phenomenon. Anyone presenting these as discoveries has misread their own table.

**The informative layer is the 101 cross-kind pairs**: significant at q<0.05, linking two *different*
entity kinds (gene↔drug, molecule↔gene, drug↔condition), and not explainable by one name being nested
inside the other or by shared surface strings.

| Pair | Kinds | Shared papers | Lift | q |
|---|---|---:|---:|---:|
| **tafamidis ↔ transthyretin** | drug ↔ gene | 5 | 83.7 | 2.1e-09 |
| **hemin ↔ HMBS** | drug ↔ gene | 3 | 408.0 | 7.3e-08 |
| **L-serine ↔ SPTLC1** | molecule ↔ gene | 4 | 145.1 | 1.5e-08 |
| 1-deoxysphingolipid ↔ SPTLC2 | molecule ↔ gene | 3 | 181.3 | 1.1e-06 |
| atropine ↔ muscarinic M2 receptor autoantibody | drug ↔ molecule | 3 | 272.0 | 2.9e-07 |
| CCL5 ↔ IL-21 | gene ↔ molecule | 3 | 544.0 | 2.3e-08 |
| NMDA receptor autoantibody ↔ ovarian teratoma | molecule ↔ condition | 3 | 133.2 | 2.9e-06 |
| ELP1 ↔ kinetin | gene ↔ molecule | 4 | 41.8 | 1.3e-06 |
| blood volume ↔ sodium | physiological ↔ molecule | 3 | 43.5 | 7.3e-05 |
| LRRK2 ↔ neurofilament light chain | gene ↔ molecule | 3 | 28.3 | 2.4e-04 |
| diabetes duration ↔ diabetic autonomic neuropathy | other ↔ condition | 3 | 103.6 | 6.0e-06 |

**The first three are the validation signal, and they matter more than any novel pair.** Tafamidis is a
transthyretin stabilizer. Hemin treats acute porphyria, which is caused by HMBS deficiency. L-serine is
the therapeutic substrate strategy for SPTLC1-mutant HSAN1. The pipeline was told nothing about
pharmacology; it recovered three correct drug–target relationships from co-occurrence in extracted text
alone. **A method that cannot recover known biology should not be trusted with unknown biology** — this
is the check that says the association layer is measuring something real.

Note also the reverse-direction check this passes: 51 low-confidence entity mappings exist in the
vocabulary, and the association layer flags `map_confidence_a` / `map_confidence_b` on every row, so a
skeptical reader can drop pairs resting on a shaky mapping.

> *In plain terms: the strongest "connections" in the data are mostly just measurements that get reported
> in the same table as each other — not biology. But buried in the list, the method independently
> rediscovered three real drug–gene relationships it was never told about, which is a good sign that the
> connections it finds are not random.*

*Traceable to: `association_table.parquet` (columns `entity_kind_a/b`, `n_papers_both`, `lift`, `q_bh`,
`significant_fdr05`, `trivial_component_link`, `name_level_nested`, `surface_string_linked`,
`included_in_primary`).*

---

## 7. Convergence — what Tier 1 can and cannot say

308 convergence records were computed: entities reported in a concordant direction across more than one
condition. **106 clear the bar of ≥2 non-POTS supporting papers; 45 are headline-eligible.**

Headline-eligible examples: COMPASS-31 elevated across 6 conditions (15 papers) · antinuclear antibody
elevated across 5 (17 papers) · intraepidermal nerve fiber density reduced across POTS, fibromyalgia and
small-fiber neuropathy (10 papers, 9 of them non-POTS) · total HRV power reduced across ME/CFS, POTS,
dysautonomia and fibromyalgia (11 papers) · β2-adrenergic receptor autoantibody elevated across ME/CFS,
POTS, dysautonomia and long COVID (7 papers) · endothelin-1 elevated across ME/CFS, dysautonomia and
long COVID (6 papers) · GPCR autoantibody elevated across POTS, dysautonomia and long COVID (8 papers).

**And now the honest part.** Every one of those "non-POTS" papers is a POTS/dysautonomia paper that
mentioned another condition. The corpus says so on every row (`scope_warning`): non-POTS support is
incidental mention within POTS/dysautonomia papers; true cross-condition convergence requires Tier 2–4
extraction. So:

- **What Tier 1 can say:** these entities are reported in a consistent direction whenever
  POTS/dysautonomia researchers looked across condition boundaries, and the convergence machinery works.
- **What Tier 1 cannot say:** that any mechanism is genuinely shared between POTS and ME/CFS,
  fibromyalgia, EDS, MCAS, IBS, migraine, or autism. That comparison requires each condition's own
  literature, and none of it is extracted yet.

The cross-condition question this project exists to answer is **not answerable from Tier 1**, and any
presentation implying otherwise would be wrong.

> *In plain terms: a handful of markers look like they behave the same way across several of these
> conditions — but so far we have only read the POTS research, and those other conditions only appear
> when a POTS paper mentioned them in passing. Until the ME/CFS, fibromyalgia and EDS literatures are
> read directly, "shared mechanism" remains a hypothesis, not a finding.*

*Traceable to: `convergence_tier1.parquet` (columns `n_conditions`, `n_papers_pots_dysautonomia`,
`n_papers_other_condition`, `passes_nonpots_bar`, `headline_eligible`, `scope_warning`).*

---

## 8. Limitations, and what would change the picture

**Limitations, stated plainly:**

1. **Scope.** POTS/dysautonomia only, ~3,121 of ~14,263 corpus papers. Not a cross-condition resource.
2. **Automated extraction has errors.** Direction, tier, and certainty labels are model judgments over
   source text. 51 low-confidence and 240 medium-confidence entity string mappings exist; filter on
   `map_confidence` before any quantitative use.
3. **Entity coverage is 29.8%, not "most of the table."** 17,152 rows (47.6% of the 36,067 pre-split
   rows) name no entity at all; a further 8,449 name one that got no canonical mapping. `canonical_entity`
   is populated on 10,858 rows across 2,185 of 3,121 papers. Entity counts are counts over those rows only
   — never imply full coverage.
4. **Co-occurrence is not causation.** 23,193 findings are labeled correlational-only; 4,373 carry an
   author causal claim. Associations in §6 are statistical co-occurrence in text.
5. **Thin evidence contains noise.** The §4 list is a hypothesis generator; 2–3 papers can be one lab's
   artifact, and the filters (≥2 last authors, no case-report-only) reduce but do not remove that.
6. **Contradictions may be pooling artifacts.** 376 of 532 sit under umbrella condition labels;
   61 of the 127 moderator signals are `fulltext_status`, an extraction artifact, not biology.
7. **Evidence tier is bottom-heavy.** 877 RCT-tier and 840 meta-analysis-tier findings out of 36,459.
8. **Publication window.** 2019–2026, median publication year 2025. Older foundational work is
   under-represented; 1,763 of 3,129 paper records are open access.
9. **Provenance quotes are copyrighted source text.** They are truncated to ≤200 characters and always
   shown adjacent to the full citation and link. There is no bulk quote export, by design.
10. **Duplicate collapse was validated, not applied blindly — and title-only matching would have been
    wrong.** 9 duplicate-title groups (18 PMIDs, 179 findings) were examined. 8 were merged: 5
    preprint→published pairs, 1 guideline co-published simultaneously in two journals, 1 single-page
    companion/correction, 1 erratum stub — folding 8 PMIDs into their canonical record and reattributing
    53 findings, with nothing deleted. **1 group was deliberately not merged.** "Post-COVID-19 Postural
    Orthostatic Tachycardia Syndrome" is a generic title shared by two genuinely distinct papers with
    fully disjoint author lists (`author_jaccard = 0.0`): Ishibashi Y et al. (2021) *Internal Medicine*
    [PubMed](https://pubmed.ncbi.nlm.nih.gov/34053992/) ·
    [DOI](https://doi.org/10.2169/internalmedicine.7626-21) and Savytskyi IV et al. (2022) *Cardiology
    Journal* [PubMed](https://pubmed.ncbi.nlm.nih.gov/35470419/) ·
    [DOI](https://doi.org/10.5603/cj.a2022.0021). Merging on title alone would have destroyed a real
    independent replication. All 9 groups are recorded in `pmid_dedup_map.parquet` with a
    `merge_applied` flag and a `merged_reason`, so the decision on each is auditable and reversible.

**What would change the picture, in priority order:**

1. **Tier 2 extraction — 7,243 papers covering ME/CFS, MCAS, EDS, fibromyalgia, IBS, small-fiber
   neuropathy and gastroparesis. This is the single highest-value next step,** and it is the only thing
   that converts §7 from a method demonstration into an answer to the project's actual question.
   Projected at Tier-1 measured rates (82% of papers yield findings, ~11.5 findings per yielding paper),
   the full corpus lands near ~135,000 findings, roughly 3.8× the current table.
2. **Human adjudication of the 127 moderator-bearing contradictions**, starting with the two
   `pots_subtype` rows. Small, cheap, and directly generates trial-design hypotheses.
3. **Review of the 291 low- and medium-confidence entity mappings**, which is what would let entity
   counts be quoted without a confidence filter.
4. **Replication attempts on the top of the §4 list** — REM sleep behavior disorder, deceleration
   capacity, gut-derived metabolites — where 5–6 independent groups already agree but nobody has
   consolidated.

---

### Provenance and reuse

All numbers in this document were computed from: `tier1_findings_canonical.parquet` (36,459 × 80),
`entity_vocabulary.parquet` (2,019), `paper_metadata.parquet` (3,129 records → 3,121 distinct papers,
99.9% with authors, 100% with a DOI or PubMed link), `pmid_dedup_map.parquet` (9 groups examined, 8
merged, 1 rejected),
`association_table.parquet` (555), `understudied_signals.parquet` (329), `contradictions.parquet` (532),
`null_results.parquet` (5,324), `convergence_tier1.parquet` (308), plus `canonicalization_report.md`,
`tier1_validation_report.md`, and `PRE_TIER2_AUDIT.md`.

Quoted spans are verbatim text from the cited papers, truncated to ≤200 characters and reproduced only
alongside the full citation and link. Please cite the original papers, not this document, for any finding
you use. And again: **this is machine-extracted research information, not medical advice.**
