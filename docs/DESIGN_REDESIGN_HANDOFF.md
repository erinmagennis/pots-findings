# POTS design and redesign handoff

> Historical design-sprint record. Superseded by `docs/REDESIGN_NOTES.md`. Do not use the navigation, graph-library, build-boundary, or next-action sections below as current implementation instructions.

Date: 2026-08-05

## Direction decided

- Homepage copy: “A living map of POTS and dysautonomia research. Explore what is known, what is connected, and what is next.”
- Keep the page light, airy, editorial, and research-friendly. The graph is the main visual instrument, not decoration.
- Use a connected constellation logo in the upper-left, a short floating pill nav, and a slim match notification at the top.
- Homepage layout: title and compact search on the left; a POTS-centered graph on the right. The graph should fade toward the left and reveal overlap conditions and research areas through interaction.
- Search prompt: “What are you curious about?” Enter opens the existing Search page with the query preserved.
- Nav: Explore, Analyze, About, Connect, search icon. The Connect page heading is “Collaborate with the project.”

## Graph direction

- First prototype should use `force-graph` with real POTS-centered data and a restrained visual treatment: thin pale links, small quiet nodes, charcoal text, muted blue active relationships, rust reserved for POTS and primary support action.
- Resting state is intentionally sparse. Hover brightens the local neighborhood; click opens Explore focused on the node with evidence count, papers, authors, relationship type, and limitations.
- Use “overlap in the literature” unless the source supports a stronger claim. Do not invent relationships, labels, metrics, or comorbidity claims for decoration.
- Mobile: text, search, then a shallow graph band. Tap replaces hover.

## Supporting surfaces

- About describes the project, dataset, extraction process, relationship definitions, limitations, authorship, source links, and possible use for other research domains. It is project-level context, not a methods page for every paper.
- Connect includes email, X (`https://x.com/erinmagennis`), collaboration invitation, and the Artizen support link.
- Match strip: “4× match live through Thursday at 11:00 AM Pacific. Every $1 becomes $5, up to $5,000.” Supporting action: “Help keep this research open and growing.” Countdown endpoint: `2026-08-06T18:00:00Z`.

## Next build boundary

Build only the homepage, graph interaction, About, Connect, and match banner first. Defer Analyze redesign until those surfaces are right. Use the existing static-site architecture and leave `data/` and `site/data/` untouched. Verify with `python site_tools/verify_site.py --self-test` before and after the prototype.

No code or research data was changed during this design sprint. The generated image concepts were rejected. The next useful artifact is an isolated, real-data graph prototype reviewed through the design gate.
