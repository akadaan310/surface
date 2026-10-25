#!/usr/bin/env python3
"""Compile explicitly reviewed UTF-8 source mappings into finite commissions.

The parser preserves bytes; it does not infer executable semantics from prose.
Only predefined local verification adapters can run, through supervise.py.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict
import fcntl
import hashlib
import html
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve()
SUPERVISOR_PATH = HERE.with_name("supervise.py")
_spec = importlib.util.spec_from_file_location("surface_commission_supervisor", SUPERVISOR_PATH)
_supervise = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _supervise
_spec.loader.exec_module(_supervise)
TaskSpec, Supervisor = _supervise.TaskSpec, _supervise.Supervisor

PLAN_SCHEMA = "surface.commission.plan.v1"
ACTIONS = ("source-integrity", "python-tests", "polyia-demo", "foundation-audit", "external-agent")
ATLAS_DOMAINS = (
    "logic", "set_theory", "type_theory", "arithmetic", "algebra", "order_lattices",
    "combinatorics", "graph_theory", "automata_languages", "information_coding",
    "geometry", "topology", "analysis_calculus", "differential_equations",
    "spectral_harmonic", "probability_statistics", "optimization_control",
    "numerical_analysis", "category_composition", "physics_units",
    "quantum_information", "computation_complexity", "metrology_uncertainty",
)
MAX_SOURCE_BYTES = 1024 * 1024
MAX_JSON_BYTES = 8 * 1024 * 1024
MAX_TASKS = 64
MAX_REQUIREMENTS = 256
MAX_TOTAL_SECONDS = 3600
TERMINAL_STATES = ("SUCCEEDED", "FAILED", "BLOCKED", "DEADLINE")


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _read_bytes(path, maximum=MAX_JSON_BYTES):
    # O_NONBLOCK plus fstat avoids hanging on a FIFO and bounds reads before
    # allocation. The descriptor check also covers a path replaced after stat.
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("input must be a regular file")
        if info.st_size > maximum:
            raise ValueError("input exceeds finite byte limit")
        with os.fdopen(fd, "rb", closefd=False) as handle:
            raw = handle.read(maximum + 1)
        if len(raw) > maximum:
            raise ValueError("input exceeds finite byte limit")
        return raw
    finally:
        os.close(fd)


def read_json(path):
    return _parse_json(_read_bytes(path))


def _parse_json(raw):
    def duplicate_safe(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    def reject_constant(value):
        raise ValueError(f"nonfinite JSON constant: {value}")
    return json.loads(raw, object_pairs_hook=duplicate_safe, parse_constant=reject_constant)


def _object(value, required, optional=(), label="object"):
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    missing, extra = set(required) - value.keys(), value.keys() - set(required) - set(optional)
    if missing or extra:
        raise ValueError(f"{label} keys: missing={sorted(missing)}, unknown={sorted(extra)}")
    return value


def _text(value, label, maximum=4000):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"{label} must be a nonempty bounded string")
    value.encode("utf-8")  # Reject unpaired surrogates as well as invalid source bytes.
    return value


def _identifier(value, label="identifier"):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", value):
        raise ValueError(f"invalid {label}")
    return value


def _number(value, maximum, label):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or not 0 < value <= maximum:
        raise ValueError(f"{label} must be finite, positive, and <= {maximum}")
    return value


def _integer(value, low, high, label):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be an integer in [{low},{high}]")
    return value


def _strings(value, label, maximum=256):
    if not isinstance(value, list) or len(value) > maximum or any(not isinstance(x, str) or not x or len(x) > 4000 for x in value):
        raise ValueError(f"{label} must be a bounded list of strings")
    if len(set(value)) != len(value):
        raise ValueError(f"{label} contains duplicates")
    return value


def source_identity(source):
    if not isinstance(source, bytes) or len(source) > MAX_SOURCE_BYTES:
        raise ValueError("source must be bytes within the 1 MiB limit")
    source.decode("utf-8", errors="strict")
    return {"sha256": digest(source), "byte_length": len(source)}


def draft_text(source):
    identity = source_identity(source)
    offset, clauses = 0, []
    raw_lines = source.splitlines(keepends=True)
    if len(raw_lines) > MAX_REQUIREMENTS:
        raw_lines = raw_lines[:MAX_REQUIREMENTS - 1] + [b"".join(raw_lines[MAX_REQUIREMENTS - 1:])]
    for index, raw in enumerate(raw_lines):
        clauses.append({"id": f"clause-{index + 1:04d}", "status": "UNREVIEWED", "span": {"start": offset, "end": offset + len(raw), "quote": raw.decode("utf-8")}})
        offset += len(raw)
    return {"schema": "surface.commission.draft.v1", "source": identity, "review": {"status": "UNREVIEWED"}, "clauses": clauses, "tasks": [], "notice": "Line boundaries are syntactic only. No clause has executable meaning until a reviewer supplies a grounded plan."}


def _topological(tasks):
    remaining = {task["id"]: set(task["requires"]) for task in tasks}
    ordered = []
    while remaining:
        ready = sorted(key for key, dependencies in remaining.items() if not dependencies)
        if not ready:
            raise ValueError("task dependency cycle")
        for key in ready:
            ordered.append(key)
            del remaining[key]
        for dependencies in remaining.values():
            dependencies.difference_update(ready)
    return ordered


def validate_plan(source, plan):
    identity = source_identity(source)
    if len(canonical(plan)) > MAX_JSON_BYTES:
        raise ValueError("plan exceeds finite JSON budget")
    _object(plan, ("schema", "commission_id", "title", "source", "review", "requirements", "tasks", "atlas_review"), ("budget",), "plan")
    if plan["schema"] != PLAN_SCHEMA:
        raise ValueError("unknown plan schema")
    _identifier(plan["commission_id"], "commission_id")
    _text(plan["title"], "title", 300)
    if plan["source"] != identity:
        raise ValueError("source digest or byte length does not match reviewed plan")
    _object(plan["review"], ("status", "reviewer"), label="review")
    if plan["review"]["status"] != "REVIEWED":
        raise ValueError("a plan must be explicitly REVIEWED before compilation")
    _text(plan["review"]["reviewer"], "reviewer", 300)
    budget = plan.get("budget", {"total_seconds": 900, "max_tasks": MAX_TASKS})
    _object(budget, ("total_seconds", "max_tasks"), label="budget")
    _number(budget["total_seconds"], MAX_TOTAL_SECONDS, "total_seconds")
    _integer(budget["max_tasks"], 1, MAX_TASKS, "max_tasks")
    requirements, tasks = plan["requirements"], plan["tasks"]
    if not isinstance(requirements, list) or len(requirements) > MAX_REQUIREMENTS:
        raise ValueError("requirements must be a bounded list")
    if not isinstance(tasks, list) or len(tasks) > budget["max_tasks"]:
        raise ValueError("tasks exceed finite task budget")
    req_by_id, task_by_id = {}, {}
    for item in requirements:
        _object(item, ("id", "span", "interpretation", "disposition", "task_ids", "acceptance"), label="requirement")
        key = _identifier(item["id"], "requirement id")
        if key in req_by_id:
            raise ValueError("duplicate requirement id")
        req_by_id[key] = item
        span = _object(item["span"], ("start", "end", "quote"), label="span")
        _integer(span["start"], 0, len(source), "span start")
        _integer(span["end"], span["start"] + 1, len(source), "span end")
        if not isinstance(span["quote"], str) or source[span["start"]:span["end"]].decode("utf-8") != span["quote"]:
            raise ValueError("span quote does not match exact UTF-8 source bytes")
        _text(item["interpretation"], "interpretation")
        if item["disposition"] not in ("TASK", "BLOCKED", "CONTEXT", "PROHIBITION"):
            raise ValueError("invalid requirement disposition")
        references = _strings(item["task_ids"], "requirement task_ids", MAX_TASKS)
        if item["disposition"] == "TASK" and not references:
            raise ValueError("TASK requirement has no reviewed task")
        if item["disposition"] in ("CONTEXT", "PROHIBITION") and references:
            raise ValueError("context or prohibition cannot admit tasks")
        acceptance = _object(item["acceptance"], ("status", "gate", "evidence", "tolerance"), label="acceptance")
        if acceptance["status"] not in ("OPEN", "BLOCKED", "NOT_APPLICABLE"):
            raise ValueError("acceptance cannot be asserted by a commission plan")
        _text(acceptance["gate"], "acceptance gate")
        _text(acceptance["tolerance"], "acceptance tolerance")
        _strings(acceptance["evidence"], "acceptance evidence", 64)
    for task in tasks:
        _object(task, ("id", "action", "requires", "requirement_ids", "timeout_seconds", "semantic_timeout_seconds"), label="task")
        key = _identifier(task["id"], "task id")
        if key in task_by_id:
            raise ValueError("duplicate task id")
        task_by_id[key] = task
        if task["action"] not in ACTIONS:
            raise ValueError("unknown action; source-derived commands are forbidden")
        _number(task["timeout_seconds"], 300, "timeout_seconds")
        _number(task["semantic_timeout_seconds"], 120, "semantic_timeout_seconds")
        if task["semantic_timeout_seconds"] > task["timeout_seconds"]:
            raise ValueError("semantic timeout cannot exceed task timeout")
        _strings(task["requires"], "requires", MAX_TASKS)
        _strings(task["requirement_ids"], "requirement_ids", MAX_REQUIREMENTS)
        if not task["requirement_ids"]:
            raise ValueError("every task needs a grounded requirement")
    for task in tasks:
        if set(task["requires"]) - task_by_id.keys():
            raise ValueError("unknown task dependency")
        for key in task["requirement_ids"]:
            if key not in req_by_id or task["id"] not in req_by_id[key]["task_ids"]:
                raise ValueError("requirement/task cross-reference mismatch")
            if req_by_id[key]["disposition"] == "BLOCKED" and task["action"] != "external-agent":
                raise ValueError("BLOCKED requirement can only name an external-agent task")
    for requirement in requirements:
        for key in requirement["task_ids"]:
            if key not in task_by_id or requirement["id"] not in task_by_id[key]["requirement_ids"]:
                raise ValueError("task/requirement cross-reference mismatch")
    _topological(tasks)
    reviews = plan["atlas_review"]
    if not isinstance(reviews, list) or len(reviews) != len(ATLAS_DOMAINS):
        raise ValueError("atlas review must cover every required domain")
    seen = set()
    for review in reviews:
        _object(review, ("domain", "applicability", "reason", "evidence", "status"), label="atlas review")
        if review["domain"] not in ATLAS_DOMAINS or review["domain"] in seen:
            raise ValueError("unknown or duplicate atlas domain")
        seen.add(review["domain"])
        if review["applicability"] not in ("APPLICABLE", "NOT_APPLICABLE", "OPEN") or review["status"] not in ("OPEN", "BLOCKED", "NOT_APPLICABLE"):
            raise ValueError("invalid atlas applicability or review status")
        if (review["applicability"] == "NOT_APPLICABLE") != (review["status"] == "NOT_APPLICABLE"):
            raise ValueError("NOT_APPLICABLE atlas decisions must agree with review status")
        _text(review["reason"], "atlas reason")
        _strings(review["evidence"], "atlas evidence", 64)
    return {**plan, "budget": budget}


def _source_map(source, plan):
    intervals = sorted((r["span"]["start"], r["span"]["end"]) for r in plan["requirements"])
    uncovered, cursor = [], 0
    for start, end in intervals:
        if start > cursor:
            uncovered.append({"start": cursor, "end": start, "quote": source[cursor:start].decode("utf-8"), "status": "UNMAPPED"})
        cursor = max(cursor, end)
    if cursor < len(source):
        uncovered.append({"start": cursor, "end": len(source), "quote": source[cursor:].decode("utf-8"), "status": "UNMAPPED"})
    return {"schema": "surface.commission.source-map.v1", "source": plan["source"], "offset_unit": "UTF-8 bytes; half-open [start,end)", "mapped": [{"requirement_id": r["id"], **r["span"], "disposition": r["disposition"], "task_ids": r["task_ids"]} for r in plan["requirements"]], "unmapped": uncovered}


def _limits(value, *, root):
    names = ("max_depth", "max_children", "max_tasks", "total_seconds") if root else ("max_tasks", "total_seconds")
    _object(value, names, label="generator limits")
    _integer(value["max_tasks"], 1, MAX_TASKS, "generator max_tasks")
    _number(value["total_seconds"], MAX_TOTAL_SECONDS, "generator total_seconds")
    if root:
        _integer(value["max_depth"], 2, 4, "generator max_depth")
        _integer(value["max_children"], 1, 8, "generator max_children")


def validate_factory(recipe):
    if len(canonical(recipe)) > MAX_JSON_BYTES:
        raise ValueError("generator recipe too large")
    _object(recipe, ("schema", "generator_id", "allowed_actions", "limits", "children"), label="factory")
    if recipe["schema"] != "surface.commission.factory.v1":
        raise ValueError("unknown factory schema")
    _identifier(recipe["generator_id"], "generator id")
    _limits(recipe["limits"], root=True)
    actions = _strings(recipe["allowed_actions"], "factory allowed_actions", len(ACTIONS))
    if not actions or set(actions) - set(ACTIONS):
        raise ValueError("unknown factory action")
    children = recipe["children"]
    if not isinstance(children, list) or not 1 <= len(children) <= recipe["limits"]["max_children"]:
        raise ValueError("generator child count exceeds finite limit")
    seen = set()
    for child in children:
        _object(child, ("generator_id", "allowed_actions", "limits"), label="factory child")
        key = _identifier(child["generator_id"], "child generator id")
        if key in seen or key == recipe["generator_id"]:
            raise ValueError("duplicate or recursive generator id")
        seen.add(key)
        _limits(child["limits"], root=False)
        permitted = _strings(child["allowed_actions"], "child allowed_actions", len(ACTIONS))
        if not permitted or set(permitted) - set(actions):
            raise ValueError("child generator cannot expand allowed actions")
        if any(child["limits"][name] > recipe["limits"][name] for name in ("max_tasks", "total_seconds")):
            raise ValueError("child generator cannot expand parent limits")
    return recipe


def _child_recipe(parent, child):
    return {"schema": "surface.commission.generator.v1", **child, "depth": 1, "parent_sha256": digest(canonical(parent)), "parent_recipe": parent}


def validate_generator(generator):
    _object(generator, ("schema", "generator_id", "allowed_actions", "limits", "depth", "parent_sha256", "parent_recipe"), label="generator")
    parent = validate_factory(generator["parent_recipe"])
    selected = [c for c in parent["children"] if c["generator_id"] == generator["generator_id"]]
    if len(selected) != 1 or generator != _child_recipe(parent, selected[0]):
        raise ValueError("generator parent digest, depth, or inherited limits mismatch")
    if generator["depth"] + 1 > parent["limits"]["max_depth"]:
        raise ValueError("generator depth exceeds inherited bound")
    return generator


def _compiler_identity():
    return {"schema_version": 1, "commission_py_sha256": digest(_read_bytes(HERE)), "supervise_py_sha256": digest(_read_bytes(SUPERVISOR_PATH))}


def _task_template(task):
    return {"task_id": task["id"], "action": task["action"], "command_template": None if task["action"] == "external-agent" else ["{python}", "-B", "{commission.py}", "__action", task["action"], "--bundle", "{bundle}", "--repo", "{repo}"], "timeout": task["timeout_seconds"], "semantic_timeout": task["semantic_timeout_seconds"], "milestones": ["adapter-started", "adapter-finished"], "outputs": ["evidence.json"] + (["polyia-demo.json"] if task["action"] == "polyia-demo" else []), "retry_exit_codes": [75], "requires": task["requires"]}


def _external_envelopes(machine):
    tasks = []
    for task in machine["tasks"]:
        if task["action"] != "external-agent":
            continue
        tasks.append({
            "task_id": task["id"], "task_sha256": digest(canonical(task)),
            "commission_id": machine["commission_id"], "source": machine["source"],
            "requirement_ids": task["requirement_ids"], "adapter_status": "BLOCKED",
            "budget": {"timeout_seconds": task["timeout_seconds"], "semantic_timeout_seconds": task["semantic_timeout_seconds"]},
            "allowed_capabilities": ["read supplied immutable inputs", "propose reviewable artifacts", "submit hashed evidence for independent review"],
            "issued_envelope": "RUN/envelopes/" + task["id"] + ".json",
            "result_schema": "surface.commission.agent-result.v1",
            "result_outcomes": ["PROPOSED", "BLOCKED", "FAILED"],
            "submission_status": "SUBMITTED_FOR_REVIEW",
            "automatic_execution": False,
            "scientific_acceptance": "NOT_EVALUATED",
        })
    return {"schema": "surface.commission.agent-envelopes.v1", "commission_id": machine["commission_id"], "machine_sha256": digest(canonical(machine)), "scientific_acceptance": "NOT_EVALUATED", "tasks": tasks}


def _markdown(machine, witness):
    lines = [f"# {machine['title']}", "", f"Commission: `{machine['commission_id']}`", "", f"Source SHA-256: `{machine['source']['sha256']}` ({machine['source']['byte_length']} UTF-8 bytes).", "", "Execution and scientific acceptance are separate. Successful adapters prove only their stated checks. Scientific acceptance: **NOT_EVALUATED**.", "", "## Task state machine", "", "```mermaid", "stateDiagram-v2", "    [*] --> PENDING", "    PENDING --> READY: Dependencies succeeded", "    PENDING --> BLOCKED: Missing adapter or failed dependency", "    READY --> RUNNING: Fixed deadline and fenced epoch", "    RUNNING --> SUCCEEDED: Exit zero and verified publication", "    RUNNING --> FAILED: Deadline, output, or process failure", "    RUNNING --> BLOCKED: Superseded epoch", "    SUCCEEDED --> [*]", "    FAILED --> [*]", "    BLOCKED --> [*]", "```", "", "## Dependency graph", "", "```mermaid", "flowchart TD"]
    nodes = {task["id"]: f"n{index}" for index, task in enumerate(machine["tasks"])}
    for task in machine["tasks"]:
        lines.append(f'    {nodes[task["id"]]}["{task["id"]}: {task["action"]}"]')
        for dep in task["requires"]:
            lines.append(f"    {nodes[dep]} --> {nodes[task['id']]}")
    if not nodes:
        lines.append('    review["No executable tasks admitted"]')
    lines += ["```", "", "## Grounded requirements", "", "| Requirement | UTF-8 bytes | Disposition | Tasks | Acceptance |", "|---|---|---|---|---|"]
    for r in machine["requirements"]:
        lines.append(f"| {r['id']} | [{r['span']['start']},{r['span']['end']}) | {r['disposition']} | {', '.join(r['task_ids']) or '—'} | {r['acceptance']['status']} |")
    lines += ["", f"Unmapped source: {sum(x['end'] - x['start'] for x in witness['unmapped'])} bytes in {len(witness['unmapped'])} intervals. Exact quotes and all uncovered text remain in `source-map.json`.", "", "## Atlas review", "", "| Domain | Applicability | Status | Reason |", "|---|---|---|---|"]
    for item in machine["atlas_review"]:
        reason = item["reason"].replace("|", "\\|").replace("\n", " ").replace("\r", " ")
        lines.append(f"| {item['domain']} | {item['applicability']} | {item['status']} | {reason} |")
    lines += ["", "These domains are a required review checklist, not a claim that all mathematics has been exhausted. OPEN and BLOCKED decisions remain unresolved.", "", "## Execution and resume", "", "From the repository root, use the following command forms, replacing the explicit path placeholders:", "", "```text", "python3 tools/commission.py validate --bundle BUNDLE", "python3 tools/commission.py run --bundle BUNDLE --runs NEW_RUN_DIRECTORY --repo .", "python3 tools/commission.py replay --bundle BUNDLE --runs RUN_DIRECTORY --repo .", "python3 tools/commission.py resume --bundle BUNDLE --runs RUN_DIRECTORY --repo .", "```", "", "Run directories are append-only evidence containers. Resume validates the bundle, implementation pins, receipts, publication hashes and current Supervisor epochs; it does not reset the commission deadline or silently rerun completed tasks.", "", "The compiler does not install Hermes or a language model. External-agent tasks remain BLOCKED until a separately reviewed adapter is implemented. See `external-envelopes.json` and `docs/COMMISSION_COMPILER.md`.", ""]
    return "\n".join(lines).encode("utf-8")


def _svg(machine):
    def escape(text):
        clean = "".join(c if c in "\t\n\r" or 0x20 <= ord(c) <= 0xD7FF or 0xE000 <= ord(c) <= 0xFFFD or 0x10000 <= ord(c) <= 0x10FFFF else "�" for c in str(text))
        return html.escape(clean, quote=True)
    tasks = machine["tasks"]
    height = 238 + max(1, len(tasks)) * 94
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="{height}" viewBox="0 0 1120 {height}" role="img" aria-labelledby="title description">', f'<title id="title">{escape(machine["title"])}</title>', '<desc id="description">Reviewed grounded commission dependency graph. Task execution success never asserts scientific acceptance.</desc>', '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="#64748b"/></marker></defs>', f'<rect width="1120" height="{height}" fill="#f4f7fb"/>', '<g font-family="sans-serif" fill="#15263b">', f'<text x="38" y="43" font-size="25" font-weight="700">{escape(machine["title"][:75])}</text>', f'<text x="38" y="74" font-size="15">{escape(machine["commission_id"])} · {machine["source"]["byte_length"]} UTF-8 bytes · explicit reviewed mapping</text>', '<text x="38" y="103" font-size="15">Scientific acceptance: NOT_EVALUATED</text>', f'<text x="38" y="131" font-size="12">Source SHA-256: {machine["source"]["sha256"]}</text>']
    positions = {task["id"]: 166 + index * 94 for index, task in enumerate(tasks)}
    for index, task in enumerate(tasks):
        y = positions[task["id"]]
        for dep in task["requires"]:
            start = positions[dep] + 60
            lane = 52 + (index % 8) * 8
            lines.append(f'<path d="M220 {start} H{lane} V{y + 29} H220" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#arrow)"/>')
    for task in tasks:
        y = positions[task["id"]]
        blocked = task["action"] == "external-agent"
        lines += [f'<rect x="222" y="{y}" width="846" height="66" rx="9" fill="{"#edf0f4" if blocked else "#e5f0ff"}" stroke="#b5c8de"/>', f'<text x="242" y="{y + 26}" font-size="17" font-weight="700">{escape(task["id"])} · {task["action"]}</text>', f'<text x="242" y="{y + 49}" font-size="13">{"BLOCKED: external adapter absent" if blocked else "PENDING: execution receipt required"} · deadline ≤ {task["timeout_seconds"]}s · source: {escape(", ".join(task["requirement_ids"])[:70])}</text>']
    if not tasks:
        lines.append('<text x="38" y="200" font-size="18">No executable tasks were admitted.</text>')
    lines += [f'<text x="38" y="{height - 28}" font-size="13">Exact source quotes, unresolved intervals, review decisions and evidence contracts accompany this diagram.</text>', '</g></svg>']
    return "\n".join(lines).encode("utf-8")


def _artifacts(source, plan, generator=None):
    plan = validate_plan(source, plan)
    lineage = None
    if generator is not None:
        generator = validate_generator(generator)
        if set(task["action"] for task in plan["tasks"]) - set(generator["allowed_actions"]):
            raise ValueError("plan action exceeds generator allowlist")
        if plan["budget"]["max_tasks"] > generator["limits"]["max_tasks"] or plan["budget"]["total_seconds"] > generator["limits"]["total_seconds"]:
            raise ValueError("plan budget exceeds inherited generator limits")
        lineage = {"generator_id": generator["generator_id"], "generator_sha256": digest(canonical(generator)), "parent_sha256": generator["parent_sha256"], "depth": generator["depth"] + 1}
    order = _topological(plan["tasks"])
    by_id = {task["id"]: task for task in plan["tasks"]}
    witness = _source_map(source, plan)
    machine = {"schema": "surface.commission.machine.v1", "commission_id": plan["commission_id"], "title": plan["title"], "source": plan["source"], "review": plan["review"], "budget": plan["budget"], "requirements": plan["requirements"], "atlas_review": plan["atlas_review"], "tasks": [by_id[key] for key in order], "topological_order": order, "scientific_acceptance": "NOT_EVALUATED", "generator_lineage": lineage, "initial_state": "PENDING", "task_states": ["PENDING", "READY", "RUNNING", "SUCCEEDED", "FAILED", "BLOCKED", "DEADLINE"], "transitions": [{"from": "PENDING", "to": "READY", "when": "all dependencies have verified success receipts"}, {"from": "PENDING", "to": "BLOCKED", "when": "adapter absent or dependency not successful"}, {"from": "READY", "to": "RUNNING", "when": "durable intent, fixed deadline, new fenced epoch"}, {"from": "RUNNING", "to": "SUCCEEDED", "when": "zero exit, current epoch, verified outputs before deadline"}, {"from": "RUNNING", "to": "FAILED", "when": "process, output, semantic timeout, or deadline failure"}, {"from": "RUNNING", "to": "BLOCKED", "when": "superseded by a newer epoch"}, {"from": "PENDING", "to": "DEADLINE", "when": "commission deadline already expired"}], "unmapped_intervals": len(witness["unmapped"])}
    artifacts = {"source.txt": source, "plan.json": canonical(plan), "machine.json": canonical(machine), "source-map.json": canonical(witness), "task-specs.json": canonical({"schema": "surface.commission.task-specs.v1", "tasks": [_task_template(task) for task in machine["tasks"]]}), "external-envelopes.json": canonical(_external_envelopes(machine)), "machine.md": _markdown(machine, witness), "machine.svg": _svg(machine)}
    if generator is not None:
        artifacts["generator.json"] = canonical(generator)
    return artifacts


def _write_bundle(out, artifacts, kind, metadata):
    out = Path(out)
    _plain_components(out.parent)
    # Exclusive creation means no compilation can replace an existing evidence directory.
    out.mkdir(parents=True, exist_ok=False)
    for name, raw in sorted(artifacts.items()):
        with (out / name).open("xb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    manifest = {"schema": kind, **metadata, "files": {name: {"sha256": digest(raw), "bytes": len(raw)} for name, raw in sorted(artifacts.items())}}
    with (out / "manifest.json").open("xb") as handle:
        handle.write(canonical(manifest))
        handle.flush()
        os.fsync(handle.fileno())
    return {"valid": True, "manifest_sha256": digest(canonical(manifest)), "artifacts": len(artifacts), "source": metadata.get("source")}


def compile_commission(source, plan, out, *, generator=None):
    artifacts = _artifacts(source, plan, generator)
    return _write_bundle(out, artifacts, "surface.commission.manifest.v1", {"source": source_identity(source), "compiler": _compiler_identity()})


def generate_factory(recipe, out):
    recipe = validate_factory(recipe)
    artifacts = {"factory.json": canonical(recipe)}
    children = []
    for child in recipe["children"]:
        name = child["generator_id"] + ".generator.json"
        raw = canonical(_child_recipe(recipe, child))
        artifacts[name] = raw
        children.append({"path": name, "sha256": digest(raw), "generator_id": child["generator_id"]})
    artifacts["index.json"] = canonical({"schema": "surface.commission.factory-index.v1", "parent_sha256": digest(canonical(recipe)), "depth": 0, "children": children})
    return _write_bundle(out, artifacts, "surface.commission.factory-manifest.v1", {"parent_sha256": digest(canonical(recipe)), "compiler": _compiler_identity()})


def validate_bundle(bundle):
    _guard_tree(bundle, maximum_entries=32)
    bundle = Path(bundle).resolve(strict=True)
    manifest = read_json(bundle / "manifest.json")
    _object(manifest, ("schema", "source", "compiler", "files"), label="bundle manifest")
    if manifest["schema"] != "surface.commission.manifest.v1" or manifest["compiler"] != _compiler_identity():
        raise ValueError("bundle compiler identity does not match this implementation")
    files = manifest["files"]
    allowed = {"source.txt", "plan.json", "machine.json", "source-map.json", "task-specs.json", "external-envelopes.json", "machine.md", "machine.svg", "generator.json"}
    if not isinstance(files, dict) or set(files) - allowed or set(p.name for p in bundle.iterdir()) != set(files) | {"manifest.json"}:
        raise ValueError("bundle artifact set mismatch or unsafe path")
    for name, entry in files.items():
        _object(entry, ("sha256", "bytes"), label="artifact manifest entry")
        path = bundle / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("bundle artifacts must be regular files")
        raw = _read_bytes(path)
        if len(raw) > MAX_JSON_BYTES or entry != {"sha256": digest(raw), "bytes": len(raw)}:
            raise ValueError(f"artifact digest or bytes mismatch: {name}")
    source = _read_bytes(bundle / "source.txt", MAX_SOURCE_BYTES)
    if manifest["source"] != source_identity(source):
        raise ValueError("manifest source digest mismatch")
    generator = read_json(bundle / "generator.json") if "generator.json" in files else None
    regenerated = _artifacts(source, read_json(bundle / "plan.json"), generator)
    if set(regenerated) != set(files) or any(_read_bytes(bundle / name) != raw for name, raw in regenerated.items()):
        raise ValueError("compiled bundle differs from deterministic source/plan replay")
    return {"valid": True, "manifest_sha256": digest(_read_bytes(bundle / "manifest.json")), "source": manifest["source"], "artifacts": len(files), "scientific_acceptance": "NOT_EVALUATED"}


def _plain_components(path):
    path = Path(path).absolute()
    for candidate in (path, *path.parents):
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode):
            raise ValueError("linked evidence path component is refused: " + str(candidate))


def _guard_tree(root, maximum_entries=16384):
    """Reject links/special files before reading or writing saved evidence."""
    root = Path(root).absolute()
    _plain_components(root)
    if not root.is_dir():
        raise ValueError("evidence root must be a regular directory")
    count = total = 0
    for directory, directories, files in os.walk(root, followlinks=False):
        for name in directories + files:
            count += 1
            if count > maximum_entries:
                raise ValueError("evidence tree exceeds finite entry budget")
            info = (Path(directory) / name).lstat()
            if stat.S_ISLNK(info.st_mode) or not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
                raise ValueError("linked or nonregular evidence entry is refused")
            if stat.S_ISREG(info.st_mode):
                if info.st_size > Supervisor.MAX_OUTPUT_BYTES:
                    raise ValueError("evidence file exceeds finite byte limit")
                total += info.st_size
                if total > MAX_TASKS * Supervisor.MAX_TOTAL_OUTPUT_BYTES:
                    raise ValueError("evidence tree exceeds finite aggregate byte limit")


def _new_json(path, value):
    """Publish once without replacing an existing evidence record."""
    path = Path(path)
    _plain_components(path.parent)
    fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(canonical(value))
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)  # Atomic, and fails if the target already exists.
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        os.unlink(temporary)


def _append_event(runs, value):
    _plain_components(runs)
    fd = os.open(runs / "journal.jsonl", os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "ab", buffering=0) as handle:
        handle.write(canonical({"wall_time": time.time(), **value}))
        os.fsync(handle.fileno())


@contextmanager
def _run_lock(runs):
    _guard_tree(runs)
    fd = os.open(runs / "lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "a+b") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("another commission runner holds this run lock") from error
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def _clock_identity():
    boot = Path("/proc/sys/kernel/random/boot_id")
    # On hosts without a persistent monotonic-clock identity, only replay is safe
    # after process interruption; resume refuses instead of renewing a deadline.
    return boot.read_text().strip() if boot.is_file() else None


def _input_pins(machine, repo, bundle, runs):
    selected = {"tools/commission.py": HERE, "tools/supervise.py": SUPERVISOR_PATH}
    for task in machine["tasks"]:
        action = task["action"]
        if action == "python-tests":
            selected["repo/tests/test_supervisor.py"] = repo / "tests/test_supervisor.py"
            selected["repo/tools/supervise.py"] = repo / "tools/supervise.py"
        if action == "polyia-demo":
            selected["repo/tools/polyia_surface_demo.py"] = repo / "tools/polyia_surface_demo.py"
            selected["repo/vendor/polyia/IMPORT_MANIFEST.json"] = repo / "vendor/polyia/IMPORT_MANIFEST.json"
            root = repo / "vendor/polyia"
            if root.exists():
                for index, path in enumerate(root.rglob("*")):
                    if index >= 4096 or len(selected) > 512:
                        raise ValueError("adapter input census exceeds finite limit")
                    if path.is_file() and "__pycache__" not in path.parts and path.suffix in (".py", ".json", ".mjs", ".ts"):
                        selected["repo/" + path.relative_to(repo).as_posix()] = path
        if action == "foundation-audit":
            for name in ("tools/materialize_foundation.py", "build/foundation/MATERIALIZATION.json", "lineage/cosmos-continuation-parts/manifest.json"):
                selected["repo/" + name] = repo / name
    if len(selected) > 512:
        raise ValueError("adapter input census exceeds finite limit")
    pins = {}
    for name, path in sorted(selected.items()):
        if path.is_symlink():
            raise ValueError("linked implementation inputs are refused")
        if path.is_file():
            if path.stat().st_size > 64 * 1024 * 1024:
                raise ValueError("adapter input exceeds finite file limit")
            raw = _read_bytes(path, 64 * 1024 * 1024)
            pins[name] = {"sha256": digest(raw), "bytes": len(raw)}
        else:
            pins[name] = {"missing": True}
    return {"schema": "surface.commission.execution-inputs.v1", "repo": str(repo), "bundle": str(bundle), "runs": str(runs), "compiler_path": str(HERE), "python": sys.version, "executable": sys.executable, "files": pins}


def _adapter_missing(task, repo):
    if task["action"] == "external-agent":
        return "external-agent adapter is not installed; use the issued task envelope"
    prerequisites = {
        "source-integrity": [],
        "python-tests": ["tests/test_supervisor.py", "tools/supervise.py"],
        "polyia-demo": ["tools/polyia_surface_demo.py", "vendor/polyia/IMPORT_MANIFEST.json"],
        "foundation-audit": ["tools/materialize_foundation.py", "build/foundation/MATERIALIZATION.json"],
    }[task["action"]]
    missing = [name for name in prerequisites if not (repo / name).is_file()]
    return "missing adapter or prerequisite: " + ", ".join(missing) if missing else None


def _command(task, bundle, repo):
    return (sys.executable, "-B", str(HERE), "__action", task["action"], "--bundle", str(bundle), "--repo", str(repo))


def _spec_for(task, bundle, repo, remaining):
    template = _task_template(task)
    timeout = min(task["timeout_seconds"], remaining)
    return TaskSpec(task_id=task["id"], command=_command(task, bundle, repo), cwd=str(repo), timeout=timeout, semantic_timeout=min(task["semantic_timeout_seconds"], timeout), milestones=tuple(template["milestones"]), outputs=tuple(template["outputs"]), retry_exit_codes=(75,))


def _issued_envelope(task, machine, bundle_identity, run_identity, run):
    return {"schema": "surface.commission.issued-agent-task.v1", "commission_id": machine["commission_id"], "task_id": task["id"], "task_sha256": digest(canonical(task)), "bundle_manifest_sha256": bundle_identity, "source": machine["source"], "run_sha256": run_identity, "submission_epoch": 1, "attempt_limit": 1, "deadline_unix": min(run["deadline_wall"], run["started_wall"] + task["timeout_seconds"]), "budget": {"timeout_seconds": task["timeout_seconds"], "semantic_timeout_seconds": task["semantic_timeout_seconds"], "max_artifacts": 32, "max_artifact_bytes": 16 * 1024 * 1024, "max_total_bytes": 64 * 1024 * 1024}, "allowed_capabilities": ["read supplied immutable source and evidence", "propose reviewable artifacts", "submit hashed evidence for independent review"], "automatic_execution": False, "requirements": [r for r in machine["requirements"] if r["id"] in task["requirement_ids"]], "result_schema": "surface.commission.agent-result.v1", "scientific_acceptance": "NOT_EVALUATED"}


def _plain_receipt(task, bundle_sha, status, reason):
    return {"schema": "surface.commission.task-receipt.v1", "bundle_manifest_sha256": bundle_sha, "task_id": task["id"], "action": task["action"], "status": status, "reason": reason, "epoch": None, "attempts": 0, "returncode": None, "published": [], "supervisor_state_sha256": None, "scientific_acceptance": "NOT_EVALUATED"}


def _state_receipt(task, bundle_sha, state):
    result = _plain_receipt(task, bundle_sha, {"succeeded": "SUCCEEDED", "failed": "FAILED", "superseded": "BLOCKED"}[state["status"]], state["reason"])
    result.update(epoch=state["epoch"], attempts=state["attempts"], returncode=state["returncode"], published=state["published"], supervisor_state_sha256=digest(canonical(state)))
    return result


def _verify_spec(state, task, bundle, repo, recorded_context=None):
    spec = state["spec"]
    template = _task_template(task)
    expected_command, expected_cwd = list(_command(task, bundle, repo)), str(repo)
    if recorded_context is not None:
        context = recorded_context
        expected_command = [context["executable"], "-B", context["compiler_path"], "__action", task["action"], "--bundle", context["bundle"], "--repo", context["repo"]]
        expected_cwd = context["repo"]
    if spec["task_id"] != task["id"] or spec["command"] != expected_command or spec["cwd"] != expected_cwd or spec["milestones"] != template["milestones"] or spec["outputs"] != template["outputs"] or spec["retry_exit_codes"] != [75]:
        raise ValueError("supervisor task spec differs from the predefined adapter")
    _number(spec["timeout"], task["timeout_seconds"], "recorded task timeout")
    _number(spec["semantic_timeout"], min(task["semantic_timeout_seconds"], spec["timeout"]), "recorded semantic timeout")


def _verify_receipt(receipt, task, bundle_sha, bundle, runs, repo, recorded_context=None):
    keys = ("schema", "bundle_manifest_sha256", "task_id", "action", "status", "reason", "epoch", "attempts", "returncode", "published", "supervisor_state_sha256", "scientific_acceptance")
    _object(receipt, keys, label="task receipt")
    if receipt["scientific_acceptance"] != "NOT_EVALUATED":
        raise ValueError("receipt cannot assert scientific acceptance")
    if receipt["schema"] != "surface.commission.task-receipt.v1" or receipt["task_id"] != task["id"] or receipt["action"] != task["action"] or receipt["bundle_manifest_sha256"] != bundle_sha or receipt["status"] not in TERMINAL_STATES:
        raise ValueError("task receipt identity/status mismatch")
    if receipt["epoch"] is None:
        if receipt["status"] not in ("BLOCKED", "DEADLINE") or receipt["attempts"] != 0 or receipt["published"] or receipt["supervisor_state_sha256"] is not None or receipt["returncode"] is not None:
            raise ValueError("unexecuted task cannot claim an execution receipt")
        return receipt
    _integer(receipt["epoch"], 1, 2**63 - 1, "receipt epoch")
    _integer(receipt["attempts"], 1, 2, "receipt attempts")
    job = runs / "jobs" / task["id"]
    state = read_json(job / "resume.json")
    if digest(canonical(state)) != receipt["supervisor_state_sha256"]:
        raise ValueError("supervisor state digest mismatch")
    _verify_spec(state, task, bundle, repo, recorded_context)
    fence = read_json(job / "fence.json")
    if fence["epoch"] != receipt["epoch"] or state["epoch"] != receipt["epoch"]:
        raise ValueError("receipt is not in the current supervisor fence epoch")
    if _state_receipt(task, bundle_sha, state) != receipt:
        raise ValueError("receipt differs from the actual supervisor result")
    if receipt["status"] == "SUCCEEDED":
        publication = read_json(job / "current.json")
        if publication["epoch"] != receipt["epoch"] or publication["outputs"] != receipt["published"]:
            raise ValueError("publication epoch or receipt output mismatch")
        expected = _task_template(task)["outputs"]
        if [entry["name"] for entry in receipt["published"]] != expected:
            raise ValueError("receipt output set differs from adapter declarations")
        for entry in receipt["published"]:
            if entry["path"] != f"committed/{receipt['epoch']}/{entry['name']}":
                raise ValueError("unsafe publication output path")
            path = job / entry["path"]
            if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(job.resolve()):
                raise ValueError("missing or escaped committed artifact")
            raw = _read_bytes(path, Supervisor.MAX_OUTPUT_BYTES)
            if len(raw) != entry["bytes"] or digest(raw) != entry["sha256"]:
                raise ValueError("committed artifact digest/bytes mismatch")
        evidence = read_json(job / f"committed/{receipt['epoch']}/evidence.json")
        if evidence.get("scientific_acceptance") != "NOT_EVALUATED" or evidence.get("action") != task["action"] or evidence.get("bundle_manifest_sha256") != bundle_sha or evidence.get("status") != "CHECK_PASSED":
            raise ValueError("adapter evidence identity or acceptance mismatch")
    return receipt


def _load_run(bundle, runs, repo, *, portable=False):
    _guard_tree(runs)
    validated = validate_bundle(bundle)
    machine = read_json(bundle / "machine.json")
    run = read_json(runs / "run.json")
    _object(run, ("schema", "commission_id", "bundle_manifest_sha256", "inputs_sha256", "started_wall", "deadline_wall", "deadline_monotonic", "clock_identity", "scientific_acceptance"), label="run")
    if run["schema"] != "surface.commission.run.v1" or run["bundle_manifest_sha256"] != validated["manifest_sha256"] or run["commission_id"] != machine["commission_id"] or run["scientific_acceptance"] != "NOT_EVALUATED":
        raise ValueError("run identity or acceptance mismatch")
    for name in ("started_wall", "deadline_wall", "deadline_monotonic"):
        _number(run[name], 10**14, name)
    if not 0 < run["deadline_wall"] - run["started_wall"] <= machine["budget"]["total_seconds"] + 0.01:
        raise ValueError("run deadline exceeds the reviewed budget")
    journal = _read_bytes(runs / "journal.jsonl").splitlines()
    if not journal:
        raise ValueError("original run journal is missing")
    origin = _parse_json(journal[0])
    if origin.get("event") != "run-start" or origin.get("run_sha256") != digest(canonical(run)) or origin.get("bundle_manifest_sha256") != validated["manifest_sha256"]:
        raise ValueError("original run digest differs from the durable run-start journal")
    pins = read_json(runs / "execution-inputs.json")
    current_pins = _input_pins(machine, repo, bundle, runs)
    if digest(canonical(pins)) != run["inputs_sha256"] or (pins["files"] != current_pins["files"] if portable else pins != current_pins):
        raise ValueError("execution input digest or host path changed; use a newly reviewed run")
    return validated, machine, run


def _summary(machine, validated, receipts):
    states = {receipt["status"] for receipt in receipts}
    status = "NO_TASKS" if not receipts else "TASKS_SUCCEEDED"
    if "BLOCKED" in states:
        status = "BLOCKED"
    if "FAILED" in states:
        status = "FAILED"
    if "DEADLINE" in states:
        status = "DEADLINE"
    if len(receipts) < len(machine["tasks"]):
        status = "INCOMPLETE"
    return {"schema": "surface.commission.execution-summary.v1", "commission_id": machine["commission_id"], "bundle_manifest_sha256": validated["manifest_sha256"], "execution_status": status, "scientific_acceptance": "NOT_EVALUATED", "tasks": receipts}


def _envelope_for(task, machine, validated, run, runs):
    envelope = read_json(runs / "envelopes" / (task["id"] + ".json"))
    expected = _issued_envelope(task, machine, validated["manifest_sha256"], digest(canonical(run)), run)
    if envelope != expected:
        raise ValueError("issued external envelope identity/digest mismatch")
    return envelope


def _validate_agent_result(result, envelope):
    _object(result, ("schema", "commission_id", "task_id", "task_sha256", "bundle_manifest_sha256", "source_sha256", "run_sha256", "submission_epoch", "outcome", "summary", "artifacts", "scientific_acceptance"), label="agent result")
    if result["schema"] != "surface.commission.agent-result.v1":
        raise ValueError("unknown external result schema")
    if result["scientific_acceptance"] != "NOT_EVALUATED" or result["outcome"] not in ("PROPOSED", "BLOCKED", "FAILED"):
        raise ValueError("external result cannot assert acceptance or execution success")
    for name in ("commission_id", "task_id", "task_sha256", "bundle_manifest_sha256", "run_sha256", "submission_epoch"):
        if result[name] != envelope[name] or name == "submission_epoch" and type(result[name]) is not int:
            raise ValueError("external result identity or submission epoch mismatch: " + name)
    if result["source_sha256"] != envelope["source"]["sha256"]:
        raise ValueError("external result source digest mismatch")
    _text(result["summary"], "external result summary")
    artifacts = result["artifacts"]
    if not isinstance(artifacts, list) or len(artifacts) > envelope["budget"]["max_artifacts"]:
        raise ValueError("external artifact count exceeds finite budget")
    if result["outcome"] == "PROPOSED" and not artifacts:
        raise ValueError("PROPOSED results need at least one evidence artifact")
    seen, total = set(), 0
    for entry in artifacts:
        _object(entry, ("path", "bytes", "sha256", "command", "observed_result", "tolerance"), label="external artifact")
        name = _text(entry["path"], "artifact path", 500)
        if len(name.split("/")) > 16 or Path(name).is_absolute() or "\\" in name or "\0" in name or ":" in name or any(part in ("", ".", "..", ".git") for part in name.split("/")) or name in seen:
            raise ValueError("unsafe or duplicate external artifact path")
        seen.add(name)
        _integer(entry["bytes"], 0, envelope["budget"]["max_artifact_bytes"], "artifact bytes")
        if not isinstance(entry["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
            raise ValueError("invalid external artifact digest")
        for field in ("command", "observed_result", "tolerance"):
            _text(entry[field], "artifact " + field)
        total += entry["bytes"]
    if total > envelope["budget"]["max_total_bytes"]:
        raise ValueError("external total artifact bytes exceed finite budget")
    return result


def _read_external_artifacts(result, root, envelope):
    _validate_agent_result(result, envelope)
    root = Path(root).resolve(strict=True)
    copied = {}
    for entry in result["artifacts"]:
        path = root / entry["path"]
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError("external artifact path is missing or escapes its root")
        for parent in path.parents:
            if parent == root:
                break
            if parent.is_symlink():
                raise ValueError("external artifact path contains a linked parent")
        if path.stat().st_size != entry["bytes"]:
            raise ValueError("external artifact bytes mismatch")
        raw = _read_bytes(path, envelope["budget"]["max_artifact_bytes"])
        if len(raw) != entry["bytes"] or digest(raw) != entry["sha256"]:
            raise ValueError("external artifact digest/bytes mismatch")
        copied[entry["path"]] = raw
    return copied


def _external_submissions(machine, validated, run, runs):
    summaries = []
    for task in machine["tasks"]:
        if task["action"] != "external-agent":
            continue
        directory = runs / "submissions" / task["id"] / "1"
        if not directory.exists():
            continue
        envelope = _envelope_for(task, machine, validated, run, runs)
        record = read_json(directory / "submission.json")
        _object(record, ("schema", "status", "received_wall", "received_monotonic", "envelope_sha256", "result", "scientific_acceptance"), label="external submission record")
        if record["schema"] != "surface.commission.submission.v1" or record["status"] != "SUBMITTED_FOR_REVIEW" or record["scientific_acceptance"] != "NOT_EVALUATED" or record["envelope_sha256"] != digest(canonical(envelope)):
            raise ValueError("external submission status, acceptance, or envelope digest mismatch")
        _number(record["received_wall"], envelope["deadline_unix"], "submission received wall time")
        start_mono = run["deadline_monotonic"] - machine["budget"]["total_seconds"]
        _number(record["received_monotonic"], min(run["deadline_monotonic"], start_mono + task["timeout_seconds"]), "submission received monotonic time")
        if record["received_wall"] < run["started_wall"] or record["received_monotonic"] < start_mono:
            raise ValueError("submission predates its issued run")
        _read_external_artifacts(record["result"], directory / "artifacts", envelope)
        actual = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()}
        expected = {"submission.json"} | {"artifacts/" + entry["path"] for entry in record["result"]["artifacts"]}
        if actual != expected:
            raise ValueError("external submission artifact census mismatch")
        summaries.append({"task_id": task["id"], "submission_epoch": 1, "status": "SUBMITTED_FOR_REVIEW", "outcome": record["result"]["outcome"], "submission_sha256": digest(canonical(record)), "scientific_acceptance": "NOT_EVALUATED"})
    return summaries


def reconcile_results(bundle, runs, repo, result, artifacts_root):
    """Import non-executable evidence once. No task or science gate is accepted."""
    _plain_components(runs)
    bundle, runs, repo = Path(bundle).resolve(strict=True), Path(runs).resolve(strict=True), Path(repo).resolve(strict=True)
    with _run_lock(runs):
        validated, machine, run = _load_run(bundle, runs, repo)
        if run["clock_identity"] is None or run["clock_identity"] != _clock_identity():
            raise ValueError("external submission cannot establish the original deadline clock")
        tasks = {task["id"]: task for task in machine["tasks"]}
        if not isinstance(result, dict) or result.get("task_id") not in tasks or tasks[result["task_id"]]["action"] != "external-agent":
            raise ValueError("external result does not name an issued external-agent task")
        task = tasks[result["task_id"]]
        envelope = _envelope_for(task, machine, validated, run, runs)
        _validate_agent_result(result, envelope)
        target = runs / "submissions" / task["id"] / "1"
        if target.exists():
            raise ValueError("submission epoch already consumed; stale results are refused")
        start_mono = run["deadline_monotonic"] - machine["budget"]["total_seconds"]
        if time.time() >= envelope["deadline_unix"] or time.monotonic() >= min(run["deadline_monotonic"], start_mono + task["timeout_seconds"]):
            raise ValueError("original external task deadline expired")
        artifacts = _read_external_artifacts(result, artifacts_root, envelope)
        target.parent.mkdir(exist_ok=True)
        if target.parent.is_symlink() or not target.parent.resolve().is_relative_to(runs):
            raise ValueError("unsafe submission destination")
        with tempfile.TemporaryDirectory(prefix=".pending-", dir=target.parent) as temporary:
            stage = Path(temporary)
            (stage / "artifacts").mkdir()
            for name, raw in artifacts.items():
                path = stage / "artifacts" / name
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as handle:
                    handle.write(raw)
                    handle.flush()
                    os.fsync(handle.fileno())
            wall, mono = time.time(), time.monotonic()
            if wall >= envelope["deadline_unix"] or mono >= min(run["deadline_monotonic"], start_mono + task["timeout_seconds"]):
                raise ValueError("external task publication deadline expired")
            record = {"schema": "surface.commission.submission.v1", "status": "SUBMITTED_FOR_REVIEW", "received_wall": wall, "received_monotonic": mono, "envelope_sha256": digest(canonical(envelope)), "result": result, "scientific_acceptance": "NOT_EVALUATED"}
            _new_json(stage / "submission.json", record)
            os.rename(stage, target)
        _append_event(runs, {"event": "external-submission", "task_id": task["id"], "submission_epoch": 1, "status": "SUBMITTED_FOR_REVIEW", "submission_sha256": digest(canonical(record))})
        return {"task_id": task["id"], "submission_epoch": 1, "status": "SUBMITTED_FOR_REVIEW", "submission_sha256": digest(canonical(record)), "scientific_acceptance": "NOT_EVALUATED"}


def replay_run(bundle, runs, repo):
    _plain_components(runs)
    bundle, runs, repo = Path(bundle).resolve(strict=True), Path(runs).resolve(strict=True), Path(repo).resolve(strict=True)
    validated, machine, run = _load_run(bundle, runs, repo, portable=True)
    recorded_context = read_json(runs / "execution-inputs.json")
    receipts = []
    for task in machine["tasks"]:
        path = runs / "receipts" / (task["id"] + ".json")
        if path.exists():
            receipts.append(_verify_receipt(read_json(path), task, validated["manifest_sha256"], bundle, runs, repo, recorded_context))
    summary = _summary(machine, validated, receipts)
    summary["external_submissions"] = _external_submissions(machine, validated, run, runs)
    return summary


def run_bundle(bundle, runs, repo, *, resume=False):
    _plain_components(runs)
    bundle, runs, repo = Path(bundle).resolve(strict=True), Path(runs).absolute(), Path(repo).resolve(strict=True)
    validated = validate_bundle(bundle)
    machine = read_json(bundle / "machine.json")
    if resume:
        if not runs.is_dir() or runs.is_symlink():
            raise ValueError("resume requires an existing regular run directory")
    else:
        runs.mkdir(parents=True, exist_ok=False)
    runs = runs.resolve()
    with _run_lock(runs):
        if not resume:
            for name in ("receipts", "jobs", "summaries", "envelopes", "submissions"):
                (runs / name).mkdir()
            pins = _input_pins(machine, repo, bundle, runs)
            _new_json(runs / "execution-inputs.json", pins)
            wall, mono = time.time(), time.monotonic()
            run = {"schema": "surface.commission.run.v1", "commission_id": machine["commission_id"], "bundle_manifest_sha256": validated["manifest_sha256"], "inputs_sha256": digest(canonical(pins)), "started_wall": wall, "deadline_wall": wall + machine["budget"]["total_seconds"], "deadline_monotonic": mono + machine["budget"]["total_seconds"], "clock_identity": _clock_identity(), "scientific_acceptance": "NOT_EVALUATED"}
            _new_json(runs / "run.json", run)
            for task in machine["tasks"]:
                if task["action"] == "external-agent":
                    _new_json(runs / "envelopes" / (task["id"] + ".json"), _issued_envelope(task, machine, validated["manifest_sha256"], digest(canonical(run)), run))
            _append_event(runs, {"event": "run-start", "bundle_manifest_sha256": validated["manifest_sha256"], "run_sha256": digest(canonical(run)), "deadline_wall": run["deadline_wall"]})
        else:
            validated, machine, run = _load_run(bundle, runs, repo)
            if run["clock_identity"] is None or run["clock_identity"] != _clock_identity():
                raise ValueError("resume cannot establish the original monotonic clock; replay only")
            _append_event(runs, {"event": "resume", "original_deadline_wall": run["deadline_wall"]})
        supervisor = Supervisor(runs / "jobs")
        receipts, by_id = [], {}
        for task in machine["tasks"]:
            path = runs / "receipts" / (task["id"] + ".json")
            if path.exists():
                receipt = _verify_receipt(read_json(path), task, validated["manifest_sha256"], bundle, runs, repo)
            else:
                state_path = runs / "jobs" / task["id"] / "resume.json"
                if state_path.exists():
                    state = supervisor.inspect(task["id"])
                    _verify_spec(state, task, bundle, repo)
                    if state.get("status") in ("succeeded", "failed", "superseded"):
                        receipt = _state_receipt(task, validated["manifest_sha256"], state)
                        _verify_receipt(receipt, task, validated["manifest_sha256"], bundle, runs, repo)
                    else:
                        receipt = _plain_receipt(task, validated["manifest_sha256"], "BLOCKED", "unfinished supervisor intent requires host-process inspection; automatic duplicate execution refused")
                else:
                    remaining = min(run["deadline_wall"] - time.time(), run["deadline_monotonic"] - time.monotonic())
                    if remaining <= 0:
                        receipt = _plain_receipt(task, validated["manifest_sha256"], "DEADLINE", "original commission deadline expired")
                    elif any(by_id[dep]["status"] != "SUCCEEDED" for dep in task["requires"]):
                        receipt = _plain_receipt(task, validated["manifest_sha256"], "BLOCKED", "dependency does not have a verified success receipt")
                    elif (missing := _adapter_missing(task, repo)) is not None:
                        receipt = _plain_receipt(task, validated["manifest_sha256"], "BLOCKED", missing)
                    else:
                        result = supervisor.run(_spec_for(task, bundle, repo, remaining))
                        state = supervisor.inspect(task["id"])
                        if state["epoch"] != result.epoch:
                            raise ValueError("supervisor result superseded before receipt publication")
                        receipt = _state_receipt(task, validated["manifest_sha256"], state)
                        _verify_receipt(receipt, task, validated["manifest_sha256"], bundle, runs, repo)
                _new_json(path, receipt)
                _append_event(runs, {"event": "task-receipt", "task_id": task["id"], "status": receipt["status"], "receipt_sha256": digest(canonical(receipt))})
            receipts.append(receipt)
            by_id[task["id"]] = receipt
        summary = _summary(machine, validated, receipts)
        summary["external_submissions"] = _external_submissions(machine, validated, run, runs)
        generation = len(list((runs / "summaries").glob("*.json"))) + 1
        _new_json(runs / "summaries" / f"{generation:06d}.json", summary)
        _append_event(runs, {"event": "run-summary", "generation": generation, "execution_status": summary["execution_status"], "scientific_acceptance": "NOT_EVALUATED"})
        return summary


def _action(action, bundle, repo):
    if action not in ACTIONS or action == "external-agent":
        raise ValueError("action has no local adapter")
    bundle, repo = Path(bundle).resolve(strict=True), Path(repo).resolve(strict=True)
    stage = Path(os.environ["SURFACE_TASK_STAGE"]).resolve(strict=True)
    epoch = int(os.environ["SURFACE_TASK_EPOCH"])
    validated = validate_bundle(bundle)
    print(json.dumps({"type": "progress", "epoch": epoch, "milestone": "adapter-started"}), flush=True)
    command, observations = None, None
    if action == "source-integrity":
        observations = validated
    elif action == "python-tests":
        command = [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_supervisor.py", "-v"]
    elif action == "polyia-demo":
        command = [sys.executable, "-B", str(repo / "tools/polyia_surface_demo.py"), "--output", str(stage / "polyia-demo.json")]
    elif action == "foundation-audit":
        command = [sys.executable, "-B", str(repo / "tools/materialize_foundation.py"), "--output", str(repo / "build/foundation"), "--check"]
    if command is not None:
        completed = subprocess.run(command, cwd=repo, stdin=subprocess.DEVNULL, check=False)
        if completed.returncode != 0:
            return completed.returncode if 1 <= completed.returncode <= 255 else 1
        observations = {"returncode": completed.returncode, "output": "Supervisor epoch log retains actual command output"}
    evidence = {"schema": "surface.commission.adapter-evidence.v1", "action": action, "status": "CHECK_PASSED", "bundle_manifest_sha256": validated["manifest_sha256"], "source": validated["source"], "implementation": _compiler_identity(), "command": command, "observed_result": observations, "tolerance": "Exact artifact hashes and predefined adapter exit zero; science gates remain open", "scientific_acceptance": "NOT_EVALUATED"}
    _new_json(stage / "evidence.json", evidence)
    print(json.dumps({"type": "progress", "epoch": epoch, "milestone": "adapter-finished"}), flush=True)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    for name in ("draft", "compile", "generate"):
        sub = commands.add_parser(name)
        sub.add_argument("--source", required=True, type=Path)
        sub.add_argument("--out", required=True, type=Path)
        if name != "draft":
            sub.add_argument("--plan", required=True, type=Path)
        if name == "generate":
            sub.add_argument("--recipe", required=True, type=Path)
    factory = commands.add_parser("factory")
    factory.add_argument("--recipe", required=True, type=Path)
    factory.add_argument("--out", required=True, type=Path)
    for name in ("validate", "replay", "run", "resume"):
        sub = commands.add_parser(name)
        sub.add_argument("--bundle", required=True, type=Path)
        if name != "validate":
            sub.add_argument("--runs", required=name in ("run", "resume"), type=Path)
            sub.add_argument("--repo", default=HERE.parents[1], type=Path)
    reconcile = commands.add_parser("reconcile-results")
    reconcile.add_argument("--bundle", required=True, type=Path)
    reconcile.add_argument("--runs", required=True, type=Path)
    reconcile.add_argument("--repo", default=HERE.parents[1], type=Path)
    reconcile.add_argument("--result", required=True, type=Path)
    reconcile.add_argument("--artifacts", required=True, type=Path)
    action = commands.add_parser("__action", help=argparse.SUPPRESS)
    action.add_argument("action", choices=ACTIONS)
    action.add_argument("--bundle", required=True, type=Path)
    action.add_argument("--repo", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.operation == "draft":
            raw = _read_bytes(args.source, MAX_SOURCE_BYTES)
            result = _write_bundle(args.out, {"source.txt": raw, "draft.json": canonical(draft_text(raw))}, "surface.commission.draft-manifest.v1", {"source": source_identity(raw)})
        elif args.operation in ("compile", "generate"):
            result = compile_commission(_read_bytes(args.source, MAX_SOURCE_BYTES), read_json(args.plan), args.out, generator=read_json(args.recipe) if args.operation == "generate" else None)
        elif args.operation == "reconcile-results":
            result = reconcile_results(args.bundle, args.runs, args.repo, read_json(args.result), args.artifacts)
        elif args.operation == "factory":
            result = generate_factory(read_json(args.recipe), args.out)
        elif args.operation == "validate" or args.operation == "replay" and args.runs is None:
            result = validate_bundle(args.bundle)
        elif args.operation == "replay":
            result = replay_run(args.bundle, args.runs, args.repo)
        elif args.operation in ("run", "resume"):
            result = run_bundle(args.bundle, args.runs, args.repo, resume=args.operation == "resume")
        else:
            return _action(args.action, args.bundle, args.repo)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, f"commission refused: {error}\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False))
    return 0 if result.get("execution_status", "TASKS_SUCCEEDED") in ("TASKS_SUCCEEDED", "NO_TASKS") else 3


if __name__ == "__main__":
    raise SystemExit(main())
