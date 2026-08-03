#!/usr/bin/env python3
"""Verify the public 55% Tier 2 checkpoint and its static-site projection."""
from __future__ import annotations

import argparse
import copy
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path


EXPECTED_COUNTS = {
    "findings_tier1": 36459,
    "findings_tier2": 36611,
    "findings": 73070,
    "papers_tier1": 3121,
    "papers_tier2": 3123,
    "papers": 6244,
    "canonical_entities": 2803,
    "n_shards": 13,
    "tier2_chunks_extracted": 81,
    "tier2_chunks_total": 146,
}

DISCOVERY_SCHEMAS = {
    "associations.json": {
        "entity_a", "entity_b", "n_papers_both", "expected_papers_both", "lift", "jaccard",
        "q_bh", "significant_fdr05", "cross_kind", "assoc_score_recomputed", "pmids",
    },
    "understudied.json": {
        "canonical_entity", "condition", "direction", "n_papers", "n_findings", "best_tier",
        "case_report_only", "is_thin", "replication_score", "source_literatures", "pmids",
    },
    "contradictions.json": {
        "canonical_entity", "condition", "conflict_type", "side_A_direction", "n_papers_A",
        "pmids_A", "side_B_direction", "n_papers_B", "pmids_B", "source_literatures",
    },
    "null_results.json": {
        "canonical_pmid", "tier", "source_literature", "null_class", "canonical_entity",
        "entity", "condition", "evidence_tier", "year", "provenance_quote_trunc",
    },
    "convergence.json": {
        "canonical_entity", "concordant_direction", "n_source_literatures", "source_literatures",
        "n_conditions", "n_papers", "n_findings", "tiers", "cross_tier", "best_tier",
    },
}

STALE_SITE_TEXT = {
    "Tier-1 MVP": "stale Tier 1 product label",
    "POTS/dysautonomia only": "stale POTS-only scope",
    "not yet extracted": "stale extraction status",
    "36,459 extracted findings": "stale Tier 1 headline",
    "3,121 distinct papers": "stale Tier 1 paper headline",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def add(failures, what, got, expected, source):
    if got != expected:
        failures.append((what, got, expected, source))


def site_rows(data: Path, failures):
    facets = read_json(data / "findings_facets.json")
    papers = read_json(data / "papers.json")
    entities = read_json(data / "entities.json")

    add(failures, "facets.n", facets.get("n"), EXPECTED_COUNTS["findings"], "findings_facets.json")
    add(failures, "facets.n_shards", facets.get("n_shards"), 13, "findings_facets.json")
    add(failures, "facet column lengths", sorted({len(v) for v in facets.get("cols", {}).values()}),
        [facets.get("n")], "findings_facets.json")
    for key in ("ti", "sl"):
        if key not in facets.get("dicts", {}) or key not in facets.get("cols", {}):
            failures.append((f"combined facet {key}", "missing", "dictionary and column", "site contract"))

    add(failures, "papers rows", len(papers.get("rows", [])), EXPECTED_COUNTS["papers"], "papers.json")
    add(failures, "entities.n", entities.get("n"), EXPECTED_COUNTS["canonical_entities"], "entities.json")
    add(failures, "entities list", len(entities.get("entities", [])), EXPECTED_COUNTS["canonical_entities"],
        "entities.json")
    return facets, papers


def shards(data: Path, facets, failures):
    total = facets["n"]
    shard_rows = facets["shard_rows"]
    for index in range(facets["n_shards"]):
        start, end = index * shard_rows, min((index + 1) * shard_rows, total)
        for prefix in ("text", "detail"):
            path = data / f"{prefix}_{index:02d}.json"
            if not path.exists():
                failures.append((str(path.name), "missing", "present", "shard contract"))
                continue
            payload = read_json(path)
            add(failures, f"{path.name} bounds", (payload.get("start"), payload.get("end")),
                (start, end), "shard contract")
            arrays = [value for key, value in payload.items() if key not in {"start", "end"}]
            lengths = sorted({len(value) for value in arrays}) if arrays else []
            add(failures, f"{path.name} array lengths", lengths, [end - start], "shard contract")

    manifest = read_json(data / "emb" / "manifest.json")
    add(failures, "embedding total rows", manifest.get("total_rows"), total, "embedding manifest")
    add(failures, "embedding shard rows", manifest.get("shard_rows"), shard_rows, "embedding manifest")
    add(failures, "embedding shard count", len(manifest.get("shards", [])), facets["n_shards"],
        "embedding manifest")
    cursor = 0
    for row in manifest.get("shards", []):
        add(failures, f"{row.get('file')} start", row.get("start"), cursor, "embedding contiguity")
        cursor = row.get("end")
        path = data / "emb" / row["file"]
        if not path.exists():
            failures.append((row["file"], "missing", "present", "embedding manifest"))
        else:
            add(failures, f"{row['file']} bytes", path.stat().st_size, row.get("bytes"), "embedding manifest")
    add(failures, "embedding final row", cursor, total, "embedding contiguity")


def discovery(data: Path, failures):
    for filename, required in DISCOVERY_SCHEMAS.items():
        payload = read_json(data / filename)
        rows = payload.get("rows", [])
        add(failures, f"{filename} declared rows", payload.get("n"), len(rows), filename)
        if not rows:
            failures.append((f"{filename} rows", 0, "at least one", "site contract"))
            continue
        missing = sorted(required - set(rows[0]))
        if missing:
            failures.append((f"{filename} schema", missing, "no required fields missing", "page-discover.js"))


def source_rows(root: Path, data: Path, facets, papers, failures):
    fields = papers["fields"]
    pmid_index = fields.index("pmid")
    paper_pmids = [str(row[pmid_index]) for row in papers["rows"]]
    paper_codes = facets["cols"]["p"]
    tier_values = facets["dicts"]["ti"]
    tier_codes = facets["cols"]["ti"]
    texts = []
    for index in range(facets["n_shards"]):
        texts.extend(read_json(data / f"text_{index:02d}.json")["t"])

    offset = 0
    specs = [
        (root / "data" / "tier1_findings.csv.gz", "1", EXPECTED_COUNTS["findings_tier1"]),
        (root / "data" / "tier2" / "tier2_findings_canonical.csv.gz", "2", EXPECTED_COUNTS["findings_tier2"]),
    ]
    for path, tier, expected in specs:
        seen = 0
        with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                position = offset + seen
                canonical = str(row.get("canonical_pmid") or row.get("pmid"))
                projected = paper_pmids[paper_codes[position]]
                if canonical != projected:
                    failures.append((f"row {position} paper", projected, canonical, path.name))
                    break
                projected_tier = str(tier_values[tier_codes[position]])
                if projected_tier != tier:
                    failures.append((f"row {position} tier", projected_tier, tier, "findings_facets.json"))
                    break
                text = row.get("finding_text") or (
                    f"[no summary sentence extracted] {row.get('relation_subject', '')} — "
                    f"{row.get('relation_type', '')} — {row.get('relation_object', '')}"
                )
                if texts[position] != text:
                    failures.append((f"row {position} text", texts[position][:100], text[:100], path.name))
                    break
                seen += 1
        add(failures, f"{path.name} rows checked", seen, expected, "row-order contract")
        offset += expected
    add(failures, "projected text rows", len(texts), offset, "row-order contract")


def public_record(root: Path, failures):
    tier2 = root / "data" / "tier2"
    csv_path = tier2 / "tier2_findings_canonical.csv.gz"
    with gzip.open(csv_path, "rt", encoding="utf-8", newline="") as handle:
        header = next(csv.reader(handle))
    if "_blob" in header:
        failures.append(("public CSV _blob", "present", "absent", "public export rule"))
    parquet = tier2 / "tier2_findings_canonical.parquet"
    if b"_blob" in parquet.read_bytes():
        failures.append(("public Parquet _blob", "present", "absent", "public export rule"))

    aliases = set()
    with open(root / "data" / "pmid_dedup_map.csv", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["pmid"] != row["canonical_pmid"] and row["merge_applied"].lower() == "true":
                aliases.add(row["pmid"])
    with open(tier2 / "crosswalk_papers_tier1_tier2.csv", encoding="utf-8", newline="") as handle:
        crosswalk = list(csv.DictReader(handle))
    pmids = [row["canonical_pmid"] for row in crosswalk]
    add(failures, "paper crosswalk rows", len(crosswalk), EXPECTED_COUNTS["papers"],
        "canonical paper union")
    add(failures, "paper crosswalk unique canonical PMIDs", len(set(pmids)), len(pmids),
        "canonical paper union")
    leaked = sorted(aliases & set(pmids))
    add(failures, "merged raw PMID aliases in paper crosswalk", leaked, [], "pmid_dedup_map.csv")


def presentation(root: Path, failures):
    for path in sorted((root / "site").rglob("*")):
        if path.suffix not in {".html", ".js"}:
            continue
        text = path.read_text(encoding="utf-8")
        for phrase, label in STALE_SITE_TEXT.items():
            if phrase.lower() in text.lower():
                failures.append((label, f"{path.relative_to(root)} contains {phrase!r}", "absent",
                                 "combined-site scope"))


def public_documentation(root: Path, failures):
    path = root / "docs" / "tier2" / "DATA_DICTIONARY_tier2.md"
    text = path.read_text(encoding="utf-8")
    expected = "## crosswalk_papers_tier1_tier2.csv: 6,244 canonical papers"
    if expected not in text:
        failures.append(("paper crosswalk documentation", "missing canonical 6,244 heading", expected,
                         str(path.relative_to(root))))


def checksums(folder: Path, failures):
    manifest = folder / "CHECKSUMS.txt"
    if not manifest.exists():
        failures.append((str(manifest.relative_to(folder.parent)), "missing", "present", "checkpoint integrity"))
        return
    declared = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        declared[name] = digest
    actual = {
        path.relative_to(folder).as_posix(): path
        for path in folder.rglob("*") if path.is_file() and path != manifest
    }
    add(failures, f"{folder.name} checksum file list", sorted(declared), sorted(actual), "checkpoint integrity")
    for name, path in actual.items():
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        add(failures, f"checksum {folder.name}/{name}", digest, declared.get(name), "checkpoint integrity")


def tier1_checksums(root: Path, failures):
    folder = root / "data"
    manifest = folder / "CHECKSUMS.txt"
    declared = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        digest, name, *_ = line.split()
        declared.append((name, digest))
    for name, expected in declared:
        path = folder / name
        if not path.exists():
            failures.append((f"Tier 1 checksum {name}", "missing", expected, "data/CHECKSUMS.txt"))
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        add(failures, f"Tier 1 checksum {name}", digest, expected, "data/CHECKSUMS.txt")


def check(data_dir: Path, root: Path, meta_override=None):
    failures = []
    meta_path = data_dir / "meta.json"
    if not meta_path.exists():
        return [("meta.json", "missing", "present", str(data_dir))], 1
    meta = copy.deepcopy(meta_override) if meta_override is not None else read_json(meta_path)
    counts = meta.get("counts", {})
    for key, expected in EXPECTED_COUNTS.items():
        add(failures, key, counts.get(key), expected, "frozen checkpoint")
    caveat = meta.get("scope_caveat", "")
    if "81 of 146" not in caveat or "absence" not in caveat.lower():
        failures.append(("scope caveat", caveat, "81 of 146 and absence warning", "scope honesty"))

    facets, papers = site_rows(data_dir, failures)
    shards(data_dir, facets, failures)
    discovery(data_dir, failures)
    source_rows(root, data_dir, facets, papers, failures)
    public_record(root, failures)
    presentation(root, failures)
    public_documentation(root, failures)
    checksums(root / "site", failures)
    checksums(root / "data" / "tier2", failures)
    tier1_checksums(root, failures)
    checksum_assertions = sum(1 for path in (root / "site").rglob("*") if path.is_file())
    checksum_assertions += sum(1 for path in (root / "data" / "tier2").rglob("*") if path.is_file())
    return failures, (11 + facets["n_shards"] * 2 + len(DISCOVERY_SCHEMAS)
                      + EXPECTED_COUNTS["findings"] + checksum_assertions + 26)


def report(failures, checks, label=""):
    if failures:
        print(f"FAIL{label}: {len(failures)} failures across {checks:,} checkpoint assertions")
        for what, got, expected, source in failures:
            print(f"\n  {what}\n    got: {got}\n    expected: {expected}\n    source: {source}")
        return 1
    print(f"PASS{label}: {checks:,} checkpoint assertions")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="site/data")
    parser.add_argument("--root", default=".")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    data = Path(args.data)
    if not data.is_absolute():
        data = root / data
    failures, checks = check(data, root)
    result = report(failures, checks)
    if result:
        return result
    if args.self_test:
        bad = read_json(data / "meta.json")
        bad["counts"]["papers"] = 6252
        bad["counts"]["findings"] = 1
        bad["scope_caveat"] = ""
        planted, planted_checks = check(data, root, bad)
        caught = {row[0] for row in planted}
        required = {"papers", "findings", "scope caveat"}
        if not required <= caught:
            print(f"SELF-TEST FAIL: caught {sorted(caught)}, expected at least {sorted(required)}")
            return 1
        print(f"SELF-TEST PASS: caught all {len(required)} planted failures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
