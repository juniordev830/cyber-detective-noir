"""Tests for graph integrity, hint reachability, undo and snapshot validation."""
import unittest

from investigation import Clue, Investigation, demo_case


class GraphValidationTests(unittest.TestCase):
    def test_reject_empty_identifier(self):
        with self.assertRaises(ValueError):
            Clue("", "description", "room")

    def test_reject_empty_description(self):
        with self.assertRaises(ValueError):
            Clue("id", " ", "room")

    def test_reject_empty_location(self):
        with self.assertRaises(ValueError):
            Clue("id", "description", "")

    def test_reject_overlong_identifier(self):
        with self.assertRaises(ValueError):
            Clue("x" * 81, "description", "room")

    def test_reject_self_dependency(self):
        with self.assertRaises(ValueError):
            Clue("id", "description", "room", ("id",))

    def test_reject_duplicate_dependency(self):
        with self.assertRaises(ValueError):
            Clue("id", "description", "room", ("a", "a"))

    def test_reject_non_tuple_dependency(self):
        with self.assertRaises(ValueError):
            Clue("id", "description", "room", ["a"])

    def test_reject_non_string_dependency(self):
        with self.assertRaises(ValueError):
            Clue("id", "description", "room", ([],))

    def test_reject_missing_dependency(self):
        clue = Clue("a", "description", "room", ("missing",))
        with self.assertRaisesRegex(ValueError, "unknown prerequisite"):
            Investigation({"a": clue})

    def test_reject_two_clue_cycle(self):
        a = Clue("a", "description", "room", ("b",))
        b = Clue("b", "description", "room", ("a",))
        with self.assertRaisesRegex(ValueError, "circular"):
            Investigation({"a": a, "b": b})

    def test_reject_three_clue_cycle(self):
        clues = {
            "a": Clue("a", "description", "room", ("c",)),
            "b": Clue("b", "description", "room", ("a",)),
            "c": Clue("c", "description", "room", ("b",)),
        }
        with self.assertRaisesRegex(ValueError, "circular"):
            Investigation(clues)

    def test_reject_mismatched_key(self):
        with self.assertRaises(ValueError):
            Investigation({"wrong": Clue("right", "description", "room")})

    def test_reject_unknown_discovery(self):
        with self.assertRaises(ValueError):
            Investigation({"a": Clue("a", "description", "room")}, {"unknown"})

    def test_reject_discovered_without_prerequisites(self):
        clues = {
            "a": Clue("a", "description", "room"),
            "b": Clue("b", "description", "room", ("a",)),
        }
        with self.assertRaisesRegex(ValueError, "missing prerequisites"):
            Investigation(clues, {"b"})

    def test_accept_consistent_discovery(self):
        clues = {
            "a": Clue("a", "description", "room"),
            "b": Clue("b", "description", "room", ("a",)),
        }
        case = Investigation(clues, {"a", "b"})
        self.assertEqual(case.progress(), (2, 2))

    def test_empty_case_is_valid(self):
        case = Investigation({})
        self.assertEqual(case.progress(), (0, 0))
        self.assertIsNone(case.hint())

    def test_reject_more_than_five_hundred_clues(self):
        clues = {
            str(i): Clue(str(i), "description", "room")
            for i in range(501)
        }
        with self.assertRaises(ValueError):
            Investigation(clues)


class InvestigationProgressTests(unittest.TestCase):
    def setUp(self):
        self.case = demo_case()

    def test_initial_locations(self):
        self.assertEqual(self.case.available_locations(), ["alley"])

    def test_hint_follows_available_clues(self):
        self.assertEqual(self.case.hint().identifier, "camera")
        self.case.inspect("camera", "alley")
        self.assertEqual(self.case.hint().identifier, "badge")
        self.case.inspect("badge", "alley")
        self.assertEqual(self.case.hint().identifier, "terminal")

    def test_hint_after_completion(self):
        self.case.inspect("camera", "alley")
        self.case.inspect("badge", "alley")
        self.case.inspect("terminal", "office")
        self.assertIsNone(self.case.hint())

    def test_blocked_clue_has_missing_prerequisite(self):
        self.assertEqual(self.case.blocked(), {"terminal": ("badge",)})
        self.case.inspect("badge", "alley")
        self.assertEqual(self.case.blocked(), {})

    def test_retract_dependency_cascade(self):
        self.case.inspect("badge", "alley")
        self.case.inspect("terminal", "office")
        self.assertEqual(self.case.retract("badge"), {"badge", "terminal"})
        self.assertEqual(self.case.discovered, set())
        self.assertEqual(self.case.blocked(), {"terminal": ("badge",)})

    def test_retract_independent_clue(self):
        self.case.inspect("camera", "alley")
        self.case.inspect("badge", "alley")
        self.case.inspect("terminal", "office")
        self.assertEqual(self.case.retract("camera"), {"camera"})
        self.assertEqual(self.case.discovered, {"badge", "terminal"})

    def test_retract_unknown_clue(self):
        with self.assertRaises(KeyError):
            self.case.retract("missing")

    def test_retract_undiscovered_clue(self):
        with self.assertRaises(ValueError):
            self.case.retract("badge")

    def test_retract_allows_reinspection(self):
        self.case.inspect("camera", "alley")
        self.case.retract("camera")
        self.assertEqual(self.case.inspect("camera", "alley").identifier, "camera")

    def test_required_clues_must_be_known(self):
        with self.assertRaises(ValueError):
            self.case.solved({"unknown"})

    def test_empty_required_set_is_satisfied(self):
        self.assertTrue(self.case.solved(set()))

    def test_serialization_roundtrip(self):
        self.case.inspect("badge", "alley")
        restored = Investigation.from_dict(self.case.to_dict())
        self.assertEqual(restored.to_dict(), self.case.to_dict())
        self.assertEqual(restored.hint().identifier, "camera")


class SnapshotValidationTests(unittest.TestCase):
    def setUp(self):
        self.payload = demo_case().to_dict()

    def test_reject_wrong_version(self):
        self.payload["version"] = 42
        with self.assertRaises(ValueError):
            Investigation.from_dict(self.payload)

    def test_reject_missing_clues(self):
        self.payload.pop("clues")
        with self.assertRaises(ValueError):
            Investigation.from_dict(self.payload)

    def test_reject_missing_discovered(self):
        self.payload.pop("discovered")
        with self.assertRaises(ValueError):
            Investigation.from_dict(self.payload)

    def test_reject_duplicate_clue(self):
        self.payload["clues"].append(self.payload["clues"][0].copy())
        with self.assertRaises(ValueError):
            Investigation.from_dict(self.payload)

    def test_reject_duplicate_discovery(self):
        self.payload["discovered"] = ["badge", "badge"]
        with self.assertRaises(ValueError):
            Investigation.from_dict(self.payload)

    def test_reject_unhashable_discovery(self):
        self.payload["discovered"] = [[]]
        with self.assertRaises(ValueError):
            Investigation.from_dict(self.payload)

    def test_reject_non_list_prerequisites(self):
        self.payload["clues"][0]["unlocks"] = "badge"
        with self.assertRaises(ValueError):
            Investigation.from_dict(self.payload)

    def test_reject_malformed_clue(self):
        self.payload["clues"][0] = "camera"
        with self.assertRaises(ValueError):
            Investigation.from_dict(self.payload)

    def test_reject_discovered_without_dependency(self):
        self.payload["discovered"] = ["terminal"]
        with self.assertRaises(ValueError):
            Investigation.from_dict(self.payload)

    def test_reject_unknown_discovery(self):
        self.payload["discovered"] = ["nonexistent"]
        with self.assertRaises(ValueError):
            Investigation.from_dict(self.payload)

    def test_reject_oversized_snapshot(self):
        self.payload["clues"] = self.payload["clues"] * 200
        with self.assertRaises(ValueError):
            Investigation.from_dict(self.payload)


if __name__ == "__main__":
    unittest.main()
