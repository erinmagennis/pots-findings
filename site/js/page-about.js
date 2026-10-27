import { loadMeta, loadFacets, state, fmt, esc } from './data.js';
import { mount, entityCoverageNote } from './ui.js';

await loadMeta(); await loadFacets();
mount('about');
const C=state.meta.counts, M=state.meta;
const V = state.meta.verification_stats || {};
const pl=(n,one,many)=>`${fmt(n)} ${n===1?one:many}`;
const literatures=Object.entries(C.findings_by_source_literature||{}).sort((a,b)=>b[1]-a[1]);

document.getElementById('body').innerHTML=`<div class="about-grid"><nav class="section-index" aria-label="About sections"><a href="#scope">Scope</a><a href="#limits">Limits</a><a href="#flags">Paper flags</a><a href="#reuse">Reuse</a><a href="#related">Related data</a><a href="#connect">Collaborate</a></nav><div class="about-content">
<div class="page-intro">
  <h1>About the data, its limits, and how to reuse it</h1>
  <p class="lede">A searchable index of ${fmt(C.findings)} machine-extracted findings from
  ${fmt(C.papers)} papers published ${C.year_min}–${C.year_max} on POTS, dysautonomia and ${C.conditions} related conditions.</p>
</div>

<div class="panel" id="scope">
  <h2>Scope</h2>
  <p>${fmt(C.findings)} findings from ${fmt(C.papers)} papers (${C.year_min}–${C.year_max}), released as five data packages on
  <a href="https://github.com/erinmagennis/pots-findings">GitHub</a> (version ${esc(M.version)}). Each finding is one extracted statement with its
  verbatim source quote, direction, evidence tier, condition label and, where the paper named one, the entity it concerns. A missing finding may mean the
  paper was outside the retrieval queries, had no accessible text, or that the extractor missed it. Absence here is not evidence of absence in the literature.</p>
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
  <p>Each PubMed record counts as one paper, as in the data packages: ${fmt(C.papers)} papers. Some records belong together, such as a preprint
  and its published version. The site links them with <a href="#flags">paper flags</a> and does not merge them. Finding rows keep the order of the
  five released packages, so a row number here is a stable citation into the GitHub data.</p>
  <h3 id="verification">Verification status</h3>
  <p>Each finding carries a verbatim quote from its paper. Across ${fmt(V.trace_rows_total)} findings in the first four packages,
  ${fmt(V.trace_found)} of ${fmt(V.trace_verifiable)} quotes whose source could be re-fetched were found in that source (${V.trace_pct}%).
  In a ${fmt(V.sample_n)}-finding sample drawn across all five packages, ${fmt(V.sample_found)} of ${fmt(V.sample_n)} quotes were found in freshly fetched text.
  In version ${esc(M.version)} every model-written ontology identifier was checked at its authority and corrected or withheld
  (${fmt(C.verified_id_rows)} findings now carry a verified identifier; ${fmt(C.withheld_id_rows)} identifiers were withheld). <b>Whether each finding also
  states what its paper found has not yet been checked by a human reader.</b> That audit is in progress; its result will be posted here when it is done.</p>
</div>

<div class="panel" id="flags">
  <h2>Paper flags</h2>
  <p>Some papers carry a flag taken from PubMed. ${pl(C.flag_retracted,'paper was','papers were')} retracted, and ${pl(C.flag_erratum_notice,'record is a correction notice','records are correction notices')}
  for another paper. Their ${pl(C.excluded_findings,'finding is','findings are')} kept for the record and left out of counts, charts and the Signals tables by default.
  To bring them back, tick “Include retracted papers and correction notices” on Search or Analyze.</p>
  <p>${pl(C.flag_has_correction,'paper has','papers have')} a published correction, ${pl(C.flag_expression_of_concern,'paper has','papers have')} an expression of concern,
  and ${pl(C.flag_preprint,'record is a preprint','records are preprints')}. ${pl(C.flag_preprint_with_published_version,'preprint has its','preprints have their')} published version
  in this dataset too. These papers stay in all counts and show a small label. Each paper page explains its flag and links the related record.</p>
  <p><a href="papers?flag=retracted">Retracted papers</a> · <a href="papers?flag=erratum_notice">Correction notices</a> · <a href="papers?flag=preprint">Preprints</a></p>
</div>

<div class="panel" id="reuse">
  <h2>Search, chat, and reuse</h2>
  <p>Keyword search works without an external model. Semantic search may become unavailable when its browser model
  cannot load; keyword search remains available. The chat page uses a key supplied by the visitor and stores it only
  in that browser's local storage. This site has no server-side API key.</p>
  <p id="privacy"><b>Privacy.</b> Your key, your questions, the answers and any saved chats stay in your browser. The
  site counts three things on the Ask page, using PostHog: which AI provider is chosen, when a key is saved and when a
  question is sent. Each count holds only the provider name. There are no cookies, no recordings of the page and no
  location lookup.</p>
</div>

<div class="panel">
  <h2>Not medical advice</h2>
  <p>This browser reports what papers said. It does not diagnose conditions, recommend treatments, or replace
  advice from a qualified clinician.</p>
</div></div></div>`;

document.querySelector('.about-content').insertAdjacentHTML('beforeend', `
<div class="panel" id="related">
  <h2>Related data</h2>
  <p>This site is part of <a href="https://github.com/erinmagennis/condition-findings" target="_blank" rel="noopener">condition-findings</a>,
  a set of open datasets built the same way. It includes <a href="https://github.com/erinmagennis/eds-findings" target="_blank" rel="noopener">EDS findings</a>:
  findings from papers on the Ehlers-Danlos syndromes and hypermobility, published 1946 to 2026.
  The method that builds them is open too, in <a href="https://github.com/erinmagennis/condition-findings-builder" target="_blank" rel="noopener">condition-findings-builder</a>.</p>
</div>`);

document.querySelector('.about-content').insertAdjacentHTML('beforeend', `
<div class="panel" id="connect">
  <h2>Connect with the project</h2>
  <p>Have a question, a useful source, or a way to help this literature become easier to navigate?</p>
  <p><a href="mailto:hi@erinmagennis.com">Email Erin</a> · <a href="https://x.com/erinmagennis" target="_blank" rel="noopener">Follow on X</a> · <a href="https://github.com/erinmagennis/pots-findings" target="_blank" rel="noopener">View the project on GitHub</a></p>
</div>`);
