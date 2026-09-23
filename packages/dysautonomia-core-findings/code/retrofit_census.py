"""Row-level traceability census of Tiers 1-3 against re-fetched source text.

Instrument: pots-corpus/tier4/code/quote_trace.py (pinned; imported, never
reimplemented) — read element [1] of quote_traceability. census_stratum from
tier4_quote_census.py supplies the mandatory wrong-paper negative control.
"""
import sys, os, json, gzip, glob, hashlib, datetime, time
import pandas as pd, numpy as np

sys.path.insert(0, "pots-corpus/tier4/code")
from quote_trace import quote_traceability, selftest
from tier4_quote_census import census_stratum
assert selftest() == [], selftest()

QT_SHA = hashlib.sha256(open("pots-corpus/tier4/code/quote_trace.py", "rb").read()).hexdigest()[:12]
COMPARATOR_VERSION = f"quote_trace.py sha256:{QT_SHA}"
TIERS = ["tier1", "tier2a", "tier2b", "tier3"]
README_VERIFIABLE_PCT = {"tier1": 18.12, "tier2a": 21.07, "tier2b": 19.39, "tier3": 12.22}
os.makedirs("annotations", exist_ok=True)

# ---- fetched text + per-paper log ----
texts = {}
for f in sorted(glob.glob("fetch_ckpt/ckpt_*.json.gz")):
    with gzip.open(f, "rt", encoding="utf-8") as fh:
        texts.update(json.load(fh))
log = pd.DataFrame([json.loads(l) for l in open("fetch_ckpt/fetch_log.jsonl") if l.strip()])
log["pmid"] = log["pmid"].astype(str)
log["fetched_at"] = log["fetched_at"].astype(str)
log = log.drop_duplicates("pmid", keep="last").reset_index(drop=True)
assert set(log.pmid) == set(texts), (len(set(log.pmid) ^ set(texts)))
fetch_date_by_pmid = dict(zip(log.pmid, log.fetched_at.str[:10]))
status_by_pmid = dict(zip(log.pmid, log.fetch_status))
progress = open("fetch_ckpt/progress.txt").read().strip().splitlines()
fin = [l for l in progress if l.startswith("FINISHED")]
run_stats = {"n_requests": int(fin[-1].split("reqs=")[1].split()[0]) if fin else None,
             "wall_seconds": float(fin[-1].split("wall_s=")[1]) if fin else None,
             "n_papers_attempted": int(len(log)), "n_targets": 10428,
             "fetch_complete": bool(fin) and len(log) == 10428}

# Source maps. The extraction model saw title + body (full-text papers) or title + abstract.
# Full-text source = title + abstract + body[:120000] (body cap == FT_INPUT_CHAR_CAP the model saw).
# Abstract-only source (README-comparable) = abstract text alone, as quote_trace.census_with_control used.
abs_map, ft_map = {}, {}
for p, v in texts.items():
    a = (v.get("abstract") or "").strip()
    if a:
        abs_map[p] = a
    if (v.get("body") or "").strip():
        ft_map[p] = " ".join(x for x in (v.get("title", ""), a, v["body"]) if x)

summary = {"generated_at": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
           "comparator_version": COMPARATOR_VERSION, "fetch_run": run_stats,
           "sources": {"fulltext_source_definition": "title + abstract + JATS body paragraphs (first 120,000 chars, = FT_INPUT_CHAR_CAP the extraction model saw)",
                       "abstract_source_definition": "Europe PMC abstractText alone (identical basis to the shipped README census)",
                       "n_papers_with_abstract": len(abs_map), "n_papers_with_fulltext": len(ft_map)},
           "per_tier": {}}
report_examples = {}

for t in TIERS:
    t0 = time.time()
    df = pd.read_parquet(f"pots-corpus/{t}/data/{t}_findings.parquet")
    df = df.reset_index(drop=True)
    n = len(df)
    pm = df.pmid.astype(str)
    quotes = df.provenance_quote
    has_q = quotes.notna() & (quotes.astype(str).str.len() > 0)
    is_ft = df.fulltext_status == "retrieved-fulltext"

    # per-row source depth
    depth = np.where(is_ft & pm.isin(ft_map.keys()), "fulltext",
             np.where(pm.isin(abs_map.keys()), "abstract", "none"))
    depth = np.where(has_q, depth, "none")

    exact = pd.array([None] * n, dtype="boolean")
    trace = pd.array([None] * n, dtype="boolean")
    nsh = np.zeros(n, dtype="int64")
    for i in range(n):
        d = depth[i]
        if d == "none":
            continue
        src = ft_map[pm[i]] if d == "fulltext" else abs_map[pm[i]]
        ex, tr, k = quote_traceability(str(quotes[i]), src)
        exact[i] = bool(ex); trace[i] = bool(tr); nsh[i] = int(k)

    ann = pd.DataFrame({
        "row_idx": np.arange(n, dtype="int64"),
        "pmid": pm.values,
        "quote_sha1": [hashlib.sha1(str(q).encode("utf-8")).hexdigest() if h else None for q, h in zip(quotes, has_q)],
        "fulltext_status": df.fulltext_status.values,
        "retrofit_fetch_status": pm.map(status_by_pmid).fillna("not_attempted").values,
        "retrofit_source_depth": depth,
        "retrofit_exact": exact,
        "retrofit_traceable": trace,
        "retrofit_n_shingles": nsh,
        "retrofit_fetch_date": pm.map(fetch_date_by_pmid).values,
        "comparator_version": COMPARATOR_VERSION,
    })
    ann["quote_sha1"] = ann["quote_sha1"].astype("string")
    ann["pmid"] = ann["pmid"].astype("string")
    ann.to_parquet(f"annotations/quote_retrofit_{t}.parquet", index=False)

    # ---- strata with mandatory negative control (census_stratum re-derives the decision) ----
    q_df = df[has_q]
    strata = {}
    ft_rows = q_df[is_ft[has_q]]
    strata["fulltext_rows_vs_fulltext"] = census_stratum(ft_rows, ft_map, quote_traceability,
                                                        f"{t}:retrieved-fulltext rows vs re-fetched full text")
    abs_rows = q_df[~is_ft[has_q]]
    strata["abstract_stratum_rows_vs_abstract"] = census_stratum(abs_rows, abs_map, quote_traceability,
                                                                f"{t}:abstract-only+blocked rows vs re-fetched abstract")
    # full-text rows whose full text could NOT be re-fetched fall back to abstract
    fb_rows = ft_rows[~ft_rows.pmid.astype(str).isin(ft_map.keys())]
    strata["fulltext_rows_fallback_vs_abstract"] = census_stratum(fb_rows, abs_map, quote_traceability,
                                                                 f"{t}:retrieved-fulltext rows lacking re-fetched body, vs abstract")
    # README-comparable: ALL quote rows vs abstract only
    strata["all_rows_vs_abstract_only"] = census_stratum(q_df, abs_map, quote_traceability,
                                                        f"{t}:ALL quote rows vs abstract only")
    strata["fulltext_rows_vs_abstract_only"] = census_stratum(ft_rows, abs_map, quote_traceability,
                                                             f"{t}:retrieved-fulltext rows vs abstract only")

    # consistency: strata counts must equal row-level annotation counts
    d_ft = (ann.retrofit_source_depth == "fulltext")
    d_ab = (ann.retrofit_source_depth == "abstract")
    assert strata["fulltext_rows_vs_fulltext"]["n_checked"] == int(d_ft.sum())
    assert strata["fulltext_rows_vs_fulltext"]["n_traceable"] == int(ann.retrofit_traceable[d_ft].sum())
    n_ab_expected = strata["abstract_stratum_rows_vs_abstract"]["n_checked"] + strata["fulltext_rows_fallback_vs_abstract"]["n_checked"]
    assert n_ab_expected == int(d_ab.sum()), (n_ab_expected, int(d_ab.sum()))

    # ---- paper-level fetch outcomes for this tier ----
    tier_pmids = sorted(set(pm))
    tier_ft_pmids = sorted(set(pm[is_ft]))
    tl = log[log.pmid.isin(tier_pmids)]
    tlf = log[log.pmid.isin(tier_ft_pmids)]
    papers = {
        "n_papers": len(tier_pmids), "n_papers_attempted": int(len(tl)),
        "n_papers_abstract_fetched": int(tl.has_abstract.sum()),
        "n_papers_needing_fulltext": len(tier_ft_pmids), "n_papers_fulltext_attempted": int(len(tlf)),
        "n_papers_fulltext_fetched": int(tlf.has_fulltext.sum()),
        "paper_fetch_status_counts": {k: int(v) for k, v in tl.fetch_status.value_counts().items()},
        "fulltext_paper_failure_causes": {k: int(v) for k, v in tlf[~tlf.has_fulltext].fillna({"fulltext_error": ""}).apply(
            lambda r: r.fetch_status + (f" ({r.fulltext_error})" if r.fulltext_error else "") if r.fetch_status != "http_error" else f"http_error ({r.http_status_or_error})", axis=1).value_counts().items()} if (~tlf.has_fulltext).any() else {},
    }

    n_q = int(has_q.sum())
    n_ver_after = int((ann.retrofit_source_depth != "none").sum())
    n_ver_before = int(((~is_ft) & has_q).sum())          # README basis: abstract-derived rows (abstract-only + blocked)
    tr_after = int(ann.retrofit_traceable.fillna(False).sum())
    # permanent losses: quote rows with no source at all, itemised by paper-level cause
    lost = ann[(ann.retrofit_source_depth == "none")]
    loss_causes = {}
    for _, r in lost.iterrows():
        st = r.retrofit_fetch_status
        if r.fulltext_status == "retrieved-fulltext":
            cause = f"fulltext row; paper {st}; no abstract either"
        else:
            cause = f"abstract-stratum row; paper {st}"
        loss_causes[cause] = loss_causes.get(cause, 0) + 1
    ft_lost_to_abstract = int((is_ft & (ann.retrofit_source_depth == "abstract")).sum())

    row_status_counts = {k: int(v) for k, v in ann.retrofit_fetch_status.value_counts().items()}
    depth_counts = {k: int(v) for k, v in ann.retrofit_source_depth.value_counts().items()}

    summary["per_tier"][t] = {
        "rows_total": n, "rows_with_quote": n_q,
        "rows_by_fulltext_status": {k: int(v) for k, v in df.fulltext_status.value_counts().items()},
        "papers": papers,
        "rows_by_retrofit_fetch_status": row_status_counts,
        "rows_by_retrofit_source_depth": depth_counts,
        "verifiable_before": {"n": n_ver_before, "denominator": n, "pct": round(100 * n_ver_before / n, 2),
                              "readme_pct": README_VERIFIABLE_PCT[t],
                              "basis": "README basis: rows with fulltext_status in {abstract-only, blocked} (abstract-derived); body text discarded"},
        "verifiable_after": {"n": n_ver_after, "denominator": n, "pct": round(100 * n_ver_after / n, 2),
                             "basis": "rows whose own re-fetched source (full text or abstract) exists: retrofit_source_depth != none"},
        "traceable_after_all_verifiable": {"n": tr_after, "denominator": n_ver_after,
                                           "pct": round(100 * tr_after / n_ver_after, 2) if n_ver_after else None,
                                           "pct_of_all_rows": round(100 * tr_after / n, 2)},
        "fulltext_rows_downgraded_to_abstract_source": ft_lost_to_abstract,
        "permanent_losses": {"n_rows_no_source": int(len(lost)), "by_cause": loss_causes},
        "strata": strata,
        "census_seconds": round(time.time() - t0, 1),
    }
    report_examples[t] = strata["fulltext_rows_vs_fulltext"]["untraceable_examples"]
    print(t, "verifiable", n_ver_before, "->", n_ver_after, "of", n, "| traceable", tr_after, "/", n_ver_after,
          "| ft-stratum", strata["fulltext_rows_vs_fulltext"]["traceable_pct"],
          "ctrl", strata["fulltext_rows_vs_fulltext"]["negative_control"]["false_positive_pct"],
          f"{time.time()-t0:.0f}s", flush=True)

# ---- fetch log parquet ----
log_out = log[["pmid", "needs_fulltext", "has_abstract", "has_fulltext", "pmcid", "is_oa",
               "http_status_or_error", "fulltext_error", "body_chars", "fetched_at", "fetch_status"]].copy()
log_out["pmid"] = log_out["pmid"].astype("string")
log_out["body_chars"] = log_out["body_chars"].astype("Int64")
log_out.to_parquet("annotations/retrofit_fetch_log.parquet", index=False)
summary["fetch_log"] = {"n_rows": int(len(log_out)),
                        "fetch_status_counts": {k: int(v) for k, v in log_out.fetch_status.value_counts().items()},
                        "n_has_abstract": int(log_out.has_abstract.sum()),
                        "n_needs_fulltext": int(log_out.needs_fulltext.sum()),
                        "n_has_fulltext": int(log_out.has_fulltext.sum())}
json.dump(summary, open("annotations/retrofit_summary.json", "w"), indent=1, default=str)
json.dump(report_examples, open("handoff/retrofit_examples.json", "w"), indent=1)
print("DONE")
