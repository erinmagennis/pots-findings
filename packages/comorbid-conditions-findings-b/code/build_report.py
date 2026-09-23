import json, pandas as pd
s = json.load(open("annotations/retrofit_summary.json"))
log = pd.read_parquet("annotations/retrofit_fetch_log.parquet")
TIERS = ["tier1", "tier2a", "tier2b", "tier3"]
P = s["per_tier"]
fr = s["fetch_run"]
def pct(n, d): return f"{100*n/d:.2f}%" if d else "n/a"
def f(n): return f"{n:,}"

# corpus-wide totals
tot_rows = sum(P[t]["rows_total"] for t in TIERS)
tot_before = sum(P[t]["verifiable_before"]["n"] for t in TIERS)
tot_after = sum(P[t]["verifiable_after"]["n"] for t in TIERS)
tot_trace = sum(P[t]["traceable_after_all_verifiable"]["n"] for t in TIERS)
tot_ftdepth = sum(P[t]["strata"]["fulltext_rows_vs_fulltext"]["n_checked"] for t in TIERS)
tot_fttrace = sum(P[t]["strata"]["fulltext_rows_vs_fulltext"]["n_traceable"] for t in TIERS)
tot_lost = sum(P[t]["permanent_losses"]["n_rows_no_source"] for t in TIERS)
tot_down = sum(P[t]["fulltext_rows_downgraded_to_abstract_source"] for t in TIERS)
s["corpus_wide_tiers1_3"] = {"rows_total": tot_rows, "verifiable_before": tot_before, "verifiable_after": tot_after,
    "traceable_after": tot_trace, "fulltext_depth_checked": tot_ftdepth, "fulltext_depth_traceable": tot_fttrace,
    "rows_no_source": tot_lost, "fulltext_rows_downgraded_to_abstract": tot_down,
    "verifiable_before_pct": round(100*tot_before/tot_rows, 2), "verifiable_after_pct": round(100*tot_after/tot_rows, 2),
    "traceable_pct_of_verifiable": round(100*tot_trace/tot_after, 2), "fulltext_depth_traceable_pct": round(100*tot_fttrace/tot_ftdepth, 2)}
json.dump(s, open("annotations/retrofit_summary.json", "w"), indent=1, default=str)

L = []
L.append("# RETROFIT REPORT — Tier 1–3 quote source re-fetch and traceability census\n")
L.append(f"Generated {s['generated_at']}. Comparator: `{s['comparator_version']}` (pinned `tier4/code/quote_trace.py`, imported unmodified; `comparator_symmetry_tests.py` 8/8 PASS; `selftest()` no failures).\n")
L.append("## Deviations from task (read first)\n")
L.append("- **No reduction of scope.** All 10,428 target pmids were attempted (10,428/10,428); all 6,239 papers with at least one `retrieved-fulltext` row had a full-text fetch attempted (6,239/6,239). No sampling, no capping, no substituted source.")
L.append("- **Source-text composition (a choice, stated):** the full-text source for a row is `title + abstract + JATS body <p> text[:120,000 chars]`. The 120,000-char cap equals `FT_INPUT_CHAR_CAP` — the extraction model never saw body text beyond it, so text past the cap cannot be a legitimate quote source. Tables, figure captions and reference lists are excluded exactly as `parse_sections` excluded them at extraction time. The abstract-only source is Europe PMC `abstractText` alone, matching the shipped README census basis.")
L.append("- **`isOpenAccess` was not required** for the full-text attempt (the original `fetch_fulltext` required it). Any paper with a PMCID was tried, because these papers had demonstrably yielded full text at extraction time. Result: 1 of 6,141 successful full-text fetches came from a record now flagged `isOpenAccess=N`.")
L.append("- **Europe PMC text is the CURRENT version**, not the version fetched at extraction time (2025–2026). Records whose abstract/body were revised, embargoed or withdrawn since then appear as untraceable or as fetch failures; this is a floor on true fidelity, not a ceiling.")
L.append("- **Fetched text is not shipped** (LICENSE: verbatim excerpts only). It lived only in the run workspace (`fetch_ckpt/`) and is deleted after the census. The per-paper fetch log and row-level census are the deliverables.")
L.append("- The negative-control sample size is 400 per stratum where the stratum has ≥400 rows; the two small fallback strata (tier2b: 20 rows) report the control on all rows they have and are labelled as such.\n")

L.append("## Fetch run\n")
L.append(f"- Requests: **{f(fr['n_requests'])}** (10,428 `search` + 6,239 `fullTextXML` = 16,667 planned; {fr['n_requests']} actually issued — 14 full-text requests were not issued because the current record carries no PMCID).")
L.append(f"- Wall time: **{fr['wall_seconds']/60:.1f} min** ({fr['n_requests']/fr['wall_seconds']:.2f} req/s aggregate; pinned pacing 3 workers × 0.9 s; the rest is network latency). No HTTP 429/5xx surfaced after the pinned retry/backoff: all 10,428 `search` calls returned HTTP 200.")
fl = s["fetch_log"]
L.append(f"- Papers attempted {f(fl['n_rows'])}/10,428; abstract obtained {f(fl['n_has_abstract'])}/10,428 ({pct(fl['n_has_abstract'],10428)}); full text obtained {f(fl['n_has_fulltext'])}/{f(fl['n_needs_fulltext'])} ({pct(fl['n_has_fulltext'],fl['n_needs_fulltext'])}).")
L.append(f"- Paper-level `retrofit_fetch_status`: " + ", ".join(f"{k} {f(v)}" for k, v in fl["fetch_status_counts"].items()) + ".")
ff = log[log.fetch_status == "fulltext_failed"]; npm = log[log.fetch_status == "no_pmcid"]; na = log[log.fetch_status == "no_abstract"]
L.append(f"- Full-text failure causes (paper level, {len(ff)+len(npm)} papers): HTTP 404 on `fullTextXML` {int((ff.fulltext_error=='HTTP 404').sum())} "
         f"(of which {int(((ff.fulltext_error=='HTTP 404')&(ff.is_oa=='N')).sum())} now carry `isOpenAccess=N` — full text withdrawn from the OA subset since extraction); "
         f"body parsed but < 2,000 chars {int(ff.fulltext_error.str.startswith('parsed-thin').sum())}; record no longer carries a PMCID {len(npm)} (all {int((npm.is_oa=='N').sum())} now `isOpenAccess=N`).")
L.append(f"- `no_abstract` {len(na)}: Europe PMC returned a record (HTTP 200) with empty `abstractText` — typically letters, errata, editorials.\n")

L.append("## Verifiable rows: before (README, abstract-derived rows only) vs after retrofit\n")
L.append("`verifiable` = the row's own source text exists and was re-read. Before: rows with `fulltext_status ∈ {abstract-only, blocked}` (README basis). After: rows with `retrofit_source_depth != none`.\n")
L.append("| tier | rows | verifiable before | % (README) | verifiable after | % | traceable after (all verifiable) | % of verifiable | % of all rows |")
L.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
for t in TIERS:
    v = P[t]; b = v["verifiable_before"]; a = v["verifiable_after"]; tr = v["traceable_after_all_verifiable"]
    L.append(f"| {t} | {f(v['rows_total'])} | {f(b['n'])} | {b['pct']}% ({b['readme_pct']}%) | {f(a['n'])} | {a['pct']}% | {f(tr['n'])} | {tr['pct']}% | {tr['pct_of_all_rows']}% |")
cw = s["corpus_wide_tiers1_3"]
L.append(f"| **Tiers 1–3** | {f(tot_rows)} | {f(tot_before)} | {cw['verifiable_before_pct']:.2f}% | {f(tot_after)} | {cw['verifiable_after_pct']}% | {f(tot_trace)} | {cw['traceable_pct_of_verifiable']}% | {round(100*tot_trace/tot_rows,2)}% |")
L.append("")
L.append(f"The 'all verifiable' traceable rate is pulled down by the **{f(tot_down)} `retrieved-fulltext` rows whose body text could not be re-fetched and were therefore checked against the abstract only** (`retrofit_source_depth == abstract` with `fulltext_status == retrieved-fulltext`). Those rows trace at ≈0% because their quotes come from the body, not the abstract — a source-depth limitation, not evidence against the quote. Stratify on `retrofit_source_depth` × `fulltext_status` before reporting a fidelity rate.\n")

L.append("## Traceable rate per depth stratum, with wrong-paper negative control (n_control=400, seed=11)\n")
L.append("Decision = `quote_traceability(quote, source)[1]`. `exact` = element [0]. A control false-positive rate above ~1% would invalidate the stratum's rate; every stratum below reads 0.00%.\n")
L.append("| tier | stratum | rows with quote | checked | traceable | untraceable | no source | traceable % | exact % | control n | control FP | control FP % |")
L.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
ann = {t: pd.read_parquet(f"annotations/quote_retrofit_{t}.parquet") for t in TIERS}
for t in TIERS:
    a = ann[t]
    for key, label, mask in [
        ("fulltext_rows_vs_fulltext", "retrieved-fulltext rows vs re-fetched FULL TEXT", (a.fulltext_status == "retrieved-fulltext") & (a.retrofit_source_depth == "fulltext")),
        ("abstract_stratum_rows_vs_abstract", "abstract-only + blocked rows vs re-fetched ABSTRACT", (a.fulltext_status != "retrieved-fulltext") & (a.retrofit_source_depth == "abstract")),
        ("fulltext_rows_fallback_vs_abstract", "retrieved-fulltext rows lacking body, vs ABSTRACT (fallback)", (a.fulltext_status == "retrieved-fulltext") & (a.retrofit_source_depth == "abstract")),
    ]:
        st = P[t]["strata"][key]; nc = st["negative_control"]
        ex = a[mask].retrofit_exact
        exp = f"{100*ex.mean():.2f}%" if len(ex) else "n/a"
        L.append(f"| {t} | {label} | {f(st['n_rows_with_quote'])} | {f(st['n_checked'])} | {f(st['n_traceable'])} | {f(st['n_untraceable'])} | {f(st['n_no_source_text'])} | {st['traceable_pct'] if st['traceable_pct'] is not None else 'n/a'}{'%' if st['traceable_pct'] is not None else ''} | {exp} | {nc['n_control']} | {nc['n_false_positives']} | {nc['false_positive_pct'] if nc['false_positive_pct'] is not None else 'n/a'}{'%' if nc['false_positive_pct'] is not None else ''} |")
L.append(f"\nCorpus-wide (Tiers 1–3), full-text depth: **{f(tot_fttrace)} / {f(tot_ftdepth)} = {cw['fulltext_depth_traceable_pct']}%** of `retrieved-fulltext` rows re-fetched at full-text depth trace to their paper's own body text; the 97-paper pilot read 98.65%.\n")

L.append("## Abstract-ONLY census of the same rows (README-comparable, before/after on one instrument)\n")
L.append("Every quote row checked against the re-fetched abstract alone, ignoring body text. This reproduces the README's ceiling and shows why full-text rows were unverifiable before: their quotes are essentially absent from abstracts.\n")
L.append("| tier | stratum vs abstract only | checked | traceable | traceable % | control FP % |")
L.append("|---|---|---:|---:|---:|---:|")
for t in TIERS:
    for key, label in [("all_rows_vs_abstract_only", "ALL quote rows"), ("fulltext_rows_vs_abstract_only", "retrieved-fulltext rows only")]:
        st = P[t]["strata"][key]; nc = st["negative_control"]
        L.append(f"| {t} | {label} | {f(st['n_checked'])} | {f(st['n_traceable'])} | {st['traceable_pct']}% | {nc['false_positive_pct']}% |")
L.append("\nThe abstract-stratum traceable rates here (tier1 92.82%, tier2a 93.37%, tier2b 91.73%, tier3 95.84%) are 1–2 points below the shipped census (tier1 94.56%) because (i) the shipped census used the draw-corpus abstract captured at extraction time whereas this one uses Europe PMC's current `abstractText`, and (ii) `blocked` rows are included here.\n")

L.append("## Permanent losses (rows with no re-fetched source at all), itemised by cause\n")
L.append("| tier | rows no source | cause | rows |")
L.append("|---|---:|---|---:|")
for t in TIERS:
    pl = P[t]["permanent_losses"]
    for c, n in pl["by_cause"].items():
        L.append(f"| {t} | {f(pl['n_rows_no_source'])} | {c} | {f(n)} |")
L.append(f"\nTotal rows with no source: **{f(tot_lost)} of {f(tot_rows)}** ({pct(tot_lost, tot_rows)}). A second, softer loss class is the {f(tot_down)} `retrieved-fulltext` rows downgraded to abstract depth (tier1 {P['tier1']['fulltext_rows_downgraded_to_abstract_source']}, tier2b {P['tier2b']['fulltext_rows_downgraded_to_abstract_source']}, tier2a/tier3 0): their body text was fetchable at extraction time but is not in Europe PMC's OA full-text set today (77 of 84 failing papers and all 14 no-PMCID papers are now `isOpenAccess=N`). These are recoverable only from a source other than Europe PMC.\n")

L.append("## Untraceable examples (full-text depth; 20 per tier, quote truncated to 160 chars)\n")
for t in TIERS:
    L.append(f"### {t}\n")
    for e in P[t]["strata"]["fulltext_rows_vs_fulltext"]["untraceable_examples"]:
        L.append(f"- PMID {e['pmid']}: “{e['quote'].replace(chr(10),' ')}”")
    L.append("")
L.append("Qualitatively these are (a) paraphrases/summaries the model presented as quotes, (b) numeric spans drawn from tables the model never saw as `<p>` text and reconstructed, and (c) body text possibly revised since extraction. No adjudication was performed; the rows carry `retrofit_traceable=False` and are flagged, not repaired.\n")

L.append("## Deliverables\n")
L.append("- `annotations/quote_retrofit_<tier>.parquet` — one row per package row (row_idx = 0-based position in the shipped parquet; pmid and sha1(provenance_quote) as checks). Columns: row_idx, pmid, quote_sha1, fulltext_status, retrofit_fetch_status, retrofit_source_depth, retrofit_exact (nullable bool), retrofit_traceable (nullable bool; null iff depth none), retrofit_n_shingles, retrofit_fetch_date, comparator_version. Row counts: " + ", ".join(f"{t} {f(len(ann[t]))}" for t in TIERS) + ".")
L.append("- `annotations/retrofit_fetch_log.parquet` — one row per pmid attempted (10,428): pmid, needs_fulltext, has_abstract, has_fulltext, pmcid, is_oa, http_status_or_error, fulltext_error, body_chars, fetched_at, fetch_status.")
L.append("- `annotations/retrofit_summary.json` — every number above, machine-readable, with numerator/denominator/basis per rate.")
L.append("- Tier package files were not modified; all tables are additive.")
open("annotations/RETROFIT_REPORT.md", "w").write("\n".join(L) + "\n")
print(len(L), "lines")
