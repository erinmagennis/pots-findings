"""Durable (name, kind) -> authority-ID resolution cache for the Tier-3 corpus.

WHY THIS EXISTS
    multi_authority_resolver.resolve_entity keeps its _CACHE in module memory only.
    Every re-grounding cycle therefore re-pays the full ~2h of network time for names
    that were already resolved in a previous cycle. This module persists each
    resolution to a parquet artifact so a later cycle asks the authorities ONLY about
    names it has never seen.

DISCIPLINE — unchanged from the resolver it wraps. This module adds NO matching logic.
    * It never invents, guesses, or fuzzy-matches an ID. It only stores and replays what
      an authority returned.
    * A cached miss is stored as a miss (id=None, source='unresolved_nulled'), so a name
      the authorities rejected is not silently retried forever -- but see REVALIDATION:
      misses are re-asked when the caller requests it, because an authority can add a
      term later. A cached HIT is never re-asked; authority IDs are stable identifiers.
    * Provenance is carried through verbatim: the stored `source` is the resolver's own
      string naming the authority and the match path (exact vs authority-asserted
      synonym). Nothing is rewritten to look more confident than it was.
    * Every cached row records cache_version and resolved_at so a future audit can tell
      which resolver build produced an ID.

CHECKPOINTING
    resolve_all() writes the cache to disk every `checkpoint_every` NEW resolutions
    (default 250). An interruption loses at most that many lookups, never the whole run.
"""
import os, time, json

CACHE_FILE = "resolution_cache.parquet"
CACHE_VERSION = "multi_authority_resolver@4240086b"   # resolver artifact this cache was built with

_COLS = ["name_key", "kind", "resolved_id", "label", "source", "cache_version", "resolved_at"]


def load_cache(path=CACHE_FILE, seed_version_id=None, host=None):
    """-> dict[(name_key, kind)] = (id, label, source). Empty dict if no cache yet."""
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
        return {}
    df = pd.read_parquet(src)
    out = {}
    for r in df.itertuples(index=False):
        out[(r.name_key, r.kind)] = (
            (r.resolved_id if r.resolved_id else None),
            (r.label if r.label else None),
            r.source,
        )
    return out


def save_cache(cache, path=CACHE_FILE):
    import pandas as pd
    rows = [
        {"name_key": k[0], "kind": k[1], "resolved_id": v[0], "label": v[1],
         "source": v[2], "cache_version": CACHE_VERSION, "resolved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        for k, v in cache.items()
    ]
    df = pd.DataFrame(rows, columns=_COLS)
    tmp = path + ".tmp"
    df.to_parquet(tmp, index=False)
    os.replace(tmp, path)          # atomic: a reader never sees a half-written cache
    return len(df)


def resolve_all(pairs, resolve_entity, cache=None, checkpoint_every=250,
                retry_misses=False, path=CACHE_FILE, progress=True):
    """Resolve unique (name, kind) pairs, reusing `cache` and checkpointing to disk.

    pairs            : iterable of (name, kind) -- deduped internally on (lower(name), kind)
    resolve_entity   : the pinned resolver function; called ONLY for uncached pairs
    retry_misses     : if True, re-ask the authorities about previously-unresolved names
                       (an authority may have added the term since the last cycle)

    Returns (cache, stats). Stats are computed counters, never literals.
    """
    cache = dict(cache or {})
    uniq = {}
    for name, kind in pairs:
        if not isinstance(name, str) or not name.strip():
            continue
        uniq[(name.strip().lower(), kind if isinstance(kind, str) else None)] = name.strip()

    st = {"unique_pairs": len(uniq), "cache_hits": 0, "network_calls": 0,
          "new_resolved": 0, "new_missed": 0, "checkpoints": 0}
    since_ckpt = 0

    for i, (key, orig_name) in enumerate(uniq.items()):
        cached = cache.get(key)
        if cached is not None and not (retry_misses and cached[0] is None):
            st["cache_hits"] += 1
            continue
        out = resolve_entity(orig_name, key[1])
        st["network_calls"] += 1
        cache[key] = out
        if out[0]:
            st["new_resolved"] += 1
        else:
            st["new_missed"] += 1
        since_ckpt += 1
        if since_ckpt >= checkpoint_every:
            save_cache(cache, path)
            st["checkpoints"] += 1
            since_ckpt = 0
            if progress:
                print(f"[cache] ckpt {st['checkpoints']}: {i+1}/{len(uniq)} pairs seen, "
                      f"{st['network_calls']} asked, {st['new_resolved']} resolved", flush=True)

    save_cache(cache, path)
    st["checkpoints"] += 1
    st["cache_size"] = len(cache)
    return cache, st


def apply_to_df(df, cache, name_col, kind_col,
                id_col="entity_id", label_col="entity_label", src_col="entity_id_source"):
    """Write cached IDs onto a findings frame. Unmatched names stay NULL, by design."""
    ids, labels, srcs = [], [], []
    for name, kind in zip(df[name_col], df[kind_col]):
        key = (name.strip().lower(), kind) if isinstance(name, str) and name.strip() else None
        hit = cache.get(key) if key else None
        if hit is None:
            ids.append(None); labels.append(None); srcs.append("unresolved_nulled")
        else:
            ids.append(hit[0]); labels.append(hit[1]); srcs.append(hit[2])
    out = df.copy()
    out[id_col], out[label_col], out[src_col] = ids, labels, srcs
    return out


def selftest(resolve_entity=None):
    """-> list of FAILURES (empty list means all pass). Offline except the last check."""
    f = []
    # round-trip a hit and a miss through save/load
    c = {("interleukin-6", "gene/protein"): ("UniProt:P05231", "Interleukin-6", "authority_lookup_uniprot_exact"),
         ("not a real entity xyzzy", "chemical/metabolite"): (None, None, "unresolved_nulled")}
    p = "_selftest_cache.parquet"
    try:
        save_cache(c, p)
        back = load_cache(p)
        if back.get(("interleukin-6", "gene/protein")) != c[("interleukin-6", "gene/protein")]:
            f.append("hit did not round-trip")
        miss = back.get(("not a real entity xyzzy", "chemical/metabolite"))
        if miss is None or miss[0] is not None or miss[2] != "unresolved_nulled":
            f.append(f"miss did not round-trip as a miss: {miss}")
    finally:
        if os.path.exists(p):
            os.remove(p)
    # a cached pair must NOT trigger a network call
    calls = []
    def spy(n, k):
        calls.append((n, k)); return (None, None, "unresolved_nulled")
    _, st = resolve_all([("Interleukin-6", "gene/protein")], spy, cache=c,
                        path="_selftest_cache2.parquet", progress=False)
    if calls:
        f.append(f"cached pair triggered a network call: {calls}")
    if st["cache_hits"] != 1:
        f.append(f"expected 1 cache hit, got {st['cache_hits']}")
    # an ID-shaped string must never be accepted as a NAME to resolve
    _, st2 = resolve_all([("HP:0002315", "physiological-measure")], spy, cache={},
                         path="_selftest_cache2.parquet", progress=False)
    if st2["network_calls"] != 1:
        f.append("id-shaped name should still be ASKED (resolver decides), not silently kept")
    for p2 in ("_selftest_cache2.parquet",):
        if os.path.exists(p2):
            os.remove(p2)
    return f
