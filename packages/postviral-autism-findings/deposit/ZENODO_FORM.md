# Zenodo upload form: POTS findings v1.2, package 4 of 5: long COVID, post-viral and autism intersections (26,032 findings, 1,587 papers)

Manual uploads do not read `.zenodo.json`; paste these values into the form. Upload the package
tarball `postviral-autism-findings-v1.2.tar.gz` as the single file. Do not publish until every value below is in.

| form field | value |
|---|---|
| Resource type | Dataset |
| Title | POTS findings v1.2, package 4 of 5: long COVID, post-viral and autism intersections (26,032 findings, 1,587 papers) |
| Publication date | the day you click Publish (must equal `date-released` in CITATION.cff: 2026-10-22) |
| Creators | Magennis, Erin (ORCID 0009-0007-9013-8052) |
| Description | see block below |
| License | Creative Commons Attribution 4.0 International (CC-BY-4.0) |
| Version | tier3-v1.2 |
| Keywords | POTS, postural orthostatic tachycardia syndrome, dysautonomia, ME/CFS, myalgic encephalomyelitis, chronic fatigue syndrome, Ehlers-Danlos syndrome, hypermobility, fibromyalgia, mast cell activation syndrome, long COVID, post-viral syndrome, small fiber neuropathy, autism, migraine, text mining, literature extraction, biomarkers, structured findings, text and data mining, large language model extraction |
| Related identifiers | 10.5281/zenodo.23671720 (references); 10.5281/zenodo.23671722 (references); 10.5281/zenodo.23671724 (references); 10.5281/zenodo.23671728 (references) |
| Related identifiers (add) | https://github.com/erinmagennis/pots-findings, relation isSupplementTo, type Software |

## Description (paste as-is)

<p>Package 4 of 5. 26,032 structured findings extracted from 1,587 papers (2020–2026) covering long COVID autonomic, autism intersection, post-viral syndromes.</p><p>One block of a five-way partition of an 11,519-paper, 148,186-finding corpus of the POTS, dysautonomia and comorbid-condition literature. The five packages share <strong>zero papers</strong>; per-package counts sum exactly to the corpus totals.</p><p><strong>Self-contained.</strong> Includes the findings table (parquet and CSV), a data dictionary with fill rates measured on this slice, the QA evidence behind every stated number, the pinned extraction and validation code, and <code>code/verify_package.py</code>, which re-derives every headline number from the shipped data and exits non-zero on disagreement.</p><p><strong>Ontology identifiers:</strong> authority-derived (the extraction model emitted names only; a resolver looked identifiers up afterwards), scoring 0.986 on identifier-denotes-entity rate.</p><p><strong>Quote verifiability:</strong> 12.22% of rows have a provenance quote whose own source text is still available and re-checkable.</p><p><strong>Scientific fidelity is unmeasured.</strong> All QA verifies well-formedness, not whether a finding correctly interprets its source. Treat every row as a pointer to a paper to read.</p><p><strong>Paper flags:</strong> includes annotations/paper_flags.csv, which marks 2 retracted papers, 0 correction notices extracted as papers, 31 papers with a published correction and 7 duplicate records (preprint and published versions, co-publications). Exclude or count them as the file recommends; no row was removed. Checked against PubMed and Crossref on 2026-10-26.</p><p><strong>Not medical advice.</strong></p>
