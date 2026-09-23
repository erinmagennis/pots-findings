"""Comparator symmetry tests — entity codes, whitespace-class characters, superscripts.

WHY THIS FILE EXISTS
    128 shipped quotes (t1 2, t2 82, t3 2, t4 42) carry raw HTML entity codes
    (`p&#x202f;<&#x2009;0.001`) because the extraction model was fed un-unescaped
    text. Their retained source carries the same codes; freshly fetched source does
    not. A comparator that normalizes only one side would report these as
    fabricated quotes during a full-text retrofit. `quote_trace.normalize()` is
    applied to BOTH sides inside `quote_traceability()`, so it is symmetric by
    construction — this file pins that property with one case per failure mode,
    and it is the regression gate before any retrofit census runs.

    Measured 2026-09-16 on the 42 Tier-4 rows against their own retained archive:
    42/42 traceable as stored, 42/42 with the quote unescaped, 42/42 against an
    unescaped (clean) copy of the archive; full Tier-4 census 15,504/15,646 = 99.09%
    row-identical on raw and unescaped archive, wrong-paper control 0/400.

    Never "repair" a stored quote. Normalization is a comparison-time operation.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quote_trace import quote_traceability, normalize

CLEAN_SRC = ("Orthostatic hypotension frequency was 35.8 % based on the supine-to-stand "
             "test, and heart-rate variability was reduced (p < 0.001) in the patient "
             "group compared with controls; heterogeneity was moderate (I\u00b2 = 45%).")
CODED_SRC = ("Orthostatic hypotension frequency was 35.8&#xa0;% based on the supine-to-stand "
             "test, and heart-rate variability was reduced (p&#x202f;<&#x2009;0.001) in the "
             "patient group compared with controls; heterogeneity was moderate (I&#xb2; = 45%).")
DOUBLE_SRC = CODED_SRC.replace("&#", "&amp;#")

CASES = [
    # (name, quote, source, expected traceable)
    ("coded quote vs clean source (the retrofit case)",
     "frequency was 35.8&#xa0;% based on the supine-to-stand test, and heart-rate variability was reduced (p&#x202f;<&#x2009;0.001)", CLEAN_SRC, True),
    ("clean quote vs coded source (the retained-archive case)",
     "frequency was 35.8 % based on the supine-to-stand test, and heart-rate variability was reduced (p < 0.001)", CODED_SRC, True),
    ("coded quote vs coded source",
     "frequency was 35.8&#xa0;% based on the supine-to-stand test, and heart-rate variability was reduced (p&#x202f;<&#x2009;0.001)", CODED_SRC, True),
    ("clean quote vs double-escaped source",
     "frequency was 35.8 % based on the supine-to-stand test, and heart-rate variability was reduced (p < 0.001)", DOUBLE_SRC, True),
    ("literal nbsp / thin / narrow-no-break in quote vs ASCII source",
     "frequency was 35.8\u00a0% based on the supine-to-stand test, and heart-rate variability was reduced (p\u202f<\u20090.001)", CLEAN_SRC, True),
    ("superscript I\u00b2 quote vs coded source",
     "in the patient group compared with controls; heterogeneity was moderate (I\u00b2 = 45%)", CODED_SRC, True),
    ("plain I2 quote vs superscript source (folding must be symmetric, not one-sided)",
     "in the patient group compared with controls; heterogeneity was moderate (I2 = 45%)", CLEAN_SRC, True),
    ("negative control: unrelated quote must not trace",
     "Serum tryptase was elevated in mast cell activation syndrome patients with hypermobile Ehlers-Danlos", CLEAN_SRC, False),
]


def run():
    failures = []
    for name, q, s, exp in CASES:
        got = quote_traceability(q, s)[1]
        if got is not exp:
            failures.append(f"{name}: expected {exp}, got {got}")
    # normalize() must be idempotent and identical on coded/clean/double-coded input
    forms = {normalize(CLEAN_SRC), normalize(CODED_SRC), normalize(DOUBLE_SRC)}
    if len(forms) != 1:
        failures.append(f"normalize() not entity-symmetric: {len(forms)} distinct forms")
    if normalize(normalize(CLEAN_SRC)) != normalize(CLEAN_SRC):
        failures.append("normalize() not idempotent")
    return failures


if __name__ == "__main__":
    f = run()
    for x in f:
        print("FAIL", x)
    print(f"{len(CASES) - len([x for x in f if not x.startswith('normalize')])}/{len(CASES)} cases pass; "
          f"{'OK' if not f else str(len(f)) + ' FAILURES'}")
    sys.exit(1 if f else 0)
