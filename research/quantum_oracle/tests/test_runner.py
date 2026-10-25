import tempfile
import json
import unittest
from pathlib import Path
from research.quantum_oracle import run


class RunnerTests(unittest.TestCase):
    def test_empty_forged_receipt_cannot_claim_executed_tests(self):
        from research.quantum_oracle.discovery import run_affine_cycle
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            committed = root / "scientific-reference/committed/1"
            committed.mkdir(parents=True)
            (root / "result.json").write_text(json.dumps({"status": "SUCCEEDED", "epoch": 1}))
            (committed / "verification.json").write_text(json.dumps({"source_files": {}, "outputs": {}, "environment": {}}))
            (committed / "discovery.json").write_text(json.dumps(run_affine_cycle()))
            with self.assertRaises(ValueError):
                run.replay_run(root)

    def test_file_manifest_rejects_tamper_and_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "result.json").write_text('{"checked":16}')
            pins = run.pin_files(root, ("result.json",))
            self.assertTrue(run.verify_files(root, pins))
            (root / "result.json").write_text('{"checked":17}')
            with self.assertRaises(ValueError):
                run.verify_files(root, pins)
            with self.assertRaises(ValueError):
                run.pin_files(root, ("../outside",))

    def test_refuses_linked_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "real").write_text("source")
            (root / "link").symlink_to(root / "real")
            with self.assertRaises(ValueError):
                run.pin_files(root, ("link",))


if __name__ == "__main__":
    unittest.main()
