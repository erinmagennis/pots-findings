#!/usr/bin/env python3
"""Prepare and verify the public Tier 2 record.

This is intentionally separate from the site projection. It removes an undocumented
processing helper and reconciles public crosswalk counts to canonical paper IDs.

Requires pyarrow only when the Parquet finding file still contains ``_blob``.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import os
from collections import defaultdict
from pathlib import Path
from tempfile import NamedTemporaryFile


EXPECTED = {
    "tier1_papers": 3121,
    "tier2_papers": 3123,
    "combined_papers": 6244,
    "combined_entities": 2803,
}


def rows(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as handle:
        yield from csv.DictReader(handle)


def write_rows(path: Path, fieldnames, data):
    with NamedTemporaryFile("w", encoding="utf-8", newline="", dir=path.parent,
                            prefix=f".{path.name}.", delete=False) as handle:
        temp = Path(handle.name)
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    os.replace(temp, path)


def drop_blob_csv(path: Path):
    with gzip.open(path, "rt", encoding="utf-8", newline="") as source:
        reader = csv.reader(source)
        header = next(reader)
        if "_blob" not in header:
            return False
        blob_index = header.index("_blob")
        with NamedTemporaryFile("wb", dir=path.parent, prefix=f".{path.name}.",
                                delete=False) as raw:
            temp = Path(raw.name)
            with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as zipped:
                with io.TextIOWrapper(zipped, encoding="utf-8", newline="") as target:
                    writer = csv.writer(target)
                    writer.writerow(header[:blob_index] + header[blob_index + 1:])
                    for row in reader:
                        writer.writerow(row[:blob_index] + row[blob_index + 1:])
    os.replace(temp, path)
    return True


def drop_blob_parquet(path: Path):
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError(
            "pyarrow is required to remove _blob from the Parquet export"
        ) from exc
    table = pq.read_table(path)
    metadata_has_blob = any(b"_blob" in value for value in (table.schema.metadata or {}).values())
    if "_blob" not in table.column_names and not metadata_has_blob:
        return False
    if "_blob" in table.column_names:
        table = table.drop(["_blob"])
    # Pandas records every original column in schema metadata. Keeping that stale metadata would
    # continue to advertise `_blob` even after the physical column was removed.
    table = table.replace_schema_metadata(None)
    with NamedTemporaryFile("wb", dir=path.parent, prefix=f".{path.name}.",
                            delete=False) as handle:
        temp = Path(handle.name)
    pq.write_table(table, temp, compression="snappy")
    os.replace(temp, path)
    return True


def entity_stats(path: Path):
    stats = defaultdict(lambda: {"papers": set(), "findings": 0})
    for row in rows(path):
        entity = (row.get("canonical_entity") or "").strip()
        pmid = (row.get("canonical_pmid") or row.get("pmid") or "").strip()
        if not entity or not pmid:
            continue
        stats[entity]["papers"].add(pmid)
        stats[entity]["findings"] += 1
    return stats


def merged_aliases(path: Path):
    aliases = set()
    for row in rows(path):
        if row["pmid"] != row["canonical_pmid"] and row["merge_applied"].lower() == "true":
            aliases.add(row["pmid"])
    return aliases


def repair_crosswalks(root: Path, apply: bool):
    tier2 = root / "data" / "tier2"
    paper_path = tier2 / "crosswalk_papers_tier1_tier2.csv"
    paper_rows = list(rows(paper_path))
    aliases = merged_aliases(root / "data" / "pmid_dedup_map.csv")
    filtered = [row for row in paper_rows if row["canonical_pmid"] not in aliases]
    if apply and len(filtered) != len(paper_rows):
        write_rows(paper_path, paper_rows[0].keys(), filtered)

    t1 = entity_stats(root / "data" / "tier1_findings.csv.gz")
    t2 = entity_stats(tier2 / "tier2_findings_canonical.csv.gz")

    entity_path = tier2 / "crosswalk_entities_tier1_tier2.csv"
    entity_rows = list(rows(entity_path))
    changed_entities = []
    for row in entity_rows:
        entity = row["canonical_entity"]
        p1, p2 = t1[entity]["papers"], t2[entity]["papers"]
        expected = {
            "t1_papers": str(len(p1)),
            "t1_findings": str(t1[entity]["findings"]),
            "t2_papers": str(len(p2)),
            "t2_findings": str(t2[entity]["findings"]),
            "combined_papers": str(len(p1 | p2)),
            "presence": "both" if p1 and p2 else "tier1_only" if p1 else "tier2_only",
        }
        if any(row[key] != value for key, value in expected.items()):
            changed_entities.append(entity)
            row.update(expected)
    if apply and changed_entities:
        write_rows(entity_path, entity_rows[0].keys(), entity_rows)

    biology_path = tier2 / "crossover_shared_biology.csv"
    biology_rows = list(rows(biology_path))
    changed_biology = []
    for row in biology_rows:
        entity = row["canonical_entity"]
        papers = t1[entity]["papers"] | t2[entity]["papers"]
        findings = t1[entity]["findings"] + t2[entity]["findings"]
        if row["n_papers"] != str(len(papers)) or row["n_findings"] != str(findings):
            changed_biology.append(entity)
            row["n_papers"] = str(len(papers))
            row["n_findings"] = str(findings)
    if apply and changed_biology:
        write_rows(biology_path, biology_rows[0].keys(), biology_rows)

    counts = {
        "tier1_papers": sum(row["in_tier1"].lower() == "true" for row in filtered),
        "tier2_papers": sum(row["in_tier2"].lower() == "true" for row in filtered),
        "combined_papers": len({row["canonical_pmid"] for row in filtered}),
        "combined_entities": len(entity_rows),
    }
    errors = []
    for key, expected in EXPECTED.items():
        if counts[key] != expected:
            errors.append(f"{key}: {counts[key]} != {expected}")
    if len(filtered) != len({row["canonical_pmid"] for row in filtered}):
        errors.append("paper crosswalk still contains duplicate canonical PMIDs")
    if not apply and len(filtered) != len(paper_rows):
        errors.append(f"paper crosswalk contains {len(paper_rows) - len(filtered)} merged raw aliases")
    if not apply and changed_entities:
        errors.append(f"entity crosswalk has stale canonical counts for: {', '.join(changed_entities)}")
    if not apply and changed_biology:
        errors.append(f"shared-biology table has stale counts for: {', '.join(changed_biology)}")
    return errors, changed_entities, changed_biology


def public_columns(root: Path):
    csv_path = root / "data" / "tier2" / "tier2_findings_canonical.csv.gz"
    parquet_path = root / "data" / "tier2" / "tier2_findings_canonical.parquet"
    with gzip.open(csv_path, "rt", encoding="utf-8", newline="") as handle:
        csv_columns = next(csv.reader(handle))
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError("pyarrow is required to verify the public Parquet export") from exc
    parquet = pq.read_table(parquet_path)
    errors = []
    if "_blob" in csv_columns:
        errors.append("_blob is still present in the public CSV")
    if "_blob" in parquet.column_names:
        errors.append("_blob is still present in the public Parquet file")
    if csv_columns != parquet.column_names:
        errors.append("public CSV and Parquet columns differ")
    if parquet.num_rows != 36611:
        errors.append(f"public Parquet has {parquet.num_rows} rows, expected 36611")
    return errors


def write_checksums(root: Path):
    folder = root / "data" / "tier2"
    manifest = folder / "CHECKSUMS.txt"
    lines = []
    for path in sorted(p for p in folder.iterdir() if p.is_file() and p != manifest):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.name}\n")
    manifest.write_text("".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    if args.apply:
        csv_changed = drop_blob_csv(root / "data" / "tier2" / "tier2_findings_canonical.csv.gz")
        parquet_changed = drop_blob_parquet(root / "data" / "tier2" / "tier2_findings_canonical.parquet")
        print(f"_blob removed: CSV={csv_changed}, Parquet={parquet_changed}")

    errors, changed_entities, changed_biology = repair_crosswalks(root, args.apply)
    if args.apply:
        errors, _, _ = repair_crosswalks(root, False)
    errors.extend(public_columns(root))

    if errors:
        print("FAIL: public Tier 2 preparation")
        for error in errors:
            print(f"  {error}")
        raise SystemExit(1)

    if args.apply:
        write_checksums(root)
    print("PASS: public Tier 2 record uses canonical counts and excludes _blob")
    if changed_entities:
        print(f"corrected entity crosswalk rows: {', '.join(changed_entities)}")
    if changed_biology:
        print(f"corrected shared-biology rows: {', '.join(changed_biology)}")


if __name__ == "__main__":
    main()
