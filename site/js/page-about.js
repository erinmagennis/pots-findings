import { loadMeta, loadFacets, state, fmt, esc } from './data.js';
import { mount, entityCoverageNote } from './ui.js';

await loadMeta(); await loadFacets();
mount('about.html');
const C=state.meta.counts, M=state.meta;
const literatures=Object.entries(C.findings_by_source_literature||{}).sort((a,b)=>b[1]-a[1]);

document.getElementById('body').innerHTML=`
<div class="panel">
  <h1>About this browser, its coverage, and its limits</h1>
  <p class="lede">A searchable checkpoint containing ${fmt(C.findings)} machine-extracted findings from
  ${fmt(C.papers)} canonical papers. It combines the published Tier 1 record with the first
  ${fmt(C.tier2_chunks_extracted)} of ${fmt(C.tier2_chunks_total)} Tier 2 chunks.</p>
</div>

<div class="panel" id="scope">
  <h2>1. Current scope</h2>
  <div class="note stop"><b>Tier 2 is ${C.tier2_coverage_pct}% complete.</b> Every Tier 2 and combined count on
  this site is a subset count. A literature with no displayed finding may simply be in an unprocessed chunk.
  Absence of a signal here is not evidence of absence in the research literature.</div>
  <p>Tier 1 contributes ${fmt(C.findings_tier1)} findings from ${fmt(C.papers_tier1)} canonical papers.
  The current Tier 2 subset contributes ${fmt(C.findings_tier2)} findings from ${fmt(C.papers_tier2)} papers.
  The paper sets do not overlap after canonicalization.</p>
  <h3>Findings by source literature</h3>
  <div class="statgrid">${literatures.map(([name,n])=>`<div class="stat"><div class="v">${fmt(n)}</div>
    <div class="k">${esc(name)}</div></div>`).join('')}</div>
  <p class="kv">Source literature records where a paper entered the extraction pipeline. It is different from
  the condition label assigned to an individual finding.</p>
</div>

<div class="panel">
  <h2>2. What the data can and cannot show</h2>
  <ul>
    <li>Co-mention means two entities appeared in the same paper. It does not establish interaction or causation.</li>
    <li>Shared biology across source literatures is not the same claim as patient comorbidity.</li>
    <li>A null or failed result does not prove ineffectiveness. Dose, comparator, sample size, and population matter.</li>
    <li>Contradictory directions may reflect different populations or methods rather than a direct replication failure.</li>
  </ul>
  ${entityCoverageNote('entity pages, entity filters, and entity-based charts')}
</div>

<div class="panel" id="limits">
  <h2>3. Extraction and provenance</h2>
  <p>These are automated extractions and can contain errors. Read the cited paper before relying on a finding.
  The website shows provenance excerpts of up to ${M.quote_max_chars} characters beside the citation so a reader
  can locate the relevant passage.</p>
  <p>Paper counts use canonical PMID. The combined total is ${fmt(C.papers)}, not a count of raw PMID rows.
  Finding rows remain append-only: Tier 1 occupies rows 0 through ${fmt(C.findings_tier1-1)}, followed by the
  current Tier 2 rows.</p>
</div>

<div class="panel">
  <h2>4. Search and chat</h2>
  <p>Keyword search works without an external model. Semantic search may become unavailable when its browser model
  cannot load; keyword search remains available. The chat page uses a key supplied by the visitor and stores it only
  in that browser's local storage. This site has no server-side API key.</p>
</div>

<div class="panel">
  <h2>5. Not medical advice</h2>
  <p>This browser reports what papers said. It does not diagnose conditions, recommend treatments, or replace
  advice from a qualified clinician.</p>
</div>`;
