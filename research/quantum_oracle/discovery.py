"""Versioned finite PHANTOM research cycle; no physical discovery inference.

The target is f(x)=(3*x+1) mod 2**width. Training is fixed before search.
All other inputs challenge the frozen candidate. Exact arithmetic supplies an
independent control, and a truth-table permutation supplies a finite unitary
representation. This controlled example is not observational evidence.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PHANTOM = ROOT / "build/foundation/phantom_division_viii_v04/division8"
PINS = {
    "__init__.py": "8d6782405df442c6d2d45a87153b00a16204ce8b58b55e9bfb19595ca6e23958",
    "_runtime.py": "33bfc046b67f90d7a470cd57ea146b54c8f210be4780a61e59fbe000b3ad8734",
    "contracts.py": "442b0c68d984479dc67c89fbce69ca1ca2c789c1e46f8d103dacff981e8b749e",
    "generators.py": "77d792b22d3bcfae3b6a48f0ed74db6352e73188daa999f03e5ee2aaa9d90fa9",
    "kernel.py": "aeb34870bc79f238514987639c2d15f5c0a1b30e6ae084866b7168b45fc50a6e",
}
PHASES = ("SCOPE", "ACQUIRE", "VERIFY SOURCE", "FORMALIZE", "GENERATE",
          "EXECUTE", "PERTURB", "COMPARE", "CHALLENGE")
DECISIONS = ("ACCEPT", "REJECT", "UNKNOWN")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low},{high}]")
    return value


def _next(before, after):
    if before in PHASES[:-1]:
        return after == PHASES[PHASES.index(before) + 1]
    if before == "CHALLENGE":
        return after in DECISIONS
    if before in DECISIONS:
        return after == "ARCHIVE"
    return before == "ARCHIVE" and after == "SELECT NEXT"


class Cycle:
    """Append-only in-memory event construction; serialized snapshots are copies.

    The hash chain detects accidental modification relative to a retained root;
    it is not an authenticated scientific review or a hostile-writer defense.
    """
    def __init__(self, subject, scope):
        if not isinstance(subject, str) or not 1 <= len(subject) <= 128:
            raise ValueError("bounded subject required")
        self._events = []
        self._subject = subject
        self._append("SCOPE", scope)

    @property
    def events(self):
        return json.loads(canonical(self._events))

    def _append(self, state, payload):
        raw = canonical(payload)
        if len(raw) > 1024 * 1024 or len(self._events) >= 32:
            raise ValueError("event budget exceeded")
        event = {"ordinal": len(self._events), "subject": self._subject,
                 "state": state, "parent": self._events[-1]["id"] if self._events else None,
                 "payload": json.loads(raw)}
        self._events.append({**event, "id": digest(event)})

    def advance(self, state, payload):
        if not _next(self._events[-1]["state"], state):
            raise ValueError("illegal research transition")
        if state in DECISIONS:
            challenge = self._events[-1]["payload"]
            if challenge.get("decision") != state or not challenge.get("method"):
                raise ValueError("decision requires the preceding explicit challenge")
        self._append(state, payload)


def verify_events(events):
    if not isinstance(events, list) or not 1 <= len(events) <= 32:
        raise ValueError("event count")
    previous = None
    for index, event in enumerate(events):
        if set(event) != {"ordinal", "subject", "state", "parent", "payload", "id"}:
            raise ValueError("event schema")
        content = {k: v for k, v in event.items() if k != "id"}
        if event["ordinal"] != index or event["id"] != digest(content):
            raise ValueError("event hash or ordinal mismatch")
        if event["parent"] != (previous["id"] if previous else None):
            raise ValueError("event parent mismatch")
        if index == 0 and event["state"] != "SCOPE":
            raise ValueError("missing scope")
        if previous and (event["subject"] != previous["subject"] or
                         not _next(previous["state"], event["state"])):
            raise ValueError("event transition mismatch")
        if event["state"] in DECISIONS and (
                previous["payload"].get("decision") != event["state"] or
                not previous["payload"].get("method")):
            raise ValueError("unwitnessed decision")
        previous = event
    return True


def _phantom():
    # Only locally retained, digest-pinned original modules are executed.
    for name, expected in PINS.items():
        path = PHANTOM / name
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("PHANTOM source mismatch: " + name)
    namespace = "_qo_pinned_phantom_v04"
    if namespace not in sys.modules:
        spec = importlib.util.spec_from_file_location(namespace, PHANTOM / "__init__.py",
                                                      submodule_search_locations=[str(PHANTOM)])
        module = importlib.util.module_from_spec(spec)
        sys.modules[namespace] = module
        spec.loader.exec_module(module)
    return __import__(namespace + ".generators", fromlist=["generators"])


def _operations(operations, width):
    if not isinstance(operations, list) or len(operations) > 2:
        raise ValueError("at most two finite grammar operations")
    for op in operations:
        if not isinstance(op, dict) or set(op) != {"op", "operand"} or op["op"] not in ("ADD", "MUL", "XOR", "AND"):
            raise ValueError("operation outside finite grammar")
        _integer(op["operand"], "operand", 0, (1 << width) - 1)


def _evaluate(operations, value, width):
    mask = (1 << width) - 1
    for op in operations:
        operand = op["operand"]
        if op["op"] == "ADD":
            value = value + operand
        elif op["op"] == "MUL":
            value = value * operand
        elif op["op"] == "XOR":
            value = value ^ operand
        else:
            value = value & operand
        value &= mask
    return value


def challenge_operations(operations, *, width, train):
    """Independent finite exhaustive integer/control implementation.

    Check coherent vector transport via a full permutation matrix separately
    from its direct scatter implementation; no physical execution is inferred.
    """
    import numpy as np
    _integer(width, "width", 2, 6)
    _operations(operations, width)
    n = 1 << width
    if not isinstance(train, tuple) or not 1 <= len(train) < n or len(set(train)) != len(train):
        raise ValueError("unique proper training subset required")
    for x in train:
        _integer(x, "training index", 0, n - 1)
    table = [_evaluate(operations, x, width) for x in range(n)]
    expected = [(3 * x + 1) % n for x in range(n)]
    failures = [{"input": x, "expected": expected[x], "actual": table[x],
                 "partition": "train" if x in train else "held_out"}
                for x in range(n) if table[x] != expected[x]]
    # Alternative Gray representation is a conjugacy, not equality of bytes.
    encoding = [x ^ (x >> 1) for x in range(n)]
    inverse = {value: x for x, value in enumerate(encoding)}
    encoded_table = [encoding[table[inverse[y]]] for y in range(n)]
    conjugacy = all(inverse[encoded_table[encoding[x]]] == table[x] for x in range(n))
    basis = {"dimension": n, "admissible_unitary": len(set(table)) == n}
    if basis["admissible_unitary"]:
        matrix = np.zeros((n, n), dtype=complex)
        for x, y in enumerate(table):
            matrix[y, x] = 1
        psi = np.exp(2j * np.pi * np.arange(n) ** 2 / (n + 1)) / np.sqrt(n)
        scatter = np.zeros(n, dtype=complex)
        for x in range(n):
            scatter[table[x]] = psi[x]
        basis.update({"unitarity_residual": float(np.linalg.norm(matrix.conj().T @ matrix - np.eye(n))),
                      "coherent_transport_residual": float(np.linalg.norm(matrix @ psi - scatter)),
                      "tolerance": 1e-12, "basis_order": "integer-msb-display; column x maps to row f(x)"})
    null_mismatches = sum(x != expected[x] for x in range(n))
    perturb_mismatches = sum((table[x] ^ 1) != expected[x] for x in range(n))
    return {"decision": "REJECT" if failures else "ACCEPT",
            "method": "independent integer arithmetic, exhaustive finite held-out challenge",
            "checked": n, "training": len(train), "held_out": n - len(train),
            "counterexamples": failures, "truth_table": table,
            "alternate_encoding_conjugacy": conjugacy,
            "identity_null_mismatches": null_mismatches,
            "one_bit_output_perturbation_mismatches": perturb_mismatches,
            "basis_permutation": basis,
            "scope": "exact finite function only; no generalization to other widths, datasets or physics"}


def run_affine_cycle(*, width=4, max_candidates=512):
    _integer(width, "width", 2, 6)
    _integer(max_candidates, "candidate budget", 1, 512)
    train = (0, 1, 2, 3) if width > 2 else (0, 1)
    fixture = [{"input": x, "output": (3 * x + 1) % (1 << width)} for x in train]
    config = {"width": width, "max_candidates": max_candidates}
    cycle = Cycle("phantom-affine-to-basis-v1", config)
    cycle.advance("ACQUIRE", {"kind": "controlled exact integer fixture", "observations": fixture,
                              "sha256": digest(fixture), "physical_evidence": False})
    engine = _phantom()
    cycle.advance("VERIFY SOURCE", {"original_modules": PINS})
    cycle.advance("FORMALIZE", {"domain": f"unsigned U{width}", "target": "(3*x+1) mod 2**width",
                                "training_inputs": train, "loss": "modular wrap declared",
                                "grammar": "ADD/MUL/XOR/AND constants 0,1,3; depth <=2"})
    search = engine.synthesize_word(fixture, width=width, max_depth=2,
                                    max_candidates=max_candidates, constants=(0, 1, 3))
    cycle.advance("GENERATE", {"search_sha256": digest(search), "status": search["status"],
                               "parent_source": PINS["generators.py"],
                               "tested": search["tested"]})
    if search["status"] == "CANDIDATE":
        candidate = search["generator"]
        outputs = [engine.execute_ir(candidate, x)["value"] for x in range(1 << width)]
        cycle.advance("EXECUTE", {"generator_id": candidate["id"], "outputs_sha256": digest(outputs)})
        challenge = challenge_operations(candidate["parameters"]["operations"], width=width, train=train)
        cycle.advance("PERTURB", {"one_bit_output_perturbation_mismatches": challenge["one_bit_output_perturbation_mismatches"],
                                   "identity_null_mismatches": challenge["identity_null_mismatches"]})
        if outputs != challenge["truth_table"]:
            raise ValueError("PHANTOM independent implementation disagreement")
        cycle.advance("COMPARE", {"phantom_matches_independent_truth_table": True,
                                  "alternate_encoding_conjugacy": challenge["alternate_encoding_conjugacy"]})
    else:
        cycle.advance("EXECUTE", {"skipped": "no candidate within search bound"})
        cycle.advance("PERTURB", {"skipped": "no candidate"})
        cycle.advance("COMPARE", {"skipped": "no candidate"})
        challenge = {"decision": "UNKNOWN", "method": "no candidate available for challenge",
                     "checked": 0, "reason": search["status"]}
    cycle.advance("CHALLENGE", challenge)
    cycle.advance(challenge["decision"], {"scope": "finite controlled affine transfer fixture only",
                                          "full_initiative_acceptance": "UNKNOWN"})
    cycle.advance("ARCHIVE", {"search_sha256": digest(search), "challenge_sha256": digest(challenge)})
    cycle.advance("SELECT NEXT", {"criterion": "earliest unfulfilled independent original gate",
                                   "next": "real-data held-out transfer and independent quantum libraries"})
    return {"schema": "phantom.quantum.research-cycle.v1", "config": config,
            "source_pins": dict(PINS), "search": search, "challenge": challenge,
            "decision": challenge["decision"], "events": cycle.events,
            "physical_evidence": False,
            "resources": {"max_width": 6, "max_dimension": 64, "max_candidates": 512,
                          "max_depth": 2, "max_events": 32, "max_event_bytes": 1048576,
                          "runner_hard_seconds": 60, "runner_memory_mib": 2048},
            "replay": "research.quantum_oracle.discovery.replay(report)"}


def replay(report):
    if not isinstance(report, dict) or report.get("schema") != "phantom.quantum.research-cycle.v1":
        raise ValueError("research report schema")
    verify_events(report["events"])
    actual = run_affine_cycle(**report["config"])
    if canonical(actual) != canonical(report):
        raise ValueError("research replay differs from independently recomputed result")
    return True
