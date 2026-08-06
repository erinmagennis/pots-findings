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

## Release note

The August 2026 redesign is presentation-only. It was published in GitHub commit `1b8aa32`; the core research data was unchanged. The next open QA step is a real-browser interaction review at desktop and mobile sizes.
