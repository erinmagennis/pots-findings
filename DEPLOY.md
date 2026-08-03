# How to publish this checkpoint

This repository contains the completed Tier 1 record plus the current Tier 2 checkpoint. Tier 2 covers 81 of
146 chunks, or 55.5%. Every Tier 2 and combined figure is a subset figure. Absence of a finding is not evidence
of absence.

Nothing needs a build step or application server. The website is served from static files in `site/`.

## 1. Verify the exact commit

From the repository root:

```bash
python site_tools/verify_site.py --self-test
python site_tools/rebuild_site.py --check
```

The current checkpoint passes 73,246 assertions and catches all three planted failures. The complete evidence,
including the 24-view Chrome review, is in
[`docs/TIER2_55PCT_CHECKPOINT_VERIFICATION.md`](docs/TIER2_55PCT_CHECKPOINT_VERIFICATION.md).

The full public-export schema check also needs `pyarrow`:

```bash
python site_tools/prepare_public_tier2.py
```

## 2. Push the repository

Push `main` only after publication approval:

```bash
git push origin main
```

No tracked file exceeds 50 MB, so Git LFS is not required. The intake and local release folders are ignored.

## 3. Publish immutable downloads

Two local tags and clean Git archives are prepared:

| Tag | Download | Purpose |
|---|---|---|
| `tier1-v1` | `pots_tier1_v1.zip` | Completed Tier 1 repository snapshot |
| `tier2-55pct-2026-08-03` | `pots_tier1_plus_tier2_55pct_2026-08-03.zip` | Tier 1 plus the 55.5% Tier 2 checkpoint |

The files and their checksums are in `_release/`. Upload the ZIPs and `SHA256SUMS.txt` as GitHub release assets.
Do not add the ZIPs to the Git repository.

## 4. Deploy the website

The production site is `https://pots.erinmagennis.com`. `vercel.json` serves `site/` at the domain root, and
`.vercelignore` keeps research source files off the website CDN.

After GitHub publication is approved, deploy from the repository root:

```bash
vercel deploy --prod
```

Run the verification gate again immediately before deploying. Treat the GitHub push and production deployment
as separate public actions even if a Git integration is connected.

## What visitors receive

Search, browsing, charts, the chart builder, and downloads work without an account or API key. Semantic search
loads its model in the browser. The Ask page is the only feature that needs a provider key, and each visitor
supplies their own. The key stays on that visitor's device.

The website limits displayed source excerpts to 200 characters. The Tier 2 research files preserve longer
`provenance_quote` passages for extraction checking and source location. Those passages remain the copyright of
their authors and publishers. See [`NOTICE.md`](NOTICE.md).

## Before broad promotion

The completed checkpoint can be published with its stated limitations. Two review tasks remain useful before
making strong scientific claims from it:

1. Spot-check the 51 Tier 1 mappings flagged `map_confidence == "low"`, plus medium-confidence mappings as time
   permits.
2. Have a domain expert review biomedical interpretations used in any public narrative. The database and website
   checks do not substitute for scientific review.
