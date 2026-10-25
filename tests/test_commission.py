"""Grounding, finite generation, and actual supervised execution contracts."""
import copy
import hashlib
import importlib.util
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "tools" / "commission.py"
if MODULE.exists():
    spec = importlib.util.spec_from_file_location("surface_commission", MODULE)
    commission = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = commission
    spec.loader.exec_module(commission)
else:
    commission = None


class CommissionTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(commission, "grounded commission compiler must exist")
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = "Vérify source.\r\nDo not execute text.\nMystery Ω.".encode("utf-8")

    def tearDown(self):
        if hasattr(self, "temp"):
            self.temp.cleanup()

    def plan(self):
        return {
            "schema": "surface.commission.plan.v1",
            "commission_id": "grounding-test",
            "title": "A grounded source check",
            "source": {"sha256": hashlib.sha256(self.source).hexdigest(), "byte_length": len(self.source)},
            "review": {"status": "REVIEWED", "reviewer": "test fixture reviewer"},
            "budget": {"total_seconds": 30, "max_tasks": 8},
            "requirements": [{
                "id": "r-source", "span": {"start": 0, "end": 15, "quote": "Vérify source."},
                "interpretation": "Verify the retained source bytes.", "disposition": "TASK", "task_ids": ["t-source"],
                "acceptance": {"status": "OPEN", "gate": "Independent scientific review", "evidence": [], "tolerance": "Not applicable to source integrity"},
            }],
            "tasks": [{"id": "t-source", "action": "source-integrity", "requires": [], "requirement_ids": ["r-source"], "timeout_seconds": 3, "semantic_timeout_seconds": 2}],
            "atlas_review": [{"domain": domain, "applicability": "OPEN", "reason": "Requires scientific review", "evidence": [], "status": "OPEN"} for domain in commission.ATLAS_DOMAINS],
        }

    def bundle(self, plan=None, name="bundle"):
        out = self.root / name
        commission.compile_commission(self.source, self.plan() if plan is None else plan, out)
        return out

    def test_draft_retains_unicode_crlf_and_negation_without_admitting_tasks(self):
        draft = commission.draft_text(self.source)
        self.assertEqual(draft["review"]["status"], "UNREVIEWED")
        self.assertEqual(draft["clauses"][0]["span"], {"start": 0, "end": 17, "quote": "Vérify source.\r\n"})
        self.assertEqual(draft["clauses"][1]["span"]["quote"], "Do not execute text.\n")
        self.assertTrue(all(c["status"] == "UNREVIEWED" for c in draft["clauses"]))
        self.assertEqual(draft["tasks"], [])
        self.assertEqual(b"".join(self.source[c["span"]["start"]:c["span"]["end"]] for c in draft["clauses"]), self.source)

    def test_compile_is_deterministic_and_unmapped_bytes_remain_visible(self):
        left, right = self.bundle(name="one"), self.bundle(name="two")
        self.assertEqual({p.name: p.read_bytes() for p in left.iterdir()}, {p.name: p.read_bytes() for p in right.iterdir()})
        witness = json.loads((left / "source-map.json").read_text())
        self.assertEqual(witness["unmapped"], [{"start": 15, "end": len(self.source), "quote": "\r\nDo not execute text.\nMystery Ω.", "status": "UNMAPPED"}])
        machine = json.loads((left / "machine.json").read_text())
        self.assertEqual(machine["scientific_acceptance"], "NOT_EVALUATED")
        self.assertEqual(machine["topological_order"], ["t-source"])
        ET.fromstring((left / "machine.svg").read_bytes())
        self.assertTrue(commission.validate_bundle(left)["valid"])

    def test_tampered_source_digest_quote_and_utf8_boundary_are_rejected(self):
        for mutate in (
            lambda p: p["source"].update(sha256="0" * 64),
            lambda p: p["requirements"][0]["span"].update(quote="Verify source."),
            lambda p: p["requirements"][0]["span"].update(start=2),
        ):
            with self.subTest(mutate=mutate):
                plan = self.plan()
                mutate(plan)
                with self.assertRaises(ValueError):
                    commission.validate_plan(self.source, plan)

    def test_unreviewed_mapping_cannot_compile(self):
        plan = self.plan()
        plan["review"]["status"] = "UNREVIEWED"
        with self.assertRaisesRegex(ValueError, "REVIEWED"):
            commission.compile_commission(self.source, plan, self.root / "unreviewed")
        self.assertFalse((self.root / "unreviewed").exists())

    def test_cycle_is_rejected_before_output_or_process_launch(self):
        plan = self.plan()
        plan["tasks"][0]["requires"] = ["t-second"]
        plan["tasks"].append({**plan["tasks"][0], "id": "t-second", "requires": ["t-source"]})
        plan["requirements"][0]["task_ids"].append("t-second")
        with self.assertRaisesRegex(ValueError, "cycle"):
            commission.compile_commission(self.source, plan, self.root / "cycle")
        self.assertFalse((self.root / "cycle").exists())

    def test_unknown_actions_and_text_commands_cannot_be_admitted(self):
        for patch in ({"action": "shell"}, {"command": ["sh", "-c", "touch injected"]}):
            plan = self.plan()
            plan["tasks"][0].update(patch)
            with self.assertRaises(ValueError):
                commission.validate_plan(self.source, plan)

    def test_scientific_acceptance_cannot_be_forged_in_plan(self):
        plan = self.plan()
        plan["requirements"][0]["acceptance"]["status"] = "ACCEPT"
        with self.assertRaisesRegex(ValueError, "acceptance"):
            commission.validate_plan(self.source, plan)

    def test_atlas_review_requires_every_domain_and_reason(self):
        for mutation in (lambda p: p["atlas_review"].pop(), lambda p: p["atlas_review"][0].update(reason="")):
            plan = self.plan()
            mutation(plan)
            with self.assertRaises(ValueError):
                commission.validate_plan(self.source, plan)

    def test_nonfinite_or_excessive_budgets_are_rejected(self):
        for key, value in (("timeout_seconds", float("inf")), ("timeout_seconds", 301), ("semantic_timeout_seconds", 121), ("timeout_seconds", -1), ("timeout_seconds", True)):
            plan = self.plan()
            plan["tasks"][0][key] = value
            with self.assertRaises(ValueError):
                commission.validate_plan(self.source, plan)

    def test_bundle_tampering_and_existing_output_are_rejected(self):
        bundle = self.bundle()
        with self.assertRaises(FileExistsError):
            self.bundle()
        (bundle / "source.txt").write_bytes(self.source + b" altered")
        with self.assertRaisesRegex(ValueError, "digest|hash|bytes"):
            commission.validate_bundle(bundle)

    def test_actual_source_action_replays_and_resume_does_not_rerun(self):
        bundle = self.bundle()
        runs = self.root / "runs"
        result = commission.run_bundle(bundle, runs, ROOT)
        self.assertEqual(result["execution_status"], "TASKS_SUCCEEDED")
        self.assertEqual(result["scientific_acceptance"], "NOT_EVALUATED")
        journal = runs / "jobs" / "t-source" / "journal.jsonl"
        before = journal.read_bytes()
        replay = commission.replay_run(bundle, runs, ROOT)
        self.assertEqual(replay["tasks"][0]["status"], "SUCCEEDED")
        resumed = commission.run_bundle(bundle, runs, ROOT, resume=True)
        self.assertEqual(resumed["execution_status"], "TASKS_SUCCEEDED")
        self.assertEqual(journal.read_bytes(), before)
        receipt = json.loads((runs / "receipts" / "t-source.json").read_text())
        artifact = runs / "jobs" / "t-source" / receipt["published"][0]["path"]
        artifact.write_text("forged")
        with self.assertRaisesRegex(ValueError, "digest|hash|bytes"):
            commission.replay_run(bundle, runs, ROOT)

    def test_receipt_cannot_upgrade_task_success_to_scientific_acceptance(self):
        bundle, runs = self.bundle(), self.root / "runs"
        commission.run_bundle(bundle, runs, ROOT)
        path = runs / "receipts" / "t-source.json"
        value = json.loads(path.read_text())
        value["scientific_acceptance"] = "ACCEPT"
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, "acceptance"):
            commission.replay_run(bundle, runs, ROOT)

    def test_external_adapter_and_its_dependents_remain_blocked(self):
        plan = self.plan()
        plan["tasks"][0]["action"] = "external-agent"
        plan["tasks"].append({**plan["tasks"][0], "id": "t-next", "action": "source-integrity", "requires": ["t-source"]})
        plan["requirements"][0]["task_ids"].append("t-next")
        bundle = self.bundle(plan)
        result = commission.run_bundle(bundle, self.root / "runs", ROOT)
        self.assertEqual([x["status"] for x in result["tasks"]], ["BLOCKED", "BLOCKED"])
        self.assertEqual(result["execution_status"], "BLOCKED")
        self.assertFalse((self.root / "runs" / "jobs" / "t-next").exists())

    def test_deadline_is_enforced_by_supervisor_not_reported_as_success(self):
        plan = self.plan()
        plan["tasks"][0].update(timeout_seconds=0.001, semantic_timeout_seconds=0.001)
        result = commission.run_bundle(self.bundle(plan), self.root / "runs", ROOT)
        self.assertEqual(result["tasks"][0]["status"], "FAILED")
        self.assertIn(result["tasks"][0]["reason"], ("deadline", "no-semantic-progress"))
        self.assertEqual(result["scientific_acceptance"], "NOT_EVALUATED")
        self.assertFalse((self.root / "runs" / "jobs" / "t-source" / "current.json").exists())

    def test_replay_rejects_superseded_supervisor_epoch(self):
        bundle, runs = self.bundle(), self.root / "runs"
        commission.run_bundle(bundle, runs, ROOT)
        path = runs / "jobs" / "t-source" / "fence.json"
        fence = json.loads(path.read_text())
        fence["epoch"] += 1
        path.write_text(json.dumps(fence))
        with self.assertRaisesRegex(ValueError, "fence|epoch"):
            commission.replay_run(bundle, runs, ROOT)

    def test_factory_emits_actual_child_generator_and_bounded_lineage(self):
        recipe = {
            "schema": "surface.commission.factory.v1", "generator_id": "test-factory",
            "allowed_actions": ["source-integrity"],
            "limits": {"max_depth": 2, "max_children": 2, "max_tasks": 8, "total_seconds": 30},
            "children": [{"generator_id": "source-generator", "allowed_actions": ["source-integrity"], "limits": {"max_tasks": 8, "total_seconds": 30}}],
        }
        out = self.root / "factory"
        commission.generate_factory(recipe, out)
        child = json.loads((out / "source-generator.generator.json").read_text())
        self.assertEqual(child["schema"], "surface.commission.generator.v1")
        self.assertEqual(child["depth"], 1)
        commission.compile_commission(self.source, self.plan(), self.root / "generated", generator=child)
        machine = json.loads((self.root / "generated" / "machine.json").read_text())
        self.assertEqual(machine["generator_lineage"]["depth"], 2)
        self.assertEqual(machine["generator_lineage"]["parent_sha256"], child["parent_sha256"])
        bad = copy.deepcopy(child)
        bad["parent_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            commission.compile_commission(self.source, self.plan(), self.root / "forged", generator=bad)
        recipe["limits"]["max_children"] = 0
        with self.assertRaises(ValueError):
            commission.generate_factory(recipe, self.root / "unbounded")

    def test_generator_constraints_cannot_be_bypassed_by_reviewed_plan(self):
        recipe = {
            "schema": "surface.commission.factory.v1", "generator_id": "small-factory",
            "allowed_actions": ["source-integrity"],
            "limits": {"max_depth": 2, "max_children": 1, "max_tasks": 1, "total_seconds": 30},
            "children": [{"generator_id": "small-generator", "allowed_actions": ["source-integrity"], "limits": {"max_tasks": 1, "total_seconds": 30}}],
        }
        commission.generate_factory(recipe, self.root / "factory")
        child = json.loads((self.root / "factory" / "small-generator.generator.json").read_text())
        with self.assertRaisesRegex(ValueError, "generator"):
            commission.compile_commission(self.source, self.plan(), self.root / "too-many", generator=child)

    def external_submission(self, *, timeout=30):
        self.assertTrue(callable(getattr(commission, "reconcile_results", None)), "external result reconciliation must be implemented")
        plan = self.plan()
        plan["tasks"][0].update(action="external-agent", timeout_seconds=timeout, semantic_timeout_seconds=min(timeout, 2))
        bundle, runs = self.bundle(plan), self.root / "runs"
        commission.run_bundle(bundle, runs, ROOT)
        envelope = json.loads((runs / "envelopes" / "t-source.json").read_text())
        artifacts = self.root / "agent-output"
        artifacts.mkdir()
        (artifacts / "proposal.txt").write_bytes(b"Review this bounded proposal.\n")
        result = {
            "schema": "surface.commission.agent-result.v1", "commission_id": envelope["commission_id"],
            "task_id": envelope["task_id"], "task_sha256": envelope["task_sha256"],
            "bundle_manifest_sha256": envelope["bundle_manifest_sha256"], "source_sha256": envelope["source"]["sha256"],
            "run_sha256": envelope["run_sha256"], "submission_epoch": 1, "outcome": "PROPOSED",
            "summary": "A proposal awaiting independent review", "scientific_acceptance": "NOT_EVALUATED",
            "artifacts": [{"path": "proposal.txt", "bytes": 30, "sha256": hashlib.sha256(b"Review this bounded proposal.\n").hexdigest(),
                           "command": "No command executed; document proposed", "observed_result": "Proposal text produced", "tolerance": "Exact bytes only"}],
        }
        return bundle, runs, artifacts, result

    def test_external_submission_is_operational_but_never_marks_execution_or_science_accepted(self):
        bundle, runs, artifacts, result = self.external_submission()
        receipt = commission.reconcile_results(bundle, runs, ROOT, result, artifacts)
        self.assertEqual(receipt["status"], "SUBMITTED_FOR_REVIEW")
        self.assertEqual(receipt["scientific_acceptance"], "NOT_EVALUATED")
        replay = commission.replay_run(bundle, runs, ROOT)
        self.assertEqual(replay["execution_status"], "BLOCKED")
        self.assertEqual(replay["external_submissions"][0]["status"], "SUBMITTED_FOR_REVIEW")
        self.assertEqual(replay["tasks"][0]["status"], "BLOCKED")
        with self.assertRaisesRegex(ValueError, "epoch|already"):
            commission.reconcile_results(bundle, runs, ROOT, result, artifacts)

    def test_external_submission_rejects_wrong_identity_future_epoch_and_acceptance(self):
        bundle, runs, artifacts, result = self.external_submission()
        for patch in ({"source_sha256": "0" * 64}, {"submission_epoch": 2}, {"scientific_acceptance": "ACCEPT"}, {"task_sha256": "0" * 64}):
            with self.subTest(patch=patch):
                with self.assertRaises(ValueError):
                    commission.reconcile_results(bundle, runs, ROOT, {**result, **patch}, artifacts)
        self.assertFalse((runs / "submissions" / "t-source" / "1").exists())

    def test_external_artifact_tampering_and_traversal_are_rejected(self):
        bundle, runs, artifacts, result = self.external_submission()
        (artifacts / "proposal.txt").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "digest|bytes"):
            commission.reconcile_results(bundle, runs, ROOT, result, artifacts)
        result["artifacts"][0]["path"] = "../outside.txt"
        with self.assertRaisesRegex(ValueError, "path"):
            commission.reconcile_results(bundle, runs, ROOT, result, artifacts)

    def test_external_submission_cannot_renew_an_expired_deadline(self):
        bundle, runs, artifacts, result = self.external_submission(timeout=0.01)
        time.sleep(0.03)
        with self.assertRaisesRegex(ValueError, "deadline"):
            commission.reconcile_results(bundle, runs, ROOT, result, artifacts)

    def test_replay_verifies_relocated_bundle_and_receipts_without_executing_old_paths(self):
        bundle, runs = self.bundle(), self.root / "runs"
        commission.run_bundle(bundle, runs, ROOT)
        copied_bundle, copied_runs = self.root / "copied-bundle", self.root / "copied-runs"
        shutil.copytree(bundle, copied_bundle)
        shutil.copytree(runs, copied_runs)
        try:
            replay = commission.replay_run(copied_bundle, copied_runs, ROOT)
        except ValueError as error:
            self.fail("read-only replay must support relocated evidence: " + str(error))
        self.assertEqual(replay["execution_status"], "TASKS_SUCCEEDED")
        self.assertEqual(replay["tasks"][0]["status"], "SUCCEEDED")
        with self.assertRaisesRegex(ValueError, "input|path|host"):
            commission.run_bundle(copied_bundle, copied_runs, ROOT, resume=True)

    def test_resume_recovers_terminal_supervisor_record_without_reexecuting(self):
        bundle, runs = self.bundle(), self.root / "runs"
        commission.run_bundle(bundle, runs, ROOT)
        receipt = runs / "receipts" / "t-source.json"
        saved = receipt.read_bytes()
        receipt.unlink()  # Simulated interruption after Supervisor publication, before root receipt publication.
        journal = runs / "jobs" / "t-source" / "journal.jsonl"
        before = journal.read_bytes()
        resumed = commission.run_bundle(bundle, runs, ROOT, resume=True)
        self.assertEqual(resumed["execution_status"], "TASKS_SUCCEEDED")
        self.assertEqual(receipt.read_bytes(), saved)
        self.assertEqual(journal.read_bytes(), before)

    def test_draft_bounds_clause_count_while_retaining_all_source_bytes(self):
        source = (b"unknown\n" * 1024) + "Ω".encode("utf-8")
        draft = commission.draft_text(source)
        self.assertLessEqual(len(draft["clauses"]), 256)
        self.assertEqual("".join(c["span"]["quote"] for c in draft["clauses"]).encode("utf-8"), source)

    def test_cli_rejects_nonregular_source_without_blocking_on_a_fifo(self):
        fifo = self.root / "never-producing-input"
        os.mkfifo(fifo)
        try:
            result = subprocess.run([sys.executable, "-B", str(MODULE), "draft", "--source", str(fifo), "--out", str(self.root / "draft")], capture_output=True, text=True, timeout=0.8)
        except subprocess.TimeoutExpired:
            self.fail("finite compiler must reject a FIFO before reading it")
        self.assertEqual(result.returncode, 2)
        self.assertIn("regular", result.stderr)

    def test_resume_rejects_deadline_mutation_against_original_run_journal(self):
        bundle, runs = self.bundle(), self.root / "runs"
        commission.run_bundle(bundle, runs, ROOT)
        path = runs / "run.json"
        run = json.loads(path.read_text())
        for key in ("started_wall", "deadline_wall", "deadline_monotonic"):
            run[key] += 86400
        path.write_text(json.dumps(run))
        with self.assertRaisesRegex(ValueError, "run.*digest|original.*run|journal"):
            commission.run_bundle(bundle, runs, ROOT, resume=True)

    def test_resume_rejects_symlinked_evidence_directory_before_writing_outside(self):
        bundle, runs = self.bundle(), self.root / "runs"
        commission.run_bundle(bundle, runs, ROOT)
        outside = self.root / "outside-summaries"
        (runs / "summaries").rename(outside)
        (runs / "summaries").symlink_to(outside, target_is_directory=True)
        before = sorted(p.name for p in outside.iterdir())
        with self.assertRaisesRegex(ValueError, "symlink|linked|evidence"):
            commission.run_bundle(bundle, runs, ROOT, resume=True)
        self.assertEqual(sorted(p.name for p in outside.iterdir()), before)

    def test_replay_rejects_linked_receipt_and_resume_rejects_linked_lock(self):
        bundle, runs = self.bundle(), self.root / "runs"
        commission.run_bundle(bundle, runs, ROOT)
        receipt = runs / "receipts" / "t-source.json"
        outside = self.root / "outside-receipt.json"
        receipt.rename(outside)
        receipt.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "symlink|linked|evidence"):
            commission.replay_run(bundle, runs, ROOT)
        receipt.unlink()
        outside.rename(receipt)
        lock = runs / "lock"
        lock.unlink()
        lock.symlink_to(receipt)
        with self.assertRaisesRegex(ValueError, "symlink|linked|evidence"):
            commission.run_bundle(bundle, runs, ROOT, resume=True)

    def test_svg_escapes_reviewed_titles_while_preserving_original_json_text(self):
        plan = self.plan()
        plan["title"] = "<quoted> & Ω " + chr(0xFFFF)
        bundle = self.bundle(plan)
        try:
            ET.fromstring((bundle / "machine.svg").read_bytes())
        except ET.ParseError as error:
            self.fail("standalone SVG must remain valid for accepted UTF-8 titles: " + str(error))
        self.assertEqual(json.loads((bundle / "machine.json").read_text())["title"], plan["title"])

    def test_cli_draft_compile_validate_and_replay_work_without_optional_packages(self):
        source, plan = self.root / "input.txt", self.root / "plan.json"
        source.write_bytes(self.source)
        plan.write_text(json.dumps(self.plan()))
        for arguments in (
            ["draft", "--source", str(source), "--out", str(self.root / "draft")],
            ["compile", "--source", str(source), "--plan", str(plan), "--out", str(self.root / "cli-bundle")],
            ["validate", "--bundle", str(self.root / "cli-bundle")],
            ["replay", "--bundle", str(self.root / "cli-bundle")],
        ):
            completed = subprocess.run([sys.executable, "-B", str(MODULE), *arguments], text=True, capture_output=True, timeout=10)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIsInstance(json.loads(completed.stdout), dict)


if __name__ == "__main__":
    unittest.main()
