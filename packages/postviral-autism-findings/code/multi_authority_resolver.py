"""Multi-authority name->identifier resolver (Tier 3.5).

DISCIPLINE (inherited from Tier 3, unchanged):
  * The MODEL never emits identifiers. Only names go in; IDs come from authorities.
  * EXACT label match, or a synonym the AUTHORITY ITSELF asserts. Never fuzzy.
    (Fuzzy matching was 59% wrong in Tier 2 -- it is not used at any point here.)
  * Every ID carries a provenance source naming the authority and the match path.
  * A name that does not match is left NULL. A missing ID is honest; a wrong ID
    corrupts every downstream join.

Authorities by entity_kind:
    chemical/metabolite   -> ChEBI      (as Tier 3)
    gene/protein          -> UniProt    (NEW)
    cell-type             -> Cell Ontology / CL   (NEW)
    anatomical-structure  -> UBERON     (NEW)
    physiological-measure -> HPO        (NEW; these names are largely symptoms)
    pathogen              -> NCBI Taxonomy via OLS  (NEW)
"""
import json, time, urllib.parse, urllib.request

OLS4 = "https://www.ebi.ac.uk/ols4/api/search"
UNIPROT = "https://rest.uniprot.org/uniprotkb/search"
UA = {"Accept": "application/json"}
_CACHE = {}

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

def _ols(name, ontology, prefix):
    """Exact label, then authority-asserted synonym, within ONE ontology."""
    q = urllib.parse.quote(name)
    d = _get(f"{OLS4}?q={q}&ontology={ontology}&rows=8&exact=true&fieldList=iri,label,obo_id,synonym")
    docs = ((d or {}).get("response") or {}).get("docs") or []
    nl = name.strip().lower()
    for doc in docs:
        oid = doc.get("obo_id") or ""
        if oid.startswith(prefix) and (doc.get("label") or "").strip().lower() == nl:
            return oid, doc.get("label"), "exact"
    d = _get(f"{OLS4}?q={q}&ontology={ontology}&rows=12&fieldList=iri,label,obo_id,synonym")
    docs = ((d or {}).get("response") or {}).get("docs") or []
    for doc in docs:
        oid = doc.get("obo_id") or ""
        if not oid.startswith(prefix):
            continue
        if (doc.get("label") or "").strip().lower() == nl:
            return oid, doc.get("label"), "exact"
        syns = doc.get("synonym") or []
        if any((s or "").strip().lower() == nl for s in syns):
            return oid, doc.get("label"), "synonym"
    return None, None, None

def _uniprot(name):
    """Human protein by EXACT recommended/alternative name. Reviewed (SwissProt) only."""
    q = urllib.parse.quote(f'protein_name:"{name}" AND organism_id:9606 AND reviewed:true')
    d = _get(f"{UNIPROT}?query={q}&format=json&size=5"
             f"&fields=accession,protein_name,id")
    nl = name.strip().lower()
    for r in (d or {}).get("results", []):
        acc = r.get("primaryAccession")
        pd_ = r.get("proteinDescription") or {}
        rec = ((pd_.get("recommendedName") or {}).get("fullName") or {}).get("value")
        if rec and rec.strip().lower() == nl:
            return f"UniProt:{acc}", rec, "exact"
        alts = [((a.get("fullName") or {}).get("value")) for a in (pd_.get("alternativeNames") or [])]
        if any(a and a.strip().lower() == nl for a in alts):
            return f"UniProt:{acc}", rec or name, "synonym"
    return None, None, None

ROUTES = {
    "chemical/metabolite":   ("chebi",  "CHEBI:", "chebi"),
    "cell-type":             ("cl",     "CL:",    "cl"),
    "anatomical-structure":  ("uberon", "UBERON:", "uberon"),
    "physiological-measure": ("hp",     "HP:",    "hp"),
    "pathogen":              ("ncbitaxon", "NCBITaxon:", "ncbitaxon"),
}

def resolve_entity(name, kind):
    """-> (id, label, source). source names the authority AND the match path."""
    if not isinstance(name, str) or not name.strip() or not isinstance(kind, str):
        return None, None, "unresolved_nulled"
    key = (name.strip().lower(), kind)
    if key in _CACHE:
        return _CACHE[key]
    nm = name.strip()
    if kind == "gene/protein":
        i, l, path = _uniprot(nm)
        src = f"authority_lookup_uniprot_{path}" if i else "unresolved_nulled"
        out = (i, l, src)
    elif kind in ROUTES:
        onto, prefix, tag = ROUTES[kind]
        i, l, path = _ols(nm, onto, prefix)
        src = f"authority_lookup_ols_{tag}_{path}" if i else "unresolved_nulled"
        out = (i, l, src)
    else:
        out = (None, None, "unresolved_nulled")   # 'other'/null kind: no authority to ask
    _CACHE[key] = out
    return out
