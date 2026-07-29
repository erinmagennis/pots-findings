import { loadMeta, loadFacets, loadPapers, state, ensureRows, fmt, esc, paper } from './data.js';
import { mount, findingCard, qs } from './ui.js';

await loadMeta(); await loadFacets(); await loadPapers();
mount('papers.html');

const pmid=qs('pmid');
let pi=-1;
for(let i=0;i<state.papers.rows.length;i++){ if(String(state.papers.rows[i][state.papers.idx.pmid])===String(pmid)){ pi=i; break; } }

if(pi<0){
  document.getElementById('head').innerHTML=`<div class="panel"><h1>Paper not found</h1>
    <p>No paper with pmid <code>${esc(pmid)}</code>. <a href="papers.html">Browse papers →</a></p></div>`;
} else {
  const p=paper(pi);
  const rows=[]; const col=state.facets.cols.p;
  for(let r=0;r<state.facets.n;r++) if(col[r]===pi) rows.push(r);
  const etal=p.author_count>1?' et al.':'';
  document.getElementById('head').innerHTML=`<div class="panel">
    <h1>${esc(p.title||'(untitled)')}</h1>
    <p class="kv"><b>${esc(p.authors||p.first_author||'—')}</b></p>
    <p class="kv"><span class="jr">${esc(p.journal||'—')}</span> ${p.year?`(${p.year})`:''} ·
      pmid <span class="mono">${esc(p.pmid)}</span> ·
      ${p.is_open_access?'<span class="pill grey">open access</span>':'<span class="pill grey">not open access</span>'} ·
      cited by ${fmt(p.cited_by_count)}</p>
    <p>${p.doi_url?`<a href="${esc(p.doi_url)}" target="_blank" rel="noopener">Read the paper (DOI)</a> · `:''}
       ${p.pubmed_url?`<a href="${esc(p.pubmed_url)}" target="_blank" rel="noopener">PubMed</a>`:''}
       ${p.pmc_url?` · <a href="${esc(p.pmc_url)}" target="_blank" rel="noopener">PMC full text</a>`:''}</p>
    <div class="note plain">The ${fmt(rows.length)} items below are <b>machine-generated summaries</b> of this
      paper, not the authors' own words (except the short verbatim quotes, which are truncated excerpts).
      Extraction can be wrong — please read the original before citing anything here.
      Citation: ${esc(p.citation_short||'')}</div>
  </div>`;
  document.getElementById('count').innerHTML=`${fmt(rows.length)} findings`;
  await ensureRows(rows);
  document.getElementById('results').innerHTML=rows.map(r=>findingCard(r)).join('');
}
