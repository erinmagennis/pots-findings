"""Autonomous rolling-concurrency driver for the POTS full-corpus extraction.
Run via: exec(open("driver.py").read()) in a background repl cell (host in scope).
Reads done chunks from the artifact store each refill -> fully resumable from any interruption.
"""
import json, re, time

PIPE="2da2db65-c7b7-4850-85e5-9b8677e3ad28"
CO="4f03bac3-f3e2-4a7c-b22f-b03b1a5939f0"
CORPUS="528e0f3a-769b-4818-ba75-03454ef20f65"
N_INFLIGHT=6           # ~saturates the aggregate rate ceiling; more just slows each chunk & thins checkpoints
MAX_ATTEMPTS=3         # per-chunk retry cap before permafail
N_CHUNKS=286
BUDGET_HALT_STREAK=2   # consecutive all-failed refills => pause (budget likely exhausted)
MIN_YIELD=0.60         # min fraction of papers/chunk that must yield >=1 finding; below => transient
                       # fault (measured: healthy chunks 0.66-1.00; the 3 known-bad were 0.22-0.42).
CO_VID="4f03bac3-f3e2-4a7c-b22f-b03b1a5939f0"  # chunk_order (for per-chunk expected paper count)

CODE_TMPL = '''import pandas as pd, json
exec(open(host.artifact_path("%s")).read())
_load_common(host)
CID = __CID__
co = pd.read_parquet(host.artifact_path("%s"))
corpus = pd.read_parquet(host.artifact_path("%s")).drop_duplicates("pmid")
pmids = co[co.chunk_id==CID].pmid.tolist()
chunk_df = corpus[corpus.pmid.isin(pmids)].copy()
chunk_df["chunk_id"] = CID
rows, stats = process_chunk(host, chunk_df)
gdf = ground_findings_df(pd.DataFrame(rows)) if rows else pd.DataFrame()
for col in ["effect_size","study_quality"]:
    if col in gdf.columns:
        gdf[col]=gdf[col].apply(lambda x: json.dumps(x) if isinstance(x,(dict,list)) else x)
fn = "chunk_%%03d_findings.parquet" %% CID
gdf.to_parquet(fn, index=False)
print("SAVED_FILE", fn, "rows", len(gdf))
print("STATS", json.dumps(stats, default=str))
''' % (PIPE, CO, CORPUS)

SCHEMA={"type":"object","properties":{
  "chunk_id":{"type":"integer"},"version_id":{"type":"string"},"stats":{"type":"object"}},
  "required":["chunk_id","version_id","stats"]}

def build_task(cid):
    code = CODE_TMPL.replace("__CID__", str(cid))
    return (
        f"You are a deterministic extraction worker for chunk {cid} of a POTS/dysautonomia "
        f"literature-mining pipeline. Do EXACTLY these three steps, no deviation, no extra analysis:\n\n"
        f"STEP 1 - run this exact code in the `python` tool, environment='litmap' (it fetches full text, "
        f"extracts findings with a truncation guard, and grounds ontology IDs; may take 10-20 min):\n\n"
        f"```python\n{code}```\n\n"
        f"STEP 2 - save it: save_artifacts(files=[\"chunk_{cid:03d}_findings.parquet\"], language=\"python\"). "
        f"Read the returned version_id.\n\n"
        f"STEP 3 - submit structured output with chunk_id={cid}, the version_id from step 2, and the STATS "
        f"dict printed after the 'STATS' marker in stdout.\n\n"
        f"If the code raises, retry ONCE; if it still fails, submit version_id='' with the error in stats.error. "
        f"Do not attempt to fix the pipeline module."
    )

_expected_counts=None
def _expected():
    global _expected_counts
    if _expected_counts is None:
        _co=pd.read_parquet(host.artifact_path(CO_VID))
        _expected_counts=_co.groupby("chunk_id").pmid.nunique().to_dict()
    return _expected_counts

def audit_chunk(cid, vid):
    """Return (ok, yield_frac). A chunk passes only if >=MIN_YIELD of its papers produced findings.
    Guards against the silent transient fault where a chunk saves valid-but-mostly-empty output."""
    try:
        df=pd.read_parquet(host.artifact_path(vid))
    except Exception:
        return False, 0.0
    exp=_expected().get(cid, 50)
    got=df.pmid.nunique() if len(df) else 0
    frac=got/exp if exp else 0.0
    return frac>=MIN_YIELD, frac

def done_chunks():
    """A chunk counts as done ONLY if its BEST artifact passes audit_chunk. Re-runs create a NEW
    artifact with the same filename (save_artifacts without version_of), so a chunk may have several
    artifacts; take the one with the highest yield. Under-yield => NOT done, so the driver re-runs it."""
    r = host.artifacts(filename="_findings.parquet", limit=500)
    best={}  # cid -> best yield fraction seen
    for a in r["artifacts"]:
        m=re.match(r"chunk_(\d+)_findings\.parquet", a["filename"])
        if not m: continue
        cid=int(m.group(1)); _,frac=audit_chunk(cid, a["latest_version_id"])
        best[cid]=max(best.get(cid,0.0), frac)
    return {c for c,f in best.items() if f>=MIN_YIELD}

def _fid_of(r):
    return r.get("sender_frame_id") or r.get("frame_id")

def run_driver(adopt=None):
    attempts={}
    inflight=dict(adopt or {})   # frame_id -> chunk_id (adopt already-running workers)
    for c in inflight.values(): attempts[c]=1
    fail_streak=0
    def refill():
        dc=done_chunks()
        busy=set(inflight.values())
        pending=[c for c in range(N_CHUNKS)
                 if c not in dc and c not in busy and attempts.get(c,0)<MAX_ATTEMPTS]
        while len(inflight)<N_INFLIGHT and pending:
            c=pending.pop(0)
            d=host.delegate({"task":build_task(c),"name":f"chunk{c:03d}","output_schema":SCHEMA}, wait=False)
            inflight[d["frame_id"]]=c
            attempts[c]=attempts.get(c,0)+1
        return len(dc)
    ndone=refill()
    print(f"[driver] start: {ndone}/{N_CHUNKS} already done; {len(inflight)} in flight")
    while inflight:
        res=host.collect(list(inflight.keys()), timeout=300)
        finished=0; failed=0
        for r in res:
            if r.get("status")=="running": continue
            fid=_fid_of(r); cid=inflight.pop(fid, None)
            so=r.get("structured_output") or {}
            vid=so.get("version_id")
            ok, frac = (audit_chunk(cid, vid) if (r.get("status")=="completed" and vid) else (False, 0.0))
            if ok:
                finished+=1
            else:
                failed+=1
                # under-yield or hard-fail: leave attempts<MAX so refill re-dispatches (new version overwrites)
                reason = f"under-yield {frac:.2f}<{MIN_YIELD}" if (r.get("status")=="completed" and vid) else r.get("status")
                with open("driver_failures.txt","a") as fp:
                    fp.write(f"chunk {cid} attempt {attempts.get(cid)}: {reason} {json.dumps(so)[:150]}\n")
        if finished==0 and failed>0:
            fail_streak+=1
        elif finished>0:
            fail_streak=0
        if fail_streak>=BUDGET_HALT_STREAK:
            print(f"[driver] PAUSE: {fail_streak} consecutive all-failed refills - budget likely exhausted. "
                  f"Stopping remaining in-flight and exiting for clean resume.")
            if inflight: host.stop_child(list(inflight.keys()))
            break
        ndone=refill()
        with open("progress.txt","a") as fp:
            fp.write(f"{ndone} of {N_CHUNKS} chunks done | in-flight {len(inflight)} | +{finished} -{failed}\n")
        print(f"[driver] {ndone}/{N_CHUNKS} done | in-flight {len(inflight)} | +{finished} -{failed} | fail_streak {fail_streak}")
    dc=done_chunks()
    permafail=[c for c in range(N_CHUNKS) if c not in dc and attempts.get(c,0)>=MAX_ATTEMPTS]
    print(f"[driver] EXIT: {len(dc)}/{N_CHUNKS} done. permafail={permafail}")
    return {"done":len(dc),"permafail":permafail,"paused_budget":fail_streak>=BUDGET_HALT_STREAK}
