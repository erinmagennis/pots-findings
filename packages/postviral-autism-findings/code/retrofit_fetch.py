"""Retrofit fetch: abstract (+ full text via PMCID) for every Tier 1-3 pmid.

Uses the PINNED fetcher from tier4/code/tier4_pipeline.py (epmc_search,
epmc_fulltext, parse_sections, _http_retry) and its pinned pacing:
FETCH_PACING=0.9 s after every HTTP request per worker, 3 workers.
Checkpoints: gzipped JSON per 500 papers under fetch_ckpt/, JSONL log
appended per paper. Resumable: pmids already in a checkpoint are skipped.
"""
import sys, os, json, gzip, time, glob, threading, datetime, traceback
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, "pots-corpus/tier4/code")
import tier4_pipeline as tp
tp.EMAIL = None                      # repl-only get_user_email is unavailable here; EPMC works without it
assert tp.FETCH_PACING == 0.9, tp.FETCH_PACING
N_WORKERS = 3
CKPT_EVERY = 500
FT_CAP = tp.FT_INPUT_CHAR_CAP        # 120000 — the model only ever saw the first 120k chars of body

TIERS = ["tier1", "tier2a", "tier2b", "tier3"]
os.makedirs("fetch_ckpt", exist_ok=True)
LOG = "fetch_ckpt/fetch_log.jsonl"
PROGRESS = "fetch_ckpt/progress.txt"

# ---- target set ----
need_ft = {}
for t in TIERS:
    df = pd.read_parquet(f"pots-corpus/{t}/data/{t}_findings.parquet", columns=["pmid", "fulltext_status"])
    for p, s in zip(df.pmid.astype(str), df.fulltext_status):
        need_ft[p] = need_ft.get(p, False) or (s == "retrieved-fulltext")
assert len(need_ft) == 10428, len(need_ft)
assert sum(need_ft.values()) == 6239, sum(need_ft.values())

done = set()
for f in glob.glob("fetch_ckpt/ckpt_*.json.gz"):
    with gzip.open(f, "rt", encoding="utf-8") as fh:
        done |= set(json.load(fh).keys())
todo = sorted((p for p in need_ft if p not in done), key=int)
print(f"targets={len(need_ft)} done={len(done)} todo={len(todo)}", flush=True)

req_count = [0]
req_lock = threading.Lock()

def _paced(fn, *a, **k):
    try:
        return fn(*a, **k)
    finally:
        with req_lock:
            req_count[0] += 1
        time.sleep(tp.FETCH_PACING)

def fetch_paper(pmid):
    out = {"pmid": pmid, "needs_fulltext": bool(need_ft[pmid]), "has_abstract": False,
           "has_fulltext": False, "pmcid": None, "is_oa": None, "http_status_or_error": None,
           "fulltext_error": None, "body_chars": None, "fetched_at": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
           "fetch_status": None}
    text = {"title": "", "abstract": "", "body": ""}
    try:
        rec = _paced(tp.epmc_search, pmid)
    except Exception as e:
        out["http_status_or_error"] = tp._err_note(e)
        out["fetch_status"] = "http_error"
        return out, text
    if rec is None:
        out["http_status_or_error"] = "no EPMC record"
        out["fetch_status"] = "no_abstract"
        return out, text
    out["http_status_or_error"] = "HTTP 200"
    text["title"] = rec.get("title") or ""
    text["abstract"] = rec.get("abstractText") or ""
    out["has_abstract"] = bool(text["abstract"].strip())
    out["pmcid"] = rec.get("pmcid")
    out["is_oa"] = rec.get("isOpenAccess")
    if out["needs_fulltext"]:
        if not out["pmcid"]:
            out["fetch_status"] = "no_pmcid"
        else:
            try:
                xml = _paced(tp.epmc_fulltext, out["pmcid"])
                p = tp.parse_sections(xml)
                if p and p["full_chars"] > tp.MIN_FT_CHARS:
                    text["body"] = p["full"][:FT_CAP]
                    out["body_chars"] = p["full_chars"]
                    out["has_fulltext"] = True
                    out["fetch_status"] = "ok"
                else:
                    out["fulltext_error"] = f"parsed-thin:{(p or {}).get('full_chars', 0)}c"
                    out["fetch_status"] = "fulltext_failed"
            except Exception as e:
                out["fulltext_error"] = tp._err_note(e)
                out["fetch_status"] = "fulltext_failed"
    else:
        out["fetch_status"] = "ok" if out["has_abstract"] else "no_abstract"
    if out["fetch_status"] == "ok" and not out["has_abstract"] and not out["has_fulltext"]:
        out["fetch_status"] = "no_abstract"
    return out, text

t0 = time.time()
n_ck = len(glob.glob("fetch_ckpt/ckpt_*.json.gz"))
n_done = 0
with ThreadPoolExecutor(N_WORKERS) as ex:
    for i in range(0, len(todo), CKPT_EVERY):
        chunk = todo[i:i + CKPT_EVERY]
        results = list(ex.map(fetch_paper, chunk))
        texts = {r[0]["pmid"]: r[1] for r in results}
        tmp = f"fetch_ckpt/ckpt_{n_ck:03d}.json.gz.tmp"
        with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=6) as fh:
            json.dump(texts, fh)
        os.replace(tmp, f"fetch_ckpt/ckpt_{n_ck:03d}.json.gz")
        with open(LOG, "a") as fh:
            for r in results:
                fh.write(json.dumps(r[0]) + "\n")
        n_ck += 1; n_done += len(chunk)
        el = time.time() - t0
        st = pd.Series([r[0]["fetch_status"] for r in results]).value_counts().to_dict()
        msg = f"{datetime.datetime.utcnow().isoformat(timespec='seconds')} done={n_done}/{len(todo)} reqs={req_count[0]} elapsed={el/60:.1f}min rate={req_count[0]/el:.2f}req/s chunk_status={st}"
        print(msg, flush=True)
        with open(PROGRESS, "a") as fh:
            fh.write(msg + "\n")
print(f"FINISHED reqs={req_count[0]} wall_s={time.time()-t0:.0f}", flush=True)
with open(PROGRESS, "a") as fh:
    fh.write(f"FINISHED reqs={req_count[0]} wall_s={time.time()-t0:.0f}\n")
