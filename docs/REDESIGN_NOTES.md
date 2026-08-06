# Website redesign note

August 2026 redesign pass for the POTS and Dysautonomia Literature Project.

The site now shares a calmer research interface across Search, Findings, Connections, Analyze, About, and Ask. The homepage keeps its interactive literature map, while the internal pages use the same navigation, typography, palette, responsive behavior, and source-linked research patterns.

The redesign changes presentation and interaction only. The shipped research data, schemas, row order, and dataset paths are unchanged.

Highlights:

- Search uses a clear Papers / Findings switch with filters behind a disclosure.
- Findings opens with a real-data overview and keeps the detailed views available.
- Connections supports touch-friendly graph exploration and an entity drawer.
- Analyze groups controls, chart output, exact underlying numbers, and downloads.
- About explains scope, limits, provenance, reuse, and collaboration in an editorial layout.
- Mobile layouts use a compact notification strip, hamburger navigation, and a full interactive graph below the homepage introduction.

## How to use the site

- **Home**: start with the POTS-centered knowledge graph. On mobile, open the hamburger menu, then scroll below the introduction to explore the full graph by touch.
- **Search**: search Papers or Findings. Keyword search is immediate. Semantic search runs in the browser and downloads a model on first use. Open filters only when needed.
- **Findings**: use Overview for the data-led starting point. Use the tabs for Comparisons, Under-studied, Contradictions, Null / failed, and Convergence. Read each signal against its linked source paper.
- **Connections**: choose the literature scope and graph limits, then select a node. The drawer links to the complete entity record. Co-mention means shared appearance in papers, not interaction or causation.
- **Analyze**: choose a chart type, grouping, metric, and optional series. Open Filter data for constraints. Update the chart, then use the underlying table or download the PNG and CSV.
- **About**: check coverage, extraction limits, provenance, reuse details, and collaboration links.
- **Ask**: provide a visitor-owned API key only if using the local retrieval and chat panel. Answers must be checked against the cited findings and source papers.

## Adding a new data checkpoint

The browser is a static reader. Data generation happens upstream. Do not edit `data/` or `site/data/` by hand.

1. Generate the new checkpoint with the existing data pipeline and confirm the intended Tier 1 or Tier 2 scope.
2. Preserve the shared row order across findings facets, detail shards, text shards, embeddings, and metadata. Tier 1 rows remain first, followed by Tier 2 rows.
3. Regenerate the linked artifacts together: `meta.json`, `findings_facets.json`, `papers.json`, `entities.json`, `associations.json`, `contradictions.json`, `convergence.json`, `understudied.json`, `null_results.json`, text and detail shards, and embedding manifests when applicable.
4. Check that counts, coverage percentages, shard ranges, canonical PMID values, and entity mappings agree across the artifacts.
5. Run `python site_tools/verify_site.py --self-test`. Treat any failed assertion as a release blocker.
6. Confirm `git status --short -- data site/data` is empty before committing a presentation-only change. For a data release, review the data diff explicitly and record the checkpoint scope in the release notes.
7. Recheck Search, Findings Overview, Connections, Analyze, Paper, Entity, and Condition deep links against the new counts before deployment.

The overview must continue to derive its highlights from the shipped data. Do not manually select scientific claims or invent a featured signal. Every chart and statistic needs a denominator and a path to the underlying rows or source paper.

## Refining the design safely

- Shared internal pages load `site/css/app-v2.css`. Keep the homepage isolated in `site/css/home-v2.css` unless Erin explicitly approves a homepage change.
- Shared navigation, notification strip, support footer, scope disclosure, and route behavior live in `site/js/ui.js`. Preserve existing element IDs, query parameters, dataset paths, and deep-link formats.
- Page-specific behavior lives in `site/js/page-*.js`. Change layout around controls before changing control IDs or schemas.
- Keep the visual roles stable: warm off-white background, charcoal text, rust for primary action and positive direction, teal for connected or downward direction, and sage for secondary evidence states.
- Keep the graph light and sparse. Use real counts, real labels, and explicit limitations. Do not use graph density or decorative color to imply scientific strength.
- For mobile, verify the notification strip, hamburger menu, homepage graph below the intro, drawer width, filter disclosures, tables, downloads, and horizontal overflow.
- After any design pass run the JavaScript syntax checks, copy lint, `git diff --check`, and the site verifier. Review both 1440×900 and 390×844 screenshots before publishing.

## Current design source of truth

This note is the active website handoff. `docs/DESIGN_REDESIGN_HANDOFF.md` records the early design sprint, and `docs/HANDOFF-2026-08-06-homepage-ia.md` records the intermediate information-architecture pass. Both are historical and must not be used as current implementation instructions.

Current routes and owners:

- `site/index.html`, `site/css/home-v2.css`, and `site/js/home-v2.js`: production homepage, homepage graph, campaign strip, and mobile homepage navigation.
- `site/search.html`: Search. The root route is no longer the search page.
- `site/discover.html` and `site/js/page-discover.js`: Findings Overview plus the five detailed findings views.
- `site/connections.html` and `site/js/page-connections.js`: draggable connection graph and selected-entity drawer.
- `site/builder.html`: Analyze.
- `site/about.html`: project context, limits, reuse, collaboration, and support.
- `site/chat.html`: Ask with a visitor-owned key.
- `site/css/app-v2.css`: shared internal-page tokens, components, and responsive rules.
- `site/js/ui.js`: shared internal-page campaign strip, brand lockup, navigation, scope disclosure, footer, citation presentation, and route transitions.

Preserve these public navigation and deep-link contracts:

- Search: `search.html?q=`, `?e=`, `?c=`, and `?null=1`.
- Findings: `discover.html#overview`, `#assoc`, `#under`, `#contra`, `#nulls`, and `#conv`.
- Paper: `paper.html?pmid=`. Entity: `entity.html?e=`. Condition: `condition.html?c=`.
- Keep every existing DOM ID used by a `page-*.js` module. Layout may move around those controls, but an ID change requires updating and testing the owning module in the same change.

The graphs use project-owned SVG renderers, real shipped association data, pixel-coordinate view boxes, and `ResizeObserver`. There is no `force-graph` or Cytoscape runtime dependency. Keep labels deduplicated, links quiet, nodes bounded inside the canvas, and evidence strength explicit. Connections supports drag and pin behavior; graph editing and user-authored saved graphs are future work.

## Durable visual rules

- Use the current light editorial system as the baseline. Do not revive the deleted `site/css/app.css` dashboard treatment.
- Align the brand lockup, page content, major surfaces, and footer content to the same maximum-width and gutter tokens.
- Use rust for primary action and emphasis, teal for connections and informational states, and sage for secondary evidence states. Avoid decorative gradients and dense multicolor graph palettes.
- Keep utility-page headings compact, filters progressive, tables source-linked, and authors visually prominent.
- Use whitespace to establish hierarchy, but do not create large empty side fields or vertical gaps that separate related controls from their results.
- Keep the homepage graph and the Connections graph visually related. The homepage is sparse and invitational; Connections can expose more controls and detail.
- Preserve reduced-motion behavior, visible keyboard focus, touch targets, mobile graph access, and the mobile navigation menu.
- A code review is not visual approval. Any future design change needs rendered desktop and mobile screenshots before publication.

## Open design and QA work

1. Replace the expired match state on every page. Erin confirmed that the campaign strip appears on every page while active, then becomes a quiet permanent support treatment. The current code leaves the campaign copy visible and changes only the countdown to `match ended`.
2. Complete real-browser interaction QA at 1440×900 and 390×844. Check navigation, search modes, filter disclosures, Findings tabs, graph hover, tap, drag and drawer behavior, Analyze downloads, About anchors, footer placement, clipping, horizontal overflow, and the post-match support state.
3. Treat the connected five-node logo as the current placeholder. A more fitting knowledge-graph and human-discovery mark remains a future design task and needs a separate reaction round before replacement.
4. Keep `site/preview.html` synchronized only while it is intentionally retained. Production behavior is defined by `site/index.html`; do not fix one copy and assume the other changed.

## Verification commands

Run these before committing a design change:

```sh
python3 site_tools/verify_site.py --self-test
for f in site/js/*.js; do node --check "$f" || exit 1; done
/Users/erinmagennis/foundation/scripts/copy-lint.sh <changed user-facing files>
git diff --check
git status --short -- data site/data
```

The August 6 handoff run passed 73,252 checkpoint assertions, all JavaScript syntax checks, copy lint for the primary and linked redesigned pages, and `git diff --check`. `data/` and `site/data/` were clean. Rendered browser QA was still unavailable and remains open.

## Release note

The August 2026 redesign is presentation-only. It was published in GitHub commit `1b8aa32`; the core research data was unchanged. The next open changes are the expired-match transition and a real-browser interaction review at desktop and mobile sizes.
