import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from case_report import summary, load_case
from investigation import demo_case


class CaseReportTests(unittest.TestCase):
    def test_clue_progress_and_reachable(self):
        case = demo_case()
        report = summary(case)
        self.assertEqual(report["collected"], 0)
        self.assertEqual(report["available_clues"], ["badge", "camera"])
        self.assertEqual(report["blocked_prerequisites"], {"terminal": ["badge"]})
        self.assertFalse(report["solved_all"])

        case.inspect("badge", "alley")
        report = summary(case)
        self.assertIn("terminal", report["available_clues"])
        self.assertEqual(report["remaining"], 2)

    def test_report_does_not_mutate_case(self):
        case = demo_case()
        original = case.to_dict()
        self.assertEqual(summary(case), summary(case))
        self.assertEqual(case.to_dict(), original)

    def test_save_load_roundtrip(self):
        case = demo_case()
        case.inspect("camera", "alley")
        with TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            path.write_text(json.dumps(case.to_dict()), encoding="utf-8")
            restored = load_case(path)
            self.assertEqual(summary(case), summary(restored))

    def test_invalid_file_is_rejected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            with self.assertRaises(ValueError):
                load_case(path)
            path.write_text("x" * 1_048_577)
            with self.assertRaises(ValueError):
                load_case(path)


if __name__ == "__main__":
    unittest.main()
