# Canonicalization of the Tier-1 POTS/Dysautonomia Entity Vocabulary

> **Archived: Tier 1 (July 2026).** This document describes the first release (36,459 findings from 3,121 papers).
> The current data is v1.2: 148,186 findings from 11,519 papers in five packages with Zenodo DOIs. See the
> repository [README](../README.md) ("Download and cite"), each package's own docs, and the plain-language guide at
> https://pots.erinmagennis.com/start.

**Vocabulary version:** v1 · **Source table:** `tier1_findings.parquet` (36,067 rows x 70 cols)

## 1. Model provenance (per standing policy)

All biomedical judgment in this vocabulary was produced by **Sonnet-class or stronger** models. **No
haiku-class output survives in any saved artifact.**

| Stage | Producer | Strings |
|---|---|---|
| Compound-split decisions (head) | `claude-sonnet-5` | 1,086 |
| Canonical mapping, highest-risk head strings | `claude-sonnet-5` (adjudication pass) | 261 |
| Canonical mapping, remaining head strings | `claude-opus-5` (direct in-context curation) | 830 |
| Tail resolution + phantom/HRV corrections | deterministic alias rules over the curated vocabulary, plus `claude-opus-5` | 917 |

An initial exploratory pass used `claude-haiku-4-5`. Those `canonical_name`/`entity_kind` results were
**discarded**; every row's producer is recorded in `map_source` (`sonnet-adjudicated`, `curated-opus`,
`alias-rule`, `manual-curated`, `compound-split-only`). No value is `haiku`.

One implementation note, stated plainly because it changed the method: partway through, the per-frame
`host.llm` token ceiling (2.0M) was exhausted, and delegation was unavailable in this frame. The platform's
suggested fallback was a haiku-class model, which the standing policy forbids. Rather than downgrade the
model, the remaining 830 head strings were curated directly in context by `claude-opus-5` — stronger than
Sonnet, and consuming no `host.llm` budget. The tail was then resolved by **deterministic alias rules**
(qualifier stripping, parenthetical-alias matching) against that curated vocabulary, so tail rows inherit a
Sonnet-or-stronger judgment rather than a weaker model's guess. Rule-resolved rows are marked
`map_source='alias-rule'`.

## 2. Scope

The supplied head (1,086 strings) covers 9,457 of 18,915 entity-bearing rows (50.0%) and every string
appearing in >=3 papers. The head alone is **not sufficient** for the validation targets: 8 of the 14
norepinephrine synonyms and most multi-analyte strings live in the tail. Mapping was therefore extended to
the full universe of 9,582 distinct normalized strings; **1,803 strings** carry a
canonical mapping, resolving to **863 distinct canonical entities**.

## 3. Compound splitting

**216 strings** were judged genuinely compound (26 in the head,
190 in the tail) and expanded into component entities. Head decisions came from
`claude-sonnet-5`; tail splits required that **every** component resolve to the already-curated vocabulary,
so no split invents an entity.

Separator-containing strings correctly **kept whole**: `lf/hf ratio`, `nirmatrelvir/ritonavir`,
`levodopa/carbidopa intestinal gel`, `3,4-dihydroxyphenylglycol`,
`norepinephrine transporter (net/slc6a2)`, `serotonin transporter (sert/slc6a4)`, `cd26/dpp-4 (soluble)`,
`alpha/beta ratio (eeg)`, `smad1/5/8`, `lactulose/mannitol ratio`, `cd4/cd8 ratio`.

The reasoning model also **rejected three splits** an earlier cheaper pass had proposed — `smad1/5/8`
(one gene family designation), `lying and standing heart rate` (one analyte, two postures), and
`sympathetic blockade (prazosin + atenolol)` (one intervention) — and caught one it had missed
(`postural systolic/diastolic bp change`). This is the concrete accuracy difference the model upgrade bought.

## 4. Validation

### 4.1 No canonical group spans conflicting entity_kind — PASS

**0 conflicts** across 863 canonical groups. Three conflicts
found mid-build were resolved by weighted vote (`α3-nachr antibody`, the gACHR autoantibody family, and
`beta-2 adrenergic receptor autoantibody`).

### 4.2 Type-discipline tripwires — PASS

| Concept | canonical_name | entity_kind | papers |
|---|---|---|---|
| the catecholamine | `norepinephrine` | molecule-or-analyte | 177 |
| the transporter gene/protein | `slc6a2` | gene-or-protein | 17 |
| the antidepressant class | `snri` | drug-or-drug-class | 5 |

Distinct-measure pairs verified separate: SBP != DBP != MAP; heart rate != heart rate variability;
SDNN != RMSSD != PNN50 != LF power != HF power != LF/HF ratio; POTS != orthostatic intolerance !=
orthostatic hypotension.

One inconsistency was caught and fixed during spot-checking: strings like `heart rate variability (hf power)`
were being routed to the umbrella `heart rate variability` while `heart rate variability (sdnn)` went to
`sdnn`. Five such strings now route to their specific named metric; genuinely multi-metric strings
(e.g. `heart rate variability (lf, hf, lf/hf ratio)`) correctly stay on the umbrella concept.

### 4.3 Norepinephrine count correction — PASS (176 target hit exactly)

| Counting method | Papers | Verdict |
|---|---|---|
| Exact string `norepinephrine` only | **152** | undercount (fragmented) |
| Union of the 14 specified synonym strings | **176** | **target — reproduced exactly** |
| Canonical `norepinephrine`, direct strings | **177** | +1 vs target, documented below |
| Every norepinephrine/noradrenaline string | **232** | wrong — pools gene + drug class |

**Documented judgment calls on the +1:**

1. `norepinephrine (β-adrenergic signaling)` (1 row, 1 paper) is folded in, giving 177 rather than 176.
   Its finding text begins "Elevated norepinephrine after SCI inhibits maturation ... of Th1 cells" — the
   measured entity is the molecule; the parenthetical names the downstream receptor mechanism. Merging is
   correct on the evidence. Excluding it reproduces 176 exactly.
2. `norepinephrine (csf/plasma)` **is** merged (sampling-site qualifier only, retained in
   `entity_qualifier`) — consistent with the supplied 14-string set.
3. `norepinephrine (ne), orthostatic plasma` is treated as **one atomic string** with an internal comma,
   never split. An earlier build created a spurious bare `orthostatic plasma` bucket; it was removed, and no
   such string exists in the data (verified: 0 rows).
4. Splitting compound strings surfaces **18 additional papers** that
   mention norepinephrine only inside a multi-analyte phrase (195 total). This is a real
   but methodologically distinct signal, so it is **reported separately** (`papers` vs `papers_direct`)
   and never folded into the synonym-merge metric.

### 4.4 Row conservation — PASS

36,067 rows -> **36,459** (growth by duplication only). Distinct `finding_text`
values: 36,032 before and after — **0 lost**. The 17,152 null-entity rows (47.6%) are retained
with null canonical.

## 5. Count corrections, top 30 canonical entities

`papers_before` = best single exact string; `papers_direct` = synonym merge only; `papers` = including
split-derived rows.

**`delta` is scoped to the synonym merge: `delta = papers_direct - papers_before`, NOT
`papers - papers_before`.** It deliberately excludes split-derived gains, because merging true synonyms and
splitting compound strings are separate corrections that should not be reported as one number. A reader
wanting the full change including split-derived rows should compute `papers - papers_before` directly
(e.g. norepinephrine: 195 - 152 = +43, of which +25 is synonym merge and +18 is compound splitting).

| canonical_entity | kind | n_strings | papers_before | papers_direct | papers | delta (synonym-only) |
|---|---|---|---|---|---|---|
| norepinephrine | molecule-or-analyte | 16 | 152 | 177 | 195 | +25 |
| heart rate | physiological-measure | 41 | 124 | 168 | 178 | +44 |
| heart rate variability | physiological-measure | 77 | 100 | 168 | 170 | +68 |
| orthostatic hypotension | clinical-sign-or-condition | 16 | 105 | 115 | 115 | +10 |
| midodrine | drug-or-drug-class | 1 | 86 | 86 | 95 | +0 |
| sdnn | physiological-measure | 19 | 38 | 80 | 94 | +42 |
| rmssd | physiological-measure | 18 | 33 | 70 | 84 | +37 |
| lf/hf ratio | physiological-measure | 15 | 60 | 78 | 81 | +18 |
| snca | gene-or-protein | 17 | 66 | 77 | 77 | +11 |
| il-6 | molecule-or-analyte | 4 | 28 | 51 | 75 | +23 |
| ivabradine | drug-or-drug-class | 1 | 61 | 61 | 63 | +0 |
| systolic blood pressure | physiological-measure | 7 | 45 | 55 | 62 | +10 |
| intravenous immunoglobulin | drug-or-drug-class | 2 | 33 | 62 | 62 | +29 |
| fludrocortisone | drug-or-drug-class | 1 | 54 | 54 | 61 | +0 |
| elp1 | gene-or-protein | 8 | 50 | 57 | 58 | +7 |
| blood pressure | physiological-measure | 16 | 38 | 51 | 57 | +13 |
| tnf-alpha | molecule-or-analyte | 4 | 24 | 33 | 54 | +9 |
| hf power | physiological-measure | 25 | 9 | 49 | 52 | +40 |
| c-reactive protein | molecule-or-analyte | 3 | 33 | 37 | 46 | +4 |
| diastolic blood pressure | physiological-measure | 6 | 34 | 40 | 45 | +6 |
| epinephrine | molecule-or-analyte | 4 | 20 | 31 | 43 | +11 |
| baroreflex sensitivity | physiological-measure | 13 | 21 | 43 | 43 | +22 |
| age | other | 2 | 37 | 38 | 42 | +1 |
| pyridostigmine | drug-or-drug-class | 1 | 40 | 40 | 42 | +0 |
| cortisol | molecule-or-analyte | 4 | 32 | 36 | 41 | +4 |
| ace2 | gene-or-protein | 1 | 40 | 40 | 41 | +0 |
| propranolol | drug-or-drug-class | 1 | 35 | 35 | 37 | +0 |
| ganglionic acetylcholine receptor autoantibody | molecule-or-analyte | 14 | 19 | 36 | 36 | +17 |
| lf power | physiological-measure | 16 | 8 | 28 | 34 | +20 |
| hemoglobin a1c | molecule-or-analyte | 4 | 16 | 32 | 33 | +16 |

Fragmentation is worst for HRV metrics: **HF power went from 9 papers to 49** on synonym merge alone (25
surface strings), SDNN 38 -> 80, RMSSD 33 -> 70, LF power 8 -> 28. Exact-string counting was undercounting
these by 2-5x — a bigger distortion than the norepinephrine case that motivated this work.

## 6. Ten largest merges (spot-check)

**heart rate variability** (77 strings, kind `physiological-measure`)

- `24-hour hrv`
- `heart rate variability`
- `heart rate variability (autonomic nervous system activity)`
- `heart rate variability (avnn)`
- `heart rate variability (composite)`
- `heart rate variability (composite: sdnn, sdnn index, pnn50, rmssd, sdann, triangular index)`
- `heart rate variability (deep breathing)`
- `heart rate variability (elite hrv, sdnn, rmssd)`
- `heart rate variability (entropy-based complexity measures)`
- `heart rate variability (frequency-domain: tp, vlf, lf, hf, lf/hf)`
- `heart rate variability (hf band)`
- `heart rate variability (hf power, lf/hf ratio)`
- `heart rate variability (hf/lf power)`
- `heart rate variability (high-frequency power of r-r interval)`
- `heart rate variability (hrv)`
- `heart rate variability (hrv, composite of components)`
- `heart rate variability (hrv, general)`
- `heart rate variability (hrv-lf, hrv-hf, hrv-lf/hf ratio)`
- `heart rate variability (humoral/nervous regulatory activity)`
- `heart rate variability (lf and hf power)`
- _… +57 more_

**heart rate** (41 strings, kind `physiological-measure`)

- `baseline heart rate`
- `heart rate`
- `heart rate (24-hour ambulatory)`
- `heart rate (5 min standing)`
- `heart rate (acute)`
- `heart rate (bpm, 24h holter)`
- `heart rate (circadian pattern)`
- `heart rate (early vs late recording segments)`
- `heart rate (evening/night, no prior exercise)`
- `heart rate (hr)`
- `heart rate (max/min/mean, pre-hutt 24h holter)`
- `heart rate (maximum pulse rate, ppg-derived)`
- `heart rate (mean)`
- `heart rate (orthostatic response)`
- `heart rate (orthostatic)`
- `heart rate (post-exercise, >2h)`
- `heart rate (pulse rate, ppg-derived)`
- `heart rate (resting pulse rate, ppg-derived)`
- `heart rate (short-term hrv)`
- `heart rate (short-term hrv, resting supine)`
- _… +21 more_

**hf power** (25 strings, kind `physiological-measure`)

- `heart rate variability (hf power)`
- `heart rate variability (high frequency)`
- `hf power`
- `hf power (24h holter)`
- `hf power (abnormal value counts)`
- `hf power (absolute, ms2)`
- `hf power (heart rate variability)`
- `hf power (high-frequency hrv)`
- `hf power (high-frequency hrv, %)`
- `hf power (hrv)`
- `hf power (normalized units)`
- `hf power (peak high-frequency spectrum)`
- `hf power (pre-operative)`
- `hf power (δmean)`
- `high frequency (hf) power`
- `high frequency (hf) power (hrv)`
- `high-frequency (hf) power`
- `high-frequency (hf) power (hrv)`
- `high-frequency heart rate variability`
- `high-frequency heart rate variability (hf hrv)`
- _… +5 more_

**sdnn** (19 strings, kind `physiological-measure`)

- `heart rate variability (sdnn)`
- `nocturnal sdnn`
- `sdnn`
- `sdnn (24h holter)`
- `sdnn (dichotomized ≤100ms)`
- `sdnn (dichotomized ≤100ms, cox model)`
- `sdnn (heart rate variability time-domain indices)`
- `sdnn (heart rate variability)`
- `sdnn (heart rate variability, time-domain)`
- `sdnn (hrv time-domain measure)`
- `sdnn (hrv time-domain parameter)`
- `sdnn (hrv)`
- `sdnn (individual subject chf10)`
- `sdnn (standard deviation of n-n interval)`
- `sdnn (standard deviation of nn interval)`
- `sdnn (standard deviation of nn intervals)`
- `sdnn (standard deviation of normal-to-normal interval)`
- `sdnn (standard deviation of normal-to-normal intervals)`
- `standard deviation of nn intervals (sdnn)`

**rmssd** (18 strings, kind `physiological-measure`)

- `heart rate variability (rmssd)`
- `rmssd`
- `rmssd (24h holter)`
- `rmssd (heart rate variability index)`
- `rmssd (heart rate variability)`
- `rmssd (heart rate variability, time-domain)`
- `rmssd (heart rate variability, vagal tone index)`
- `rmssd (hrv mediators)`
- `rmssd (hrv time-domain measure)`
- `rmssd (hrv time-domain parameter)`
- `rmssd (hrv)`
- `rmssd (pre-operative)`
- `rmssd (root mean square of successive differences)`
- `rmssd (root mean square of successive rr interval differences)`
- `rmssd (root mean square successive difference of rr intervals)`
- `rmssd (short-term hrv)`
- `root mean square of successive differences (rmssd)`
- `standing rmssd`

**snca** (17 strings, kind `gene-or-protein`)

- `alpha-synuclein`
- `alpha-synuclein (arrector pili muscle, scalp skin)`
- `alpha-synuclein (myocardial)`
- `alpha-synuclein (neuron- and oligodendroglia-derived exosomes)`
- `alpha-synuclein (oligodendroglia-derived exosomes)`
- `alpha-synuclein (phosphorylated)`
- `alpha-synuclein (skin rt-quic)`
- `alpha-synuclein (snca)`
- `alpha-synuclein (α-syn)`
- `alpha-synuclein oligomers (pmca maximum tht fluorescence)`
- `alpha-synuclein seeds`
- `alpha-synuclein seeds (tht fluorescence kinetics)`
- `csf alpha-synuclein (total α-syn)`
- `oligomeric alpha-synuclein`
- `snca`
- `snca (a30p mutant human α-synuclein)`
- `snca (alpha-synuclein)`

**norepinephrine** (16 strings, kind `molecule-or-analyte`)

- `24-h urinary norepinephrine`
- `noradrenaline`
- `noradrenaline (na)`
- `noradrenaline (norepinephrine)`
- `norepinephrine`
- `norepinephrine (csf/plasma)`
- `norepinephrine (ne)`
- `norepinephrine (ne), orthostatic plasma`
- `norepinephrine (plasma)`
- `norepinephrine (plasma, baseline cohort)`
- `norepinephrine (β-adrenergic signaling)`
- `orthostatic plasma norepinephrine`
- `plasma noradrenaline`
- `plasma norepinephrine`
- `plasma norepinephrine (ne)`
- `urinary norepinephrine`

**orthostatic hypotension** (16 strings, kind `clinical-sign-or-condition`)

- `classical orthostatic hypotension`
- `orthostatic hypotension`
- `orthostatic hypotension (3-minute consensus)`
- `orthostatic hypotension (any oh)`
- `orthostatic hypotension (any oh, 30/60/90/120s)`
- `orthostatic hypotension (classic, coh)`
- `orthostatic hypotension (consensus-based)`
- `orthostatic hypotension (delayed, m5)`
- `orthostatic hypotension (delayed, m6)`
- `orthostatic hypotension (genome-wide snps)`
- `orthostatic hypotension (head-up tilt test)`
- `orthostatic hypotension (immediate, m1-m3)`
- `orthostatic hypotension (mean delayed, m4-m6)`
- `orthostatic hypotension (mean immediate, m1-m3)`
- `orthostatic hypotension (oh)`
- `postural hypotension`

**lf power** (16 strings, kind `physiological-measure`)

- `heart rate variability (lf power)`
- `lf power`
- `lf power (24h holter)`
- `lf power (absolute, ms2)`
- `lf power (heart rate variability)`
- `lf power (hrv frequency-domain)`
- `lf power (low-frequency hrv)`
- `lf power (low-frequency hrv, %)`
- `lf power (peak low-frequency spectrum)`
- `low frequency (lf) power`
- `low frequency (lf) power (hrv)`
- `low-frequency heart rate variability`
- `low-frequency heart rate variability (lf hrv)`
- `low-frequency heart rate variability (lf-hrv)`
- `low-frequency heart rate variability (resting)`
- `resting low-frequency heart rate variability (rest lf hrv)`

**blood pressure** (16 strings, kind `physiological-measure`)

- `blood pressure`
- `blood pressure (diastolic)`
- `blood pressure (diastolic, sitting)`
- `blood pressure (sbp, dbp, map)`
- `blood pressure (sbp, dbp, pulse pressure)`
- `blood pressure (sbp/dbp)`
- `blood pressure (symptomatic vs asymptomatic oh)`
- `blood pressure (systolic)`
- `blood pressure (systolic/diastolic)`
- `blood pressure (systolic/diastolic, standing)`
- `mean blood pressure`
- `mean blood pressure (adjusted mixed-effects model)`
- `nocturnal blood pressure`
- `orthostatic blood pressure`
- `sitting blood pressure`
- `supine mean blood pressure`

## 7. Ontology resolution

Resolved against live authorities only — **no model-invented identifiers**. Genes via MyGene/HGNC,
chemicals via ChEBI (EBI OLS4, exact-label match required), conditions via MeSH (NLM, exact token-set match
required, tolerating MeSH inversion). **368 of 863** canonical
entities carry an id; the rest are `ontology_status='unresolved'` rather than force-matched.

| entity_kind | canonical entities | with ontology id |
|---|---|---|
| clinical-sign-or-condition | 81 | 34 |
| drug-or-drug-class | 166 | 128 |
| gene-or-protein | 158 | 145 |
| molecule-or-analyte | 181 | 61 |
| other | 107 | 0 |
| physiological-measure | 170 | 0 |

Physiological measures are deliberately 0: HRV indices, orthostatic BP deltas, and questionnaire scores have
no genuine ChEBI/HGNC/MeSH descriptor, so forcing a match would be worse than leaving them unresolved.

## 8. Low-confidence mappings flagged for review

51 strings are `map_confidence='low'` and 240 are `medium`; filter on
`map_confidence` before using these downstream.

| entity_norm | canonical_name | entity_kind |
|---|---|---|
| `acceleration index` | acceleration index | physiological-measure |
| `acceleration index (ecg)` | acceleration index | physiological-measure |
| `adrenergic autoantibodies` | adrenergic receptor autoantibody | clinical-sign-or-condition |
| `ansindex` | ansindex | physiological-measure |
| `autonomic nervous system function` | autonomic nervous system function | physiological-measure |
| `delayed orthostatic bp recovery` | blood pressure recovery | physiological-measure |
| `blood volume deviation` | blood volume deviation | physiological-measure |
| `closure technique (surgical vs transcatheter)` | closure technique | other |
| `c7` | complement component c7 | molecule-or-analyte |
| `sdfa scaling exponent` | dfa scaling exponent | physiological-measure |
| `diurnal rhythm disruption (brian)` | diurnal rhythm disruption | clinical-sign-or-condition |
| `dst` | dst | gene-or-protein |
| `dst-b` | dst | gene-or-protein |
| `electrical risk score` | electrical risk score | physiological-measure |
| `elp1 mrna splicing` | elp1 mrna splicing | other |
| `fuligo plantae carbon dots (fp-cds)` | fuligo plantae carbon dots | other |
| `functional ability` | functional ability | physiological-measure |
| `gba` | gut-brain axis | other |
| `hrv` | heart rate variability | physiological-measure |
| `hrv (composite, low vs high)` | heart rate variability | physiological-measure |
| `hrv (hf power, nrem)` | heart rate variability | physiological-measure |
| `hrv (lf, hf)` | heart rate variability | physiological-measure |
| `hrv (lf, hf, sdnni, rmssd, pnn50)` | heart rate variability | physiological-measure |
| `hrv (preoperative)` | heart rate variability | physiological-measure |
| `hrv (reference, no-exercise holter)` | heart rate variability | physiological-measure |
| `hrv (sdnn, rmssd, hf power)` | heart rate variability | physiological-measure |
| `hrv (sdnn/rmssd)` | heart rate variability | physiological-measure |
| `hrv (short-term, 5-min)` | heart rate variability | physiological-measure |
| `hrv (time- and frequency-domain)` | heart rate variability | physiological-measure |
| `nocturnal hrv` | heart rate variability | physiological-measure |
| `overnight hrv` | heart rate variability | physiological-measure |
| `high-inflammation cluster (cluster 2)` | high-inflammation cluster | other |
| `hippocampal supply vessel signal intensity` | hippocampal supply vessel signal intensity | physiological-measure |
| `valacyclovir/celecoxib (imc-2)` | imc-2 | drug-or-drug-class |
| `impulse response (ir) metrics` | impulse response metrics | physiological-measure |
| `integrated stress response` | integrated stress response | other |
| `malnutrition` | malnutrition | clinical-sign-or-condition |
| `malnutrition (conut score)` | malnutrition | clinical-sign-or-condition |
| `malnutrition (glim)` | malnutrition | clinical-sign-or-condition |
| `malnutrition (pni/gnri-defined)` | malnutrition | clinical-sign-or-condition |
| `mean network connectivity (dysautonomic network)` | mean network connectivity | physiological-measure |
| `ormdl` | ormdl | gene-or-protein |
| `p75ntr/ngf complex` | p75ntr/ngf complex | other |
| `p75ntr/ngf complex (pdb 1sg1)` | p75ntr/ngf complex | other |
| `polyscore (7-parameter autonomic risk score)` | polyscore | physiological-measure |
| `ptc258` | ptc258 | drug-or-drug-class |
| `rectas` | rectas | other |
| `stoppfall medications (≥2 classes) combined with delayed bp recovery` | stoppfall medications with delayed blood pressure recovery | other |
| `stoppfall medications (≥2 classes) combined with any oh` | stoppfall medications with orthostatic hypotension | other |
| `tecpr2 (zebrafish)` | tecpr2 | gene-or-protein |
| `troponin` | troponin | molecule-or-analyte |

## 9. Artifacts and how Tiers 2-4 should extend this

**`entity_vocabulary.parquet`** (2,019 rows) — `entity_norm`, `canonical_name`, `entity_kind`,
`entity_qualifier`, `map_confidence`, `is_compound`, `components`, `rows`, `papers`, `in_head`,
`ontology_id`/`_label`/`_source`/`_status`, `map_source`, `vocab_version`.

**`tier1_findings_canonical.parquet`** (36,459 rows) — all 70 original columns with `entity`
**untouched**, plus `entity_norm_original`, `entity_component_string`, `canonical_entity`, `entity_kind`,
`entity_qualifier`, `split_derived`, `map_source`, `map_confidence`, `canonical_ontology_id`,
`canonical_ontology_source`. Every merge is auditable and reversible from `entity` alone.

**Extension protocol.** Do **not** recompute this vocabulary — recomputing shifts counts between releases.
Load it, left-join new strings, and map only the residue, appending rows with `vocab_version='v2'`.
Preserve existing `canonical_name` values even when a better term appears; add a synonym row instead.
When adding a string near an existing canonical, check `entity_kind` first — the molecule/gene/drug-class
separation is the invariant that makes these counts trustworthy.
