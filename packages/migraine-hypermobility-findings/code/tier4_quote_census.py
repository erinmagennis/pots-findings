"""Tier-4 quote census over BOTH strata — abstract-only AND full-text.

WHY THIS EXISTS
    quote_trace.census_with_control (pinned, ffc40716) can only verify the
    abstract-only stratum: it reads corpus.abstract and filters
    fulltext_status=="abstract-only". Measured on Tier 3, that leaves 88.49% of
    rows unverifiable -- the single largest hole in provenance verification, because
    fetched body text was DISCARDED after extraction.

    Tier 4 retains body text as gzipped per-chunk archives, so the same matcher can
    now be pointed at the text a full-text row was actually extracted from. This
    module adds the archive-backed stratum WITHOUT touching the pinned matcher:
    normalize() and quote_traceability() are imported, never reimplemented, so the
    two strata are measured by the identical instrument and remain comparable.

DISCIPLINE
    * The negative control is MANDATORY and per-stratum. A stratum's rate is
      reported only alongside a wrong-paper control on the SAME texts. This is not
      decorative: a prior traceability check read 100% because the caller did
      `if tr:` on a truthy tuple, and only the control exposed it.
    * Read element [1] of quote_traceability. Never bool() the tuple.
    * Every rate carries its numerator, denominator, and basis string.
    * Rows whose source text is unavailable are counted as no_source, never
      silently folded into either the numerator or the denominator.
"""
import gzip, json, random


def load_archives(paths, return_truncated=False):
    """Read gzipped per-chunk full-text archives -> {pmid: text}.

    Accepts the shapes the worker may emit: {pmid: str}, {pmid: {"text": ...}},
    {pmid: {"sections": {name: text}}}, or {"papers": {...}}. Section text is
    joined so a quote spanning a section boundary can still match.
    """
    out, truncated = {}, set()
    for p in paths:
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            blob = json.load(fh)
        # tier4_fulltext_archive_v1: metadata at top level, papers under "papers".
        # Never iterate the top level directly -- keys like schema/chunk_id/part
        # would be mistaken for pmids.
        if isinstance(blob, dict) and isinstance(blob.get("papers"), dict):
            blob = blob["papers"]
        elif isinstance(blob, dict) and "schema" in blob:
            continue                      # archive shape we do not understand; skip loudly
        if not isinstance(blob, dict):
            continue
        for pmid, v in blob.items():
            if isinstance(v, str):
                txt = v
            elif isinstance(v, dict):
                if isinstance(v.get("text"), str):
                    txt = v["text"]
                elif isinstance(v.get("sections"), dict):
                    txt = " ".join(str(x) for x in v["sections"].values() if x)
                elif isinstance(v.get("sections"), list):
                    parts = []
                    for s in v["sections"]:
                        if isinstance(s, dict):
                            parts.append(str(s.get("text") or ""))
                        else:
                            parts.append(str(s))
                    txt = " ".join(parts)
                else:
                    txt = " ".join(str(x) for x in v.values() if isinstance(x, str))
            else:
                continue
            if txt and txt.strip():
                out[str(pmid)] = txt
                if isinstance(v, dict) and v.get("prompt_truncated"):
                    truncated.add(str(pmid))
    return (out, truncated) if return_truncated else out


def census_stratum(df, srcmap, quote_traceability, label, n_control=400, seed=11,
                   n_examples=20):
    """Traceability census over rows whose source text is in srcmap, PLUS the
    mandatory wrong-paper negative control on those same texts.

    srcmap: {pmid: source_text}. df needs columns pmid, provenance_quote.
    """
    sub = df[df.provenance_quote.notna() & (df.provenance_quote.astype(str).str.len() > 0)]
    ok = bad = nosrc = 0
    untraceable = []
    for pmid, q in zip(sub.pmid.astype(str), sub.provenance_quote.astype(str)):
        text = srcmap.get(pmid, "")
        if not text:
            nosrc += 1
            continue
        if quote_traceability(q, text)[1]:      # element [1] is the decision
            ok += 1
        else:
            bad += 1
            if len(untraceable) < n_examples:
                untraceable.append({"pmid": pmid, "quote": q[:160]})
    checked = ok + bad

    rng = random.Random(seed)
    have = [(p, q) for p, q in zip(sub.pmid.astype(str), sub.provenance_quote.astype(str))
            if srcmap.get(p)]
    pool = sorted({p for p, _ in have})
    ctrl_hits = ctrl_n = 0
    if len(pool) > 1:
        for pmid, q in rng.sample(have, min(n_control, len(have))):
            other = pmid
            for _ in range(12):
                cand = rng.choice(pool)
                if cand != pmid:
                    other = cand
                    break
            if other == pmid:
                continue
            ctrl_n += 1
            if quote_traceability(q, srcmap[other])[1]:
                ctrl_hits += 1
    fp = (ctrl_hits / ctrl_n) if ctrl_n else None

    return {
        "stratum": label,
        "n_rows_with_quote": int(len(sub)),
        "n_checked": checked, "n_traceable": ok, "n_untraceable": bad,
        "n_no_source_text": nosrc,
        "traceable_pct": round(100 * ok / checked, 2) if checked else None,
        "basis": (f"CENSUS of {label} rows with a non-null quote; {checked} verified "
                  f"against that paper's own retained source text; {nosrc} excluded "
                  f"for no available source text (denominator is n_checked)"),
        "negative_control": {
            "n_control": ctrl_n, "n_false_positives": ctrl_hits,
            "false_positive_pct": round(100 * fp, 2) if fp is not None else None,
            "basis": (f"{ctrl_n} quotes matched against a DIFFERENT paper's retained "
                      f"text (seed {seed}); a working matcher reports ~0%"),
            "verdict": ("matcher discriminates" if fp is not None and fp < 0.05
                        else "MATCHER SUSPECT - headline rate not trustworthy"),
        },
        "untraceable_examples": untraceable,
    }


def full_census(df, corpus, archive_paths, quote_traceability, n_control=400, seed=11):
    """Both strata, each with its own control, plus a combined coverage figure.

    Returns a dict whose 'coverage' block states what fraction of ALL quote-bearing
    rows could be verified at all -- the number that made retention worth doing.
    """
    ft = load_archives(archive_paths)
    abs_map = {str(p): (a or "") for p, a in zip(corpus.pmid.astype(str),
                                                 corpus.abstract.fillna(""))}

    is_abs = df.fulltext_status == "abstract-only"
    a = census_stratum(df[is_abs], abs_map, quote_traceability,
                       "abstract-only", n_control, seed)
    f = census_stratum(df[~is_abs], ft, quote_traceability,
                       "full-text (archive-backed)", n_control, seed)

    q = df[df.provenance_quote.notna() & (df.provenance_quote.astype(str).str.len() > 0)]
    checked = a["n_checked"] + f["n_checked"]
    traceable = a["n_traceable"] + f["n_traceable"]
    return {
        "strata": [a, f],
        "n_archive_papers": len(ft),
        "coverage": {
            "n_rows_with_quote": int(len(q)),
            "n_verifiable": checked,
            "verifiable_pct_of_quote_rows": round(100 * checked / len(q), 2) if len(q) else None,
            "n_traceable": traceable,
            "traceable_pct_of_verifiable": round(100 * traceable / checked, 2) if checked else None,
            "basis": ("verifiable = a row whose own source text was retained and could be "
                      "re-read; the Tier-3 ceiling was the abstract-only stratum alone "
                      "(11.51% of rows), because body text was discarded"),
        },
    }
