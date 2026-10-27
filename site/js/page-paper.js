import { loadMeta, loadFacets, loadPapers, state, ensureRows, fmt, esc, paper, flagsOf, paperByPmid } from './data.js';
import { mount, findingCard, qs } from './ui.js';

const pubmed = pm => `https://pubmed.ncbi.nlm.nih.gov/${encodeURIComponent(pm)}/`;
/* a linked record: its page here when it is in the dataset, otherwise PubMed */
const unent = t => String(t).replace(/&#x([0-9a-f]+);/gi,(_,h)=>String.fromCodePoint(parseInt(h,16))).replace(/&#(\d+);/g,(_,d)=>String.fromCodePoint(+d));
function linked(x, fallback){
  if(!x.lp) return '';
  const p = x.li ? paperByPmid(x.lp) : null;
  const title = esc(unent(x.lt || p?.title || fallback || `PubMed record ${x.lp}`).replace(/\.$/,''));
  return p ? `<a href="paper?pmid=${esc(x.lp)}">${title}</a>` : `<a href="${pubmed(x.lp)}" target="_blank" rel="noopener">${title}</a>`;
}
/* banners for retraction, correction notice and expression of concern; short lines for linked records */
function flagBlock(pmid){
  const F = flagsOf(pmid); if(!F.length) return {banners:'', lines:''};
  const has = f => F.find(x=>x.f===f);
  const banners = [], lines = [];
  const notice = (x, text) => x.lp ? ` <a href="${pubmed(x.lp)}" target="_blank" rel="noopener">${text}</a>` : '';
  let x;
  if((x = has('retracted'))) banners.push(`<div class="note stop flag-banner" role="note"><b>Retracted.</b>This paper was retracted on PubMed; its findings are kept for the record and left out of counts and charts by default.${notice(x,'Read the retraction notice on PubMed')}</div>`);
  if((x = has('partially_retracted'))) banners.push(`<div class="note stop flag-banner" role="note"><b>Partially retracted.</b>Part of this paper was retracted on PubMed; its findings are kept for the record and left out of counts and charts by default.${notice(x,'Read the notice on PubMed')}</div>`);
  if((x = has('erratum_notice'))) banners.push(`<div class="note stop flag-banner" role="note"><b>Correction notice.</b>This PubMed record is a correction notice for another paper, not a research paper. Its findings are kept for the record and left out of counts and charts by default.${x.lp?` It corrects: ${linked(x)}.`:''}</div>`);
  if((x = has('expression_of_concern'))) banners.push(`<div class="note flag-banner" role="note"><b>Expression of concern.</b>The journal published an expression of concern about this paper. Its findings stay in counts and charts. Read them with care.${notice(x,'Read the notice on PubMed')}</div>`);
  const pre = has('preprint_with_published_version');
  if(pre) lines.push(`<b>Preprint.</b> The published version is also in this dataset: ${linked(pre)}`);
  else if(has('preprint')) lines.push(`<b>Preprint.</b> PubMed lists this record as a preprint. It was not peer reviewed when it was posted.`);
  F.filter(y=>y.f==='published_version_of_preprint').forEach(y=>lines.push(`<b>Published version.</b> An earlier preprint of this paper is also in this dataset: ${linked(y)}`));
  F.filter(y=>y.f==='has_correction').forEach(y=>lines.push(`<b>Correction published:</b> <a href="${pubmed(y.lp)}" target="_blank" rel="noopener">correction notice on PubMed</a>${y.li?` (also in this dataset: ${linked(y)})`:''}`));
  F.filter(y=>y.f==='same_work_other_record').forEach(y=>lines.push(`<b>Same work, other record.</b> ${y.n?esc(y.n)+': ':''}${linked(y)}`));
  if((x = has('publisher_removal_notice'))) lines.push(`<b>Publisher removal notice.</b> ${x.n?esc(x.n):'The publisher registered a removal notice for this paper. Check the publisher page before relying on it.'}`);
  F.filter(y=>y.f==='update_of').forEach(y=>lines.push(`<b>Update of an earlier record:</b> ${linked(y)}`));
  return {banners: banners.join(''), lines: lines.length ? `<div class="flag-links">${lines.map(l=>`<p>${l}</p>`).join('')}</div>` : ''};
}

await loadMeta(); await loadFacets(); await loadPapers();
mount('papers');

const pmid=qs('pmid');
let pi=-1;
for(let i=0;i<state.papers.rows.length;i++){ if(String(state.papers.rows[i][state.papers.idx.pmid])===String(pmid)){ pi=i; break; } }

if(pi<0){
  document.getElementById('head').innerHTML=`<div class="panel"><h1>Paper not found</h1>
    <p>No paper with pmid <code>${esc(pmid)}</code>. <a href="papers">Browse papers →</a></p></div>`;
} else {
  const p=paper(pi);
  const rows=[]; const col=state.facets.cols.p;
  for(let r=0;r<state.facets.n;r++) if(col[r]===pi) rows.push(r);
  const etal=p.author_count>1?' et al.':'';
  const fb=flagBlock(p.pmid);
  document.getElementById('head').innerHTML=`<div class="panel">
    ${fb.banners}
    <h1>${esc(p.title||'(untitled)')}</h1>
    <p class="kv"><b>${esc(p.authors||p.first_author||'N/A')}</b></p>
    <p class="kv"><span class="jr">${esc(p.journal||'N/A')}</span> ${p.year?`(${p.year})`:''} ·
      pmid <span class="mono">${esc(p.pmid)}</span> ·
      ${p.is_open_access?'<span class="pill grey">open access</span>':'<span class="pill grey">not open access</span>'} ·
      cited by ${fmt(p.cited_by_count)}</p>
    <p>${p.doi_url?`<a href="${esc(p.doi_url)}" target="_blank" rel="noopener">Read the paper (DOI)</a> · `:''}
       ${p.pubmed_url?`<a href="${esc(p.pubmed_url)}" target="_blank" rel="noopener">PubMed</a>`:''}
       ${p.pmc_url?` · <a href="${esc(p.pmc_url)}" target="_blank" rel="noopener">PMC full text</a>`:''}</p>
    ${fb.lines}
    <div class="note plain">The ${fmt(rows.length)} items below are <b>machine-generated summaries</b> of this
      paper, not the authors' own words (except the short verbatim quotes, which are truncated excerpts).
      Extraction can be wrong: please read the original before citing anything here.
      Citation: ${esc(p.citation_short||'')}</div>
  </div>`;
  document.getElementById('count').innerHTML=`${fmt(rows.length)} findings`;
  await ensureRows(rows);
  document.getElementById('results').innerHTML=rows.map(r=>findingCard(r)).join('');
}
