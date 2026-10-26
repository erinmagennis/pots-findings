# Zenodo upload form: POTS findings v1.2, package 1 of 5: POTS and dysautonomia core literature (36,067 findings, 3,129 papers)

Manual uploads do not read `.zenodo.json`; paste these values into the form. Upload the package
tarball `dysautonomia-core-findings-v1.2.tar.gz` as the single file. Do not publish until every value below is in.

| form field | value |
|---|---|
| Resource type | Dataset |
| Title | POTS findings v1.2, package 1 of 5: POTS and dysautonomia core literature (36,067 findings, 3,129 papers) |
| Publication date | the day you click Publish (must equal `date-released` in CITATION.cff: 2026-10-22) |
| Creators | Magennis, Erin (ORCID 0009-0007-9013-8052) |
| Description | see block below |
| License | Creative Commons Attribution 4.0 International (CC-BY-4.0) |
| Version | tier1-v1.2 |
| Keywords | POTS, postural orthostatic tachycardia syndrome, dysautonomia, ME/CFS, myalgic encephalomyelitis, chronic fatigue syndrome, Ehlers-Danlos syndrome, hypermobility, fibromyalgia, mast cell activation syndrome, long COVID, post-viral syndrome, small fiber neuropathy, autism, migraine, text mining, literature extraction, biomarkers, structured findings, text and data mining, large language model extraction |
| Related identifiers | 10.5281/zenodo.23671722 (references); 10.5281/zenodo.23671724 (references); 10.5281/zenodo.23671726 (references); 10.5281/zenodo.23671728 (references) |
| Related identifiers (add) | https://github.com/erinmagennis/pots-findings, relation isSupplementTo, type Software |

## Description (paste as-is)

<p>Package 1 of 5. 36,067 structured findings extracted from 3,129 papers (2019–2026) covering dysautonomia, POTS, dysautonomia subtypes, hyperadrenergic POTS.</p><p>One block of a five-way partition of an 11,519-paper, 148,186-finding corpus of the POTS, dysautonomia and comorbid-condition literature. The five packages share <strong>zero papers</strong>; per-package counts sum exactly to the corpus totals.</p><p><strong>Self-contained.</strong> Includes the findings table (parquet and CSV), a data dictionary with fill rates measured on this slice, the QA evidence behind every stated number, the pinned extraction and validation code, and <code>code/verify_package.py</code>, which re-derives every headline number from the shipped data and exits non-zero on disagreement.</p><p><strong>Ontology identifiers (v1.2):</strong> every identifier the extraction model emitted was checked by id at its authority (HGNC, ChEBI, MeSH). Of 4,373 rows with an id, 2,385 were confirmed, 1,161 were replaced by the id the entity name resolves to, and 827 were withheld. Join only on rows where <code>ontology_id_verification</code> is <code>authority_verified</code> or <code>authority_verified_retrospective</code>. See LIMITATIONS.md.</p><p><strong>Quote verifiability:</strong> 18.12% of rows have a provenance quote whose own source text is still available and re-checkable.</p><p><strong>Scientific fidelity is unmeasured.</strong> All QA verifies well-formedness, not whether a finding correctly interprets its source. Treat every row as a pointer to a paper to read.</p><p><strong>Not medical advice.</strong></p>
