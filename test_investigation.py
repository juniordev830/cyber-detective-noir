import unittest
from investigation import demo_case


class InvestigationTests(unittest.TestCase):
    def setUp(self):
        self.case = demo_case()

    def test_initial_clues(self):
        self.assertEqual({c.identifier for c in self.case.available_at("alley")}, {"camera", "badge"})

    def test_locked_clue_requires_badge(self):
        self.assertEqual(self.case.available_at("office"), [])
        self.case.inspect("badge", "alley")
        self.assertEqual(self.case.available_at("office")[0].identifier, "terminal")

    def test_wrong_location_rejected(self):
        with self.assertRaises(ValueError):
            self.case.inspect("camera", "office")

    def test_unknown_clue_rejected(self):
        with self.assertRaises(KeyError):
            self.case.inspect("missing", "alley")

    def test_case_completion(self):
        self.assertFalse(self.case.solved({"badge", "terminal"}))
        self.case.inspect("badge", "alley")
        self.case.inspect("terminal", "office")
        self.assertTrue(self.case.solved({"badge", "terminal"}))


if __name__ == "__main__":
    unittest.main()
