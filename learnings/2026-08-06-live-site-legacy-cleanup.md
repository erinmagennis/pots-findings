# Live-site legacy cleanup

## Problem

The redesign left behind old styles, preview-only routes, and an unused graph implementation. They were not linked by the live site but increased ambiguity during future changes.

## Approach

Audited stylesheet, script, and route references across `site/`. Removed only assets with no live references: the old app stylesheet, preview stylesheet and subpages, the unused preview graph script, and the retired framing-banner code. Kept `preview.html` because it remains the approved homepage reference.

## Verification

`python site_tools/verify_site.py --self-test` passed with 73,252 checkpoint assertions. JavaScript syntax checks and `git diff --check` passed. Data directories showed no changes.
