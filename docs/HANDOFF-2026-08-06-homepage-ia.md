# POTS homepage and information architecture handoff

Date: 2026-08-06

## Current state

The isolated homepage prototype is approved by Erin and should be treated as frozen:

- `site/preview.html`
- `site/css/home-v2.css`
- `site/js/home-v2.js`

The homepage has a light POTS-centered graph, full-hero composition, card-safe node layout,
curved pointer-responsive links, visible labels, and a five-link nav wired to the real pages.

The real-page IA pass is implemented but not visually redesigned to match the homepage:

- `site/index.html`: Search, Papers default, Papers / Findings switch, BYOK link
- `site/discover.html`: Findings summary cards plus existing comparisons, understudied,
  contradictions, null/failed, and convergence views
- `site/connections.html`: new Connections graph with POTS scope, all-associations scope,
  significance, cross-kind, and top-N controls
- `site/builder.html`: Analyze label, existing chart builder, BYOK link
- `site/about.html`: existing scope/limits plus contact, X, GitHub, and support
- `site/js/ui.js`: shared nav now Search, Findings, Connections, Analyze, About; BYOK appears
  on Search and Analyze

## Critical correction for the next model

The real pages still use the old `app.css` visual system. Erin correctly rejected the state where
the homepage links into old-looking pages. The next action is to restyle the real pages using the
approved homepage system before claiming the IA pass complete. Do not change the homepage graph
unless Erin asks.

## Decisions locked

- Main tabs: Search, Findings, Connections, Analyze, About.
- Search defaults to Papers, with Findings as a switch.
- Findings is curated for now and includes existing comparisons, contradictions, understudied
  areas, null/failed findings, and convergence.
- Connections is the full literature network with POTS centered and filter/toggle controls.
- Analyze is mostly the builder.
- BYOK Ask is accessible from Search and Analyze.
- About absorbs Connect, limits, contact, support, and GitHub.
- Data files remain unchanged.

## Evidence

- `python site_tools/verify_site.py --self-test` passes: 73,255 assertions.
- JS syntax checks pass for changed page scripts.
- Copy lint passes; existing en-dash range warnings remain in year-range inputs.
- No rendered desktop/mobile screenshot was produced in this session because no browser renderer
  was available.

## Next action

Create a shared real-page visual shell based on the approved homepage tokens, then restyle Search,
Findings, Connections, Analyze, and About. Render at 1440x900 and 390x844 and review before any
public deployment.
