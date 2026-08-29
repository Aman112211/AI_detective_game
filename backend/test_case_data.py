import unittest

from services.case_data import discover_evidence, load_case


class DiscoverEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.case = load_case("pirate")

    def test_greeting_does_not_unlock_evidence(self):
        unlocked = discover_evidence(self.case, "hello there captin", [])
        self.assertEqual(unlocked, [])

    def test_casual_greeting_variants_do_not_unlock(self):
        messages = [
            "hello captain",
            "hi there",
            "good morning",
            "hey salty",
        ]
        for message in messages:
            with self.subTest(message=message):
                self.assertEqual(discover_evidence(self.case, message, []), [])

    def test_targeted_questions_unlock_expected_evidence(self):
        expectations = [
            ("What was found in Toby's sea chest?", "wire_tool"),
            ("Tell me about Toby's night watch schedule.", "watch_log"),
            ("What was found around the captain's porthole?", "torn_cloth"),
            ("Did anyone see a boat leaving the ship around 2am?", "fisherman_report"),
            ("What about Finch's alibi?", "dice_witnesses"),
            ("Where was Mags during the storm?", "kitchen_log"),
            ("Why was Pip near the captain's cabin?", "boatswain_account"),
        ]
        discovered = []
        for message, evidence_id in expectations:
            with self.subTest(message=message, evidence_id=evidence_id):
                unlocked = discover_evidence(self.case, message, discovered)
                self.assertIn(evidence_id, unlocked)
                discovered.extend(unlocked)

    def test_substring_words_do_not_unlock(self):
        unlocked = discover_evidence(self.case, "hello there captin", [])
        self.assertNotIn("wire_tool", unlocked)
        self.assertNotIn("watch_log", unlocked)
        self.assertNotIn("torn_cloth", unlocked)

    def test_already_discovered_evidence_is_not_returned_again(self):
        unlocked = discover_evidence(
            self.case,
            "What was found in Toby's sea chest?",
            ["wire_tool"],
        )
        self.assertEqual(unlocked, [])


if __name__ == "__main__":
    unittest.main()
