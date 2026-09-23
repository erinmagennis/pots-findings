"""Cross-tier entity canonicalizer (built over tiers 1-4; mapping-only, never mutates a corpus).

Discipline inherited from the pinned tier3_vocab.py: additive-only, zero-collision assertion,
one canonical form per raw string. Its DEFAULT str.lower() canonical_fn is UNSAFE and is NOT used.

CASE PROTECTION RULE (the reason lowercasing is unsafe):
  A single-token gene symbol is case-protected -- CNTNAP2 (HGNC, human) and Cntnap2 (MGI, mouse)
  are distinct entities. Case protection is scoped to SINGLE-TOKEN symbols only, because the
  HGNC-upper / MGI-title convention that carries the species signal applies to symbols, not to
  multi-word protein names ("corticotropin-releasing factor"), where case is free variation.

GENE-SYMBOL DETECTION (evidence order, no model-emitted identifiers):
  G1  entity_kind == 'gene/protein' (tiers 3-4 authority column) AND single-token symbolish -> protected
  G1b entity_kind == 'gene/protein' but multi-word                                          -> not protected
  G2  entity_kind known and != 'gene/protein'                                               -> not protected
  G3  no entity_kind, but single-token symbolish and present in the AUTHORITY gene lexicon   -> protected
  G0  no evidence                                                                            -> not protected
  The authority lexicon is built by tokenizing `gene_marker` at rows with gene_resolved == True
  (gene_id_source == 'pipeline_symbol_lookup'), i.e. symbols the pipeline verified against an
  authority -- plus entity strings authoritatively kinded 'gene/protein' in tiers 3-4.

ERROR MODES (measured, not assumed):
  - A gene symbol never seen resolved and never kinded is unprotected; a differently-cased twin
    would merge. Bounded by lexicon coverage (5163 symbols; all mandated control pairs covered).
  - A non-gene acronym colliding with a real symbol (eGFR vs EGFR) is over-protected: it stays
    unmerged from its own case variants. Conservative -- splits, never merges.
  - Kind conflict within a candidate group splits the group (520 splits). This can refuse a
    legitimate merge when one variant is mis-kinded (1 observed: CASPR2/Caspr2 antibody).
"""
import re, unicodedata

DASH = dict.fromkeys(map(ord, "\u2010\u2011\u2012\u2013\u2014\u2015\u2212\u00ad"), "-")
SYM  = re.compile(r"^[A-Za-z][A-Za-z0-9]{0,8}(?:-[A-Za-z0-9]{1,4})?$")

def norm_form(s):
    """Unicode/whitespace/punctuation normalization. CASE IS PRESERVED."""
    s = unicodedata.normalize("NFKC", str(s)).translate(DASH).replace("\u00a0", " ")
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"^[\s\-\u2022\*\.,;:]+|[\s\-\u2022\*\.,;:]+$", "", s)
    s = re.sub(r"\s*-\s*", "-", s)
    s = re.sub(r"\s*/\s*", "/", s)
    s = re.sub(r"\s*\(\s*", "(", s)
    s = re.sub(r"\s*\)\s*", ")", s)
    return s.strip()

def punct_key(s):
    """Punctuation-insensitive skeleton. Case preserved -- do not casefold here."""
    return re.sub(r"[^0-9A-Za-z]+", "", s)

def is_symbol_token(n):
    toks = [t for t in re.split(r"[;,/\s\(\)\[\]]+", n) if t]
    return len(toks) == 1 and bool(SYM.match(toks[0])) and 2 <= len(toks[0]) <= 10

def build_gene_lexicon(frames):
    """Authority symbols only, BOTH halves of the documented rule:
      (i)  tokens of `gene_marker` at rows where gene_resolved is True
           (gene_id_source == 'pipeline_symbol_lookup'), and
      (ii) single-token entity strings carrying entity_kind == 'gene/protein'
           in tiers 3-4 (authority column).
    Half (i) alone yields 4950 symbols; both halves yield the 5163 used to build and
    validate entity_vocabulary_crosstier.parquet. Callers must not use half (i) alone --
    it silently weakens case protection relative to the ERROR MODES section above.
    """
    lex = set()
    for df in frames:
        if "gene_marker" in df and "gene_resolved" in df:
            m = df["gene_resolved"].fillna(False).astype(bool)
            for v in df.loc[m, "gene_marker"].dropna().astype(str):
                for t in re.split(r"[;,/\s\(\)\[\]]+", norm_form(v)):
                    if t and is_symbol_token(t):
                        lex.add(t.upper())
        if "entity_kind" in df and "entity" in df:
            sub = df.loc[df["entity_kind"].eq("gene/protein") & df["entity"].notna(), "entity"]
            for e in sub.astype(str):
                n = norm_form(e)
                if n and is_symbol_token(n):
                    lex.add(n.upper())
    return lex

def case_protected(n, kind_evidence, lexicon):
    """(protected, rule). kind_evidence: {string: {entity_kind: count}} from tiers 3-4."""
    sym = is_symbol_token(n)
    c = {k: v for k, v in (kind_evidence.get(n) or {}).items() if k is not None}
    if c:
        top = max(c.items(), key=lambda kv: kv[1])[0]
        if top == "gene/protein":
            return (True, "G1_kind_gene_protein_single_token_symbol") if sym \
                   else (False, "G1b_kind_gene_protein_multiword_no_case_risk")
        return False, "G2_entity_kind_nongene"
    if sym and n.upper() in lexicon:
        return True, "G3_authority_gene_lexicon_single_token"
    return False, "G0_no_gene_evidence"

def group_key(n, kind_evidence, lexicon):
    """Case-folded skeleton for unprotected strings; case-EXACT skeleton for gene symbols."""
    prot, _ = case_protected(n, kind_evidence, lexicon)
    pk = punct_key(n)
    return ("G", pk) if prot else ("N", pk.casefold())

def assert_no_collision(mapping_df, raw_col="raw_entity", canon_col="canonical_entity"):
    """Pinned tier3_vocab invariant: one canonical form per raw string, no duplicate raws."""
    assert mapping_df[raw_col].duplicated().sum() == 0, "duplicate raw strings"
    assert mapping_df.groupby(raw_col)[canon_col].nunique().max() == 1, "collision: raw -> 2 canonicals"
