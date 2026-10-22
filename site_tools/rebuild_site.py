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
        "This entrypoint belongs to the 2026-08 checkpoint generator and is kept for the archive. The current site is built by:\n"
        "  python site_tools/build_v12_projection.py --root . --out site/data\n"
        "  python site_tools/embed_v12.py site/data            # sentence-transformers env\n"
        "  python site_tools/apply_counts.py site README.md\n"
        "  python site_tools/verify_site_v12.py --self-test"
    )


if __name__ == "__main__":
    main()
