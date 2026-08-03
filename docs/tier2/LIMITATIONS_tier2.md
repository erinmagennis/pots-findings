# LIMITATIONS - Tier-2

## 1. Coverage is ~55%, not complete
81 of 146 tier-2 chunks are extracted. Per-condition coverage after this
work: EDS/hypermobility ~55%, ME/CFS ~57%, MCAS ~58%, IBS ~60%, small-fiber ~60%, fibromyalgia ~58%,
patient-evidence ~56%, RCCX ~50%. **Absence of a finding is not evidence of absence** - the paper may
be in an unextracted chunk. Do not compute "the literature says X in N papers" as if N were complete.

## 2. Entity coverage is head-only
60.9% of entity-bearing rows carry a canonical entity. The 8,296
unmapped rows are single-occurrence strings. Verified: **0 span >=2 conditions**, so the crossover
analysis is unaffected. ~315 (3.8%) are near-duplicates of a head string and would add at most one paper
of support each if mapped. Entity-level *prevalence* counts are therefore lower bounds.

## 3. `cross-mention` evidence is weaker than it looks
1,521 of 4,820 convergence rows are `cross-mention` - a paper in condition X's literature commenting on
condition Y. These are real statements but they are not condition-Y primary literature. Filter to
`within-literature` for primary evidence. Failing to do so inflates apparent support for the
better-known condition in any pair.

## 4. Comorbidity claims are claims, not epidemiology
The 355 explicit claims record **what papers assert**. They are not
pooled prevalence estimates, carry no shared denominator, are not corrected for referral or
ascertainment bias, and over-represent specialist-clinic cohorts. 14 of them are low-confidence.
Do not read pair counts as relative comorbidity strength - a pair may rank high because it is
well-studied, not because the association is stronger.

## 5. Adjudication is model judgement
The three-way labels come from a strong model against a written rubric, not from human expert review.
The 23.4% rejection rate shows the rubric bites, but boundary cases between `explicit_comorbidity` and
`shared_mechanism` remain judgement calls. Every row carries `rationale` and `provenance_quote` so any
verdict can be checked.

## 6. Theme labels are corpus-assigned
`source_literature` comes from the corpus theme label from search-stream construction, not from
per-paper adjudication. A paper may belong to several literatures; the label reflects its acquisition
stream. Papers carrying multiple themes contribute to each.

## 7. `finding_type == 'comorbidity'` is not the same as an adjudicated claim
The extraction schema's `comorbidity` type is an extractor judgement over 4,023 rows. Only rows that
also named >=2 conditions with a cue were screened, and only 355 survived adjudication. Do not
substitute one count for the other.

## 8. No figures
Figure regeneration on combined tier-1+2 data was scoped out, not attempted-and-abandoned. Tier-1
figures remain valid at tier-1 scope in the original bundle. No figure in this bundle shows tier-2 data
because there are none.

## 9. Grounding is partial
Ontology grounding resolved ~97% of *proposed* IDs, but IDs were proposed for only ~19% of tier-2 rows.
`pathway_id` is <1% filled - thin data, not a bug: tier-2 findings are largely clinical/symptom-level.
