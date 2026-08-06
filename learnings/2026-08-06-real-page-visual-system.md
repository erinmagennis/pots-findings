# Restyling a static research browser without changing its record

**Date:** 2026-08-06  **Context:** POTS real-page visual redesign

## The approach that worked

- Treat the approved homepage as a token reference, then move every real page directly to a new `app-v2.css`.
- Keep `ui.js` as the shared shell boundary so campaign, navigation, status, support, and footer behavior stay consistent.
- Build the Findings overview from facet and discovery files at runtime, with denominators and links to the existing tables.
- Add interaction around the existing Connections SVG instead of introducing a graph library or changing the association schema.
- Regenerate `site/CHECKSUMS.txt` after intentional front-end changes, then run the data verifier and syntax checks.

## Judgment calls

- The homepage remains isolated because its approved graph and `home-v2.css` are a separate visual proof.
- The match strip keeps the already-approved campaign wording and switches to a quiet support strip after expiry.
- Compatibility selectors from `app.css` are retained in `app-v2.css` so older functional states do not lose styling while pages no longer load the old system.

## Reusable rule

For a static data product, put new visual rules in a new stylesheet, preserve the old selector surface inside that stylesheet, and prove the data contract separately from visual changes.
