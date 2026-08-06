import { loadMeta, getJSON, fmt } from './data.js';
import { mount as mountChrome } from './ui.js';

await loadMeta();
mountChrome('connections.html');
const source = await getJSON('associations.json');
const graphRoot = document.getElementById('connectionGraph');
const caption = document.getElementById('graphCaption');
const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
const normalize = value => String(value || '').trim().toLowerCase().replace(/\s+/g, ' ');
let currentRows = [];

function selectedRows(){
  const scope = document.getElementById('scope').value;
  const significant = document.getElementById('significant').checked;
  const crossKind = document.getElementById('crossKind').checked;
  const topN = Number(document.getElementById('topN').value);
  return source.rows.filter(row => (scope === 'all' || row.conditions?.includes('POTS')) && (!significant || row.significant_fdr05) && (!crossKind || row.cross_kind)).sort((a,b) => b.assoc_score_recomputed - a.assoc_score_recomputed).slice(0, topN);
}

function render(){
  currentRows = selectedRows();
  const bounds = graphRoot.getBoundingClientRect();
  const width = bounds.width; const height = bounds.height;
  if(!width || !height) return;
  const boundary = 42;
  const center = {x: width * .5, y: height * .5};
  const nodeMap = new Map();
  const links = [];
  const potsEntities = new Set();
  currentRows.forEach(row => {
    const a = normalize(row.entity_a); const b = normalize(row.entity_b);
    if(!a || !b) return;
    const add = (key, label, kind, score) => {
      const current = nodeMap.get(key);
      if(!current || score > current.score) nodeMap.set(key, {id:key,label,kind,score,degree:current?.degree||0});
    };
    add(`entity:${a}`, row.entity_a, 'entity', row.assoc_score_recomputed);
    add(`entity:${b}`, row.entity_b, 'entity', row.assoc_score_recomputed);
    nodeMap.get(`entity:${a}`).degree += 1; nodeMap.get(`entity:${b}`).degree += 1;
    links.push({source:`entity:${a}`,target:`entity:${b}`,score:row.assoc_score_recomputed,papers:row.n_papers_both});
    if(row.conditions?.includes('POTS')) { potsEntities.add(`entity:${a}`); potsEntities.add(`entity:${b}`); }
  });
  nodeMap.set('pots', {id:'pots',label:'POTS',kind:'core',score:Infinity,degree:potsEntities.size});
  potsEntities.forEach(id => links.push({source:'pots',target:id,score:1,papers:0,context:true}));
  const nodes = [...nodeMap.values()].sort((a,b) => b.degree-a.degree);
  const radius = Math.min(width,height) * .38;
  nodes.filter(node => node.kind !== 'core').forEach((node,index) => {
    const angle = -Math.PI * .92 + index / Math.max(1,nodes.length-1) * Math.PI * 1.84;
    node.x = clamp(center.x + Math.cos(angle) * radius, boundary, width-boundary);
    node.y = clamp(center.y + Math.sin(angle) * radius, boundary, height-boundary);
  });
  const byId = new Map(nodes.map(node => [node.id,node]));
  byId.get('pots').x=center.x; byId.get('pots').y=center.y;
  const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
  svg.setAttribute('viewBox',`0 0 ${width} ${height}`);
  links.forEach(link => {
    const a=byId.get(link.source), b=byId.get(link.target); if(!a||!b) return;
    const line=document.createElementNS('http://www.w3.org/2000/svg','line');
    line.setAttribute('x1',a.x); line.setAttribute('y1',a.y); line.setAttribute('x2',b.x); line.setAttribute('y2',b.y); line.dataset.a=a.id; line.dataset.b=b.id; line.dataset.papers=link.papers; if(link.context) line.classList.add('context-link'); svg.append(line);
  });
  nodes.forEach(node => {
    const group=document.createElementNS('http://www.w3.org/2000/svg','g');
    const circle=document.createElementNS('http://www.w3.org/2000/svg','circle');
    circle.setAttribute('cx',node.x); circle.setAttribute('cy',node.y); circle.setAttribute('r',node.kind==='core'?7:node.degree>4?4.5:3); circle.dataset.id=node.id; circle.dataset.kind=node.kind; circle.setAttribute('tabindex','0'); circle.setAttribute('role','button'); circle.setAttribute('aria-label',`${node.label}, ${node.degree} visible connections`);
    const text=document.createElementNS('http://www.w3.org/2000/svg','text'); text.textContent=title(node.label); text.setAttribute('x',node.x+(node.x<center.x?-8:8)); text.setAttribute('y',node.y-7); text.setAttribute('text-anchor',node.x<center.x?'end':'start');
    group.append(circle,text); svg.append(group);
    const focus=()=>{const id=node.id; svg.querySelectorAll('circle').forEach(c=>c.classList.toggle('dim',c.dataset.id!==id)); svg.querySelectorAll('line').forEach(line=>{const hot=line.dataset.a===id||line.dataset.b===id; line.classList.toggle('hot',hot); line.classList.toggle('dim',!hot);});};
    const drawer=document.getElementById('connectionDrawer');
    const select=()=>{focus(); const label=node.label; drawer.innerHTML=`<p class="section-kicker">Selected entity</p><h2>${label}</h2><div class="drawer-stat">${fmt(node.degree)}</div><p class="kv">visible connections in this graph</p><a href="entity.html?e=${encodeURIComponent(label)}">Open the full entity record →</a>`;};
    let dragging=false;
    circle.addEventListener('mouseenter',()=>{if(!dragging)focus()}); circle.addEventListener('focus',select); circle.addEventListener('mouseleave',()=>{if(!dragging)clearFocus()}); circle.addEventListener('blur',clearFocus); circle.addEventListener('click',select);
    circle.addEventListener('pointerdown',event=>{dragging=true;circle.setPointerCapture(event.pointerId);circle.style.cursor='grabbing';select();});
    circle.addEventListener('pointermove',event=>{if(!dragging)return;const point=svg.createSVGPoint();point.x=event.clientX;point.y=event.clientY;const local=point.matrixTransform(svg.getScreenCTM().inverse());node.x=clamp(local.x,boundary,width-boundary);node.y=clamp(local.y,boundary,height-boundary);circle.setAttribute('cx',node.x);circle.setAttribute('cy',node.y);group.querySelector('text').setAttribute('x',node.x+(node.x<center.x?-8:8));group.querySelector('text').setAttribute('y',node.y-7);svg.querySelectorAll('line').forEach(line=>{const a=byId.get(line.dataset.a),b=byId.get(line.dataset.b);if(a&&b){line.setAttribute('x1',a.x);line.setAttribute('y1',a.y);line.setAttribute('x2',b.x);line.setAttribute('y2',b.y);}});});
    circle.addEventListener('pointerup',event=>{dragging=false;circle.releasePointerCapture(event.pointerId);circle.style.cursor='grab';});
  });
  function clearFocus(){svg.querySelectorAll('circle,line').forEach(el=>el.classList.remove('dim','hot'));}
  graphRoot.replaceChildren(svg);
  caption.textContent=`Showing ${fmt(currentRows.length)} associations across ${fmt(nodes.length-1)} entities. POTS links show which entities occur in the selected POTS literature scope.`;
}
function title(value){return String(value||'').replace(/_/g,' ').replace(/\b\w/g,char=>char.toUpperCase());}
document.getElementById('refreshGraph').addEventListener('click',render);
new ResizeObserver(render).observe(graphRoot);
render();
