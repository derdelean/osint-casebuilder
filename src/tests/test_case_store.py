import os
import tempfile
import unittest

from osint_casebuilder.modules.case_store import save_case, list_cases, load_case

SEED = {"username": "torvalds", "fullname": "Linus Torvalds"}
FINDINGS = [
    {"type": "username", "value": "torvalds", "platform": "GitHub", "score": 0.75,
     "meta": {"fullname": "Linus Torvalds"}},
    {"type": "email", "value": "linus@kernel.org", "platform": "Email/MX", "meta": {}},
]
SUMMARY = {"distinct_entities": 3, "clusters": 1, "corroborated": []}


class TestCaseStore(unittest.TestCase):
    def setUp(self):
        fd, self.db = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.remove(self.db)  # let the store create it fresh

    def tearDown(self):
        if os.path.exists(self.db):
            os.remove(self.db)

    def test_save_returns_id(self):
        cid = save_case(SEED, FINDINGS, SUMMARY, self.db)
        self.assertIsInstance(cid, int)
        self.assertGreaterEqual(cid, 1)

    def test_list_after_save(self):
        save_case(SEED, FINDINGS, SUMMARY, self.db)
        cases = list_cases(self.db)
        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0]["n_findings"], 2)
        self.assertEqual(cases[0]["seed"]["username"], "torvalds")

    def test_round_trip(self):
        cid = save_case(SEED, FINDINGS, SUMMARY, self.db)
        case = load_case(cid, self.db)
        self.assertEqual(case["id"], cid)
        self.assertEqual(case["seed"], SEED)
        self.assertEqual(len(case["findings"]), 2)
        self.assertEqual(case["findings"][0]["platform"], "GitHub")
        self.assertEqual(case["summary"]["distinct_entities"], 3)

    def test_load_missing_returns_none(self):
        self.assertIsNone(load_case(999, self.db))

    def test_ids_increment(self):
        a = save_case(SEED, FINDINGS, SUMMARY, self.db)
        b = save_case(SEED, FINDINGS, SUMMARY, self.db)
        self.assertEqual(b, a + 1)
        self.assertEqual(len(list_cases(self.db)), 2)


if __name__ == "__main__":
    unittest.main()
