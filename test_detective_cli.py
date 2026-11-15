"""End-to-end command-line tests exercising persistent player progress."""
from pathlib import Path
import tempfile
import unittest

from casebook import CaseFile
from detective_cli import run


class DetectiveCliTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "case.json"
        self.options = ["--save", str(self.path)]

    def execute(self, *args):
        return run([*self.options, *args])

    def new_case(self):
        code, message = self.execute("new")
        self.assertEqual(code, 0, message)

    def collect_required(self):
        for clue, location in (
            ("camera", "alley"),
            ("badge", "alley"),
            ("door", "lab"),
            ("logs", "office"),
        ):
            code, message = self.execute("inspect", clue, location)
            self.assertEqual(code, 0, message)

    def test_new_case_creates_save(self):
        self.new_case()
        self.assertTrue(self.path.exists())
        self.assertEqual(CaseFile.load(self.path).progress()["found"], 0)

    def test_new_case_refuses_to_overwrite(self):
        self.new_case()
        code, message = self.execute("new")
        self.assertEqual(code, 2)
        self.assertIn("already exists", message)

    def test_status_is_json(self):
        self.new_case()
        code, message = self.execute("status")
        self.assertEqual(code, 0)
        self.assertIn('"found": 0', message)
        self.assertNotIn("technician", message)

    def test_initial_locations(self):
        self.new_case()
        code, message = self.execute("locations")
        self.assertEqual(code, 0)
        self.assertEqual(message, "alley, lab")

    def test_hint_does_not_reveal_culprit(self):
        self.new_case()
        code, message = self.execute("hint")
        self.assertEqual(code, 0)
        self.assertIn("camera", message)
        self.assertNotIn("technician", message)

    def test_inspect_persists_across_commands(self):
        self.new_case()
        code, message = self.execute("inspect", "camera", "alley")
        self.assertEqual(code, 0)
        self.assertIn("Discovered camera", message)
        self.assertEqual(CaseFile.load(self.path).progress()["found"], 1)

    def test_locked_clue_is_rejected(self):
        self.new_case()
        code, message = self.execute("inspect", "logs", "office")
        self.assertEqual(code, 2)
        self.assertIn("unavailable", message)
        self.assertEqual(CaseFile.load(self.path).progress()["found"], 0)

    def test_missing_inspect_arguments(self):
        self.new_case()
        self.assertEqual(self.execute("inspect")[0], 2)
        self.assertEqual(self.execute("inspect", "badge")[0], 2)

    def test_missing_accusation_argument(self):
        self.new_case()
        self.assertEqual(self.execute("accuse")[0], 2)

    def test_unknown_suspect_is_rejected(self):
        self.new_case()
        code, message = self.execute("accuse", "unknown")
        self.assertEqual(code, 2)
        self.assertIn("Unknown suspect", message)

    def test_incomplete_accusation_does_not_change_save(self):
        self.new_case()
        code, message = self.execute("accuse", "technician")
        self.assertEqual(code, 0)
        self.assertIn("required evidence", message)
        self.assertEqual(CaseFile.load(self.path).attempts, [])

    def test_suspect_exoneration_is_displayed(self):
        self.new_case()
        self.execute("inspect", "door", "lab")
        self.execute("inspect", "fingerprint", "lab")
        code, message = self.execute("suspects")
        self.assertEqual(code, 0)
        self.assertIn("executive", message)
        self.assertIn("exonerated by fingerprint", message)

    def test_full_gameplay_roundtrip(self):
        self.new_case()
        self.collect_required()
        code, message = self.execute("accuse", "guard")
        self.assertEqual(code, 0)
        self.assertIn("incorrect", message)
        code, message = self.execute("accuse", "technician")
        self.assertEqual(code, 0)
        self.assertIn("solved", message)
        restored = CaseFile.load(self.path)
        self.assertTrue(restored.closed)
        self.assertEqual(restored.attempts, ["guard", "technician"])

    def test_cannot_inspect_after_solving(self):
        self.new_case()
        self.collect_required()
        self.execute("accuse", "technician")
        code, message = self.execute("inspect", "fingerprint", "lab")
        self.assertEqual(code, 2)
        self.assertIn("closed", message)

    def test_missing_save_reports_error(self):
        code, message = self.execute("status")
        self.assertEqual(code, 2)
        self.assertIn("Error:", message)

    def test_invalid_save_reports_error(self):
        self.path.write_text("not json", encoding="utf-8")
        code, message = self.execute("status")
        self.assertEqual(code, 2)
        self.assertIn("invalid case save", message)


if __name__ == "__main__":
    unittest.main()
