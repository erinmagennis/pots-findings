# Zenodo upload form — Tier 2 Part B — comorbid-condition literatures, second extraction wave — machine-extracted structured findings (33,830 findings, 2,589 papers)

Manual uploads do not read `.zenodo.json`; paste these values into the form. Upload the package
tarball `comorbid-conditions-findings-b-v1.2.tar.gz` as the single file. Do not publish until every value below is in.

| form field | value |
|---|---|
| Resource type | Dataset |
| Title | Tier 2 Part B — comorbid-condition literatures, second extraction wave — machine-extracted structured findings (33,830 findings, 2,589 papers) |
| Publication date | the day you click Publish (must equal `date-released` in CITATION.cff: 2026-10-22) |
| Creators | Magennis, Erin — ORCID 0009-0007-9013-8052 |
| Description | see block below |
| License | Creative Commons Attribution 4.0 International (CC-BY-4.0) |
| Version | tier2b-v1.2 |
| Keywords | POTS, postural orthostatic tachycardia syndrome, dysautonomia, ME/CFS, myalgic encephalomyelitis, chronic fatigue syndrome, Ehlers-Danlos syndrome, hypermobility, fibromyalgia, mast cell activation syndrome, long COVID, post-viral syndrome, small fiber neuropathy, autism, migraine, text mining, literature extraction, biomarkers, structured findings, text and data mining, large language model extraction |
| Related identifiers | PLACEHOLDER-DOI-tier1 (references); PLACEHOLDER-DOI-tier2a (references); PLACEHOLDER-DOI-tier3 (references); PLACEHOLDER-DOI-tier4 (references) |
| Related identifiers (add) | https://github.com/erinmagennis/pots-findings — isSupplementTo, Software |

## Description (paste as-is)

<p>Package 3 of 5. 33,830 structured findings extracted from 2,589 papers (2020–2026) covering EDS/hypermobility, ME/CFS, MCAS, RCCX genes, fibromyalgia, IBS, small-fiber neuropathy, patient-generated evidence, gastroparesis.</p><p>One block of a five-way partition of an 11,519-paper, 148,186-finding corpus of the POTS, dysautonomia and comorbid-condition literature. The five packages share <strong>zero papers</strong>; per-package counts sum exactly to the corpus totals.</p><p><strong>Self-contained.</strong> Includes the findings table (parquet and CSV), a data dictionary with fill rates measured on this slice, the QA evidence behind every stated number, the pinned extraction and validation code, and <code>code/verify_package.py</code>, which re-derives every headline number from the shipped data and exits non-zero on disagreement.</p><p><strong>Ontology identifiers:</strong> model-emitted and existence-checked only, scoring 0.708 on identifier-denotes-entity rate. Do not use them as an entity mapping — see LIMITATIONS.md.</p><p><strong>Quote verifiability:</strong> 19.39% of rows have a provenance quote whose own source text is still available and re-checkable.</p><p><strong>Scientific fidelity is unmeasured.</strong> All QA verifies well-formedness, not whether a finding correctly interprets its source. Treat every row as a pointer to a paper to read.</p><p><strong>Not medical advice.</strong></p>
