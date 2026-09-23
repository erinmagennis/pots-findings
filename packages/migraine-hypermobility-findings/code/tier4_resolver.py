"""Tier-4 multi-authority name->identifier resolver.

Supersedes multi_authority_resolver.py@4240086b (left intact). Matching discipline is
UNCHANGED and is repeated here because it is the whole point of the module:

  * The MODEL never emits identifiers. Only names go in; IDs come from authorities.
  * EXACT label match, or a synonym the AUTHORITY ITSELF asserts. Never fuzzy.
  * A name that does not match is left NULL. A missing ID is honest; a wrong ID
    corrupts every downstream join.
  * Every ID carries provenance naming the authority AND the match path.
  * 'other'/null entity_kind has NO authority and is never guessed at.

WHAT CHANGED, AND WHY -- OPTION (b): RECORD THE MINTING ONTOLOGY
----------------------------------------------------------------
Measured defect (Tier-3 grounded corpus, computed not asserted): 49 rows carried a
provenance tag naming authority `hp` while holding an id minted by another ontology.
Id-level prefix breakdown of the 49 offending ids: MPATH 19, PATO 13, GO 9, NBO 6,
UBERON 2. Cause: OLS4's `ontology=hp` search returns terms IMPORTED into HPO with their
NATIVE prefixes (`is_defining_ontology=false`). The stage that emitted those 49 rows --
the HPO-verification path, NOT multi_authority_resolver._ols -- stored `obo_id` verbatim
while tagging the queried authority `hp`. The ids and labels were RIGHT; the provenance
CLAIM was wrong.

For the avoidance of doubt about the pinned module: multi_authority_resolver@4240086b's
`_ols` DOES filter on the queried authority's prefix (`if oid.startswith(prefix)` in both
its exact and loosened passes), so it could not itself have emitted a non-HP id under an
`hp` tag. That filter is option (a) already in force on the entity path -- which is why
zero offenders appear in `ontology_id_source`, and equally why imported terms are
silently dropped there rather than recorded.

WHERE THE DEFECT ACTUALLY LIVES (measured, and narrower than the handoff assumed).
All 49 offending rows sit in `hpo_ids_verified` / `hpo_id_source` -- the HPO-verification
stage, whose tag vocabulary is the bare {authority_lookup_ols_hp, ..._hp_synonym}.
ZERO offenders sit in `entity_ontology_id_resolved` / `ontology_id_source`: the pinned
multi_authority_resolver@4240086b already prefix-filters inside `_ols`, i.e. it ALREADY
implements option (a) -- and that filter is precisely why it silently drops imported
terms instead of recording them. So this module does two things: it removes the
option-(a) filter from the entity path in favour of recorded minting, and it gives the
HPO-verification path (resolve_hpo_terms) the same truthful provenance shape, which is
where the 49 came from.

The handoff offered two fixes. Both were quantified against that positive control before
choosing:

  (a) constrain returns to ids whose prefix matches the queried authority
        -> keeps  64/113 ids and 26/49 rows; NULLS 23 rows outright and drops 49 ids.
  (b) record the MINTING ontology as its own column and make the tag say so
        -> keeps 113/113 ids and 49/49 rows; nothing correct is discarded.

Option (b) is implemented. Justification: an independent re-check of all 21 distinct
offending ids against their DEFINING ontology (OLS4, `is_defining_ontology=true`) found
21/21 with exact label agreement -- e.g. PATO:0001815 'fatigability', GO:0070527
'platelet aggregation', MPATH:196 'dermatitis'. These are real terms, exactly matched,
that HPO itself imports. Option (a) would delete 49 verified-correct identifiers to fix
a labelling bug, trading a provenance defect for a recall defect. Option (b) fixes the
thing that was actually broken -- the claim -- and makes the import relationship
machine-readable instead of silently collapsing it.

Provenance shape (new)
----------------------
  source tag, term minted by the queried authority:
      authority_lookup_ols_hp_exact
  source tag, term IMPORTED into the queried authority from elsewhere:
      authority_lookup_ols_hp_via_pato_exact
  and, either way, a separate column carries the minting ontology:
      <field>_minting_ontology  -> 'hp' | 'pato' | 'go' | ... (lowercase OBO id prefix)

The tag still names the queried authority AND the match path, so every Tier-3 reader
keeps working; the `_via_<minting>` infix and the column are additive. Invariant 9
(tier4_invariants_ext.py) reads either form and still FAILS on a bare `..._ols_hp` tag
sitting on a non-HP id -- the exact Tier-3 defect.

Cache compatibility
-------------------
The stored tuple grows from 3 to 4 elements. resolution_cache-format parquets written by
the old build (8,216 primed pairs, 5,095 hits last run) are NOT discarded: load_cache_v4
upgrades them in memory. The upgrade is deterministic relabelling from data already in
hand -- the minting ontology is read off the id prefix that the authority itself
returned, and an untruthful bare tag is rewritten to its `_via_<minting>` form. No
network call, no re-matching, no fuzzy step: the (name -> id) decision is never revisited.
"""
import json, re, time, urllib.parse, urllib.request

RESOLVER_VERSION = "tier4_resolver@1"
OLS4 = "https://www.ebi.ac.uk/ols4/api/search"
UNIPROT = "https://rest.uniprot.org/uniprotkb/search"
UA = {"Accept": "application/json"}
_CACHE = {}

# authority tag -> the id prefix that authority mints
AUTH_PREFIX = {"hp": "HP", "chebi": "CHEBI", "cl": "CL", "uberon": "UBERON",
               "ncbitaxon": "NCBITaxon", "uniprot": "UniProt"}


def _get(url, tries=4, pause=0.34):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            code = getattr(e, "code", None)
            if a == tries - 1 or (code and code not in (429, 500, 502, 503, 504)):
                return None
            time.sleep(pause * (2.2 ** a))
    return None


def minting_of(obo_id):
    """Lowercase minting-ontology tag read off an id prefix. 'PATO:0001815' -> 'pato'."""
    if not isinstance(obo_id, str) or ":" not in obo_id:
        return None
    return obo_id.split(":", 1)[0].strip().lower()


def _ols(name, ontology):
    """Exact label, then AUTHORITY-ASSERTED synonym, within ONE ontology's scope.

    Returns (obo_id, label, match_path, minting_ontology). Unlike the Tier-3 build this
    does NOT filter on the queried authority's prefix -- a term imported into the queried
    ontology is a legitimate answer from that ontology's scope. What changes is that the
    ontology which MINTED the id is returned alongside it, so the caller can state it.
    Matching itself is untouched: exact label or authority-asserted synonym, never fuzzy.
    """
    q = urllib.parse.quote(name)
    fields = "iri,label,obo_id,synonym,ontology_name,is_defining_ontology"
    nl = name.strip().lower()
    d = _get(f"{OLS4}?q={q}&ontology={ontology}&rows=8&exact=true&fieldList={fields}")
    docs = ((d or {}).get("response") or {}).get("docs") or []
    for doc in docs:
        oid = doc.get("obo_id") or ""
        if oid and (doc.get("label") or "").strip().lower() == nl:
            return oid, doc.get("label"), "exact", minting_of(oid)
    d = _get(f"{OLS4}?q={q}&ontology={ontology}&rows=12&fieldList={fields}")
    docs = ((d or {}).get("response") or {}).get("docs") or []
    for doc in docs:
        oid = doc.get("obo_id") or ""
        if not oid:
            continue
        if (doc.get("label") or "").strip().lower() == nl:
            return oid, doc.get("label"), "exact", minting_of(oid)
        if any((s or "").strip().lower() == nl for s in (doc.get("synonym") or [])):
            return oid, doc.get("label"), "synonym", minting_of(oid)
    return None, None, None, None


def _uniprot(name):
    """Human protein by EXACT recommended/alternative name. Reviewed (SwissProt) only."""
    q = urllib.parse.quote(f'protein_name:"{name}" AND organism_id:9606 AND reviewed:true')
    d = _get(f"{UNIPROT}?query={q}&format=json&size=5&fields=accession,protein_name,id")
    nl = name.strip().lower()
    for r in (d or {}).get("results", []):
        acc = r.get("primaryAccession")
        pd_ = r.get("proteinDescription") or {}
        rec = ((pd_.get("recommendedName") or {}).get("fullName") or {}).get("value")
        if rec and rec.strip().lower() == nl:
            return f"UniProt:{acc}", rec, "exact", "uniprot"
        alts = [((a.get("fullName") or {}).get("value")) for a in (pd_.get("alternativeNames") or [])]
        if any(a and a.strip().lower() == nl for a in alts):
            return f"UniProt:{acc}", rec or name, "synonym", "uniprot"
    return None, None, None, None


ROUTES = {
    "chemical/metabolite":   ("chebi", "chebi"),
    "cell-type":             ("cl", "cl"),
    "anatomical-structure":  ("uberon", "uberon"),
    "physiological-measure": ("hp", "hp"),
    "pathogen":              ("ncbitaxon", "ncbitaxon"),
}


def build_source_tag(authority, match_path, minting):
    """Truthful provenance string: queried authority, minting ontology, match path.

    minting == authority (or unknown) -> 'authority_lookup_ols_hp_exact'
    minting != authority              -> 'authority_lookup_ols_hp_via_pato_exact'
    """
    if authority == "uniprot":
        return f"authority_lookup_uniprot_{match_path}"
    if minting and minting != authority:
        return f"authority_lookup_ols_{authority}_via_{minting}_{match_path}"
    return f"authority_lookup_ols_{authority}_{match_path}"


def resolve_entity(name, kind):
    """-> (id, label, source, minting_ontology).

    FOUR-tuple (Tier-3 returned three). source names the queried authority, the minting
    ontology when it differs, and the match path. Unmatched names return
    (None, None, 'unresolved_nulled', None) -- never a guess.
    """
    if not isinstance(name, str) or not name.strip() or not isinstance(kind, str):
        return None, None, "unresolved_nulled", None
    key = (name.strip().lower(), kind)
    if key in _CACHE:
        return _CACHE[key]
    nm = name.strip()
    if kind == "gene/protein":
        i, l, path, mint = _uniprot(nm)
        auth = "uniprot"
    elif kind in ROUTES:
        onto, auth = ROUTES[kind]
        i, l, path, mint = _ols(nm, onto)
    else:
        # 'other'/null kind: NO authority is clearly right, so none is asked. Leaving the
        # kind unrouted is the design, not an omission.
        out = (None, None, "unresolved_nulled", None)
        _CACHE[key] = out
        return out
    out = (i, l, build_source_tag(auth, path, mint), mint) if i else (None, None, "unresolved_nulled", None)
    _CACHE[key] = out
    return out


def resolve_hpo_terms(names):
    """HPO-verification path, truthful provenance. This is where the 49 offenders came from.

    names -> (ids, labels, source_tag, minting_ontologies) as ';'-joined strings, in the
    same shape as the Tier-3 columns hpo_ids_verified / hpo_labels_verified /
    hpo_id_source, plus the new hpo_id_minting_ontology.

    Unresolvable names are DROPPED, never guessed. If nothing resolves, the row's id is
    None and the tag is 'unresolved_nulled'. When any returned id was minted outside HPO
    the tag carries `_via_<mint>[+<mint>...]`, so the claim matches the ids beside it.
    """
    ids, labels, mints, paths = [], [], [], []
    for nm in (names or []):
        if not isinstance(nm, str) or not nm.strip():
            continue
        i, l, path, mint = _ols(nm.strip(), "hp")
        if not i:
            continue
        ids.append(i); labels.append(l or nm.strip()); mints.append(mint or ""); paths.append(path)
    if not ids:
        return None, None, "unresolved_nulled", None
    path = "synonym" if "synonym" in paths else "exact"
    foreign = sorted({m for m in mints if m and m != "hp"})
    if foreign:
        tag = f"authority_lookup_ols_hp_via_{'+'.join(foreign)}_{path}"
    else:
        tag = f"authority_lookup_ols_hp_{path}"
    return ";".join(ids), ";".join(labels), tag, ";".join(mints)


# ---------------------------------------------------------------- cache compatibility

def upgrade_cache_entry(value):
    """Old 3-tuple (id, label, source) -> new 4-tuple with a truthful tag.

    Deterministic relabelling only. The minting ontology is read off the id prefix the
    authority itself returned; a bare tag sitting on a foreign-minted id is rewritten to
    its `_via_<minting>` form. The name->id decision is never revisited and no network
    call is made, so all primed pairs survive the format change.
    """
    if value is None:
        return None
    if len(value) >= 4:
        return tuple(value[:4])
    rid, label, source = value[0], value[1], value[2]
    if not rid:
        return (rid, label, source or "unresolved_nulled", None)
    mint = minting_of(rid)
    m = re.search(r"authority_lookup_ols_([a-z]+?)(?:_via_([a-z]+))?_(exact|synonym)$", str(source) or "")
    if m:
        auth, path = m.group(1), m.group(3)
        return (rid, label, build_source_tag(auth, path, mint), mint)
    m2 = re.search(r"authority_lookup_ols_([a-z]+)$", str(source) or "")
    if m2:
        # Tier-3 wrote bare '..._ols_hp' when the match path was 'exact'.
        return (rid, label, build_source_tag(m2.group(1), "exact", mint), mint)
    if str(source).startswith("authority_lookup_uniprot"):
        return (rid, label, source, "uniprot")
    return (rid, label, source, mint)


def load_cache_v4(path="resolution_cache.parquet", seed_version_id=None, host=None):
    """load_cache() from resolution_cache.py, upgraded in memory to 4-tuples.

    -> (cache, stats). Reads the old 7-column parquet OR a new one carrying
    minting_ontology. Nothing is dropped; stats report how many entries were upgraded.
    """
    import os
    import pandas as pd
    src = None
    if os.path.exists(path):
        src = path
    elif seed_version_id and host is not None:
        try:
            src = host.artifact_path(seed_version_id)
        except Exception:
            src = None
    if not src:
        return {}, {"loaded": 0, "upgraded": 0, "retagged": 0, "had_minting_column": False}
    df = pd.read_parquet(src)
    has_mint = "minting_ontology" in df.columns
    cache, upgraded, retagged = {}, 0, 0
    for r in df.itertuples(index=False):
        rid = r.resolved_id if r.resolved_id else None
        lab = r.label if r.label else None
        old = (rid, lab, r.source)
        if has_mint:
            mv = getattr(r, "minting_ontology", None)
            new = (rid, lab, r.source, (mv if mv else (minting_of(rid) if rid else None)))
        else:
            new = upgrade_cache_entry(old)
            upgraded += 1
        if new[2] != r.source:
            retagged += 1
        cache[(r.name_key, r.kind)] = new
    return cache, {"loaded": len(cache), "upgraded": upgraded, "retagged": retagged,
                   "had_minting_column": bool(has_mint)}


_V4_COLS = ["name_key", "kind", "resolved_id", "label", "source", "minting_ontology",
            "cache_version", "resolved_at"]


def save_cache_v4(cache, path="resolution_cache.parquet"):
    """Write the 4-tuple cache. Adds `minting_ontology`; old columns keep their meaning."""
    import os
    import pandas as pd
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    rows = []
    for k, v in cache.items():
        v = upgrade_cache_entry(v)
        rows.append({"name_key": k[0], "kind": k[1], "resolved_id": v[0], "label": v[1],
                     "source": v[2], "minting_ontology": v[3],
                     "cache_version": RESOLVER_VERSION, "resolved_at": now})
    df = pd.DataFrame(rows, columns=_V4_COLS)
    tmp = path + ".tmp"
    df.to_parquet(tmp, index=False)
    os.replace(tmp, path)
    return len(df)


def apply_to_df(df, cache, name_col, kind_col, id_col="entity_id", label_col="entity_label",
                src_col="entity_id_source", mint_col=None):
    """Write cached IDs onto a findings frame. Unmatched names stay NULL, by design."""
    mint_col = mint_col or f"{id_col}_minting_ontology"
    ids, labels, srcs, mints = [], [], [], []
    for name, kind in zip(df[name_col], df[kind_col]):
        key = (name.strip().lower(), kind) if isinstance(name, str) and name.strip() else None
        hit = upgrade_cache_entry(cache.get(key)) if key else None
        if hit is None:
            ids.append(None); labels.append(None); srcs.append("unresolved_nulled"); mints.append(None)
        else:
            ids.append(hit[0]); labels.append(hit[1]); srcs.append(hit[2]); mints.append(hit[3])
    out = df.copy()
    out[id_col], out[label_col], out[src_col], out[mint_col] = ids, labels, srcs, mints
    return out


def selftest():
    """-> list of FAILURES (empty means pass). Offline; no authority is contacted."""
    f = []
    if build_source_tag("hp", "exact", "hp") != "authority_lookup_ols_hp_exact":
        f.append("native tag wrong")
    if build_source_tag("hp", "exact", "pato") != "authority_lookup_ols_hp_via_pato_exact":
        f.append("imported tag wrong")
    if build_source_tag("uniprot", "synonym", "uniprot") != "authority_lookup_uniprot_synonym":
        f.append("uniprot tag wrong")
    up = upgrade_cache_entry(("PATO:0001815", "fatigability", "authority_lookup_ols_hp"))
    if up != ("PATO:0001815", "fatigability", "authority_lookup_ols_hp_via_pato_exact", "pato"):
        f.append(f"old bare-tag upgrade wrong: {up}")
    up2 = upgrade_cache_entry(("MPATH:196", "dermatitis", "authority_lookup_ols_hp_synonym"))
    if up2 != ("MPATH:196", "dermatitis", "authority_lookup_ols_hp_via_mpath_synonym", "mpath"):
        f.append(f"old synonym-tag upgrade wrong: {up2}")
    up3 = upgrade_cache_entry(("HP:0002315", "Headache", "authority_lookup_ols_hp_exact"))
    if up3 != ("HP:0002315", "Headache", "authority_lookup_ols_hp_exact", "hp"):
        f.append(f"native entry must not be retagged: {up3}")
    up4 = upgrade_cache_entry((None, None, "unresolved_nulled"))
    if up4 != (None, None, "unresolved_nulled", None):
        f.append(f"miss must stay a miss: {up4}")
    if resolve_entity("anything at all", "other") != (None, None, "unresolved_nulled", None):
        f.append("'other' kind must never be routed to an authority")
    if resolve_entity("", "physiological-measure")[0] is not None:
        f.append("empty name must not resolve")
    return f
