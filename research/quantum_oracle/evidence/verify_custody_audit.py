#!/usr/bin/env python3
"""Read-only validation of this additive custody snapshot, not scientific replay."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    evidence = root / "research/quantum_oracle/evidence"
    snapshot_manifest = json.loads((evidence / "baseline-source-snapshots.json").read_text())
    snapshots = {row["logical_path"]: row for row in snapshot_manifest["snapshots"]}
    documents = {
        name: json.loads((evidence / name).read_text())
        for name in (
            "custody-audit.json",
            "inherited-obligations.json",
            "inherited-registries.json",
        )
    }
    checked = {}
    spans = 0

    def source_bytes(path):
        # The audit describes its recorded baseline, not later status updates.
        # Only explicitly inventoried mutable documents resolve to preserved
        # standalone bytes. All other sources still resolve to their real paths.
        if path in snapshots:
            item = snapshots[path]
            if item["source_commit"] != documents["custody-audit.json"]["repository"]["commit"]:
                raise ValueError("baseline snapshot revision differs")
            resolved = (root / item["snapshot_path"]).resolve()
        else:
            resolved = (root / path).resolve()
        if not resolved.is_relative_to(root):
            raise ValueError("source path escapes repository")
        raw = resolved.read_bytes()
        if path in snapshots and (len(raw) != item["bytes"] or hashlib.sha256(raw).hexdigest() != item["sha256"]):
            raise ValueError("baseline snapshot identity differs: " + path)
        return raw

    def check(value):
        nonlocal spans
        if isinstance(value, dict):
            if {"path", "bytes", "sha256"} <= value.keys():
                path = value["path"]
                if path not in checked:
                    raw = source_bytes(path)
                    checked[path] = raw
                raw = checked[path]
                if len(raw) != value["bytes"] or hashlib.sha256(raw).hexdigest() != value["sha256"]:
                    raise ValueError("source identity differs: " + path)
            if {"source", "start_byte", "end_byte_exclusive", "text", "text_sha256"} <= value.keys():
                raw = source_bytes(value["source"]["path"])
                actual = raw[value["start_byte"] : value["end_byte_exclusive"]]
                if actual != value["text"].encode() or hashlib.sha256(actual).hexdigest() != value["text_sha256"]:
                    raise ValueError("exact source span differs")
                lines = raw.splitlines(keepends=True)
                if b"".join(lines[value["start_line"] - 1 : value["end_line"]]) != actual:
                    raise ValueError("source line coordinates differ")
                spans += 1
            for item in value.values():
                check(item)
        elif isinstance(value, list):
            for item in value:
                check(item)

    for document in documents.values():
        check(document)
    audit = documents["custody-audit.json"]
    families = documents["inherited-obligations.json"]["families"]
    for family, count in (("v2", 66), ("v3", 24), ("composer_surface", 75)):
        if len(families[family]["numbered_provisions"]) != count:
            raise ValueError("inherited provision count differs")
    if len(families["v2"]["original_gates"]) != 8 or len(families["v3"]["acceptance_examples"]) != 7:
        raise ValueError("gate/example count differs")
    records = {item["id"]: item for item in audit["missing_dependencies"]}
    unknown = ["composer_gate1_original", "historical_sparse_array_repair", "historical_wave_stability"]
    unknown += [f"historical_octave_case_{i}" for i in range(1, 9)]
    if any(records[name]["status"] != "UNKNOWN" for name in unknown):
        raise ValueError("historical unknown was silently promoted")
    registries = documents["inherited-registries.json"]
    topics = registries["university"]["topics"]
    domains = registries["mathematical_review"]["ordered_ids"]
    if len(topics) != 62 or len({row["id"] for row in topics}) != 62 or len(domains) != 23 or len(set(domains)) != 23:
        raise ValueError("registry identity count differs")
    print(json.dumps({
        "status": "PASS",
        "source_files_checked": len(checked),
        "exact_source_spans_checked": spans,
        "historical_unknown_records_preserved": len(unknown),
        "topics": len(topics),
        "domains": len(domains),
        "explicit_baseline_snapshots": sorted(snapshots),
        "scientific_acceptance_claimed": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
