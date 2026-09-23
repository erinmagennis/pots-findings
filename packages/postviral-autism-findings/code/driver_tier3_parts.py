"""Tier-3 part-aware dispatcher — chunks 244, 246-254.

WHY THIS EXISTS (three defects measured on the 242-246 run, not hypothetical)

  1. UNREACHABLE CEILING BRANCH. driver_tier3.py's gate() has a token-ceiling
     branch that returns "token-ceiling (split required)", but it is only called
     when `status=="completed" and vid` is truthy. A worker killed by the 2.0M
     per-frame ceiling submits version_id='' -- so the branch never runs, the
     chunk is scored a generic failure, and it is retried IDENTICALLY. Chunk 244
     burned two full ~2M-token attempts this way for zero rows, and a third was
     dispatched and stopped in flight once the cause was identified. Here the
     ceiling is detected from stats.error REGARDLESS of vid, and the remedy is a split.

  2. CEILING MISCLASSIFIED AS BUDGET EXHAUSTION. A ceiling kill has the same
     surface signature as the quota signature (no output, no parse_fail, no
     blocked), so it incremented the driver's infra fail_streak. Two such refills
     trip BUDGET_HALT_STREAK and halt the whole run as "budget likely exhausted".
     A ceiling failure is a DETERMINISTIC CAPACITY fact about a 50-paper chunk,
     not an account-level budget event; it must never halt the run.

  3. PART-BLIND DONE DETECTION. done_chunks() matches only chunk_NNN_findings.parquet,
     so a chunk completed as parts looks undone and is re-dispatched forever.
     Done here means: a whole file OR a COMPLETE part set.

Everything else is inherited unchanged from the pinned driver: build_task (the
worker prompt, incl. its part= support), gate (yield/blocked/enum/guard rules),
N_INFLIGHT=3, WORKER_MAX_S watchdog. Concurrency is NEVER raised above 3 --
8.5 req/s produced a 92% blocked rate; 3.3 req/s produced 0%.
"""
import json, re, time

N_INFLIGHT   = 3
MAX_ATTEMPTS = 3
WORKER_MAX_S = 3000
COLLECT_SLICE = 120
N_PARTS_DEFAULT = 2      # 25 papers/worker: measured whole-chunk cost is ~2-3M, halves fit under 2.0M

CEILING_RX = re.compile(r"token ceiling|per-frame token|2\.0M", re.I)


def is_ceiling(stats):
    """A ceiling kill is identified by the ERROR TEXT, never by the empty-output
    signature it shares with a quota stall. Misreading one as the other is what
    caused defects 1 and 2 above."""
    return bool(CEILING_RX.search(str((stats or {}).get("error") or "")))


def done_units(host, targets):
    """-> (done_chunks, have_parts) where done means a whole file or a complete
    part set. have_parts maps cid -> {(i,n) present} so a resumed run re-dispatches
    only the MISSING parts and never re-pays for one already saved."""
    r = host.artifacts(filename="_findings.parquet", limit=900)
    whole, parts = set(), {}
    for a in r["artifacts"]:
        fn = a["filename"]
        mw = re.match(r"chunk_(\d+)_findings\.parquet$", fn)
        mp = re.match(r"chunk_(\d+)_part(\d+)of(\d+)_findings\.parquet$", fn)
        if mw and int(mw.group(1)) in targets:
            whole.add(int(mw.group(1)))
        elif mp and int(mp.group(1)) in targets:
            parts.setdefault(int(mp.group(1)), set()).add((int(mp.group(2)), int(mp.group(3))))
    done = set(whole)
    for cid, got in parts.items():
        ns = {n for (_i, n) in got}
        if len(ns) == 1:
            n = ns.pop()
            if sorted(i for (i, _n) in got) == list(range(n)):
                done.add(cid)
    return done, parts


def run(host, build_task, gate, targets, split_all=True, n_parts=N_PARTS_DEFAULT, log_prefix=""):
    """Dispatch `targets` as parts. Returns a computed report -- every count in it
    comes from a variable, never a typed literal."""
    targets = set(targets)
    done, have_parts = done_units(host, targets)
    # work unit = (cid, (i,n)) for parts, or (cid, None) for a whole attempt
    pending = []
    for cid in sorted(targets - done):
        if split_all:
            got = have_parts.get(cid, set())
            for i in range(n_parts):
                if (i, n_parts) not in got:
                    pending.append((cid, (i, n_parts)))
        else:
            pending.append((cid, None))

    attempts, inflight, starts = {}, {}, {}
    gate_log, guard_log, enum_log, ceiling_log = [], [], [], []
    finished = failed = 0
    print(f"{log_prefix}[parts] start: {len(pending)} work units over "
          f"{len(targets - done)} chunks; {len(done)} already done", flush=True)

    def refill():
        while len(inflight) < N_INFLIGHT and pending:
            cid, part = pending.pop(0)
            key = (cid, part)
            if attempts.get(key, 0) >= MAX_ATTEMPTS:
                continue
            d = host.delegate({"task": build_task(cid, part),
                               "name": f"c{cid}p{part[0]}" if part else f"chunk{cid:03d}",
                               "output_schema": SCHEMA}, wait=False)
            fid = d["frame_id"]
            inflight[fid] = key
            starts[fid] = time.time()
            attempts[key] = attempts.get(key, 0) + 1
            print(f"{log_prefix}[parts] dispatched chunk {cid} part {part} "
                  f"(attempt {attempts[key]}) frame {fid[:8]}", flush=True)

    refill()
    while inflight or pending:
        res = host.collect(list(inflight.keys()), timeout=COLLECT_SLICE) if inflight else []
        # watchdog: reclaim a slot from a worker past WORKER_MAX_S
        now = time.time()
        for fid in list(inflight.keys()):
            if now - starts.get(fid, now) > WORKER_MAX_S:
                cid, part = inflight[fid]
                try:
                    host.stop_child(fid, reason=f"watchdog: exceeded {WORKER_MAX_S}s")
                except Exception:
                    pass
                d2, hp = done_units(host, targets)
                saved = (cid in d2) or (part in hp.get(cid, set()))
                inflight.pop(fid, None)
                print(f"{log_prefix}[parts] WATCHDOG reclaimed chunk {cid} part {part} "
                      f"(saved={saved})", flush=True)
                if not saved:
                    pending.append((cid, part))

        for r in (res or []):
            if r.get("status") == "running":
                continue
            fid = r.get("sender_frame_id") or r.get("frame_id")
            key = inflight.pop(fid, None)
            if key is None:
                continue
            cid, part = key
            so = r.get("structured_output") or {}
            st = so.get("stats") or {}
            vid = so.get("version_id")

            # DEFECT 1+2 FIX: ceiling detected from the error text regardless of vid,
            # and NEVER counted as an infrastructure/budget failure.
            if is_ceiling(st) and not vid:
                ceiling_log.append({"chunk": cid, "part": part, "attempt": attempts.get(key)})
                nxt = (part[1] * 2) if part else n_parts
                print(f"{log_prefix}[parts] chunk {cid} part {part} hit the 2.0M ceiling "
                      f"-> re-splitting into {nxt} parts", flush=True)
                got = have_parts.get(cid, set())
                for i in range(nxt):
                    if (i, nxt) not in got:
                        pending.append((cid, (i, nxt)))
                continue

            gv = st.get("guard_violations") or 0
            if gv:
                guard_log.append({"chunk": cid, "part": part, "count": gv,
                                  "detail": st.get("guard_violation_detail")})
                print(f"{log_prefix}[parts] chunk {cid} GUARD VIOLATIONS: {gv}", flush=True)
            ev = st.get("enum_violations") or {}
            if ev:
                enum_log.append({"chunk": cid, "part": part, "violations": ev})

            ok, frac, enum_bad, reason = (None, None, {}, r.get("status") or "no-output")
            if r.get("status") == "completed" and vid:
                ok, frac, enum_bad, reason = gate(cid, so)
                if ok is None:
                    ok, frac, reason = True, -1.0, "productive-unverifiable"
            gate_log.append({"chunk": cid, "part": part, "ok": bool(ok), "reason": reason,
                             "yield": frac, "findings": st.get("n_findings"),
                             "blocked_frac": st.get("blocked_frac"),
                             "guard_violations": gv, "attempt": attempts.get(key)})
            if ok:
                finished += 1
            else:
                failed += 1
                if attempts.get(key, 0) < MAX_ATTEMPTS:
                    pending.append((cid, part))
                print(f"{log_prefix}[parts] chunk {cid} part {part} FAILED: {reason}", flush=True)

        refill()
        for fn, obj in (("gate_log_parts.json", gate_log), ("guard_violations_parts.json", guard_log),
                        ("enum_violations_parts.json", enum_log), ("ceiling_log_parts.json", ceiling_log)):
            json.dump(obj, open(fn, "w"), indent=1)
        d3, _ = done_units(host, targets)
        with open("progress_parts.txt", "a") as fp:
            fp.write(f"{len(d3 & targets)}/{len(targets)} chunks | units in-flight {len(inflight)} "
                     f"| pending {len(pending)} | +{finished} -{failed}\n")
        print(f"{log_prefix}[parts] {len(d3 & targets)}/{len(targets)} chunks done | "
              f"in-flight {len(inflight)} | pending {len(pending)}", flush=True)

    final_done, final_parts = done_units(host, targets)
    return {"chunks_done": sorted(final_done & targets),
            "chunks_missing": sorted(targets - final_done),
            "n_done": len(final_done & targets), "n_targets": len(targets),
            "gate_log": gate_log, "guard_violations": guard_log,
            "enum_violations": enum_log, "ceiling_events": ceiling_log,
            "part_files": {c: sorted(v) for c, v in final_parts.items()}}
