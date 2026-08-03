#!/usr/bin/env python3
"""Add derived compatibility metadata to a generated combined site projection."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def write_json(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def write_checksums(site: Path):
    manifest = site / "CHECKSUMS.txt"
    lines = []
    for path in sorted(p for p in site.rglob("*") if p.is_file() and p != manifest):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(site).as_posix()}\n")
    manifest.write_text("".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="site/data")
    args = parser.parse_args()
    data = Path(args.data)

    meta_path = data / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    facets = json.loads((data / "findings_facets.json").read_text(encoding="utf-8"))
    entities = json.loads((data / "entities.json").read_text(encoding="utf-8"))
    emb = json.loads((data / "emb" / "manifest.json").read_text(encoding="utf-8"))

    coverage = facets["coverage"]
    counts = meta["counts"]
    counts.update({
        "entity_string_rows": coverage["entity_string_rows"],
        "entity_string_pct": coverage["entity_string_pct"],
        "canonical_entity_rows": coverage["canonical_rows"],
        "canonical_entity_pct": coverage["canonical_pct"],
        "entity_unmapped_rows": coverage["entity_unmapped_rows"],
        "papers_with_canonical_entity": coverage["papers_with_canonical"],
        "strings_mapped": coverage["strings_mapped"],
        "strings_total": coverage["strings_total"],
        "strings_unmapped_distinct": coverage["strings_total"] - coverage["strings_mapped"],
        "entities_with_ontology": sum(bool(row.get("oid")) for row in entities["entities"]),
        "emb_shards": len(emb["shards"]),
        "emb_mb": round(sum(row["bytes"] for row in emb["shards"]) / 1_000_000, 1),
        "emb_fidelity": emb["fidelity_mean_cosine"],
    })
    meta["presentation"] = {
        "checkpoint_label": "Tier 1 plus Tier 2 at 55%",
        "tier2_coverage_label": "81 of 146 Tier 2 chunks",
        "is_partial": True,
    }
    write_json(meta_path, meta)
    write_checksums(data.parent)
    print("site projection metadata updated from facets, entities, and embedding manifest")


if __name__ == "__main__":
    main()
