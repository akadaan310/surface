"""Fault injection exercises real children; no simulated successful watchdogs."""
import importlib.util
import json
import pathlib
import sys
import tempfile
import threading
import time
import unittest

MODULE = pathlib.Path(__file__).parents[1] / "tools" / "supervise.py"
if MODULE.exists():
    spec = importlib.util.spec_from_file_location("surface_supervise", MODULE)
    supervisor = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = supervisor
    spec.loader.exec_module(supervisor)
else:
    supervisor = None


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(supervisor, "process supervisor must be implemented")
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        self.runner = supervisor.Supervisor(self.root, poll_interval=0.01, terminate_grace=0.03)

    def tearDown(self):
        if hasattr(self, "temp"):
            self.temp.cleanup()

    def task(self, code, **kwargs):
        return supervisor.TaskSpec(task_id="fault-test", command=(sys.executable, "-u", "-c", code), **kwargs)

    def test_hung_child_is_killed_at_fixed_deadline(self):
        start = time.monotonic()
        result = self.runner.run(self.task("import time; time.sleep(30)", timeout=0.16, semantic_timeout=0.14))
        self.assertEqual(result.status, "failed")
        self.assertIn(result.reason, ("no-semantic-progress", "deadline"))
        self.assertEqual(result.attempts, 1)
        self.assertLess(time.monotonic() - start, 1.0)
        state = json.loads((self.root / "fault-test" / "resume.json").read_text())
        self.assertEqual(state["status"], "failed")

    def test_heartbeats_do_not_extend_semantic_or_hard_deadline(self):
        code = "import json,os,time\ne=int(os.environ['SURFACE_TASK_EPOCH'])\nwhile True:\n print(json.dumps({'type':'heartbeat','epoch':e}),flush=True); time.sleep(.01)"
        result = self.runner.run(self.task(code, timeout=0.4, semantic_timeout=0.12))
        self.assertEqual(result.reason, "no-semantic-progress")
        self.assertEqual(result.attempts, 1)
        self.assertLess(result.elapsed, 0.35)

    def test_only_one_classified_retry_is_allowed(self):
        result = self.runner.run(self.task("raise SystemExit(75)", timeout=1, semantic_timeout=0.5))
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.attempts, 2)
        journal = [json.loads(line) for line in (self.root / "fault-test" / "journal.jsonl").read_text().splitlines()]
        self.assertEqual(sum(item["event"] == "intent" for item in journal), 2)
        self.assertEqual(sum(item["event"] == "retry" for item in journal), 1)

    def test_unclassified_exit_never_retries(self):
        result = self.runner.run(self.task("raise SystemExit(2)", timeout=1, semantic_timeout=0.5))
        self.assertEqual(result.attempts, 1)
        self.assertEqual(result.returncode, 2)

    def test_progress_can_refresh_semantics_but_never_the_absolute_deadline(self):
        code = "import json,os,time\ne=int(os.environ['SURFACE_TASK_EPOCH'])\nfor n in range(100):\n print(json.dumps({'type':'progress','epoch':e,'milestone':str(n)}),flush=True); time.sleep(.015)"
        result = self.runner.run(self.task(code, timeout=0.17, semantic_timeout=0.08, milestones=tuple(str(n) for n in range(100))))
        self.assertEqual(result.reason, "deadline")
        self.assertLess(result.elapsed, 0.4)

    def test_duplicate_or_wrong_epoch_progress_does_not_extend_semantics(self):
        code = "import json,os,time\ne=int(os.environ['SURFACE_TASK_EPOCH'])\nprint(json.dumps({'type':'progress','epoch':e,'milestone':'one'}),flush=True)\nwhile True:\n print(json.dumps({'type':'progress','epoch':e,'milestone':'one'}),flush=True); print(json.dumps({'type':'progress','epoch':e-1,'milestone':'two'}),flush=True); time.sleep(.01)"
        result = self.runner.run(self.task(code, timeout=0.4, semantic_timeout=0.1, milestones=("one", "two")))
        self.assertEqual(result.reason, "no-semantic-progress")
        journal = [json.loads(line) for line in (self.root / "fault-test" / "journal.jsonl").read_text().splitlines()]
        self.assertEqual([item["milestone"] for item in journal if item["event"] == "progress"], ["one"])

    def test_descendants_ignoring_terminate_are_killed_with_the_process_group(self):
        marker = self.root / "escaped.txt"
        child = f"import signal,time,pathlib; signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(.35); pathlib.Path({str(marker)!r}).write_text('escaped')"
        code = f"import subprocess,sys,time; subprocess.Popen([sys.executable,'-c',{child!r}]); time.sleep(30)"
        result = self.runner.run(self.task(code, timeout=0.2, semantic_timeout=0.15))
        self.assertEqual(result.status, "failed")
        time.sleep(0.3)
        self.assertFalse(marker.exists(), "termination must include descendants that ignored SIGTERM")

    def test_late_publication_after_deadline_is_fenced(self):
        class SlowPublication(supervisor.Supervisor):
            def _publish(self, *args, **kwargs):
                time.sleep(0.15)
                return super()._publish(*args, **kwargs)
        runner = SlowPublication(self.root, poll_interval=0.01, terminate_grace=0.03)
        code = "import os,pathlib\n(pathlib.Path(os.environ['SURFACE_TASK_STAGE'])/'result.txt').write_text('late')"
        result = runner.run(self.task(code, timeout=0.1, semantic_timeout=0.1, outputs=("result.txt",)))
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.reason, "deadline")
        self.assertFalse((self.root / "fault-test" / "current.json").exists())

    def test_retry_shares_the_original_deadline(self):
        code = "import os,time\ntime.sleep(.08)\nif os.environ['SURFACE_TASK_EPOCH']=='1': raise SystemExit(75)\ntime.sleep(30)"
        result = self.runner.run(self.task(code, timeout=0.14, semantic_timeout=0.12))
        self.assertEqual(result.attempts, 2)
        self.assertEqual(result.reason, "deadline")
        self.assertLess(result.elapsed, 0.3)

    def test_reserved_manifest_cannot_be_declared_as_user_output(self):
        with self.assertRaises(ValueError):
            self.task("pass", outputs=("manifest.json",))

    def test_journal_failure_after_spawn_does_not_leave_an_unmanaged_child(self):
        class BrokenJournal(supervisor.Supervisor):
            def _record(self, directory, epoch, event, **fields):
                if event == "spawned":
                    raise OSError("injected durable journal failure")
                return super()._record(directory, epoch, event, **fields)
        marker = self.root / "unmanaged.txt"
        code = f"import time,pathlib; time.sleep(.15); pathlib.Path({str(marker)!r}).write_text('unmanaged')"
        runner = BrokenJournal(self.root, poll_interval=0.01, terminate_grace=0.03)
        with self.assertRaises(OSError):
            runner.run(self.task(code, timeout=0.5, semantic_timeout=0.4))
        time.sleep(0.2)
        self.assertFalse(marker.exists(), "journal failure cannot detach the launched child")

    def test_successful_leader_cannot_leave_background_descendants(self):
        marker = self.root / "background.txt"
        child = f"import signal,time,pathlib; signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(.15); pathlib.Path({str(marker)!r}).write_text('background')"
        code = f"import subprocess,sys; subprocess.Popen([sys.executable,'-c',{child!r}])"
        result = self.runner.run(self.task(code, timeout=0.5, semantic_timeout=0.4))
        self.assertEqual(result.status, "succeeded")
        time.sleep(0.2)
        self.assertFalse(marker.exists(), "a task owns and bounds its entire original process group")

    def test_success_publishes_only_declared_outputs_with_digest(self):
        code = "import os,pathlib\np=pathlib.Path(os.environ['SURFACE_TASK_STAGE']); (p/'result.txt').write_text('verified payload')"
        result = self.runner.run(self.task(code, timeout=1, semantic_timeout=0.5, outputs=("result.txt",)))
        self.assertEqual(result.status, "succeeded")
        manifest = json.loads((self.root / "fault-test" / "current.json").read_text())
        self.assertEqual(manifest["epoch"], result.epoch)
        artifact = manifest["outputs"][0]
        self.assertEqual((self.root / "fault-test" / artifact["path"]).read_text(), "verified payload")
        self.assertEqual(artifact["sha256"], "3aac0a1146ffe55bac7c05f61401fb1e7e4e6a94110b91585c646fe8cf745f28")

    def test_superseded_epoch_cannot_publish_late_output(self):
        old = self.task("import os,pathlib,time\np=pathlib.Path(os.environ['SURFACE_TASK_STAGE']); (p/'result.txt').write_text('old'); time.sleep(.4)", timeout=1, semantic_timeout=0.8, outputs=("result.txt",))
        results = []
        thread = threading.Thread(target=lambda: results.append(self.runner.run(old)))
        thread.start()
        marker = self.root / "fault-test" / "resume.json"
        until = time.monotonic() + 1
        while not marker.exists() and time.monotonic() < until:
            time.sleep(0.005)
        newer = self.task("import os,pathlib\n(pathlib.Path(os.environ['SURFACE_TASK_STAGE'])/'result.txt').write_text('new')", timeout=1, semantic_timeout=0.8, outputs=("result.txt",))
        fresh = supervisor.Supervisor(self.root, poll_interval=0.01, terminate_grace=0.03).run(newer)
        thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(fresh.status, "succeeded")
        self.assertEqual(results[0].status, "superseded")
        manifest = json.loads((self.root / "fault-test" / "current.json").read_text())
        self.assertEqual(manifest["epoch"], fresh.epoch)
        self.assertEqual((self.root / "fault-test" / manifest["outputs"][0]["path"]).read_text(), "new")


if __name__ == "__main__":
    unittest.main()
