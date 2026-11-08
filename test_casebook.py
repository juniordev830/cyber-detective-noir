"""Regression tests for case progress, deductions, save files and validation."""
import json
from pathlib import Path
import tempfile
import unittest

from casebook import CaseFile, Suspect, demo_case
from investigation import Clue, Investigation


class CaseFlowTests(unittest.TestCase):
    def setUp(self):
        self.case = demo_case()

    def collect_required(self):
        for identifier, location in (
            ("camera", "alley"), ("badge", "alley"),
            ("door", "lab"), ("logs", "office"),
        ):
            self.case.inspect(identifier, location)

    def test_initial_progress(self):
        progress = self.case.progress()
        self.assertEqual(progress["found"], 0)
        self.assertEqual(progress["total"], 6)
        self.assertEqual(progress["required_total"], 4)
        self.assertFalse(progress["ready_to_accuse"])
        self.assertFalse(progress["closed"])

    def test_initial_hint_is_reachable(self):
        self.assertEqual(self.case.hint(), {"location": "alley", "identifier": "camera"})

    def test_locations_unlock_after_prerequisites(self):
        self.assertEqual(self.case.investigation.available_locations(), ["alley", "lab"])
        self.case.inspect("camera", "alley")
        self.assertEqual(self.case.investigation.available_at("office"), [])
        self.case.inspect("badge", "alley")
        self.assertEqual(
            {clue.identifier for clue in self.case.investigation.available_at("office")},
            {"logs"},
        )

    def test_incomplete_accusation_does_not_count(self):
        self.assertEqual(self.case.accuse("technician"), "incomplete")
        self.assertEqual(self.case.attempts, [])

    def test_invalid_suspect_rejected(self):
        with self.assertRaises(KeyError):
            self.case.accuse("stranger")

    def test_correct_accusation_closes_case(self):
        self.collect_required()
        self.assertTrue(self.case.can_accuse())
        self.assertEqual(self.case.accuse("technician"), "solved")
        self.assertTrue(self.case.closed)
        self.assertFalse(self.case.can_accuse())
        self.assertIsNone(self.case.hint())

    def test_wrong_accusation_keeps_case_open(self):
        self.collect_required()
        self.assertEqual(self.case.accuse("guard"), "incorrect")
        self.assertEqual(self.case.attempts, ["guard"])
        self.assertFalse(self.case.closed)
        self.assertEqual(self.case.accuse("technician"), "solved")
        self.assertEqual(self.case.attempts, ["guard", "technician"])

    def test_closed_case_cannot_inspect(self):
        self.collect_required()
        self.case.accuse("technician")
        with self.assertRaisesRegex(ValueError, "closed"):
            self.case.inspect("fingerprint", "lab")

    def test_closed_case_cannot_accuse(self):
        self.collect_required()
        self.case.accuse("technician")
        with self.assertRaisesRegex(ValueError, "closed"):
            self.case.accuse("guard")

    def test_exonerating_clues(self):
        self.case.inspect("door", "lab")
        self.case.inspect("fingerprint", "lab")
        self.assertEqual(self.case.exonerated_suspects(), {"executive": ["fingerprint"]})
        self.assertEqual(
            {suspect.identifier for suspect in self.case.available_suspects()},
            {"guard", "technician"},
        )

    def test_exonerated_suspect_cannot_be_accused(self):
        self.collect_required()
        self.case.inspect("fingerprint", "lab")
        self.assertEqual(self.case.accuse("executive"), "exonerated")
        self.assertEqual(self.case.attempts, [])

    def test_all_exonerations_leave_culprit(self):
        self.collect_required()
        self.case.inspect("fingerprint", "lab")
        self.case.inspect("receipt", "office")
        self.assertEqual(
            [suspect.identifier for suspect in self.case.available_suspects()],
            ["technician"],
        )

    def test_progress_tracks_required_separately(self):
        self.case.inspect("door", "lab")
        self.case.inspect("fingerprint", "lab")
        progress = self.case.progress()
        self.assertEqual(progress["found"], 2)
        self.assertEqual(progress["required_found"], 1)
        self.assertFalse(progress["ready_to_accuse"])

    def test_unknown_and_wrong_location_do_not_change_progress(self):
        with self.assertRaises(KeyError):
            self.case.inspect("unknown", "lab")
        with self.assertRaises(ValueError):
            self.case.inspect("door", "alley")
        self.assertEqual(self.case.progress()["found"], 0)

    def test_repeat_inspection_does_not_count_twice(self):
        self.case.inspect("camera", "alley")
        with self.assertRaises(ValueError):
            self.case.inspect("camera", "alley")
        self.assertEqual(self.case.progress()["found"], 1)

    def test_case_serialization_roundtrip(self):
        self.collect_required()
        self.case.accuse("guard")
        restored = CaseFile.from_dict(self.case.to_dict())
        self.assertEqual(restored.to_dict(), self.case.to_dict())
        self.assertEqual(restored.accuse("technician"), "solved")

    def test_closed_case_serialization_roundtrip(self):
        self.collect_required()
        self.case.accuse("technician")
        restored = CaseFile.from_dict(self.case.to_dict())
        self.assertTrue(restored.closed)
        self.assertEqual(restored.progress()["required_found"], 4)

    def test_save_and_load_preserves_progress(self):
        self.case.inspect("camera", "alley")
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "progress.json"
            self.case.save(target)
            restored = CaseFile.load(target)
            self.assertEqual(restored.to_dict(), self.case.to_dict())
            self.assertEqual(list(Path(directory).iterdir()), [target])

    def test_overwrite_save_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "progress.json"
            self.case.save(target)
            self.case.inspect("badge", "alley")
            self.case.save(target)
            self.assertEqual(CaseFile.load(target).progress()["found"], 1)
            self.assertEqual(list(Path(directory).iterdir()), [target])

    def test_missing_directory_does_not_create_files(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "missing" / "save.json"
            with self.assertRaises(FileNotFoundError):
                self.case.save(target)
            self.assertFalse(target.exists())

    def test_invalid_json_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "invalid.json"
            target.write_text("{not json", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "JSON"):
                CaseFile.load(target)

    def test_invalid_utf8_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "invalid.json"
            target.write_bytes(b"\xff\xfe")
            with self.assertRaisesRegex(ValueError, "JSON"):
                CaseFile.load(target)

    def test_oversized_save_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "oversized.json"
            target.write_bytes(b" " * (1024 * 1024 + 1))
            with self.assertRaisesRegex(ValueError, "MiB"):
                CaseFile.load(target)


class CaseValidationTests(unittest.TestCase):
    def setUp(self):
        self.payload = demo_case().to_dict()

    def test_reject_unsupported_version(self):
        self.payload["version"] = 2
        with self.assertRaises(ValueError):
            CaseFile.from_dict(self.payload)

    def test_reject_boolean_version(self):
        self.payload["version"] = True
        with self.assertRaises(ValueError):
            CaseFile.from_dict(self.payload)

    def test_reject_missing_title(self):
        self.payload.pop("title")
        with self.assertRaises(ValueError):
            CaseFile.from_dict(self.payload)

    def test_reject_missing_suspects(self):
        self.payload.pop("suspects")
        with self.assertRaises(ValueError):
            CaseFile.from_dict(self.payload)

    def test_reject_duplicate_suspect(self):
        self.payload["suspects"].append(self.payload["suspects"][0].copy())
        with self.assertRaises(ValueError):
            CaseFile.from_dict(self.payload)

    def test_reject_unknown_culprit(self):
        self.payload["culprit"] = "unknown"
        with self.assertRaises(ValueError):
            CaseFile.from_dict(self.payload)

    def test_reject_unknown_required_clue(self):
        self.payload["required"].append("unknown")
        with self.assertRaises(ValueError):
            CaseFile.from_dict(self.payload)

    def test_reject_duplicate_required_clue(self):
        self.payload["required"].append("camera")
        with self.assertRaises(ValueError):
            CaseFile.from_dict(self.payload)

    def test_reject_unknown_exoneration(self):
        self.payload["suspects"][0]["exonerated_by"] = ["unknown"]
        with self.assertRaises(ValueError):
            CaseFile.from_dict(self.payload)

    def test_reject_culprit_exoneration(self):
        self.payload["suspects"][1]["exonerated_by"] = ["camera"]
        with self.assertRaises(ValueError):
            CaseFile.from_dict(self.payload)

    def test_reject_false_closed_state(self):
        self.payload["closed"] = True
        with self.assertRaises(ValueError):
            CaseFile.from_dict(self.payload)

    def test_reject_inconsistent_attempts(self):
        self.payload["attempts"] = ["technician"]
        with self.assertRaises(ValueError):
            CaseFile.from_dict(self.payload)

    def test_reject_unknown_attempt(self):
        self.payload["attempts"] = ["stranger"]
        with self.assertRaises(ValueError):
            CaseFile.from_dict(self.payload)

    def test_reject_closed_case_without_evidence(self):
        self.payload["attempts"] = ["technician"]
        self.payload["closed"] = True
        with self.assertRaises(ValueError):
            CaseFile.from_dict(self.payload)

    def test_reject_missing_closed_field(self):
        self.payload.pop("closed")
        with self.assertRaises(ValueError):
            CaseFile.from_dict(self.payload)

    def test_reject_non_boolean_closed_field(self):
        self.payload["closed"] = 0
        with self.assertRaises(ValueError):
            CaseFile.from_dict(self.payload)

    def test_reject_duplicate_exonerating_clue(self):
        with self.assertRaises(ValueError):
            Suspect("guard", "Security", ("camera", "camera"))

    def test_reject_invalid_suspect_name(self):
        with self.assertRaises(ValueError):
            Suspect("guard", "  ")

    def test_reject_empty_required_evidence(self):
        self.payload["required"] = []
        with self.assertRaises(ValueError):
            CaseFile.from_dict(self.payload)

    def test_reject_malformed_suspect_entry(self):
        self.payload["suspects"][0]["exonerated_by"] = "camera"
        with self.assertRaises(ValueError):
            CaseFile.from_dict(self.payload)

    def test_reject_too_many_attempts(self):
        self.payload["attempts"] = ["guard"] * 1001
        with self.assertRaises(ValueError):
            CaseFile.from_dict(self.payload)


if __name__ == "__main__":
    unittest.main()
