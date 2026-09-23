# RETROFIT REPORT — Tier 1–3 quote source re-fetch and traceability census

Generated 2026-09-16T07:40:23Z. Comparator: `quote_trace.py sha256:0a66bf6e1087` (pinned `migraine-hypermobility-findings/code/quote_trace.py`, imported unmodified; `comparator_symmetry_tests.py` 8/8 PASS; `selftest()` no failures).

## Deviations from task (read first)

- **No reduction of scope.** All 10,428 target pmids were attempted (10,428/10,428); all 6,239 papers with at least one `retrieved-fulltext` row had a full-text fetch attempted (6,239/6,239). No sampling, no capping, no substituted source.
- **Source-text composition (a choice, stated):** the full-text source for a row is `title + abstract + JATS body <p> text[:120,000 chars]`. The 120,000-char cap equals `FT_INPUT_CHAR_CAP` — the extraction model never saw body text beyond it, so text past the cap cannot be a legitimate quote source. Tables, figure captions and reference lists are excluded exactly as `parse_sections` excluded them at extraction time. The abstract-only source is Europe PMC `abstractText` alone, matching the shipped README census basis.
- **`isOpenAccess` was not required** for the full-text attempt (the original `fetch_fulltext` required it). Any paper with a PMCID was tried, because these papers had demonstrably yielded full text at extraction time. Result: 1 of 6,141 successful full-text fetches came from a record now flagged `isOpenAccess=N`.
- **Europe PMC text is the CURRENT version**, not the version fetched at extraction time (2025–2026). Records whose abstract/body were revised, embargoed or withdrawn since then appear as untraceable or as fetch failures; this is a floor on true fidelity, not a ceiling.
- **Fetched text is not shipped** (LICENSE: verbatim excerpts only). It lived only in the run workspace (`fetch_ckpt/`) and is deleted after the census. The per-paper fetch log and row-level census are the deliverables.
- The negative-control sample size is 400 per stratum where the stratum has ≥400 rows; the two small fallback strata (tier2b: 20 rows) report the control on all rows they have and are labelled as such.

## Fetch run

- Requests: **16,653** (10,428 `search` + 6,239 `fullTextXML` = 16,667 planned; 16653 actually issued — 14 full-text requests were not issued because the current record carries no PMCID).
- Wall time: **118.5 min** (2.34 req/s aggregate; pinned pacing 3 workers × 0.9 s; the rest is network latency). No HTTP 429/5xx surfaced after the pinned retry/backoff: all 10,428 `search` calls returned HTTP 200.
- Papers attempted 10,428/10,428; abstract obtained 10,097/10,428 (96.83%); full text obtained 6,141/6,239 (98.43%).
- Paper-level `retrofit_fetch_status`: ok 10,161, no_abstract 169, fulltext_failed 84, no_pmcid 14.
- Full-text failure causes (paper level, 98 papers): HTTP 404 on `fullTextXML` 80 (of which 77 now carry `isOpenAccess=N` — full text withdrawn from the OA subset since extraction); body parsed but < 2,000 chars 4; record no longer carries a PMCID 14 (all 14 now `isOpenAccess=N`).
- `no_abstract` 169: Europe PMC returned a record (HTTP 200) with empty `abstractText` — typically letters, errata, editorials.

## Verifiable rows: before (README, abstract-derived rows only) vs after retrofit

`verifiable` = the row's own source text exists and was re-read. Before: rows with `fulltext_status ∈ {abstract-only, blocked}` (README basis). After: rows with `retrofit_source_depth != none`.

| tier | rows | verifiable before | % (README) | verifiable after | % | traceable after (all verifiable) | % of verifiable | % of all rows |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| dysautonomia-core-findings | 36,067 | 6,536 | 18.12% (18.12%) | 35,949 | 99.67% | 33,393 | 92.89% | 92.59% |
| comorbid-conditions-findings-a | 36,611 | 7,713 | 21.07% (21.07%) | 36,547 | 99.83% | 35,498 | 97.13% | 96.96% |
| comorbid-conditions-findings-b | 33,830 | 6,560 | 19.39% (19.39%) | 33,778 | 99.85% | 32,709 | 96.84% | 96.69% |
| postviral-autism-findings | 26,032 | 3,182 | 12.22% (12.22%) | 26,021 | 99.96% | 25,441 | 97.77% | 97.73% |
| **Tiers 1–3** | 132,540 | 23,991 | 18.10% | 132,295 | 99.82% | 127,041 | 96.03% | 95.85% |

The 'all verifiable' traceable rate is pulled down by the **1,391 `retrieved-fulltext` rows whose body text could not be re-fetched and were therefore checked against the abstract only** (`retrofit_source_depth == abstract` with `fulltext_status == retrieved-fulltext`). Those rows trace at ≈0% because their quotes come from the body, not the abstract — a source-depth limitation, not evidence against the quote. Stratify on `retrofit_source_depth` × `fulltext_status` before reporting a fidelity rate.

## Traceable rate per depth stratum, with wrong-paper negative control (n_control=400, seed=11)

Decision = `quote_traceability(quote, source)[1]`. `exact` = element [0]. A control false-positive rate above ~1% would invalidate the stratum's rate; every stratum below reads 0.00%.

| tier | stratum | rows with quote | checked | traceable | untraceable | no source | traceable % | exact % | control n | control FP | control FP % |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| dysautonomia-core-findings | retrieved-fulltext rows vs re-fetched FULL TEXT | 29,531 | 28,113 | 27,390 | 723 | 1,418 | 97.43% | 92.29% | 400 | 0 | 0.0% |
| dysautonomia-core-findings | abstract-only + blocked rows vs re-fetched ABSTRACT | 6,536 | 6,465 | 6,001 | 464 | 71 | 92.82% | 89.48% | 400 | 0 | 0.0% |
| dysautonomia-core-findings | retrieved-fulltext rows lacking body, vs ABSTRACT (fallback) | 1,418 | 1,371 | 2 | 1,369 | 47 | 0.15% | 0.00% | 400 | 0 | 0.0% |
| comorbid-conditions-findings-a | retrieved-fulltext rows vs re-fetched FULL TEXT | 28,898 | 28,895 | 28,353 | 542 | 3 | 98.12% | 93.24% | 400 | 0 | 0.0% |
| comorbid-conditions-findings-a | abstract-only + blocked rows vs re-fetched ABSTRACT | 7,713 | 7,652 | 7,145 | 507 | 61 | 93.37% | 89.78% | 400 | 0 | 0.0% |
| comorbid-conditions-findings-a | retrieved-fulltext rows lacking body, vs ABSTRACT (fallback) | 3 | 0 | 0 | 0 | 3 | n/a | n/a | 0 | 0 | n/a |
| comorbid-conditions-findings-b | retrieved-fulltext rows vs re-fetched FULL TEXT | 27,270 | 27,250 | 26,739 | 511 | 20 | 98.12% | 94.11% | 400 | 0 | 0.0% |
| comorbid-conditions-findings-b | abstract-only + blocked rows vs re-fetched ABSTRACT | 6,560 | 6,508 | 5,970 | 538 | 52 | 91.73% | 87.95% | 400 | 0 | 0.0% |
| comorbid-conditions-findings-b | retrieved-fulltext rows lacking body, vs ABSTRACT (fallback) | 20 | 20 | 0 | 20 | 0 | 0.0% | 0.00% | 20 | 0 | 0.0% |
| postviral-autism-findings | retrieved-fulltext rows vs re-fetched FULL TEXT | 22,850 | 22,850 | 22,402 | 448 | 0 | 98.04% | 93.51% | 400 | 0 | 0.0% |
| postviral-autism-findings | abstract-only + blocked rows vs re-fetched ABSTRACT | 3,182 | 3,171 | 3,039 | 132 | 11 | 95.84% | 94.13% | 400 | 0 | 0.0% |
| postviral-autism-findings | retrieved-fulltext rows lacking body, vs ABSTRACT (fallback) | 0 | 0 | 0 | 0 | 0 | n/a | n/a | 0 | 0 | n/a |

Corpus-wide (Tiers 1–3), full-text depth: **104,884 / 107,108 = 97.92%** of `retrieved-fulltext` rows re-fetched at full-text depth trace to their paper's own body text; the 97-paper pilot read 98.65%.

## Abstract-ONLY census of the same rows (README-comparable, before/after on one instrument)

Every quote row checked against the re-fetched abstract alone, ignoring body text. This reproduces the README's ceiling and shows why full-text rows were unverifiable before: their quotes are essentially absent from abstracts.

| tier | stratum vs abstract only | checked | traceable | traceable % | control FP % |
|---|---|---:|---:|---:|---:|
| dysautonomia-core-findings | ALL quote rows | 35,344 | 6,097 | 17.25% | 0.0% |
| dysautonomia-core-findings | retrieved-fulltext rows only | 28,879 | 96 | 0.33% | 0.0% |
| comorbid-conditions-findings-a | ALL quote rows | 36,072 | 7,193 | 19.94% | 0.0% |
| comorbid-conditions-findings-a | retrieved-fulltext rows only | 28,420 | 48 | 0.17% | 0.0% |
| comorbid-conditions-findings-b | ALL quote rows | 33,548 | 6,021 | 17.95% | 0.0% |
| comorbid-conditions-findings-b | retrieved-fulltext rows only | 27,040 | 51 | 0.19% | 0.0% |
| postviral-autism-findings | ALL quote rows | 25,937 | 3,150 | 12.14% | 0.0% |
| postviral-autism-findings | retrieved-fulltext rows only | 22,766 | 111 | 0.49% | 0.0% |

The abstract-stratum traceable rates here (tier1 92.82%, tier2a 93.37%, tier2b 91.73%, tier3 95.84%) are 1–2 points below the shipped census (tier1 94.56%) because (i) the shipped census used the draw-corpus abstract captured at extraction time whereas this one uses Europe PMC's current `abstractText`, and (ii) `blocked` rows are included here.

## Permanent losses (rows with no re-fetched source at all), itemised by cause

| tier | rows no source | cause | rows |
|---|---:|---|---:|
| dysautonomia-core-findings | 118 | fulltext row; paper fulltext_failed; no abstract either | 47 |
| dysautonomia-core-findings | 118 | abstract-stratum row; paper no_abstract | 71 |
| comorbid-conditions-findings-a | 64 | abstract-stratum row; paper no_abstract | 61 |
| comorbid-conditions-findings-a | 64 | fulltext row; paper fulltext_failed; no abstract either | 3 |
| comorbid-conditions-findings-b | 52 | abstract-stratum row; paper no_abstract | 52 |
| postviral-autism-findings | 11 | abstract-stratum row; paper no_abstract | 11 |

Total rows with no source: **245 of 132,540** (0.18%). A second, softer loss class is the 1,391 `retrieved-fulltext` rows downgraded to abstract depth (tier1 1371, tier2b 20, comorbid-conditions-findings-a/tier3 0): their body text was fetchable at extraction time but is not in Europe PMC's OA full-text set today (77 of 84 failing papers and all 14 no-PMCID papers are now `isOpenAccess=N`). These are recoverable only from a source other than Europe PMC.

## Untraceable examples (full-text depth; 20 per tier, quote truncated to 160 chars)

### tier1

- PMID 41743836: “In FTD, increased overall autonomic symptoms (total ASQ score), positively correlated with the left anterior inferior (rs = 0.57, 95% confidence interval [CI]: ”
- PMID 38026514: “In GBA‐PD, lower E:I ratio was associated with poorer performances in FAB (r = 0.57, P = 0.009; coefficient of determination R2 = 0.32) and Benson Figure Copy (”
- PMID 41444346: “Kruskal–Wallis tests identified significant group effects for both age (χ²=18.11, p<0.001) and BMI (χ²=22.47, p<0.001). Post-hoc comparisons showed that partici”
- PMID 41743836: “Increased gastrointestinal symptoms positively correlated with the left posterior (rs = 0.58, 95% CI: −0.03 to 0.85, p = 0.012), left tubular inferior (rs = 0.5”
- PMID 40217677: “Patients with neurogenic OH had significantly higher median nighttime SBP and DBP than non-OH patients, which suggests an increased risk of adverse cardiovascul”
- PMID 41743836: “Increased thermoregulatory‐related symptoms showed a positive correlation with the left anterior inferior (rs = 0.60, 95% CI: 0.03–0.98, p = 0.018), left anteri”
- PMID 39656385: “dopamine with DOPA (Fig. 2C)... The regression lines of best fit generally passed close to the origin... suggesting a common source. Since DOPA is the precursor”
- PMID 41743836: “Increased urogenital symptoms positively correlated with the right anterior superior (rs = 0.68, 95% CI: 0.17–1.12, p = 0.005) and right tubular superior (rs = ”
- PMID 41743836: “In controls, both increased cardiovascular (rs = 0.54, 95% CI: 0.01–0.91, p = 0.026) and gastrointestinal symptoms (rs = 0.72, 95% CI: 0.09–0.99, p = 0.001) pos”
- PMID 39964606: “TTN is associated with familial hypertrophic cardiomyopathy and familial dilated cardiomyopathy, as well as a specific form of cardiomyopathy characterized by a”
- PMID 41743836: “Increased altered pain perception showed positive correlations to the left anterior superior (rs = 0.58, 95% CI: −0.18 to 0.77, p = 0.024) and left posterior (r”
- PMID 41444346: “The directionality index (ΔDir) was slightly positive in Controls (+0.0561)... Mild and Moderate OSA showed significant negative values (p<0.05), consistent wit”
- PMID 41444346: “A two-factor ANOVA on cluster-based mean amplitudes revealed a main effect of Severity (p=0.0169), whereas the main effect of Electrode (p=0.8467) and the Sever”
- PMID 38650940: “Upstream regulators analyses indicated predicted inhibition in TNF (activation Z score=-1.6, p-value of overlap=2.56E-27) ... TLR4 (Toll-like receptor 4) (activ”
- PMID 41189298: “Although HRV did not significantly correlate with HR in the control group, a correlation was observed in the T1DM group among adults (> 18 years) (T1DM: r2 = 0.”
- PMID 37308984: “Family with psychiatric disordersNo7837.545.042.452.541.144.741.7Yes1741.41.3(-2.4, 5.0)40.42.0(-5.5, 1.2)41.6-0.4(-3.1, 2.2)46.9-2.8(-5.4, -0.2)*41.8-0.3(-4.3,”
- PMID 35429449: “SARS-CoV-2 affinity to the receptor is almost 20-fold more than SARS-CoV-1, which would explain many neurological manifestations such as headache, nausea, and v”
- PMID 33886001: “In 258 patients with pulmonary arteriovenous malformations evaluated prospectively, 30% of patients had orthodeoxia, and orthostatic tachycardia was more pronou”
- PMID 41385477: “Pearson correlation analysis showed a strong positive association between test and retest values (R2 = 0.8966, 95% CI: 0.9035–0.9711, p < 0.0001), indicating hi”
- PMID 41444346: “over frontal electrodes (F3, F4), a second significant cluster appeared between 540–680 ms (cluster-level p<0.001 for both). No significant effects were found a”

### tier2a

- PMID 32814824: “In addition, the level of MC protease-1 (MCPT1) was significantly elevated in mice exposed to CS and decreased with anti-S8 treatment.”
- PMID 32814824: “Anti-S8 treatment also significantly reduced histopathologic, airway, parenchymal, and vascular inflammation scores induced by chronic CS exposure compared to i”
- PMID 32814824: “Treatment with anti-S8 significantly decreased MC numbers, activation state, and tissue levels of MCPT1 and MCPT4, indicative of MC inhibition.”
- PMID 32814824: “In addition, anti-S8 treatment significantly reduced lung fibrosis as assessed by histology, Ashcroft score, and lung tissue hydroxyproline levels.”
- PMID 32814824: “Eosinophil depletion did not decrease IL-33-induced neutrophil influx compared to mice with eosinophils.”
- PMID 32814824: “We identified 498 differentially expressed genes that were up- or downregulated upon IL-33 administration and significantly changed after anti-S8 treatment.”
- PMID 32814824: “Treatment with anti-S8 significantly reduced hMC activation as evidenced by decreased CD63 expression, suggesting Siglec-8 is functional in these cells.”
- PMID 33092395: “There was a range of illness severity, but most families described CFS/ME as a persistent...and disabling condition. It impacted the child's hobbies, activities”
- PMID 33092395: “In addition symptoms were feeling 'weak' (Willow, KS2); disturbed and unrefreshing sleep...digestive symptoms ('stomach pain um, IBS like type symptoms', Chloe'”
- PMID 33337383: “For example, in diabetic patients, axon swelling seen in skin biopsies can predict progression of distal SFN to proximal large fiber or polyneuropathy [20–22]. ”
- PMID 33461311: “We found DistEn to be negatively correlated with RHR (r2=0.11, P<0.0001) and positively correlated with RMSSD (r2=0.36, P<0.0001), but had no relationship with ”
- PMID 33562474: “reports suggest that 88 suicides have been partly attributed to CFS/ME between 2001 and 2016... Depression is not always a feature in CFS/ME-related suicide [49”
- PMID 33560495: “Unlike other typical IgE-mediated reactions to food, mammalian meat allergy can manifest with symptoms that are delayed up to 6 h after ingestion.”
- PMID 33560495: “Additionally, reported tick bite within the 12 months prior to blood sampling significantly increased the risk of α-gal-sIgE positivity.”
- PMID 33560495: “Evidence suggests that treatment of systemic reactions with epinephrine prevents progression to more severe symptoms.”
- PMID 33560495: “Steroid sparing evidence has been published using ketotifen in IA, and its mast cell stabilizing properties have also been demonstrated in mastocytosis. The usu”
- PMID 33609255: “Two FDA-approved medications, nintedanib and pirfenidone, are non-curative but have been demonstrated to slow the progression of pulmonary fibrosis.”
- PMID 33633136: “We ran the REFS algorithm ten times on the CAMDA mRNA expression dataset containing 118 samples and the algorithm found the optimal number of predictor genes to”
- PMID 33633136: “Similarly, ARRB1 protein was decreased after Epstein-Barr virus-infection in mice. Its downregulation in our study concurs with this finding.”
- PMID 33633136: “Blockage of CCR4 by mogamulizumab induced fatigue in human subjects.”

### tier2b

- PMID 36758522: “Among ME/CFS-specific species, three species (F. prausnitzii, E. rectale, and C. secundus) were deficient in ME/CFS, and nine species... were enriched in ME/CFS”
- PMID 36751332: “In dermatosparaxis EDS (dEDS), the skin is extremely and prematurely fragile with congenital or postnatal tears and sagging around the wrists and ankles.”
- PMID 37054777: “In a heterogeneous population referred for iCPET investigation of unexplained exertional intolerance, low biventricular filling pressures (ie, “preload failure””
- PMID 37046863: “Many authors reported lower health-related quality of life scores in ED patients if compared to the healthy population.”
- PMID 37007968: “Furthermore, Tnxb−/− mice also exhibited hypersensitization of myelinated Aδ- and Aβ-fibers, but not unmyelinated C fibers, by using transcutaneous sine wave st”
- PMID 37007968: “Col5a1+/− mice showed a disorganization of Nav1.8-expressing fibers including above 90% C-fibers, with less fibers crossing the epidermis of footpad glabrous sk”
- PMID 37007968: “Tnxb−/− mice show hypersensitivity of colonic nociceptive afferents and increased sensory neuron sprouting in the mucosa”
- PMID 37007968: “Tnxb−/− mice also exhibited gastric dysfunction associated with accelerated gastric emptying and hypersensitivity of gastric vagal mechanoreceptors”
- PMID 37015721: “Patients with OAB have a high risk of developing IC/BPS, and vice versa.”
- PMID 37015721: “CRF-R1 antagonist-treated rats showed an increased micturition frequency and a decreased bladder capacity.”
- PMID 37015721: “It is well known that the expression levels of 5-HT were remarkably low in the brain of depressed patients.”
- PMID 37015721: “Similar to 5-HT, a decreased level of NE is associated with depression.”
- PMID 37015721: “Of the 274 women diagnosed with OAB, many of them developed depression or anxiety, accounting for 59.8% and 62.4%, respectively.”
- PMID 37015721: “Moreover, in these OAB patients, depression turned out to induce deterioration of incontinence symptom and in quality of life.”
- PMID 37015721: “Cats treated with a serotonin antagonist (methysergide), showed reduced micturition threshold.”
- PMID 37015721: “the administration of corticosterone injection for the signs of depression and detrusor overactivity displayed a remarkable remission in SNRI (duloxetine)-treat”
- PMID 37015721: “Treatment of a patient suffering from OAB and OAB-related anxiety and depression with duloxetine ameliorated both bladder and mood disorders.”
- PMID 37015721: “Approximately 20% of the 504 women with urinary incontinence suffered from fecal incontinence.”
- PMID 37015721: “CYP-induced cystitis magnified the visceromotor responses to colonic distension, which suggests that dysfunction in bladder might cause colorectal disorders.”
- PMID 37015721: “When comparing with the healthy group, the IC/BPS and OAB groups commonly have a reduced microbial concentration and diversity in urine.”

### tier3

- PMID 33983522: “RV dysfunction was also the most common abnormality seen in a multi-center international cohort of over 300 hospitalized patients with COVID-19, around 26%.”
- PMID 33983522: “Of a cohort of 143 discharged patients in Italy from April 2020, 87% reported ongoing fatigue and dyspnea at 60 days.”
- PMID 33983522: “Within a non-hospitalized cohort of 272 individuals across the USA, 35% reported not being at baseline at 14–21 days after COVID-19 diagnosis.”
- PMID 33983522: “With regards to specific cardiovascular symptoms, approximately 20% of individuals reported chest pain and 14% reported palpitations at 60 days.”
- PMID 33491461: “There was no significant effect of state-anxiety (effect = “0.03, 95% bootstrapped CIs (“0.18, 0.05)) or depression (effect = 0.05, 95% bootstrapped CIs (“0.04,”
- PMID 33535874: “those with autism had shorter IBIs (i.e., faster HR) than those without.”
- PMID 34035473: “we determined possible variations in circulating blood glucose levels by measuring the glycaemic index... no differences were detected between P90 Rab39b WT and”
- PMID 34204243: “Spironolactone has been found in vitro to inhibit EBV VCA synthesis and capsid formation.”
- PMID 34204243: “Further, they found EBV reactivation to be associated with longer median ICU stays (15 days versus 8 days, p < 0.05).”
- PMID 34249668: “Iloreta AM (NCT04495816) Omega-3 Fatty Acid Supplement versus Placebo 2 Randomised, parallel arm Control Trial BSIT atWeek 0Week 6”
- PMID 34839263: “Dyspnea 35.1% (n=56)”
- PMID 34839263: “Decreased DLCO 31.5% (n=18)”
- PMID 34839263: “Insomnia 31.9% (n=12)”
- PMID 34839263: “Elevated circulating D-dimer concentration 26.0% (n=6)”
- PMID 34839263: “Anxiety 22.2% (n=24)”
- PMID 34839263: “Depression 21.1% (n=25)”
- PMID 34839263: “Hypertension 20.4% (n=4)”
- PMID 34839263: “Cognitive impairment 18.6% (n=13)”
- PMID 34839263: “Alopecia 18.8% (n=9)”
- PMID 34839263: “Parenchymal consolidation 16.8% (n=8)”

Qualitatively these are (a) paraphrases/summaries the model presented as quotes, (b) numeric spans drawn from tables the model never saw as `<p>` text and reconstructed, and (c) body text possibly revised since extraction. No adjudication was performed; the rows carry `retrofit_traceable=False` and are flagged, not repaired.

## Deliverables

- `annotations/quote_retrofit_<tier>.parquet` — one row per package row (row_idx = 0-based position in the shipped parquet; pmid and sha1(provenance_quote) as checks). Columns: row_idx, pmid, quote_sha1, fulltext_status, retrofit_fetch_status, retrofit_source_depth, retrofit_exact (nullable bool), retrofit_traceable (nullable bool; null iff depth none), retrofit_n_shingles, retrofit_fetch_date, comparator_version. Row counts: tier1 36,067, tier2a 36,611, tier2b 33,830, tier3 26,032.
- `annotations/retrofit_fetch_log.parquet` — one row per pmid attempted (10,428): pmid, needs_fulltext, has_abstract, has_fulltext, pmcid, is_oa, http_status_or_error, fulltext_error, body_chars, fetched_at, fetch_status.
- `annotations/retrofit_summary.json` — every number above, machine-readable, with numerator/denominator/basis per rate.
- Tier package files were not modified; all tables are additive.
