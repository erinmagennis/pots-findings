#!/usr/bin/env python3
"""Guard the supplied combined projection until the missing full generator is restored.

The overlay referenced ``combined_generator.build_all()``, but did not include that function or
the upstream combined discovery and embedding inputs. Refusing to write is safer than producing a
partial site that appears complete.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="site/data")
    parser.add_argument("--root", default=".")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--skip-embeddings", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    out = Path(args.out)
    if not out.is_absolute():
        out = root / out

    if args.check:
        from verify_site import check, report
        failures, assertions = check(out, root)
        raise SystemExit(report(failures, assertions, " rebuild-check"))

    raise SystemExit(
        "FULL REBUILD UNAVAILABLE: the supplied overlay omitted combined_generator.build_all(), "
        "the upstream combined discovery tables, and the Tier 2 embedding-generation input. "
        "The verified current projection has not been modified. See "
        "_intake/FUTURE_TIER_PUBLIC_EXPORT_HANDOFF.md for the exact inputs required."
    )


if __name__ == "__main__":
    main()
