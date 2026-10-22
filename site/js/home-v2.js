import { condLabel } from './labels.js';
const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const title = value => String(value || '').replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase());

function graphData(rows) {
  const potsRows = rows.filter(row => row.conditions?.includes('POTS'));
  const normalize = label => String(label || '').trim().toLowerCase().replace(/\s+/g, ' ');
  const conditionCounts = new Map();
  potsRows.forEach(row => row.conditions
    .filter(condition => !['POTS', 'general', 'multiple'].includes(condition))
    .forEach(condition => {
      const key = normalize(condition);
      const current = conditionCounts.get(key) || { label: condLabel(condition), count: 0 };
      current.count += Number(row.n_papers_both || 0);
      conditionCounts.set(key, current);
    }));
  const conditions = [...conditionCounts.entries()].sort((a, b) => b[1].count - a[1].count).slice(0, 10);
  const conditionKeys = new Set(conditions.map(([key]) => key));
  const evidenceByKey = new Map();
  const reserved = new Set(['pots', 'postural orthostatic tachycardia syndrome']);
  conditionCounts.forEach((item, key) => { reserved.add(key); reserved.add(normalize(item.label)); reserved.add(key.replace(/_/g, ' ')); });
  potsRows.forEach(row => {
    const condition = row.conditions.find(value => conditionKeys.has(normalize(value)));
    [row.entity_a, row.entity_b].forEach(entity => {
      const label = title(entity);
      const key = normalize(label);
      if (!key || reserved.has(key)) return;
      const current = evidenceByKey.get(key);
      const candidate = { label, count: Number(row.n_papers_both || 0), condition: condition ? normalize(condition) : null };
      if (!current || candidate.count > current.count) evidenceByKey.set(key, candidate);
    });
  });
  const evidence = [...evidenceByKey.entries()].sort((a, b) => b[1].count - a[1].count).slice(0, 36);
  return { potsCount: potsRows.length, conditions, evidence };
}

function renderGraph(data) {
  const root = document.getElementById('graph');
  let pinned = null;
  const list = document.getElementById('evidenceList');
  list.innerHTML = data.conditions.map(([key, item]) => `<li><button type="button" data-node="condition:${esc(key)}">${esc(item.label)} <span>${item.count.toLocaleString()}</span></button></li>`).join('');
  list.closest('.evidence-view').setAttribute('tabindex', '0');
  list.querySelectorAll('button').forEach(button => button.addEventListener('click', () => { pinned = button.dataset.node; draw(); }));

  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
  const positionNodes = (width, height, cardBox) => {
    const boundary = 36;
    const mobile = width < 760;
    const visibleConditions = mobile ? data.conditions.slice(0, 6) : data.conditions;
    const visibleConditionKeys = new Set(visibleConditions.map(([key]) => key));
    const visibleEvidence = (mobile ? data.evidence.slice(0, 8) : data.evidence).filter(([, item]) => item.condition && visibleConditionKeys.has(item.condition));
    const center = { x: clamp(width * (mobile ? .58 : .63), boundary, width - boundary), y: height * (mobile ? .56 : .5) };
    const box = mobile ? null : cardBox;
    const avoidBox = (x, y) => {
      if (!box || x < box.left || x > box.right || y < box.top || y > box.bottom) return { x, y };
      return { x, y: y < center.y ? box.top - boundary : box.bottom + boundary };
    };
    const innerRadius = Math.max(mobile ? 70 : 110, Math.min(width, height) * (mobile ? .22 : .30));
    const outerRadius = Math.max(mobile ? 130 : 180, Math.min(width, height) * (mobile ? .38 : .46));
    const nodes = [{ id: 'POTS', label: 'POTS', kind: 'core', count: data.potsCount, x: center.x, y: center.y }];
    const links = [];
    visibleConditions.forEach(([key, item], index) => {
      const angle = -Math.PI * .86 + (index / Math.max(1, visibleConditions.length - 1)) * Math.PI * 1.72;
      const position = avoidBox(clamp(center.x + Math.cos(angle) * innerRadius, boundary, width - boundary), clamp(center.y + Math.sin(angle) * innerRadius, boundary, height - boundary));
      const node = { id: `condition:${key}`, label: item.label, kind: 'condition', count: item.count, x: position.x, y: position.y };
      nodes.push(node); links.push({ source: 'POTS', target: node.id });
    });
    visibleEvidence.forEach(([key, item], index) => {
      const angle = -Math.PI * .92 + (index / Math.max(1, visibleEvidence.length - 1)) * Math.PI * 1.84;
      const offset = (index % 2 ? 1 : -1) * Math.min(18, height * .035);
      const conditionId = item.condition ? `condition:${item.condition}` : null;
      if (!conditionId) return;
      const position = avoidBox(clamp(center.x + Math.cos(angle) * outerRadius, boundary, width - boundary), clamp(center.y + Math.sin(angle) * outerRadius + offset, boundary, height - boundary));
      const node = { id: `evidence:${key}`, label: item.label, kind: 'evidence', count: item.count, x: position.x, y: position.y };
      nodes.push(node); links.push({ source: conditionId, target: node.id });
    });
    const gapFor = node => {
      if (node.kind === 'core') return 90;
      const labelWidth = node.label.length * (node.kind === 'condition' ? 6.4 : 5.7);
      return Math.max(node.kind === 'condition' ? 76 : 54, labelWidth + 28);
    };
    const keepClear = node => {
      const position = avoidBox(node.x, node.y);
      node.x = clamp(position.x, boundary, width - boundary);
      node.y = clamp(position.y, boundary, height - boundary);
    };
    for (let pass = 0; pass < 12; pass += 1) {
      for (let first = 0; first < nodes.length; first += 1) {
        for (let second = first + 1; second < nodes.length; second += 1) {
          const a = nodes[first]; const b = nodes[second];
          const minimum = Math.max(gapFor(a), gapFor(b));
          let dx = b.x - a.x; let dy = b.y - a.y; let distance = Math.hypot(dx, dy);
          if (distance >= minimum) continue;
          if (!distance) { dx = 1; dy = 0; distance = 1; }
          const push = (minimum - distance) * .52;
          const ux = dx / distance; const uy = dy / distance;
          if (a.kind !== 'core') { a.x -= ux * push; a.y -= uy * push; }
          if (b.kind !== 'core') { b.x += ux * push; b.y += uy * push; }
          if (a.kind !== 'core') keepClear(a);
          if (b.kind !== 'core') keepClear(b);
        }
      }
    }
    return { nodes, links };
  };

  function draw() {
    const graphBounds = root.getBoundingClientRect();
    const { width, height } = graphBounds;
    if (!width || !height) return;
    const boundary = 36;
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', 'POTS-centered map of connected research areas and evidence');
    svg.classList.add('home-graph-svg');
    const card = document.querySelector('.hero-info');
    const cardBounds = card?.getBoundingClientRect();
    const cardBox = cardBounds ? {
      left: Math.max(boundary, cardBounds.left - graphBounds.left - 42),
      right: Math.min(width - boundary, cardBounds.right - graphBounds.left + 42),
      top: Math.max(boundary, cardBounds.top - graphBounds.top - 42),
      bottom: Math.min(height - boundary, cardBounds.bottom - graphBounds.top + 42)
    } : null;
    const positioned = positionNodes(width, height, cardBox);
    const nodeEls = new Map();
    const linkEls = [];
    const byId = new Map(positioned.nodes.map(node => [node.id, node]));
    const motion = new Map(positioned.nodes.map(node => [node.id, { x: 0, y: 0, tx: 0, ty: 0 }]));
    let motionFrame = 0;
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    positioned.links.forEach((link, index) => {
      const line = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      const source = byId.get(link.source); const target = byId.get(link.target);
      line.dataset.bend = String((index % 2 ? 1 : -1) * Math.min(42, Math.hypot(target.x - source.x, target.y - source.y) * .14));
      svg.append(line); linkEls.push({ line, link });
    });
    positioned.nodes.forEach(node => {
      const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      circle.dataset.id = node.id; circle.dataset.kind = node.kind; circle.setAttribute('cx', node.x); circle.setAttribute('cy', node.y); circle.setAttribute('r', node.kind === 'core' ? 6 : node.kind === 'condition' ? 4 : 2.5); circle.setAttribute('tabindex', '0'); circle.setAttribute('role', 'button'); circle.setAttribute('aria-label', `${node.label}, ${node.count.toLocaleString()} papers in the visible association`);
      label.textContent = node.label; placeLabel(label, node, node.x, node.y, width, height, boundary); label.classList.add(`node-label-${node.kind}`);
      group.append(circle, label); svg.append(group); nodeEls.set(node.id, { circle, label, group, node });
      const activate = () => focusNode(node.id);
      circle.addEventListener('mouseenter', activate); circle.addEventListener('focus', activate); circle.addEventListener('mouseleave', () => { if (!pinned) focusNode(null); }); circle.addEventListener('blur', () => { if (!pinned) focusNode(null); }); circle.addEventListener('click', () => { pinned = pinned === node.id ? null : node.id; focusNode(pinned); });
    });
    root.replaceChildren(svg);
    function updateMotion() {
      let moving = false;
      motion.forEach((state, id) => {
        const dx = state.tx - state.x; const dy = state.ty - state.y;
        state.x += dx * .16; state.y += dy * .16;
        if (Math.abs(dx) > .1 || Math.abs(dy) > .1) moving = true;
        const element = nodeEls.get(id); const node = element.node;
        const x = node.x + state.x; const y = node.y + state.y;
        element.circle.setAttribute('cx', x); element.circle.setAttribute('cy', y);
        placeLabel(element.label, node, x, y, width, height, boundary);
      });
      linkEls.forEach(({ line, link }) => {
        const source = byId.get(link.source); const target = byId.get(link.target);
        const sourceMotion = motion.get(link.source); const targetMotion = motion.get(link.target);
        const x1 = source.x + sourceMotion.x; const y1 = source.y + sourceMotion.y;
        const x2 = target.x + targetMotion.x; const y2 = target.y + targetMotion.y;
        const bend = Number(line.dataset.bend); const dx = x2 - x1; const dy = y2 - y1; const length = Math.hypot(dx, dy) || 1;
        let controlX = (x1 + x2) / 2 - (dy / length) * bend; let controlY = (y1 + y2) / 2 + (dx / length) * bend;
        if (cardBox && controlX > cardBox.left && controlX < cardBox.right && controlY > cardBox.top && controlY < cardBox.bottom) {
          controlY = (y1 + y2) / 2 < (cardBox.top + cardBox.bottom) / 2 ? cardBox.top - 42 : cardBox.bottom + 42;
        }
        line.setAttribute('d', `M ${x1} ${y1} Q ${controlX} ${controlY} ${x2} ${y2}`);
      });
      if (moving) motionFrame = window.requestAnimationFrame(updateMotion);
      else motionFrame = 0;
    }
    function setPointerTarget(clientX, clientY) {
      if (reduceMotion) return;
      const bounds = svg.getBoundingClientRect();
      const pointer = { x: clientX - bounds.left, y: clientY - bounds.top };
      motion.forEach((state, id) => {
        const node = byId.get(id);
        if (node.kind === 'core') { state.tx = 0; state.ty = 0; return; }
        const dx = pointer.x - node.x; const dy = pointer.y - node.y;
        const distance = Math.hypot(dx, dy);
        const influence = Math.max(0, 1 - distance / Math.min(260, Math.max(180, width * .24)));
        const strength = node.kind === 'condition' ? 7 : 12;
        state.tx = dx * .035 * influence * strength;
        state.ty = dy * .035 * influence * strength;
      });
      if (!motionFrame) motionFrame = window.requestAnimationFrame(updateMotion);
    }
    svg.addEventListener('pointermove', event => setPointerTarget(event.clientX, event.clientY));
    svg.addEventListener('pointerleave', () => { if (reduceMotion) return; motion.forEach(state => { state.tx = 0; state.ty = 0; }); if (!motionFrame) motionFrame = window.requestAnimationFrame(updateMotion); });
    updateMotion();
    function focusNode(id) {
      const neighborhood = new Set(id ? [id] : []);
      positioned.links.forEach(link => { if (link.source === id) neighborhood.add(link.target); if (link.target === id) neighborhood.add(link.source); });
      nodeEls.forEach(({ circle, label, node }) => { const hot = !id || neighborhood.has(node.id); circle.classList.toggle('is-dim', !!id && !hot); label.classList.toggle('is-dim', !!id && !hot); label.classList.toggle('is-revealed', !!id && neighborhood.has(node.id)); circle.classList.toggle('is-hot', node.id === id); });
      linkEls.forEach(({ line, link }) => { const hot = !!id && (link.source === id || link.target === id); line.classList.toggle('is-hot-link', hot); line.classList.toggle('is-dim', !!id && !hot); });
      const selected = id ? byId.get(id) : null;
      document.getElementById('graphStatus').textContent = selected ? `${selected.label}: ${selected.count.toLocaleString()} papers in the visible association. Click again to release the neighborhood.` : 'POTS is connected to overlapping research areas in the literature. Hover or tap a node to pin its local neighborhood.';
    }
    focusNode(pinned);
  }
  const centerX = width => width * .58;
  // text-anchor and x chosen so the whole label stays inside the drawing (estimated 6.4 px per character)
  function placeLabel(el, node, x, y, width, height, boundary) {
    const est = String(node.label).length * 6.4;
    let anchor = node.x < centerX(width) ? 'end' : 'start';
    let lx = x + (anchor === 'end' ? -8 : 8);
    if (anchor === 'start' && lx + est > width - 6) { anchor = 'end'; lx = x - 8; }
    if (anchor === 'end' && lx - est < 6) { anchor = 'start'; lx = x + 8; }
    el.setAttribute('text-anchor', anchor);
    el.setAttribute('x', clamp(lx, 6, width - 6));
    el.setAttribute('y', clamp(y - (node.kind === 'core' ? 9 : 7), boundary, height - boundary));
  }
  const observer = new ResizeObserver(draw);
  observer.observe(root);
  draw();
}

async function init() {
  const navToggle = document.getElementById('mobileNavToggle');
  const primaryNav = document.getElementById('primaryNav');
  navToggle?.addEventListener('click', () => {
    const open = navToggle.getAttribute('aria-expanded') === 'true';
    navToggle.setAttribute('aria-expanded', String(!open));
    primaryNav?.toggleAttribute('data-open', !open);
  });
  document.querySelectorAll('.nav-pill a').forEach(link => {
    link.addEventListener('click', event => {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || link.target === '_blank') return;
      const target = new URL(link.href, location.href);
      if (target.origin !== location.origin) return;
      event.preventDefault();
      document.body.classList.add('page-leaving');
      window.setTimeout(() => { window.location.href = target.href; }, 120);
    });
  });
  const [associations, meta] = await Promise.all([fetch('data/associations.json').then(response => response.json()), fetch('data/meta.json').then(response => response.json())]);
  document.getElementById('findingCount').textContent = Number(meta.counts.findings).toLocaleString();
  document.getElementById('paperCount').textContent = Number(meta.counts.papers).toLocaleString();
  renderGraph(graphData(associations.rows));
  document.getElementById('searchForm').addEventListener('submit', event => { event.preventDefault(); const query = document.getElementById('curiosityInput').value.trim(); if (query) window.location.href = `search?q=${encodeURIComponent(query)}`; });
  const searchToggle = document.getElementById('searchToggle');
  if (searchToggle) searchToggle.addEventListener('click', () => { const input = document.getElementById('curiosityInput'); input.focus(); searchToggle.setAttribute('aria-expanded', 'true'); });
}

init().catch(() => { document.getElementById('graphStatus').textContent = 'The map could not load right now. Try the full search instead.'; });
