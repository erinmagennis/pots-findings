# SITE_CONTRACT.md: what is safe to change, and what is not

Written so a redesign has a spec to work against instead of reverse-engineering the current site.

## The three layers

Everything in this repo is exactly one of these. Know which layer a file is in before you edit it.

### Layer 1: THE RECORD (never edit, never regenerate)

```
data/**                       tier-1 findings, vocabulary, derived tables
data/tier2/**                 tier-2 findings, vocabulary v2, crossover, crosswalks
docs/**  docs/tier2/**        methods, limitations, data dictionaries
figures/**                    tier-1 figures
notebooks/**                  reproduction notebooks
validation/tier1_golden_facts.json
validation/tier2_golden_facts.json
```

This is months of extraction, adjudication and audit. It is what people cite. **Nothing in the
website is allowed to write here.** If a site build ever wants to modify a file in this list, the
build is wrong: stop it.

### Layer 2: SITE PROJECTION (never hand-edit)

```
site/data/*.json              facets, papers, entities, text_NN, detail_NN, meta, discovery tables
site/data/emb/*.bin           quantized embedding shards
site/data/emb/manifest.json
site/data/emb/quant_params.json
```

These files are the supplied combined projection. For this checkpoint they are protected by row-order,
schema, shard, source-row, and checksum verification. Do not hand-edit them.

The supplied overlay claimed full regeneration, but omitted `combined_generator.build_all()`, the upstream
combined discovery inputs, and the Tier 2 embedding-generation input. Therefore a full rebuild from Layer 1
is not currently available. `rebuild_site.py` now refuses to write rather than producing a partial result.
Run:

```
python site_tools/rebuild_site.py --check    # run the non-writing checkpoint gate
python site_tools/verify_site.py             # verify the current projection
python site_tools/verify_site.py --self-test # prove the checker catches planted errors
```

Both scripts live in `site_tools/`. `verify_site.py` exits 0 when the checkpoint passes and 1 with the
disagreement named. The future-tier handoff records the missing inputs required to restore full regeneration.

**Never hand-edit a file here.** Generate the next projection from the extraction pipeline, then rerun the gate.

### Layer 3: PRESENTATION (yours, edit freely)

```
site/*.html                   page shells
site/css/app.css              all styling
site/js/page-*.js             one module per page
site/js/ui.js                 shared components (header, footer, cards, tables)
site/js/data.js               the loader  <- see contract below before changing
site/js/search.js             semantic + keyword search
site/js/embed-worker.js       in-browser embedding worker
site/vendor/**                chart.umd.js
```

You cannot corrupt a finding by editing these. Worst case a page renders wrong and you fix the CSS
or revert the file. **This is where a redesign lives.**

## Redesign rules (the short version)

1. **Rewrite Layer 3 freely.** HTML, CSS, and any `page-*.js` can be replaced wholesale.
2. **Do not hand-edit Layer 2.** Rebuild it.
3. **Never write to Layer 1** from site code.
4. **Run `verify_site.py` before every deploy.** It fails loudly if a displayed number stopped
   matching the checkpoint record.
5. **Keep the scope caveat visible.** Tier-2 is partial (~55% of its corpus). `ui.js` exports
   `framingBanner()` and `entityCoverageNote()` for this: if you redesign, keep an equivalent.
   Removing it turns a partial map into an implied complete one.
6. **One page at a time.** Every page is an independent ES module; there is no build step and no
   framework. You can redesign `entities.html` without touching anything else.

## The data contract (what each page needs)

Architecture: framework-free ES modules. `data.js` fetches static JSON from `./data/` and caches
it. **Shard counts are read from the data, never hardcoded**: `findings_facets.json` carries `n`,
`shard_rows` and `n_shards`, so the site adapts to a larger corpus with no code change. Preserve
that property.

### `data.js`: the loader API your pages call

| Function | Returns |
|---|---|
| `loadMeta()` | `meta.json`: all corpus counts |
| `loadFacets()` | dictionary-encoded columns for every row, plus `inv` (value→code maps) |
| `loadPapers()` | `{rows, idx, get(i)}` + `state.pmidIndex` for pmid→row |
| `loadEntities()` | entity list + `state.entityByName` |
| `loadTextShard(s)` / `loadDetailShard(s)` | lazy per-shard finding text / detail fields |
| `shardOf(row)` | which shard a row lives in |
| `paper(i)` / `paperByPmid(pmid)` | a paper record |

Keep these signatures if you rewrite `data.js`; every page depends on them.

### Current site scope

The site data layer covers **both tiers**: 73,070 findings, 6,244 papers [canonical_pmid basis],
2,803 canonical entities, 13 shards. `meta.json` declares `version: "combined-t1t2-1"` and carries
the tier-2 coverage caveat.

Two facet fields exist that the tier-1-only site did not have:

| Facet key | Field | Use |
|---|---|---|
| `ti` | `tier` (`"1"` / `"2"`) | filter by extraction tier |
| `sl` | `source_literature` | filter by which condition literature a finding came from |

Both are dictionary-encoded like every other facet, so a redesign can use them with the existing
loader. Neither is required by any current page: they are available, not load-bearing.

### File shapes

| File | Shape |
|---|---|
| `meta.json` | `{version, generated_utc, counts:{...}}` |
| `findings_facets.json` | `{n, shard_rows, n_shards, dicts{}, cols{}, orig_entity{}, facet_fields{}, coverage{}}`: columns are integer codes into `dicts` |
| `papers.json` | `{fields:[...], rows:[[...]]}`: column-oriented; resolve via `idx` |
| `entities.json` | `{n, entities:[{name, kind, mapc, oid, osrc, olabel, nf, np_}]}` |
| `text_NN.json` | `{start, end, t:[...]}`: one finding text per row |
| `detail_NN.json` | `{start, end, quote, quant, eff, path, lim, fut, npart, comp, symp, treat, sec, ont}`: 14 parallel arrays |
| `associations/convergence/contradictions/understudied/null_results.json` | discovery tables for `page-discover.js` |
| `emb/manifest.json` | `{version, model, dims, dtype, quantization, fidelity_mean_cosine, total_rows, shard_rows, shards:[...]}` |

### Page → data dependencies

| Page | Needs |
|---|---|
| `index.html` | meta, facets |
| `papers.html` / `paper.html` | meta, facets, papers |
| `entities.html` / `entity.html` | meta, facets, entities (+ papers on detail) |
| `conditions.html` / `condition.html` | meta, facets, papers |
| `charts.html` | meta, facets, papers, entities |
| `builder.html` | meta, facets, papers, entities |
| `discover.html` | meta, papers + associations, contradictions, convergence, understudied, null_results |
| `search.html` (via `page-search.js`) | meta, facets, papers, entities + `emb/` |
| `chat.html` | meta, facets, papers, entities + `emb/` + visitor's own API key |
| `about.html` | meta, facets |

## The row-order contract (do not break this)

Row order across the whole data layer is **tier-1 rows first (0–36,458), then tier-2 rows
(36,459–73,069)**, each in its parquet's existing order. This is append-only: every tier-1 row index
that the shipped site already used still resolves to the same finding.

The facet columns, the text/detail shards, and the embedding shards all share this single row
indexing. If you regenerate one without the others, semantic search returns the wrong findings :
silently, with no error. `rebuild_site.py` regenerates them together for exactly this reason; that
is why you should not rebuild embeddings by hand.

Note the embedding quantization parameters were recomputed over the combined set, so
`emb/quant_params.json` must be loaded from the same build as the `.bin` shards. The site reads
shard filenames from `emb/manifest.json`, so this needs no JS change: but do not mix files from
two builds.

## Search and chat

`search.js` runs **two independent modes**:

- **Keyword**: instant, zero dependency, works with no model. The default; never let it depend
  on the model loading.
- **Semantic**: loads quantized embedding shards and embeds the query in-browser via a worker.
  Degrades to `unavailable` if the model or CDN cannot load; keyword still works.

Preserve that fallback. A redesign that makes search require the model breaks the page on slow or
restricted networks.

`chat.html` is **retrieval-augmented Q&A using a key the visitor pastes**, held in `localStorage`
on their device and sent only to the provider's endpoint. There is no server in this app.

**You never hold a key and it costs you nothing.** Keep it that way: do not add a server-side key,
and do not log or transmit the visitor's key anywhere. If you keep chat in a redesign, keep the
on-device explanation visible so visitors know where their key goes.

Two things chat needs when the corpus grows:
- Its retrieval must cover **both tiers**, so embeddings must be rebuilt over the full corpus.
- Its system prompt should state the coverage caveat, so answers do not imply completeness.
Also note the provider model ids in `page-chat.js` are pinned strings and will age: they are
Layer 3, so update them freely.

## If something goes wrong

| Symptom | Fix |
|---|---|
| A site number disagrees with a paper/report | `python verify_site.py`: it names the disagreeing values |
| Site data half-written or corrupted | restore the verified checkpoint projection, then run `verify_site.py` |
| A page is blank after a redesign | check the loader functions it calls still exist in `data.js` |
| Semantic search stopped working | expected if the model CDN is blocked; keyword must still work |
| You hand-edited a JSON and forgot what | restore the verified projection and rerun the checkpoint |

**The whole point of this layout:** you can break the website at any time and lose nothing, because
the record is untouched and the site is regenerable. Design boldly.
