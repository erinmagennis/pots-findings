"""Tier-3 merge with duplicate-artifact protection.

The pilot exposed a real hazard: re-extracting a chunk creates a SECOND artifact
record with the same filename, so a naive scan picks whichever the store returns
first — silently mixing a pre-fix run with a post-fix one. Rule adopted:
for each chunk_id keep exactly ONE record, the one with the most rows, and REPORT
every superseded record so the choice is auditable rather than implicit.
"""
import pandas as pd, re, json

WHOLE_RX = re.compile(r"chunk_(\d+)_findings\.parquet$")
PART_RX  = re.compile(r"chunk_(\d+)_part(\d+)of(\d+)_findings\.parquet$")

def collect_chunk_artifacts(host, target_chunks):
    """Returns {chunk_id: {"whole":[art,...], "parts":{(i,n):[art,...]}}}.
    A chunk that hit the per-worker token ceiling is extracted as PART files; the
    merge must treat all parts of a chunk as ONE chunk, or the chunk silently
    disappears from the corpus."""
    r = host.artifacts(filename="_findings.parquet", limit=900)
    by_chunk = {}
    for a in r["artifacts"]:
        fn = a["filename"]
        mw = WHOLE_RX.match(fn); mp = PART_RX.match(fn)
        if mw:
            cid = int(mw.group(1))
            if cid in target_chunks:
                by_chunk.setdefault(cid, {"whole":[], "parts":{}})["whole"].append(a)
        elif mp:
            cid, i, n = int(mp.group(1)), int(mp.group(2)), int(mp.group(3))
            if cid in target_chunks:
                by_chunk.setdefault(cid, {"whole":[], "parts":{}})["parts"].setdefault((i,n), []).append(a)
    return by_chunk

def _best(host, arts):
    scored = []
    for a in arts:
        try: n = len(pd.read_parquet(host.artifact_path(a["latest_version_id"])))
        except Exception: n = -1
        scored.append((n, a))
    scored.sort(key=lambda t: t[0], reverse=True)
    return scored[0], scored[1:]

def resolve_duplicates(host, by_chunk):
    """One record set per chunk. Prefers a WHOLE extraction; falls back to the
    complete set of PART files. An INCOMPLETE part set is reported, never merged
    silently (a half chunk masquerading as a whole one would corrupt coverage)."""
    chosen, report, incomplete = {}, [], []
    for cid, recs in sorted(by_chunk.items()):
        if recs["whole"]:
            (n_best, best), rest = _best(host, recs["whole"])
            chosen[cid] = {"version_ids": [best["latest_version_id"]], "rows": n_best,
                           "mode": "whole"}
            for n, a in rest:
                report.append({"chunk": cid, "superseded_version_id": a["latest_version_id"],
                               "rows": n, "kept_rows": n_best, "reason": "duplicate whole"})
            # parts become redundant once a whole extraction exists
            for key, arts in recs["parts"].items():
                for a in arts:
                    report.append({"chunk": cid, "superseded_version_id": a["latest_version_id"],
                                   "reason": f"part{key} superseded by whole extraction"})
        elif recs["parts"]:
            ns = {n for (_i, n) in recs["parts"]}
            if len(ns) != 1:
                incomplete.append({"chunk": cid, "reason": f"conflicting part schemes {ns}"}); continue
            n_total = ns.pop()
            have = sorted(i for (i, _n) in recs["parts"])
            if have != list(range(n_total)):
                incomplete.append({"chunk": cid, "reason": f"missing parts; have {have} of {n_total}"}); continue
            vids, rows = [], 0
            for i in range(n_total):
                (nb, b), rest = _best(host, recs["parts"][(i, n_total)])
                vids.append(b["latest_version_id"]); rows += max(0, nb)
                for n, a in rest:
                    report.append({"chunk": cid, "superseded_version_id": a["latest_version_id"],
                                   "rows": n, "reason": f"duplicate part {i}"})
            chosen[cid] = {"version_ids": vids, "rows": rows, "mode": f"{n_total}-part"}
    return chosen, report, incomplete

def merge_tier3(host, target_chunks):
    by_chunk = collect_chunk_artifacts(host, set(target_chunks))
    chosen, superseded, incomplete = resolve_duplicates(host, by_chunk)
    missing = [c for c in target_chunks if c not in chosen]
    frames = []
    for cid, meta in sorted(chosen.items()):
        for vid in meta["version_ids"]:
            df = pd.read_parquet(host.artifact_path(vid))
            df["_source_version_id"] = vid
            frames.append(df)
    merged = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return merged, {"chosen": chosen, "superseded": superseded,
                    "incomplete_part_sets": incomplete, "missing_chunks": missing,
                    "n_chunks": len(chosen), "n_rows": int(len(merged)),
                    "n_papers": int(merged.pmid.nunique()) if len(merged) else 0,
                    "split_chunks": {c: v["mode"] for c, v in chosen.items() if v["mode"] != "whole"}}
