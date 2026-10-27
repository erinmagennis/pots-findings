# Before an irreversible dataset publish, audit records against the registry, not just the files

**Date:** 2026-10-26  **Context:** POTS findings v1.2, five packages with reserved Zenodo DOIs, about to be published

## The approach that worked
- Verified the other agent's doc pass from scratch: rebuilt the tarballs from the committed tree and compared bytes,
  extracted them, ran every package's own verifier and the audit greps. "It said PASS" was not accepted as evidence.
- A small count mismatch (site 11,511 vs packages 11,519 papers) was the thread worth pulling. The existing dedup map
  had only checked one package and only exact titles.
- Pulled PubMed esummary for all 11,519 PMIDs (publication types plus "Retraction in", "Erratum for", "Update in"
  links). That found 10 retracted papers (139 findings, including two treatment trials), correction notices that had
  findings extracted from them, and 29 preprint/published pairs. Title matching alone would have missed the
  retractions entirely, because most corpus records had no publication type.
- Title/author matching produced candidates only; every pair got a recorded accept/reject decision (13 of 21 were
  different papers sharing a title).

## Judgment calls
- Kept 11,519 (PubMed records) as the single headline number: it is the only number a reader can reproduce from the
  shipped files, and the data was frozen. Distinct works became a derived number via the flags file.
- Flag, never delete: retracted rows stay in the data with `recommended_use = exclude`; the site hides them by default.
- Held the Zenodo publish for a rebuild rather than publishing and fixing in v1.3, because the permanent record would
  otherwise carry unflagged retracted treatment findings.
- After the flags existed, re-read the prose claims against them ("packages share zero papers" was false for 14
  studies split across packages).

## Reusable rule
Before publishing any literature dataset, query PubMed (or Crossref) for every record's publication type and linked
notices, flag retractions, notices and version pairs in a shipped file, and re-check every prose claim about counts
against that file.
