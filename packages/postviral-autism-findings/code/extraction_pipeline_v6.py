"""
Full-corpus extraction pipeline (execution thread). Resumable module.
Rehydrate on restart: exec(open(host.artifact_path(<this vid>)).read()) then call run_remaining_chunks().
All locked settings from HANDOFF_run_card.md (artifact 40eb21ad). Model claude-sonnet-5, env litmap.
"""
import urllib.request, urllib.parse, json, re, time, math, unicodedata
import pandas as pd, numpy as np
from xml.etree import ElementTree as ET
from collections import Counter

MODEL="claude-sonnet-5"; MAX_FT=32000; MAX_ABS=8000; FT_INPUT_CHAR_CAP=120000
CHUNK_SIZE=100; CONCURRENCY=8
EPMC="https://www.ebi.ac.uk/europepmc/webservices/rest"

# artifact ids (latest versions) from run-card
CORPUS_VID="528e0f3a-769b-4818-ba75-03454ef20f65"
PROMPT_VID="8380d0c4-624e-48e5-acc8-22a251c028aa"   # v6: names only, no model-emitted ids


# ===== FIX 3b: retry with exponential backoff. Measured on chunk 222: rapid-fire
# rate-limits at 12/12 HTTP 503; email + backoff + pacing drops that to 1/12. The
# 503s were transient, which is exactly what fetch_note made visible.
RETRYABLE = (429, 500, 502, 503, 504)
FETCH_ATTEMPTS = 6      # was 4; residual 503s need more chances under concurrency
FETCH_PACING = 0.9      # was 0.35; 3 workers x 0.9s ~= 3.3 req/s aggregate (was ~8.5)

def _http_retry(url, timeout=45, attempts=FETCH_ATTEMPTS):
    import random
    delay = 3.0
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            last = e
            if e.code in RETRYABLE and i < attempts - 1:
                time.sleep(delay + random.uniform(0, 1)); delay *= 2.2; continue
            raise
        except Exception as e:
            last = e
            if i < attempts - 1:
                time.sleep(delay + random.uniform(0, 1)); delay *= 2.2; continue
            raise
    if last: raise last

def _load_common(host):
    global EXTRACTION_PROMPT, EMAIL, corpus_sorted, n_chunks
    EXTRACTION_PROMPT=open(host.artifact_path(PROMPT_VID)).read()
    try: EMAIL=host.get_user_email()
    except Exception: EMAIL=None
    if not EMAIL:
        # get_user_email() is repl-only. Read a workspace-local file if the orchestrator
        # left one; NEVER read/write the address from an artifact — it must not be
        # persisted. Absent an address we simply omit the &email= param: Europe PMC
        # works without it, and retry/backoff is what actually fixed the 503s.
        try: EMAIL=json.load(open("handoff/contact.json")).get("email")
        except Exception: EMAIL=None
    corpus=pd.read_parquet(host.artifact_path(CORPUS_VID))
    corpus_sorted=corpus.sort_values("pmid",kind="stable").reset_index(drop=True)
    corpus_sorted["chunk_id"]=corpus_sorted.index//CHUNK_SIZE
    n_chunks=int(corpus_sorted["chunk_id"].max()+1)
    return corpus_sorted, n_chunks

# ---- fetch ----
def epmc_search(pmid):
    q=f"EXT_ID:{pmid} AND SRC:MED"
    url=f"{EPMC}/search?query={urllib.parse.quote(q)}&resultType=core&format=json"
    if EMAIL: url+=f"&email={urllib.parse.quote(EMAIL)}"
    d=json.loads(_http_retry(url, timeout=45).decode("utf-8","replace"))
    res=d.get("resultList",{}).get("result",[]); return res[0] if res else None

MIN_FT_CHARS = 2000   # FIX 1: below this we do NOT treat a response as usable full text

def epmc_fulltext(pmcid):
    """FIX 1: Accept */* — the endpoint returns XML and 406s on application/json.
    Measured: Accept:application/json -> HTTP 406; no-header and */* -> 150KB XML.
    Returns the body; caller asserts length before trusting it."""
    body=_http_retry(f"{EPMC}/{pmcid}/fullTextXML", timeout=60).decode("utf-8","replace")
    if len(body) < MIN_FT_CHARS:
        raise ValueError(f"fulltext-too-short:{len(body)}")
    return body

def parse_sections(xml):
    try: root=ET.fromstring(xml)
    except ET.ParseError: return None
    body=root.find(".//body")
    if body is None: return None
    out={}
    for sec in body.findall(".//sec"):
        t=sec.find("title"); title=(t.text or "").strip().lower() if t is not None else "section"
        txt=" ".join("".join(p.itertext()) for p in sec.findall("p"))
        if txt.strip(): out[title]=out.get(title,"")+" "+txt
    full=" ".join("".join(p.itertext()) for p in body.findall(".//p"))
    return {"sections":out,"full_chars":len(full),"full":full}

def get_ft_text(pmid):
    rec=epmc_search(pmid); xml=epmc_fulltext(rec["pmcid"]); p=parse_sections(xml)
    return p["full"], p["sections"]

def _err_note(e):
    """FIX 3: record the REAL failure mode, not a collapsed 'blocked' label."""
    import urllib.error
    if isinstance(e, urllib.error.HTTPError):  return f"HTTP {e.code}"
    if isinstance(e, urllib.error.URLError):   return f"URLError {str(e.reason)[:40]}"
    return f"{type(e).__name__}: {str(e)[:40]}"

def fetch_fulltext(pmid, doi=None):
    """FIX 3: every return carries fetch_note with the real status. `blocked` is
    reserved for genuinely retryable transport failures, never for abstract-only."""
    try: rec=epmc_search(pmid)
    except Exception as e:
        return {"status":"blocked","fetch_note":f"search:{_err_note(e)}","rec":None}
    if rec is None:
        return {"status":"no-epmc-record","fetch_note":"no EPMC record for pmid","rec":None}
    pmcid=rec.get("pmcid"); is_oa=rec.get("isOpenAccess")=="Y"
    if pmcid and is_oa:
        try:
            p=parse_sections(epmc_fulltext(pmcid))
            if p and p["full_chars"]>500:
                return {"status":"retrieved-fulltext","chars":p["full_chars"],"pmcid":pmcid,
                        "fetch_note":f"ok {p['full_chars']}c","rec":rec}
            return {"status":"abstract-only","pmcid":pmcid,"is_oa":is_oa,
                    "fetch_note":f"parsed-thin:{(p or {}).get('full_chars',0)}c","rec":rec}
        except Exception as e:
            # OA paper whose full text we could NOT get = retryable, not abstract-only
            return {"status":"blocked","pmcid":pmcid,"is_oa":is_oa,
                    "fetch_note":f"fulltext:{_err_note(e)}","rec":rec}
    return {"status":"abstract-only","pmcid":pmcid,"is_oa":is_oa,
            "fetch_note":("non-OA" if pmcid else "no-pmcid"),"rec":rec}

def parse_contact(rec):
    if not rec: return None
    authors=rec.get("authorList",{}).get("author",[]); found=[]
    for a in authors:
        affs=a.get("authorAffiliationDetailsList",{}).get("authorAffiliation",[])
        aff=" ".join(x.get("affiliation","") for x in affs) if affs else a.get("affiliation","")
        m=re.search(r"[\w\.\-\+]+@[\w\.\-]+\.\w+", aff or "")
        if m: found.append((a.get("fullName") or a.get("lastName"), m.group()))
    if found: n,e=found[-1]; return f"Contact: {n} <{e}>"
    return None

# ---- extract ----
def build_prompt(row, text, text_kind):
    themes=row.get("themes")
    if isinstance(themes,(list,np.ndarray)): themes=", ".join(map(str,themes))
    header=EXTRACTION_PROMPT.format(themes=themes or row.get("theme",""),
        is_covid=bool(row.get("is_covid")), text_kind=text_kind)
    return header+f"{row.get('title','')}\n\n{text}"

def extract_json(txt):
    txt=txt.strip()
    if txt.startswith("```"): txt=re.sub(r"^```(json)?\s*|\s*```$","",txt).strip()
    s=txt.find("{"); e=txt.rfind("}")
    if s==-1 or e==-1: return None
    try: return json.loads(txt[s:e+1])
    except json.JSONDecodeError: return None

def salvage_findings(txt):
    m=re.search(r'"findings"\s*:\s*\[',txt)
    if not m: return []
    arr=txt[m.end():]; out=[]; depth=0; buf=""; ino=False
    for ch in arr:
        if ch=="{":
            if depth==0: buf=""; ino=True
            depth+=1; buf+=ch
        elif ch=="}":
            depth-=1; buf+=ch
            if depth==0 and ino:
                try: out.append(json.loads(buf))
                except: pass
                ino=False
        elif ino: buf+=ch
    return out

def call_extract(host, prompt, max_tokens):
    try:
        r=host.llm({"prompt":prompt,"max_tokens":max_tokens,"model":MODEL})
        return r["text"], r.get("stop_reason"), r.get("usage",{}).get("output_tokens",0)
    except RuntimeError as e:
        if "max_tokens" in str(e) and "empty response" in str(e): return "","max_tokens",max_tokens
        raise

FINDING_FIELDS=["entity","entity_kind","gene_marker","direction","direction_reference","finding_text",
 "pathway_or_mechanism","quantitative_detail","effect_size","causal_or_correlational","evidence_tier",
 "functional_impact","condition","pots_subtype","population_age_group","sex_hormonal","anatomical_system",
 "is_covid_associated","finding_type","treatment_class","symptom_correlate","phenotype_terms","validated_instrument",
 "adverse_event_note","certainty","cohort_registry","cohort_name","dataset_accession","relation_type",
 "relation_subject","relation_object","provenance_quote","provenance_section","null_or_failed_result",
 "contradicts_finding_ref","evidence_stratum","study_quality"]
PAPER_FIELDS=["study_type","n_participants","comparator","demographics","is_duplicate_or_preprint_note",
 "contradicts_or_extends","limitations_stated","future_direction"]


# ================= FIX 2: PARSER GUARD — reject model-emitted identifiers =================
ID_SHAPED = re.compile(r'\b(?:HGNC|CHEBI|CHEBI_|HP|GO|MESH|MSH|UMLS|ENSG|UNIPROT|R-HSA|DOID|OMIM|NCIT)\s*[:_]\s*\d+|\bENSG\d{6,}|\bR-HSA-\d+', re.I)
NAME_FIELDS = ("entity","phenotype_terms","pathway_or_mechanism","symptom_correlate","gene_marker","finding_text")

def guard_finding(f):
    """Strip any id-shaped string the model emitted despite the prompt. Returns
    (cleaned_finding, violations). Tier 2 saw 27.7% fabricated ids; this makes a
    recurrence visible instead of silently written to the corpus."""
    viol=[]
    for k in NAME_FIELDS:
        v=f.get(k)
        if isinstance(v,str) and ID_SHAPED.search(v):
            found=ID_SHAPED.findall(v)
            cleaned=ID_SHAPED.sub('', v)
            cleaned=re.sub(r'\s*[\(\[]\s*[\)\]]', '', cleaned)
            cleaned=re.sub(r'\s+([;,])', r'\1', cleaned)      # no space before delimiter
            cleaned=re.sub(r'([;,])\s*([;,])', r'\1', cleaned) # no empty terms
            cleaned=re.sub(r'\s{2,}',' ',cleaned).strip(' ,;:()[]')
            f[k]=cleaned or None
            viol.append({"field":k,"stripped":found[:3],"kept":f[k]})
    # any leftover id-bearing key the model invented on its own
    for k in list(f.keys()):
        if k in ("entity_ontology_id","pathway_id","phenotype_hpo") and f.get(k) is not None:
            viol.append({"field":k,"stripped":["<forbidden field>"],"kept":None})
            f[k]=None
    return f, viol

# ---- derived columns adopted from the Tier-2 repairs ----
HEDGE_RX = re.compile(r'\b(may|might|could|suggest\w*|possib\w+|potential\w*|appear\w*|seem\w*|likely|'
                      r'unclear|preliminary|warrant\w*|hypothes\w+|trend\w*|not significant)\b', re.I)

def derive_certainty(finding_text, quote):
    """certainty_derived: hedge detection over BOTH fields. Never overwrites the
    extractor's own `certainty`."""
    a=bool(HEDGE_RX.search(str(finding_text or ""))); b=bool(HEDGE_RX.search(str(quote or "")))
    if a and b: return "hedged"
    if not a and not b: return "confirmed"
    return "mixed"

NUM_RX = re.compile(r'\d+(?:\.\d+)?')

def number_in_quote(quant, effect, quote):
    """Is the value in quantitative_detail/effect_size actually present in the quote?
    ~9.9% of Tier-2 rows fail this; it is a genuine open question, not auto-fixable."""
    q=str(quote or "")
    if not q: return None
    qn=set(NUM_RX.findall(q))
    src_nums=set()
    for v in (quant, effect):
        if v is None: continue
        src_nums |= set(NUM_RX.findall(str(v)))
    if not src_nums: return None
    return bool(src_nums & qn)

def process_chunk(host, chunk_df):
    infos=[]
    for _,row in chunk_df.iterrows():
        info={"pmid":row.pmid}
        try: f=fetch_fulltext(row.pmid,row.doi)
        except Exception as e: f={"status":"search-error","err":str(e)[:60],"rec":None}
        rec=f.get("rec")
        note=f.get("fetch_note")
        if f["status"]=="retrieved-fulltext":
            txt=None
            try: txt,_=get_ft_text(row.pmid)
            except Exception as e: note=f"reget:{_err_note(e)}"
            if txt and len(txt)>MIN_FT_CHARS:   # FIX 1: assert real full text, not a stub
                info.update(text=txt[:FT_INPUT_CHAR_CAP],text_kind="full-text",
                            fulltext_status="retrieved-fulltext",contact_note=None,fetch_note=note)
            else:
                info.update(text=str(row.abstract or ""),text_kind="title+abstract",
                            fulltext_status="blocked",contact_note=parse_contact(rec),
                            fetch_note=note or "ft-reget-empty")
        else:
            info.update(text=str(row.abstract or ""),text_kind="title+abstract",
                fulltext_status=f["status"] if f["status"]=="blocked" else "abstract-only",
                contact_note=parse_contact(rec),fetch_note=note)
        infos.append(info); time.sleep(FETCH_PACING)
    rows_by={r.pmid:r for _,r in chunk_df.iterrows()}
    reqs=[]; maxtoks=[]; order=[]
    for info in infos:
        row=rows_by[info["pmid"]]; mt=MAX_FT if info["text_kind"]=="full-text" else MAX_ABS
        reqs.append({"prompt":build_prompt(row,info["text"],info["text_kind"]),"max_tokens":mt,"model":MODEL})
        maxtoks.append(mt); order.append(info["pmid"])
    res=host.llm(reqs,max_concurrency=CONCURRENCY)
    parsed_map={}; truncated=[]; outtok=0; rawtxt={}
    for pmid,r,mt in zip(order,res,maxtoks):
        if "error" in r: parsed_map[pmid]=None; rawtxt[pmid]=""; truncated.append(pmid); continue
        txt=r["text"]; stop=r.get("stop_reason"); ot=r.get("usage",{}).get("output_tokens",0); outtok+=ot
        parsed=extract_json(txt); rawtxt[pmid]=txt; parsed_map[pmid]=parsed
        if stop=="max_tokens" or parsed is None or ot>=0.95*mt: truncated.append(pmid)
    cont_count=len(truncated); remaining=list(truncated)
    for _ in range(3):
        if not remaining: break
        creqs=[]
        for pmid in remaining:
            info=next(i for i in infos if i["pmid"]==pmid); row=rows_by[pmid]
            base=parsed_map.get(pmid); bf=base.get("findings",[]) if base else salvage_findings(rawtxt.get(pmid,""))
            if base and not base.get("findings"): base["findings"]=bf
            elif not base: parsed_map[pmid]={"findings":bf}
            mt=maxtoks[order.index(pmid)]
            cp=(build_prompt(row,info["text"],info["text_kind"])+f"\n\n[CONTINUATION] Previous response truncated. "
                f"Already emitted {len(parsed_map[pmid].get('findings',[]))} findings. Return ONLY JSON with a "
                "\"findings\" array of REMAINING findings (no repeats). If done, {\"findings\": []}.")
            creqs.append((pmid,{"prompt":cp,"max_tokens":mt,"model":MODEL}))
        cres=host.llm([c[1] for c in creqs],max_concurrency=CONCURRENCY); nr=[]
        for (pmid,_),r in zip(creqs,cres):
            if "error" in r: nr.append(pmid); continue
            cp=extract_json(r["text"]); cst=r.get("stop_reason")
            cf=cp.get("findings",[]) if cp else salvage_findings(r["text"])
            ex=parsed_map[pmid].get("findings",[]); new=[f for f in cf if f not in ex]
            parsed_map[pmid]["findings"]=ex+new
            if cst=="max_tokens" and new: nr.append(pmid)
        remaining=nr
    rows=[]; pf=[]; guard_viol=[]
    for info in infos:
        pmid=info["pmid"]; row=rows_by[pmid]; parsed=parsed_map.get(pmid)
        if parsed is None: pf.append(pmid); continue
        pm={k:parsed.get(k) for k in PAPER_FIELDS}
        for f in parsed.get("findings",[]):
            if not isinstance(f,dict): continue
            f,viol=guard_finding(f)                 # FIX 2: strip model-emitted ids
            if viol: guard_viol.extend([{"pmid":pmid,**v} for v in viol])
            fr={k:f.get(k) for k in FINDING_FIELDS}; fr.update(pm)
            fr["certainty_derived"]=derive_certainty(f.get("finding_text"),f.get("provenance_quote"))
            fr["number_in_quote"]=number_in_quote(f.get("quantitative_detail"),f.get("effect_size"),
                                                  f.get("provenance_quote"))
            fr.update(pmid=pmid,doi=row.doi,title=row.title,year=row.year,journal=row.journal,
                source_stream=row.source_stream,theme=row.theme,fulltext_status=info["fulltext_status"],
                contact_note=info["contact_note"],fetch_note=info.get("fetch_note"),
                chunk_id=int(row.chunk_id))
            rows.append(fr)
    stats=dict(papers=len(infos),
        fulltext=sum(1 for i in infos if i["fulltext_status"]=="retrieved-fulltext"),
        abstract=sum(1 for i in infos if i["fulltext_status"]=="abstract-only"),
        blocked=sum(1 for i in infos if i["fulltext_status"]=="blocked"),
        truncated_papers=cont_count,parse_fail=len(pf),parse_fail_pmids=pf,
        findings=len(rows),total_out_tokens=outtok,
        guard_violations=len(guard_viol), guard_violation_detail=guard_viol[:20],
        blocked_notes={i["pmid"]:i.get("fetch_note") for i in infos
                       if i["fulltext_status"]=="blocked"})
    stats["blocked_frac"]=round(stats["blocked"]/max(1,stats["papers"]),4)
    return rows, stats

def clean(v):
    if v is None: return None
    if isinstance(v,float) and math.isnan(v): return None
    s=str(v).strip()
    return None if s.lower() in ("null","none","nan","") else s

def save_chunk(host, save_artifacts_fn, rows, chunk_id):
    df=pd.DataFrame(rows)
    for col in ["effect_size","study_quality"]:
        if col in df: df[col]=df[col].apply(lambda x: json.dumps(x) if isinstance(x,(dict,list)) else x)
    fn=f"chunk_{chunk_id:02d}_findings.parquet"; df.to_parquet(fn,index=False)
    return fn, len(df)

# ================= GROUNDING (step 7) — batched, cached, real-authority validation =================
# Edit 1: real validation for ChEBI(OLS)/MeSH(NLM)/GO(QuickGO)/HPO(OLS)/HGNC(MyGene), not format-check.
# Edit 2: cross-chunk cache -> ~1 HTTP call per DISTINCT id over the whole corpus.
# Edit 3: Reactome R-HSA kept format-valid only (service 403s all clients; do not spoof UA).
_gcache={}  # id -> (canonical_id, label) or None

def http_get_json(url, timeout=30, headers=None):
    req=urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req,timeout=timeout) as r: return json.load(r)

def http_post_json(url, data, timeout=45):
    req=urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(),
        headers={"Content-Type":"application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req,timeout=timeout) as r: return json.load(r)

def _ols_validate(onto, curie):
    m=re.match(r'(?i)'+onto+r'[:_](\d+)', curie)
    if not m: return None
    canon=f"{onto.upper()}:{m.group(1)}"; iri=f"http://purl.obolibrary.org/obo/{onto.upper()}_{m.group(1)}"
    try:
        r=http_get_json(f"https://www.ebi.ac.uk/ols4/api/ontologies/{onto.lower()}/terms?iri={urllib.parse.quote(iri)}")
        t=r.get("_embedded",{}).get("terms",[]); return (canon,t[0]["label"]) if t else None
    except Exception: return None

def _mesh_validate(curie):
    m=re.match(r'(?i)m[e]?sh:([A-Z]?\d+)', curie)
    if not m: return None
    try:
        r=http_get_json(f"https://id.nlm.nih.gov/mesh/{m.group(1)}.json")
        lab=r.get("label",{}); lab=lab.get("@value") if isinstance(lab,dict) else lab
        return (f"MeSH:{m.group(1)}",lab) if lab else None
    except Exception: return None

def _go_validate(curie):
    m=re.match(r'(?i)go[:_](\d+)', curie)
    if not m: return None
    gid=f"GO:{m.group(1)}"
    try:
        r=http_get_json(f"https://www.ebi.ac.uk/QuickGO/services/ontology/go/terms/{gid}",headers={"Accept":"application/json"})
        res=r.get("results",[]); return (gid,res[0]["name"]) if res else None
    except Exception: return None

def resolve_ontology_id(curie):
    """Route entity_ontology_id/pathway_id to the right authority. Cached. Returns (canonical_id,label) or None."""
    curie=clean(curie)
    if not curie: return None
    if curie in _gcache: return _gcache[curie]
    cu=curie.upper(); out=None
    if cu.startswith("CHEBI"): out=_ols_validate("chebi",curie)
    elif cu.startswith("HP"):  out=_ols_validate("hp",curie)
    elif cu.startswith("GO"):  out=_go_validate(curie)
    elif cu.startswith(("MESH","MSH")): out=_mesh_validate(curie)
    elif cu.startswith("HGNC"):
        num=curie.split(":")[1] if ":" in curie else None
        if num:
            try:
                mg=http_post_json("https://mygene.info/v3/query",{"q":num,"scopes":"HGNC","fields":"symbol,HGNC","species":"human"})
                if mg and not mg[0].get("notfound") and mg[0].get("HGNC"): out=(f"HGNC:{mg[0]['HGNC']}",mg[0].get("symbol"))
            except Exception: pass
    elif cu.startswith("R-HSA"):  # Reactome service 403s all clients; keep format-valid proposal
        out=(curie,None) if re.match(r'(?i)R-HSA-\d+$',curie) else None
    _gcache[curie]=out
    return out

def resolve_genes(symbols):
    """Batch symbol->{symbol,hgnc,ensembl} via MyGene, cached. Strips variant notation."""
    norm={}
    for s in symbols:
        s=clean(s)
        if not s: continue
        base=re.sub(r'[^A-Za-z0-9\-]','',re.split(r'[\s/(),;]',s)[0].strip())
        if base: norm.setdefault(base,set()).add(s)
    uniq=[b for b in norm if f"GENE:{b}" not in _gcache]
    for i in range(0,len(uniq),100):
        batch=uniq[i:i+100]
        try:
            mg=http_post_json("https://mygene.info/v3/query",
                {"q":",".join(batch),"scopes":"symbol,alias,ensembl.gene","fields":"symbol,HGNC,ensembl.gene","species":"human"})
        except Exception: continue
        got={}
        for r in mg:
            q=r.get("query")
            if r.get("notfound") or not r.get("symbol"): continue
            ens=r.get("ensembl"); ensg=ens.get("gene") if isinstance(ens,dict) else (ens[0].get("gene") if isinstance(ens,list) and ens else None)
            got[q]={"symbol":r.get("symbol"),"hgnc":f"HGNC:{r['HGNC']}" if r.get("HGNC") else None,"ensembl":ensg}
        for b in batch: _gcache[f"GENE:{b}"]=got.get(b)
        time.sleep(0.2)
    out={}
    for base,origs in norm.items():
        hit=_gcache.get(f"GENE:{base}")
        if hit:
            for o in origs: out[o]=hit
    return out

def resolve_name_to_id(name, kind=None):
    """FIX 2: derive an ontology id FROM THE NAME by authority lookup. Returns
    (id, label, source) or (None,None,'unresolved_nulled'). Only EXACT label
    matches are accepted — fuzzy matches were 59% wrong in Tier 2, so they are
    never auto-accepted here."""
    nm=clean(name)
    if not nm: return (None,None,"unresolved_nulled")
    ck=f"NAME:{kind}:{nm.lower()}"
    if ck in _gcache: return _gcache[ck]
    out=(None,None,"unresolved_nulled")
    onto = "chebi" if kind=="chemical/metabolite" else None
    try:
        if onto:
            r=http_get_json("https://www.ebi.ac.uk/ols4/api/search?q="+urllib.parse.quote(nm)
                            +f"&ontology={onto}&exact=true&fieldList=iri,label,obo_id,synonym,obo_synonym&rows=8")
            docs=r.get("response",{}).get("docs",[])
            tgt=nm.strip().lower()
            for d in docs:                                  # 1st pass: exact label
                if d.get("label","").strip().lower()==tgt and d.get("obo_id"):
                    out=(d["obo_id"],d["label"],"authority_lookup_ols_chebi"); break
            if out[0] is None:                              # 2nd pass: authority-asserted synonym
                for d in docs:
                    syns=[s.strip().lower() for s in (d.get("synonym") or [])+(d.get("obo_synonym") or [])
                          if isinstance(s,str)]
                    if tgt in syns and d.get("obo_id"):
                        out=(d["obo_id"],d["label"],"authority_lookup_ols_chebi_synonym"); break
    except Exception: pass
    _gcache[ck]=out
    return out


def resolve_hpo_terms(term_string):
    """Multi-value HPO: split the semicolon-delimited phenotype_terms, resolve EACH
    by EXACT label match at OLS4. Returns (ids_str, labels_str, source).
    43.2% of mappable Tier-2 symptom strings resolved to >1 distinct verified id,
    which a one-id-per-row schema cannot express."""
    s=clean(term_string)
    if not s: return (None,None,"unresolved_nulled")
    terms=[t.strip() for t in re.split(r'[;]', s) if t.strip()]
    ids=[]; labels=[]; paths=[]
    for t in terms:
        ck=f"HPO:{t.lower()}"
        if ck in _gcache:
            hit=_gcache[ck]
        else:
            hit=None
            try:
                r=http_get_json("https://www.ebi.ac.uk/ols4/api/search?q="+urllib.parse.quote(t)
                                +"&ontology=hp&exact=true&fieldList=obo_id,label,synonym,obo_synonym&rows=8")
                docs=r.get("response",{}).get("docs",[]); tl=t.strip().lower()
                for d in docs:                              # exact label
                    if d.get("label","").strip().lower()==tl and d.get("obo_id"):
                        hit=(d["obo_id"],d["label"],"label"); break
                if hit is None:                             # authority-asserted synonym
                    for d in docs:
                        syns=[s.strip().lower() for s in (d.get("synonym") or [])+(d.get("obo_synonym") or [])
                              if isinstance(s,str)]
                        if tl in syns and d.get("obo_id"):
                            hit=(d["obo_id"],d["label"],"synonym"); break
            except Exception: pass
            _gcache[ck]=hit
            time.sleep(0.05)
        if hit:
            ids.append(hit[0]); labels.append(hit[1]); paths.append(hit[2] if len(hit)>2 else "label")
    if not ids: return (None,None,"unresolved_nulled")
    src_tag = ("authority_lookup_ols_hp" if all(p=="label" for p in paths)
               else "authority_lookup_ols_hp_synonym")
    return (";".join(ids), ";".join(labels), src_tag)


def ground_findings_df(df):
    """Grounding by NAME (FIX 2). Every id carries *_source provenance.
    pathway_id is GONE — only 14 of 147 Tier-2 mechanism strings were real ontology
    terms; pathway_or_mechanism stays free text."""
    if not len(df): return df
    gene_res=resolve_genes(list(df.get("gene_marker",[])))
    def _row(r):
        o={}
        gm=clean(r.get("gene_marker")); g=gene_res.get(gm) if gm else None
        o["hgnc_id"]=g["hgnc"] if g else None
        o["ensembl_id"]=g["ensembl"] if g else None
        o["gene_resolved"]=bool(g)
        o["gene_id_source"]="pipeline_symbol_lookup" if g else "unresolved_nulled"
        eid,elab,esrc=resolve_name_to_id(r.get("entity"), r.get("entity_kind"))
        o["entity_ontology_id_resolved"]=eid
        o["entity_ontology_label"]=elab
        o["ontology_id_source"]=esrc
        hids,hlabs,hsrc=resolve_hpo_terms(r.get("phenotype_terms"))
        o["hpo_ids_verified"]=hids
        o["hpo_labels_verified"]=hlabs
        o["hpo_id_source"]=hsrc
        o["hpo_id_count"]=0 if not hids else len(hids.split(";"))
        return pd.Series(o)
    return pd.concat([df, df.apply(_row,axis=1)], axis=1)
