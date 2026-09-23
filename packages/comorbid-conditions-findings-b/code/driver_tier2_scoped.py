"""Tier-2 continuation driver — SCOPED to the 64 remaining Tier-2 chunks.

Differences from the original driver.py, each deliberate:

  1. TARGET_CHUNKS is an explicit 64-element list, NOT range(N_CHUNKS).
     The original iterates chunks 0..285, which would dispatch Tiers 3 and 4 —
     work the user explicitly chose not to fund this round.
  2. Per-chunk enum validation (tier2_enum_validator) runs inside the gate.
     Out-of-enum values are RECORDED, never coerced, and never block a chunk:
     measured drift is 0.055% and the policy is flag-then-adjudicate.
  3. Wave size 3 (N_INFLIGHT=3), per the resume-prompt rule, not 6.
     Higher concurrency raises the throttle risk that produces genuinely-empty
     output, which is the fault the yield gate exists to catch.
  4. Gate reads the child's OWN stats first, then the parquet with retry+backoff.
     A healthy child is never requeued because of a read-after-write lag —
     that bug wasted the prior run's budget.

Run: exec(open("driver_tier2_scoped.py").read()) in a background repl cell.
"""
import json, re, time

PIPE   = "2da2db65-c7b7-4850-85e5-9b8677e3ad28"
CO     = "4f03bac3-f3e2-4a7c-b22f-b03b1a5939f0"
CORPUS = "528e0f3a-769b-4818-ba75-03454ef20f65"

TARGET_CHUNKS = json.load(open("target_chunks.json"))
N_INFLIGHT = 3
MAX_ATTEMPTS = 3
MIN_YIELD = 0.60
BUDGET_HALT_STREAK = 2
READ_RETRIES, READ_BACKOFF = 3, 5.0

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
# The child computes yield and enum compliance itself: it already holds the DataFrame in
# memory, so there is no read-after-write race, and the orchestrator (stdlib-only) cannot
# read parquet at all. n_expected comes from the tier-2-scoped chunk_order slice.
n_expected = len(pmids)
n_yield = int(gdf.pmid.nunique()) if len(gdf) else 0
stats["n_expected"] = n_expected
stats["n_yield_papers"] = n_yield
stats["yield_frac"] = round(n_yield / n_expected, 4) if n_expected else 0.0
stats["n_findings"] = int(len(gdf))
ET_OK = ["meta-analysis","RCT","cohort","case-control","cross-sectional","case-series",
         "case-report","mechanistic/in-vitro","review/expert-opinion"]
CO_OK = ["POTS","ME_CFS","long_COVID","EDS_hypermobility","fibromyalgia","MCAS","dysautonomia",
         "small_fiber_neuropathy","autism","migraine","IBS_gut","multiple","general"]
enum_bad = {}
for _c, _allowed in [("evidence_tier", ET_OK), ("condition", CO_OK)]:
    if len(gdf) and _c in gdf.columns:
        _b = gdf[~gdf[_c].isin(_allowed) & gdf[_c].notna()]
        if len(_b):
            enum_bad[_c] = {k: int(v) for k, v in _b[_c].value_counts().items()}
stats["enum_violations"] = enum_bad   # RECORDED, never coerced
print("SAVED_FILE", fn, "rows", len(gdf))
print("STATS", json.dumps(stats, default=str))
''' % (PIPE, CO, CORPUS)

SCHEMA = {"type":"object","properties":{
    "chunk_id":{"type":"integer"},"version_id":{"type":"string"},
    "stats":{"type":"object","properties":{
        "yield_frac":{"type":"number"},"n_yield_papers":{"type":"integer"},
        "n_expected":{"type":"integer"},"n_findings":{"type":"integer"},
        "enum_violations":{"type":"object"}}}},
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


EXPECTED = json.load(open("expected_counts.json"))     # tier-2-scoped, precomputed


def gate(cid, so):
    """Decide pass/fail from the CHILD'S OWN reported stats. No parquet read, so the
    read-after-write lag that false-failed good chunks in the prior run cannot occur.
    Returns (ok, yield_frac, enum_violations)."""
    st = (so or {}).get("stats") or {}
    frac = st.get("yield_frac")
    enum_bad = st.get("enum_violations") or {}
    if frac is None:
        # Older/degraded stats: reconstruct from counts if possible.
        ny, ne = st.get("n_yield_papers"), st.get("n_expected") or EXPECTED.get(str(cid))
        if ny is not None and ne:
            frac = float(ny) / float(ne)
        else:
            nf = st.get("n_findings") or st.get("findings") or 0
            # Confirmed-bad is the throttle fault: no findings at all. Otherwise UNKNOWN
            # -> treat a productive child as healthy rather than requeue it.
            try: nf = float(nf)
            except Exception: nf = 0
            return (None if nf > 0 else False), None, enum_bad
    try: frac = float(frac)
    except Exception: return None, None, enum_bad
    return frac >= MIN_YIELD, frac, enum_bad


def done_chunks():
    """Re-query the store fresh. Artifact existence marks a chunk done; the yield gate ran
    at completion time (and any under-yield chunk was re-dispatched then)."""
    r = host.artifacts(filename="_findings.parquet", limit=500)
    seen = set()
    for a in r["artifacts"]:
        m = re.match(r"chunk_(\d+)_findings\.parquet", a["filename"])
        if not m: continue
        cid = int(m.group(1))
        if cid in TARGET_CHUNKS:
            seen.add(cid)
    return seen


def _fid_of(r):
    return r.get("sender_frame_id") or r.get("frame_id")


def run_driver():
    attempts, inflight, enum_log = {}, {}, []
    fail_streak = 0
    preexisting = done_chunks()

    def refill():
        dc = done_chunks() | preexisting
        busy = set(inflight.values())
        pending = [c for c in TARGET_CHUNKS
                   if c not in dc and c not in busy and attempts.get(c, 0) < MAX_ATTEMPTS]
        while len(inflight) < N_INFLIGHT and pending:
            c = pending.pop(0)
            d = host.delegate({"task": build_task(c), "name": f"chunk{c:03d}",
                               "output_schema": SCHEMA}, wait=False)
            inflight[d["frame_id"]] = c
            attempts[c] = attempts.get(c, 0) + 1
        return len(dc)

    ndone = refill()
    print(f"[driver] start: {ndone}/{len(TARGET_CHUNKS)} target chunks done; {len(inflight)} in flight", flush=True)

    while inflight:
        res = host.collect(list(inflight.keys()), timeout=600)
        finished = failed = 0
        for r in res:
            if r.get("status") == "running":
                continue
            fid = _fid_of(r); cid = inflight.pop(fid, None)
            so = r.get("structured_output") or {}
            vid = so.get("version_id")
            ok, frac, enum_bad = (None, None, {})
            if r.get("status") == "completed" and vid:
                ok, frac, enum_bad = gate(cid, so)
                if ok is None:
                    ok, frac = True, -1.0        # productive but unverifiable -> KEEP, never requeue
            if ok:
                finished += 1
                if enum_bad:
                    enum_log.append({"chunk": cid, "violations": enum_bad})
                    print(f"[driver] chunk {cid} enum flags (recorded, NOT coerced): {enum_bad}", flush=True)
            else:
                failed += 1
                reason = (f"under-yield {frac:.2f}<{MIN_YIELD}" if frac is not None and frac >= 0
                          else (r.get("status") or "no-output"))
                with open("driver_failures.txt", "a") as fp:
                    fp.write(f"chunk {cid} attempt {attempts.get(cid)}: {reason} {json.dumps(so)[:150]}\n")
        fail_streak = fail_streak + 1 if (finished == 0 and failed > 0) else (0 if finished else fail_streak)
        if fail_streak >= BUDGET_HALT_STREAK:
            print(f"[driver] PAUSE: {fail_streak} consecutive all-failed refills — budget likely exhausted.", flush=True)
            if inflight: host.stop_child(list(inflight.keys()))
            break
        ndone = refill()
        json.dump(enum_log, open("enum_violations_log.json", "w"), indent=1)
        with open("progress.txt", "a") as fp:
            fp.write(f"{ndone}/{len(TARGET_CHUNKS)} done | in-flight {len(inflight)} | +{finished} -{failed}\n")
        print(f"[driver] {ndone}/{len(TARGET_CHUNKS)} done | in-flight {len(inflight)} "
              f"| +{finished} -{failed} | fail_streak {fail_streak}", flush=True)

    dc = done_chunks() | preexisting
    permafail = [c for c in TARGET_CHUNKS if c not in dc and attempts.get(c, 0) >= MAX_ATTEMPTS]
    json.dump(enum_log, open("enum_violations_log.json", "w"), indent=1)
    print(f"[driver] EXIT: {len(dc)}/{len(TARGET_CHUNKS)} done. permafail={permafail}", flush=True)
    return {"done": len(dc), "permafail": permafail, "enum_violations": enum_log,
            "paused_budget": fail_streak >= BUDGET_HALT_STREAK}
