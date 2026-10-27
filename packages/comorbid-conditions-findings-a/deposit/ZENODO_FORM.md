# Zenodo upload form: POTS findings v1.2, package 2 of 5: EDS and hypermobility, ME/CFS, MCAS, fibromyalgia, IBS, small fiber neuropathy and RCCX genes, part 1 of 2 (36,611 findings, 3,123 papers)

Manual uploads do not read `.zenodo.json`; paste these values into the form. Upload the package
tarball `comorbid-conditions-findings-a-v1.2.tar.gz` as the single file. Do not publish until every value below is in.

| form field | value |
|---|---|
| Resource type | Dataset |
| Title | POTS findings v1.2, package 2 of 5: EDS and hypermobility, ME/CFS, MCAS, fibromyalgia, IBS, small fiber neuropathy and RCCX genes, part 1 of 2 (36,611 findings, 3,123 papers) |
| Publication date | the day you click Publish (must equal `date-released` in CITATION.cff: 2026-10-22) |
| Creators | Magennis, Erin (ORCID 0009-0007-9013-8052) |
| Description | see block below |
| License | Creative Commons Attribution 4.0 International (CC-BY-4.0) |
| Version | tier2a-v1.2 |
| Keywords | POTS, postural orthostatic tachycardia syndrome, dysautonomia, ME/CFS, myalgic encephalomyelitis, chronic fatigue syndrome, Ehlers-Danlos syndrome, hypermobility, fibromyalgia, mast cell activation syndrome, long COVID, post-viral syndrome, small fiber neuropathy, autism, migraine, text mining, literature extraction, biomarkers, structured findings, text and data mining, large language model extraction |
| Related identifiers | 10.5281/zenodo.23671720 (references); 10.5281/zenodo.23671724 (references); 10.5281/zenodo.23671726 (references); 10.5281/zenodo.23671728 (references) |
| Related identifiers (add) | https://github.com/erinmagennis/pots-findings, relation isSupplementTo, type Software |

## Description (paste as-is)

<p>Package 2 of 5. 36,611 structured findings extracted from 3,123 papers (2019–2026) covering EDS/hypermobility, ME/CFS, MCAS, RCCX genes, fibromyalgia, IBS, small-fiber neuropathy, patient-generated evidence, gastroparesis.</p><p>One block of a five-way partition of an 11,519-paper, 148,186-finding corpus of the POTS, dysautonomia and comorbid-condition literature. The five packages share <strong>zero papers</strong>; per-package counts sum exactly to the corpus totals.</p><p><strong>Self-contained.</strong> Includes the findings table (parquet and CSV), a data dictionary with fill rates measured on this slice, the QA evidence behind every stated number, the pinned extraction and validation code, and <code>code/verify_package.py</code>, which re-derives every headline number from the shipped data and exits non-zero on disagreement.</p><p><strong>Ontology identifiers (v1.2):</strong> every identifier the extraction model emitted was checked by id at its authority (HGNC, ChEBI, MeSH). Of 6,716 rows with an id, 4,614 were confirmed, 1,107 were replaced by the id the entity name resolves to, and 995 were withheld. Join only on rows where <code>ontology_id_verification</code> is <code>authority_verified</code> or <code>authority_verified_retrospective</code>. See LIMITATIONS.md.</p><p><strong>Quote verifiability:</strong> 21.07% of rows have a provenance quote whose own source text is still available and re-checkable.</p><p><strong>Scientific fidelity is unmeasured.</strong> All QA verifies well-formedness, not whether a finding correctly interprets its source. Treat every row as a pointer to a paper to read.</p><p><strong>Paper flags:</strong> includes annotations/paper_flags.csv, which marks 4 retracted papers, 3 correction notices extracted as papers, 44 papers with a published correction and 6 duplicate records (preprint and published versions, co-publications). Exclude or count them as the file recommends; no row was removed. Checked against PubMed and Crossref on 2026-10-26.</p><p><strong>Not medical advice.</strong></p>
