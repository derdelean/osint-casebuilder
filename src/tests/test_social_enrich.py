import re
import unittest

# social_enrich is httpx-only → always importable.
from osint_casebuilder.modules.social_enrich import _reddit_finding, _hn_finding, _utc_date

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class TestUtcDate(unittest.TestCase):
    def test_epoch(self):
        self.assertEqual(_utc_date(0), "1970-01-01")

    def test_bad_inputs(self):
        self.assertIsNone(_utc_date(None))
        self.assertIsNone(_utc_date("not-a-ts"))


class TestRedditFinding(unittest.TestCase):
    def test_mapping(self):
        data = {"name": "spez", "total_karma": 1000, "link_karma": 600,
                "comment_karma": 400, "created_utc": 1118030400, "verified": True,
                "subreddit": {"public_description": "reddit ceo"}}
        f = _reddit_finding(data, "spez")
        self.assertEqual(f["platform"], "Reddit")
        self.assertEqual(f["type"], "username")
        self.assertEqual(f["meta"]["username"], "spez")
        self.assertEqual(f["meta"]["karma"], 1000)
        self.assertEqual(f["meta"]["bio"], "reddit ceo")
        self.assertRegex(f["meta"]["joined"], _DATE)


class TestHnFinding(unittest.TestCase):
    def test_mapping(self):
        data = {"id": "pg", "karma": 155000, "created": 1160418092, "about": "Paul Graham"}
        f = _hn_finding(data, "pg")
        self.assertEqual(f["platform"], "HackerNews")
        self.assertEqual(f["meta"]["username"], "pg")
        self.assertEqual(f["meta"]["karma"], 155000)
        self.assertEqual(f["meta"]["bio"], "Paul Graham")
        self.assertEqual(f["meta"]["joined"], "2006-10-09")
        self.assertIn("news.ycombinator.com", f["source"])


if __name__ == "__main__":
    unittest.main()
