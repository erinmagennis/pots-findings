"""Quote traceability + its MANDATORY negative control.

HISTORY THIS ENCODES
    A previous traceability check read 100% because the caller did `if tr:` on a
    function returning a TUPLE -- and a non-empty tuple is always truthy. The
    wrong-paper negative control read 400/400 false positives and exposed it.
    A metric without a control is not a measurement, so the control ships here,
    in the same file, and `census_with_control` refuses to report a rate without it.

CONTRACT
    quote_traceability(quote, text) -> (exact, traceable, n_shingles)
        exact      : normalized quote is a verbatim substring of normalized text
        traceable  : exact OR shingle-overlap >= THRESH (handles the +/- and
                     multi-sentence spans that cause false byte-mismatches)
        n_shingles : how many shingles were compared -- the basis of the decision
    Callers MUST read element [1], never bool() the tuple. tier3_qa.quote_census
    already does this correctly; this docstring exists so a future caller does too.
"""
import re, unicodedata, html

SHINGLE_N = 8
THRESH = 0.60          # fraction of quote shingles that must appear in the source
MIN_CHARS = 25         # quotes shorter than this are too weak to judge by overlap


def normalize(s):
    """Unicode-fold, collapse whitespace, strip punctuation that differs between
    JATS and abstract renderings. Deliberately NOT lossy about digits -- a number
    is the thing number_in_quote checks."""
    if s is None:
        return ""
    # Europe PMC abstracts arrive with UNESCAPED HTML entities (&#x2009; thin space,
    # &#xa0; nbsp, &#xb1; plus-minus). Measured cause of 163 false "untraceable"
    # rows: 'ASD&#x2009;+&#x2009;Anxiety' could never match 'ASD + Anxiety'.
    # Decode BEFORE folding, twice, because some records are double-escaped.
    s = html.unescape(html.unescape(str(s)))
    s = unicodedata.normalize("NFKD", s)
    s = s.replace("\u2010", "-").replace("\u2011", "-").replace("\u2012", "-")
    s = s.replace("\u2013", "-").replace("\u2014", "-").replace("\u2212", "-")
    s = s.replace("\u2018", "'").replace("\u2019", "'")
    s = s.replace("\u201c", '"').replace("\u201d", '"')
    s = s.lower()
    s = re.sub(r"[^\w\s%.<>=+/-]", " ", s)
    # Drop STANDALONE dash tokens (typographic separators inserted by one renderer
    # and not the other). Intra-word hyphens are preserved: COMPASS-31 and
    # beta-blocker must stay single tokens, or every shingle spanning them shifts.
    s = re.sub(r"\s+[-/]+\s+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _shingles(toks, n=SHINGLE_N):
    """Adaptive n: on a short quote, an 8-token window yields so few shingles that a
    single inserted token breaks every one of them (measured: a 12-token quote gave
    4 shingles and 0.0 overlap despite being a true match). Shrink n for short spans
    so the overlap statistic has enough samples to be meaningful."""
    if not toks:
        return set()
    n = min(n, max(4, len(toks) // 3))
    if len(toks) < n:
        return {" ".join(toks)}
    return {" ".join(toks[i:i + n]) for i in range(len(toks) - n + 1)}


def quote_traceability(quote, text):
    """-> (exact, traceable, n_shingles). See CONTRACT above: read element [1]."""
    q, t = normalize(quote), normalize(text)
    if not q or not t:
        return (False, False, 0)
    if len(q) < MIN_CHARS:
        # too short to judge by overlap; require an exact containment
        ex = q in t
        return (ex, ex, 0)
    if q in t:
        return (True, True, 0)
    qs = _shingles(q.split())
    ts = _shingles(t.split())
    if not qs:
        return (False, False, 0)
    hit = len(qs & ts) / len(qs)
    return (False, hit >= THRESH, len(qs))


def census_with_control(df, corpus, subset="abstract-only", n_control=400, seed=11):
    """Traceability census PLUS a wrong-paper negative control on the same rows.

    The control pairs each sampled quote with a DIFFERENT paper's text. A matcher
    that is working reports a near-zero control rate; a broken one reports ~100%
    and invalidates the headline number. Both rates are returned with their bases;
    the caller cannot get one without the other.
    """
    import random
    sub = df[df.fulltext_status == subset] if subset else df
    sub = sub[sub.provenance_quote.notna() & (sub.provenance_quote.astype(str).str.len() > 0)]
    srcmap = dict(zip(corpus.pmid.astype(str), corpus.abstract.fillna("")))

    ok = bad = nosrc = 0
    untraceable = []
    for pmid, q in zip(sub.pmid.astype(str), sub.provenance_quote.astype(str)):
        text = srcmap.get(pmid, "")
        if not text:
            nosrc += 1
            continue
        if quote_traceability(q, text)[1]:
            ok += 1
        else:
            bad += 1
            if len(untraceable) < 20:
                untraceable.append({"pmid": pmid, "quote": q[:160]})
    checked = ok + bad

    # NEGATIVE CONTROL: same quotes, deliberately wrong papers
    rng = random.Random(seed)
    have = [(p, q) for p, q in zip(sub.pmid.astype(str), sub.provenance_quote.astype(str))
            if srcmap.get(p)]
    pool = [p for p, _ in have]
    ctrl_hits = ctrl_n = 0
    if len(pool) > 1:
        picks = rng.sample(have, min(n_control, len(have)))
        for pmid, q in picks:
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

    return {
        "subset": subset,
        "n_rows_in_subset": int(len(sub)),
        "n_checked": checked, "n_traceable": ok, "n_untraceable": bad,
        "n_no_source_text": nosrc,
        "traceable_pct": round(100 * ok / checked, 2) if checked else None,
        "basis": (f"CENSUS of every fulltext_status=={subset} row with a non-null quote; "
                  f"{checked} verified against that paper's own abstract, "
                  f"{nosrc} excluded for no available source text"),
        "negative_control": {
            "n_control": ctrl_n, "n_false_positives": ctrl_hits,
            "false_positive_pct": round(100 * ctrl_hits / ctrl_n, 2) if ctrl_n else None,
            "basis": f"{ctrl_n} quotes matched against a DIFFERENT paper's abstract "
                     f"(random seed {seed}); a working matcher reports ~0%",
            "verdict": ("matcher discriminates" if ctrl_n and ctrl_hits / ctrl_n < 0.05
                        else "MATCHER SUSPECT — headline rate not trustworthy"),
        },
        "untraceable_examples": untraceable,
    }


def selftest():
    """-> list of FAILURES (empty means all pass)."""
    f = []
    text = ("Plasma norepinephrine was elevated by 34% in patients with postural "
            "orthostatic tachycardia syndrome compared with healthy controls, and "
            "correlated with symptom burden on the COMPASS-31 instrument.")
    other = ("Mast cell activation markers including tryptase were measured in a "
             "cohort of patients with hypermobile Ehlers-Danlos syndrome and no "
             "significant difference was observed between groups at baseline.")
    exact_q = "Plasma norepinephrine was elevated by 34% in patients"
    if quote_traceability(exact_q, text)[1] is not True:
        f.append("exact quote not traceable")
    if quote_traceability(exact_q, text)[0] is not True:
        f.append("exact quote not flagged exact")
    # unicode / dash variance must still trace
    if not quote_traceability("elevated by 34% in patients with postural \u2013 orthostatic tachycardia syndrome", text)[1]:
        f.append("dash/unicode variant not traceable")
    # NEGATIVE: a quote from a different paper must NOT trace
    if quote_traceability(exact_q, other)[1]:
        f.append("wrong-paper quote traced (matcher is blind)")
    # the tuple trap: element [1] must be the decision, and a False decision must
    # still return a truthy tuple (proving bool(tuple) is the wrong test)
    tr = quote_traceability(exact_q, other)
    if not isinstance(tr, tuple) or bool(tr) is not True or tr[1] is not False:
        f.append(f"tuple-trap invariant broken: {tr}")
    return f
