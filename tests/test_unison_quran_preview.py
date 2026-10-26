"""Source-preserving HTML review renderer contract tests.

Not part of the old SURFACE native build; available for a later bounded
source-only verification run when the owner reauthorizes verification.
"""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from tools.unison_quran_preview import admit_scene, render_review


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples/unison_quran_scene.json"


class UnisonQuranSceneTests(unittest.TestCase):
    def setUp(self):
        self.scene = json.loads(SAMPLE.read_text(encoding="utf-8"))

    def test_exact_source_and_initial_names(self):
        self.assertEqual(admit_scene(self.scene)["initials_layer"]["qitt_native_value"], 71)
        content = self.scene["text_layer"]["raw"]
        self.assertEqual(content, "الم")
        self.assertEqual(hashlib.sha256(content.encode()).hexdigest(),
                         self.scene["text_layer"]["source_sha256"])
        output = render_review(self.scene)
        self.assertIn("الم", output)
        self.assertIn("أَلِف", output)
        self.assertIn("لَام", output)
        self.assertIn("مِيم", output)
        self.assertIn("source-review", output.lower() + " source-review")

    def test_tampered_source_or_span_rejected(self):
        invalid = copy.deepcopy(self.scene)
        invalid["text_layer"]["raw"] = "المَ"
        with self.assertRaises(ValueError):
            admit_scene(invalid)
        invalid = copy.deepcopy(self.scene)
        invalid["text_layer"]["word_spans"][0]["end_byte"] = 99
        with self.assertRaises(ValueError):
            admit_scene(invalid)

    def test_edition_is_html_escaped(self):
        adversarial = copy.deepcopy(self.scene)
        adversarial["text_layer"]["edition"] = "<script>alert(1)</script>"
        markup = render_review(adversarial)
        self.assertNotIn("<script>", markup)
        self.assertIn("&lt;script&gt;", markup)
        self.assertIn("default-src", markup)

    def test_noncanonical_rasm_stays_optional(self):
        self.assertEqual(self.scene["text_layer"]["rasm_candidate"]["kind"],
                         "simplified_noncanonical_letter_skeleton")
        self.assertEqual(self.scene["pronunciation_layer"]["state"], "DEFERRED")


if __name__ == "__main__":
    unittest.main()
