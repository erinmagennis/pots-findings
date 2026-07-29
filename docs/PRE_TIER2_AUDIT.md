# Pre-Tier-2 Audit — What's solid, what's missing, what's wasted effort

*Everything below is measured against the actual Tier-1 table (tier1_findings.parquet, 36,067 findings /
3,129 papers) and chunk_order.parquet. Numbers are computed, not estimated, except where marked "projected".*

---

## VERDICT IN ONE LINE
The extraction machinery is sound and Tier 1 is trustworthy — but **Tier 1 is POTS/dysautonomia only**,
so the cross-condition comparisons this project exists to make are not yet possible. Two cheap fixes
(entity canonicalization, duplicate-title collapse) should land BEFORE tiers 2-4, and one expensive
planned layer (the ontology-ID grounding as primary key) should be **re-scoped** because the data
doesn't support it.

---

## 1. WHAT'S SOLID (no action needed)

| Check | Result |
|---|---|
| Tier-1 chunk completeness | 76/76 chunks, no gaps, no stale duplicates |
| Coverage of the Tier-1 paper set | 3,129 / 3,794 papers yielded findings (82.5%) |
| Papers with findings outside chunk_order | 4 (variant/duplicate pmids — known, documented) |
| Zero-finding papers | 665 (17.5%) = 3,794 − 3,129 — matches the characterized ~52% homonym / ~46% review split. (An earlier project note cited 670; that figure predates this table and does not reconcile with the 3,794 chunk_order total.) |
| provenance_quote coverage | 100% |
| Enum integrity on controlled fields | Clean; 50 singleton-drift rows normalized |
| Gene / HPO grounding *rate among proposed* | 97.0% / 99.2% — resolver works correctly |

The pipeline's own quality gate (MIN_YIELD=0.60 per chunk) plus the Pool A/C1 recovery passes did their job.
I have no concerns about Tier-1 data integrity.

---

## 2. WHAT'S MISSING (the big one — read this first)

### 2.1 Tier 1 is a SINGLE-CONDITION slice, not a cross-condition corpus
From chunk_order: Tier 1 = chunks 0-75 = **POTS, dysautonomia subtypes, hyperadrenergic only**.
Every other condition in the project's stated scope sits in tiers that are ~99% unextracted:
- **Tier 2** (chunks 76-220, 7,243 papers): ME/CFS, MCAS, EDS, fibromyalgia, IBS, small-fiber, gastroparesis, RCCX
- **Tier 3** (chunks 221-255, 1,754 papers): long COVID, autism, post-viral
- **Tier 4** (chunks 256-285, 1,471 papers): everything else

Consequence: the per-condition counts currently visible in Tier 1 are **incidental mentions inside
POTS/dysautonomia papers**, NOT that condition's own literature:

| Condition | Tier-1 papers w/ findings | Reality |
|---|---:|---|
| autism | 18 | dedicated corpus is in Tier 3 |
| IBS / gut | 64 | dedicated corpus is in Tier 2 |
| migraine | 61 | thin; Tier 2/4 |
| MCAS | 90 | dedicated corpus is in Tier 2 |
| EDS / hypermobility | 146 | dedicated corpus is in Tier 2 |
| fibromyalgia | 103 | dedicated corpus is in Tier 2 |
| ME/CFS | 136 | dedicated corpus is in Tier 2 |

**Implication for the planned capstones:** the cross-condition convergence engine and the
"mechanisms convergent across >=3 conditions" deliverable **cannot be meaningfully run on Tier 1**.
Any convergence result computed now is a statement about POTS papers that happen to mention other
conditions. Tier 2 is not optional for this project's core question — it is the main event.

### 2.2 Projected full-corpus scale
Tier-1 measured rates: 82% of papers yield findings, 11.5 findings per yielding paper.
Projected for the 10,468 remaining papers **across ALL of tiers 2-4** (not Tier 2 alone): **~8,600 papers, ~99,500 findings** → full corpus ≈ **135,000 findings (3.8x current)**.
*Basis note: uses the pre-canonicalization rate of 11.5 findings/paper. The canonical-basis rate is 11.68, and the **Tier-2-only** projection (7,238 papers) is ~69,700 new findings / ~106,200 total — see docs/TIER2_HANDOFF.md. Do not compare these two figures directly; they cover different paper sets.* Budget and any UI/index design should assume
this magnitude, not 36k.

---

## 3. WHAT'S BROKEN AND CHEAP TO FIX (do BEFORE tiers 2-4)

### 3.1 Entity canonicalization was specified in prescaling_review.md and never implemented
This is the single highest-value fix. Measured on Tier 1:
- 18,915 rows carry an entity; **9,582 distinct normalized strings**
- **78.6% of distinct entities appear exactly once** (long-tail fragmentation)
- **"norepinephrine" fragments into 98 distinct entity strings** (e.g. "24-h urinary norepinephrine",
  "cardiac norepinephrine uptake", "adrenaline; noradrenaline", "angiotensin ii, aldosterone, norepinephrine")
- microclots fragment into 7 variants — exactly the failure `prescaling_review.md` §3.3 predicted

Consequences: (a) every entity-rollup count is an UNDERCOUNT — a naive "papers per marker" tally
reported norepinephrine at 89 papers when the true figure is higher once variants merge;
(b) the convergence engine's canonicalization key is unreliable; (c) it gets ~4x worse at full corpus.

Fix now, while it's 9.5k strings instead of ~40k: a canonicalization pass (LLM-assisted mapping of
entity strings → canonical concept, plus a compound-entity splitter for the "a; b; c" rows).
Cost is small and it must exist before any convergence/rollup output is trustworthy.

### 3.2 Duplicate-title papers still double-count evidence
`prescaling_review.md` §2.1 flagged 66 duplicate titles and prescribed a pre-extraction dedup.
In the Tier-1 findings table: **9 normalized titles span >1 pmid**, contributing 9 extra paper rows and
**179 findings**. Small in absolute terms (0.5% of findings) but it inflates apparent replication —
two records of one paper look like two independent studies. Collapse on normalized title/DOI.

### 3.3 Compound entities are unsplit
Many entity values pack several analytes into one string ("adrenaline/noradrenaline/cortisol").
These will never match a single ontology ID or canonical name. Split during 3.1.

---

## 4. WHAT WE'RE DOING THAT WE PROBABLY DON'T NEED (scope cuts)

Measured fill rates expose planned layers whose data barely exists. Recommend re-scoping, not deleting:

| Planned layer | Actual Tier-1 fill | Recommendation |
|---|---:|---|
| **pathway_id / Reactome-GO grounding** | **0.1%** (22 rows of 36,067) | **Do not build the pathway-perturbation map** as a primary deliverable. The plan calls for an interactive pathway-perturbation graph keyed on resolved Reactome/GO ids; 22 rows cannot support it. Either derive pathways post-hoc from canonical entities via an external DB join, or cut it. |
| **dataset_accession** ("ships with datasets to test it in") | **0.7%** (~250 rows) | Papers rarely name accessions in text. Keep capturing (free), but drop the "every convergent mechanism ships with test datasets" promise, or source accessions by querying GEO/PRIDE directly by condition instead of hoping extraction finds them. |
| **entity_ontology_id as PRIMARY canonicalization key** | **12.8%** proposed / 12.1% resolved | Re-scope: the capstone plan makes resolved ontology IDs the primary key with embeddings as fallback. At 12% coverage that inverts — **canonical entity strings (§3.1) must be primary**, ontology IDs an enrichment. |
| **phenotype_hpo** | 2.8% | Fine as enrichment; don't build a deliverable that depends on it. |
| **contradicts_finding_ref** (controversy layer) | 4.2%, free-text, no global id index | The planned "CONTRADICTS edges in the knowledge graph" needs an id-reconciliation step that doesn't exist yet. Either build the reconciler or downgrade the controversy layer to the 59.7%-filled `contradicts_or_extends` free-text field. |
| **anatomical_study**, **entity_ontology_id_note** | **0.0%** | Dead columns. Drop from the schema for tiers 2-4 — they cost prompt tokens on every paper and return nothing. |
| **Aim 4 (proposal)** | n/a | Explicitly gated on a BIC/unhide EHR-coverage question that hasn't been asked. Not blocking, but it's been sitting — either ask the data team or mark it deferred. |

Fields worth keeping despite low fill (real signal, cheap): `effect_size` 38%, `quantitative_detail` 63%,
`treatment_class` 22%, `cohort_registry` 17.5%, `pots_subtype` 14.5%, `gene_marker` 7.7%.

---

## 5. RECOMMENDED SEQUENCE

1. **Ship the Tier-1 MVP** (repo + site) — labelled honestly as POTS/dysautonomia-scoped.
2. **Entity canonicalization + duplicate collapse** (§3.1-3.3) — cheap, and it fixes every downstream count.
3. **Trim the schema** for tiers 2-4: drop the 2 dead fields, demote pathway/accession/HPO to
   opportunistic enrichment, keep everything with >7% fill.
4. **Run Tier 2** (7,243 papers) — this is what unlocks the cross-condition question. Tier 3 next
   (long COVID/autism), Tier 4 last.
5. **Then** the convergence + hypothesis engines at full scale, keyed on canonical entities.

The main strategic point: **do not run the convergence capstone on Tier 1 and treat the output as a
cross-condition result.** Fix canonicalization, then get Tier 2 in.


---

## 6. APPENDIX — Why entity canonicalization needs judgment, not a regex

Worked example, measured on the norepinephrine family (98 distinct entity strings, 374 rows, 232 papers):

| What the string actually denotes | Strings | Rows | Merge? |
|---|---:|---:|---|
| The molecule (norepinephrine / noradrenaline / plasma NE / urinary NE / NE (plasma)) | 11 | 241 | YES — true synonyms |
| The transporter/gene (SLC6A2, NET, NET A457P variant) | 10 | 46 | NO — different biological entity |
| Drug classes (SNRIs, norepinephrine reuptake inhibitors, NE replacer therapy) | 5 | 7 | NO — treatment, not biomarker |
| Multi-analyte compound strings (e.g. "epinephrine, norepinephrine, dopamine") | 65 | 72 | SPLIT into components |
| Complex/derived measures (ΔNE aorta-coronary gradient, locus coeruleus-NE pathway) | 7 | 8 | Case-by-case |

Resulting paper counts for "norepinephrine":
- exact-string match only: **152 papers** (what a naive rollup reports today — an undercount)
- after merging the 11 true synonyms: **174 papers** (correct)
- merging all 98 strings: **232 papers** (wrong — pools a gene variant and an antidepressant class
  into a catecholamine measurement)

This is why a substring/regex merge is unsafe and why the canonicalization pass must be
entity-aware. Recommended approach: canonicalize the ~1,100 head entities (>=50% of rows) with an
LLM-assisted mapping, split compound entities into components, attach ChEBI/HGNC/MeSH IDs
opportunistically where a real term exists, and leave the 7,534 singleton strings unmerged but
searchable. Preserve the original `entity` string in a separate column so every merge is auditable
and reversible.
