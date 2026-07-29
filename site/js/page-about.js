import { loadMeta, loadFacets, state, fmt, esc } from './data.js';
import { mount } from './ui.js';

await loadMeta(); await loadFacets();
mount('about.html');
const C=state.meta.counts, I=state.meta.incidental, M=state.meta.model;

document.getElementById('body').innerHTML=`
<div class="panel">
  <h1>About this browser, what it covers, and where it will mislead you</h1>
  <p class="lede">A Tier-1 minimum viable product: a searchable index of ${fmt(C.findings)} findings that an
  automated pipeline extracted from ${fmt(C.papers)} POTS and dysautonomia papers. It exists to test whether the
  extraction method produces something a researcher can actually use, and to be usable as a discovery
  instrument while that question is open.</p>
</div>

<div class="panel" id="scope">
  <h2>1. Scope — what is and is not in here</h2>
  <p><b>Tier 1 extracted the POTS/dysautonomia literature and nothing else.</b> It processed chunks
  0–${C.tier1_chunks-1} of a ${C.corpus_chunks}-chunk corpus, which is <b>${fmt(C.papers)} of roughly
  ${fmt(C.corpus_papers_total)} corpus papers</b> — about
  ${(100*C.papers/C.corpus_papers_total).toFixed(0)}%. Within that scope, papers carry one of seven condition
  labels (listed below); the corpus was retrieved by a POTS/dysautonomia search, so those labels describe the
  extracted papers rather than seven separately searched literatures.</p>
  <div class="note stop"><b>This is not a cross-condition resource.</b> Seven related conditions appear in the
  data, but <i>only as incidental mentions inside POTS/dysautonomia papers</i>:
  ${Object.entries(I).map(([k,v])=>`${esc(k)} (${v} papers)`).join(', ')}.
  Those counts are papers about POTS/dysautonomia that happened to mention the condition — they are
  <b>not those conditions' own literature</b>, which sits in Tiers 2–4 and has <b>not yet been extracted</b>.
  Any apparent cross-condition pattern here is a statement about what POTS researchers wrote, not about the
  other field.</div>
  <p>Condition labels <i>inside</i> the Tier-1 scope: <code>POTS</code>, <code>dysautonomia</code>,
  <code>long_COVID</code>, <code>small_fiber_neuropathy</code>, <code>orthostatic_hypotension</code>, and the
  non-specific <code>general</code> / <code>multiple</code> buckets. These reflect the extracted corpus, but
  they are still labels applied within a POTS/dysautonomia search — not separately searched literatures.</p>
</div>

<div class="panel">
  <h2>2. Not medical advice</h2>
  <div class="note stop">Everything here is <b>machine-extracted research information</b>. It is not clinical
  guidance, contains no diagnostic or treatment recommendations, and must not be used to make decisions about
  anyone's health. Findings are automated summaries that can misstate what a paper found. Individual studies
  also do not generalize to individual people. Take any personal health question to a qualified clinician who
  can see your full context.</div>
</div>

<div class="panel">
  <h2>3. Attribution — this is other people's work</h2>
  <p>Every finding links to its source paper by DOI and PubMed ID, with authors and journal shown. The research
  is theirs; this site only indexes automated summaries of it. <b>Read the original before citing anything.</b>
  Where a short verbatim quote is shown it is a copyrighted excerpt from the paper, truncated to
  ${C.emb_shards? state.meta.quote_max_chars : 200} characters and always displayed next to the full citation and
  link. No bulk quote export is offered, by design.</p>
</div>

<div class="panel" id="limits">
  <h2>4. Limitations — read these before trusting any number</h2>
  <ul class="tight">
    <li><b>Automated extraction has errors.</b> Findings were produced by a language model reading paper text.
      It can misattribute a direction, merge two claims, or state a hedged result as confident. The
      <code>certainty</code> field records hedging as extracted, which is itself an extraction.</li>
    <li><b>Entity mappings are imperfect.</b> ${fmt(C.map_low)} mappings are low confidence and about
      ${fmt(C.map_medium)} are medium; both are flagged in the UI with a <span class="tag lowconf">map</span> tag.
      An over-merged canonical entity silently pools distinct things — entity pages list every original string
      folded in so you can check.</li>
    <li><b>Co-occurrence is not causation.</b> The association table measures only that two entities appeared in
      the same paper. Many significant pairs are reporting conventions (measures always reported together);
      those are labelled and hidden by default.</li>
    <li><b>Thin evidence includes noise and single-lab artifacts.</b> The under-studied table rewards
      "few papers, all agreeing" — which is exactly what a spurious finding also looks like.</li>
    <li><b>${fmt(C.contra_umbrella)} of ${fmt(C.contradictions)} contradictions sit under umbrella condition
      labels</b> and may reflect <b>pooled distinct diseases rather than replication failure</b>. Two studies of
      different populations can disagree and both be correct. ${fmt(C.contra_moderator)} have a visible
      moderator that may explain the split.</li>
    <li><b>Evidence tiers are bottom-heavy.</b> Review/expert-opinion (${fmt(6507)}) and case reports/series
      outnumber RCTs (${fmt(877)}) and meta-analyses (${fmt(840)}) by a wide margin.</li>
    <li><b>Semantic search is exact but the model is small.</b> Query embedding runs the real
      ${esc(M.name)} model in your browser, so ranking is true cosine similarity, not an approximation — but
      a 384-dimension MiniLM still misses nuance. Keyword search is the exact-match fallback.</li>
  </ul>
</div>

<div class="panel">
  <h2>5. Data dictionary and counting rules</h2>

  <h3>Entity coverage — two different numbers, often conflated</h3>
  <div class="tblwrap"><table>
    <thead><tr><th>Field</th><th>Rows with a value</th><th>% of ${fmt(C.findings)}</th><th>Meaning</th></tr></thead>
    <tbody>
      <tr><td><code>entity</code></td><td class="num">${fmt(C.entity_string_rows)}</td>
        <td class="num">${C.entity_string_pct}%</td>
        <td>The <b>original</b> extracted entity string, as written in the paper.</td></tr>
      <tr><td><code>canonical_entity</code></td><td class="num">${fmt(C.canonical_entity_rows)}</td>
        <td class="num">${C.canonical_entity_pct}%</td>
        <td>A <b>canonicalized</b> entity. This is what entity pages, entity filters and entity charts use.</td></tr>
      <tr><td>gap</td><td class="num">${fmt(C.entity_unmapped_rows)}</td><td class="num">—</td>
        <td>Rows naming an entity that received <b>no</b> canonical mapping.</td></tr>
    </tbody></table></div>
  <p><b>These are not the same thing.</b> Canonical-entity coverage is
  <b>${C.canonical_entity_pct}%</b> of findings (spanning ${fmt(C.papers_with_canonical_entity)} of
  ${fmt(C.papers)} papers), while the original entity string is present on ${C.entity_string_pct}%.
  The remaining ~47% of findings name no entity at all — mostly symptom and phenotype findings, which is
  expected by design.</p>
  <p>Of <b>${fmt(C.strings_total)}</b> distinct entity strings in the corpus,
  <b>${fmt(C.strings_mapped)}</b> resolve to a canonical entity and <b>${fmt(C.strings_unmapped_distinct)}</b>
  do not (${fmt(C.strings_mapped)} + ${fmt(C.strings_unmapped_distinct)} = ${fmt(C.strings_total)}).
  Canonicalization deliberately covered the <b>head</b> of the distribution; the tail of one-off strings was
  left alone because mapping it would cost far more than it changes any count.</p>
  <p>The entity vocabulary itself holds <b>${fmt(C.vocab_entries)}</b> entries —
  ${fmt(C.vocab_direct)} direct mappings plus ${fmt(C.vocab_compound)} compound strings that were split into
  components — which collapse to the <b>${fmt(C.canonical_entities)}</b> canonical entities used across the site
  (${fmt(C.entities_with_ontology)} of them carrying an ontology ID, by source database:
  ${Object.entries(C.ontology_sources).sort((a,b)=>b[1]-a[1])
     .map(([s,n])=>`<b>${n}</b> ${esc(s)}`).join(', ')}).
  HGNC and NCBIGene are distinct databases and are counted separately rather than pooled as "genes".
  Note that ${fmt(C.vocab_direct)} is a <i>vocabulary</i> count and
  ${fmt(C.strings_mapped)} is a count of <i>distinct strings observed in the findings</i> — different
  denominators, so they are reported separately rather than mixed.</p>
  <div class="note"><b>Consequence for the UI.</b> Entity-based views cover about ${C.canonical_entity_pct}% of
  findings, <b>not half the corpus</b>. Findings with an unmapped entity string are excluded from entity
  roll-ups but remain fully findable by <a href="index.html">keyword search</a> on their original string, and
  the browser shows that string on the result card marked <i>not canonicalized</i> so those rows never silently
  vanish.</div>

  <h3>Counting rules</h3>
  <ul class="tight">
    <li><b>Papers are counted on <code>canonical_pmid</code></b>, after validated duplicate merging. This
      differs slightly from raw-pmid counts, and the difference is stated wherever it matters.</li>
    <li><b>Total vs direct.</b> Entity pages show <i>papers</i> (all rows) and <i>papers (direct)</i>
      (excluding <code>split_derived</code> rows created by splitting a compound entity string) separately.
      Example: norepinephrine is 194 papers on canonical_pmid including split-derived rows, and
      176 on the direct-only basis (195 / 177 on raw pmid). ELP1 is 53 vs 52 direct on canonical_pmid
      (58 / 57 on raw pmid) — three of the merged groups are ELP1 preprint→published pairs.</li>
    <li><b>Findings:</b> ${fmt(C.findings)} rows from ${fmt(C.findings_pre_split)} pre-split;
      the growth is compound-entity splitting only, and the ${fmt(C.distinct_finding_text)} distinct
      finding texts are unchanged by it.</li>
  </ul>

  <h3>Duplicate-paper handling — validated, not applied blindly</h3>
  <p><b>${C.dedup_groups_examined} duplicate-title groups were examined</b>
  (${C.dedup_pmids_examined} pmids, ${C.dedup_findings_examined} findings).
  <b>${C.dedup_groups_merged} groups were merged</b>: ${C.dedup_pmids_merged} pmids folded into their canonical
  record and ${C.dedup_findings_reattributed} findings reattributed via <code>canonical_pmid</code>. No findings
  were deleted and the merge is fully reversible. The merges were 5 preprint→published pairs
  (bioRxiv / Research Square), 1 guideline co-published in two journals simultaneously, 1 single-page
  companion/correction, and 1 erratum stub.</p>
  <p><b>${C.dedup_groups_retained} group was deliberately NOT merged</b> — a false positive caught by
  author-list validation. "Post-COVID-19 Postural Orthostatic Tachycardia Syndrome" is a generic title shared
  by two genuinely distinct papers with fully disjoint author lists (author overlap 0.0):
  pmid <a href="paper.html?pmid=34053992">34053992</a> (Ishibashi et al., <i>Internal Medicine</i>, 2021) and
  pmid <a href="paper.html?pmid=35470419">35470419</a> (Savytskyi et al., <i>Cardiology Journal</i>, 2022).
  Merging them would have destroyed a real independent replication.</p>
  <p>So: <b>${C.dedup_groups_examined} groups examined, ${C.dedup_groups_merged} merged,
  ${C.dedup_groups_retained} retained as genuinely distinct papers</b> —
  ${fmt(C.papers_pmids)} pmids → ${fmt(C.papers)} distinct canonical papers. Title-only matching would have
  been wrong here, which is why the dedup map artifact records all ${C.dedup_groups_examined} groups with a
  <code>merge_applied</code> flag for auditing.</p>
</div>

<div class="panel">
  <h2>6. How search works</h2>
  <p><b>Keyword mode (default).</b> Substring and token matching over finding text, canonical entity, the
  original entity string and condition. Instant, no download, works with no key and no model — this is why it is
  the default.</p>
  <p><b>Semantic mode.</b> The ${fmt(C.findings)} findings were embedded with
  <code>${esc(M.name)}</code> (${M.dims} dimensions), quantized to int8
  (${C.emb_mb} MB in ${C.emb_shards} lazy-loaded shards; dequantization fidelity mean cosine
  ${C.emb_fidelity}). Your query is embedded <b>in your browser</b> with
  <code>${esc(M.browser_id)}</code> — the ONNX export of that same checkpoint — via transformers.js in a Web
  Worker. Because query and document vectors come from the same model, cosine ranking is <b>exact, not an
  approximation</b>. First use downloads about ${M.approx_mb} MB, then the browser caches it.</p>
  <div class="note">If the model cannot load — no network, a blocked CDN, or a browser without WASM support —
  the page says semantic search is unavailable and <b>keyword search keeps working</b>. A failed model load
  never breaks the site.</div>
</div>

<div class="panel">
  <h2>7. Chat panel and your API key</h2>
  <p>The chat panel is optional. It retrieves findings locally and sends only those findings plus your question
  to a model provider, using a key <b>you</b> paste. The key lives in this browser's
  <code>localStorage</code> and is sent only to the provider's own HTTPS endpoint — this site has no backend to
  send it to, no key is bundled in the code, and a "clear key" button removes it. Answers are required to cite
  the findings used. Search, browsing, discovery tables and both chart surfaces work with no key at all.</p>
</div>`;
