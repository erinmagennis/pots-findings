import { loadMeta, loadFacets, state, fmt, esc } from './data.js';
import { mount, entityCoverageNote } from './ui.js';

await loadMeta(); await loadFacets();
mount('about.html');
const C=state.meta.counts, M=state.meta;
const literatures=Object.entries(C.findings_by_source_literature||{}).sort((a,b)=>b[1]-a[1]);

document.getElementById('body').innerHTML=`<div class="about-grid"><nav class="section-index" aria-label="About sections"><a href="#scope">Scope</a><a href="#limits">Limits</a><a href="#reuse">Reuse</a><a href="#connect">Collaborate</a></nav><div class="about-content">
<div class="page-intro">
  <h1>About the data, its limits, and how to reuse it</h1>
  <p class="lede">A searchable index of ${fmt(C.findings)} machine-extracted findings from
  ${fmt(C.papers)} canonical papers, combining Tier 1 with the current Tier 2 subset.</p>
</div>

<div class="panel" id="scope">
  <h2>Current scope</h2>
  <div class="note stop"><b>Tier 2 is ${C.tier2_coverage_pct}% complete.</b> Combined counts are partial.
  A missing finding may reflect an unprocessed chunk. Absence here is not evidence of absence in the literature.</div>
  <p>Tier 1 contributes ${fmt(C.findings_tier1)} findings from ${fmt(C.papers_tier1)} canonical papers.
  The current Tier 2 subset contributes ${fmt(C.findings_tier2)} findings from ${fmt(C.papers_tier2)} papers.
  The paper sets do not overlap after canonicalization.</p>
  <h3>Findings by source literature</h3>
  <div class="statgrid">${literatures.map(([name,n])=>`<div class="stat"><div class="v">${fmt(n)}</div>
    <div class="k">${esc(name)}</div></div>`).join('')}</div>
  <p class="kv">Source literature records where a paper entered extraction. It is separate from the condition label on an individual finding.</p>
</div>

<div class="panel">
  <h2>What the data can and cannot show</h2>
  <ul>
    <li>Co-mention means two entities appeared in the same paper. It does not establish interaction or causation.</li>
    <li>Shared biology across source literatures is not the same claim as patient comorbidity.</li>
    <li>A null or failed result does not prove ineffectiveness. Dose, comparator, sample size, and population matter.</li>
    <li>Contradictory directions may reflect different populations or methods rather than a direct replication failure.</li>
  </ul>
  ${entityCoverageNote('entity pages, entity filters, and entity-based charts')}
</div>

<div class="panel" id="limits">
  <h2>Extraction and provenance</h2>
  <p>These are automated extractions and can contain errors. Read the cited paper before relying on a finding.
  The website shows provenance excerpts of up to ${M.quote_max_chars} characters beside the citation so a reader
  can locate the relevant passage.</p>
  <p>Paper counts use canonical PMID. The combined total is ${fmt(C.papers)}, not a count of raw PMID rows.
  Finding rows remain append-only: Tier 1 occupies rows 0 through ${fmt(C.findings_tier1-1)}, followed by the
  current Tier 2 rows.</p>
  <h3>Verification status (packages v1.2)</h3>
  <p>Each finding carries a verbatim quote from its paper. Across Tiers 1–3 of the full corpus
  (132,540 findings), 127,041 of 132,295 quotes whose source could be
  re-fetched were found in that source (96.03%; by tier 92.89% / 97.13% / 96.84% / 97.77%).
  In a 200-finding sample drawn across all five packages, 185 of 200 quotes were found in freshly fetched text.
  In v1.2 every model-written ontology identifier was checked at its authority and corrected or withheld
  (details in each package's README). <b>Whether each finding also states what its paper found has not yet been
  checked by a human reader.</b> That audit is in progress; its result will be posted here when it is done.</p>
</div>

<div class="panel" id="reuse">
  <h2>Search, chat, and reuse</h2>
  <p>Keyword search works without an external model. Semantic search may become unavailable when its browser model
  cannot load; keyword search remains available. The chat page uses a key supplied by the visitor and stores it only
  in that browser's local storage. This site has no server-side API key.</p>
</div>

<div class="panel">
  <h2>Not medical advice</h2>
  <p>This browser reports what papers said. It does not diagnose conditions, recommend treatments, or replace
  advice from a qualified clinician.</p>
</div></div></div>`;

document.querySelector('.about-content').insertAdjacentHTML('beforeend', `
<div class="panel" id="connect">
  <h2>Connect with the project</h2>
  <p>Have a question, a useful source, or a way to help this literature become easier to navigate?</p>
  <p><a href="mailto:hi@erinmagennis.com">Email Erin</a> · <a href="https://x.com/erinmagennis" target="_blank" rel="noopener">Follow on X</a> · <a href="https://github.com/erinmagennis/pots-findings" target="_blank" rel="noopener">View the project on GitHub</a> · <a href="https://artizen.fund/index/p/open-pots" target="_blank" rel="noopener">Support the project</a></p>
</div>`);
