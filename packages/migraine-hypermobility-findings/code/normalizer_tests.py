"""Text-normalizer test suite for quote-provenance matching.

Every case here corresponds to a bug that produced a FALSE defect reading on a real corpus.
Run this BEFORE trusting any quote-match statistic.
"""
import re, html, unicodedata

# A tag needs a letter right after '<' or '</', AND must close without another '<'.
# Requiring the name be tag-like (letters/digits only, then space or '>') keeps 'x<y' as prose.
# Whitelist of real HTML/JATS element names. A heuristic pattern cannot distinguish a tag from
# prose like 'x<y then y>x' — that exact string defeated three successive regexes.
TAGNAMES = ('p','br','b','i','em','strong','sub','sup','span','div','a','table','thead','tbody','tr',
 'td','th','ul','ol','li','h1','h2','h3','h4','h5','h6','sec','title','abstract','article','front',
 'body','back','ref','xref','italic','bold','underline','graphic','fig','caption','label','list',
 'list-item','disp-quote','inline-formula','mml:math','tex-math','named-content','styled-content',
 'break','hr','img','pre','code','blockquote','dl','dt','dd','tfoot','colgroup','col','col-group')

GREEK = {'\u03b1':'a','\u03b2':'b','\u03b3':'g','\u03b4':'d','\u03b5':'e','\u03ba':'k','\u03bb':'l',
         '\u03bc':'u','\u03c3':'s','\u03c4':'t','\u03c9':'w','\u0394':'d','\u03a9':'w'}

TAG = re.compile(r'</?(?:' + '|'.join(TAGNAMES) + r')(?:\s[^<>]*?)?/?>', re.I)

def normalize(s):
    s = html.unescape(html.unescape(str(s)))   # twice: some sources double-encode
    s = TAG.sub(' ', s)                        # tags -> SPACE, never '' (else words glue)
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = ''.join(GREEK.get(c, c) for c in s)   # alpha1 vs a1 vs α1 must compare equal
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', ' ', s.lower())).strip()

CASES = [
 # (name, input, must_contain, must_not_contain)
 ("inequality_not_a_tag",  "Patients (P < .05). Eight improved > baseline.", ["eight improved"], []),
 ("greedy_tag_span",       "a < b and c > d then <b>real</b> tag",           ["a b and c d", "real"], []),
 ("tag_becomes_space",     "<p>chronic disease</p><p>The cohort</p>",        ["disease the cohort"], ["diseasethe"]),
 ("double_encoded_entity", "&amp;#x3b1;1-adrenergic",                        ["a1 adrenergic"], []),
 ("single_entity",         "&#x3b1;1 receptor",                              ["a1 receptor"], []),
 ("accent_stripped",       "Sj\u00f6gren syndrome",                          ["sjogren syndrome"], []),
 ("nbsp_collapses",        "small\u00a0fiber\u00a0neuropathy",               ["small fiber neuropathy"], []),
 ("self_closing_tag",      "line<br/>break",                                ["line break"], ["linebreak"]),
 ("attribute_with_quotes", '<span class="x">tilt table</span>',              ["tilt table"], ["span", "class"]),
 ("math_lt_gt_pair",       "if x<y then y>x holds",                         ["if x y then y x holds"], []),
]

def run():
    fails = []
    for name, src, must, mustnt in CASES:
        out = normalize(src)
        for m in must:
            if m not in out: fails.append((name, f"missing {m!r}", out))
        for m in mustnt:
            if m in out: fails.append((name, f"unexpected {m!r}", out))
    return fails

if __name__ == "__main__":
    f = run()
    print(f"normalizer tests: {len(CASES)-len({x[0] for x in f})}/{len(CASES)} passed")
    for name, why, out in f: print(f"  FAIL {name}: {why} -> {out!r}")
    assert not f, f"{len(f)} normalizer assertions failed"
    print("all pass")
