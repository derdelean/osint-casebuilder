import unittest

from osint_casebuilder.modules.confidence_scorer import score_profile


class TestScoreProfile(unittest.TestCase):
    def test_none_profile_returns_zero(self):
        self.assertEqual(score_profile(None, fullname="john"), 0.0)

    def test_empty_profile_returns_zero(self):
        self.assertEqual(score_profile({}, fullname="john"), 0.0)

    def test_no_matching_fields_returns_low_score(self):
        profile = {
            "fullname": "Jane Smith",
            "location": "Berlin",
            "bio": "hello world",
            "website": "foo.com",
            "followers": 5,
        }
        result = score_profile(
            profile,
            fullname="zzz",
            location="qqq",
            keywords=["xyz"],
            domain="bar.org",
        )
        self.assertEqual(result, 0.0)

    def test_fully_matching_profile_returns_maximum(self):
        # total starts at 1 (division-by-zero guard), so 5 matching fields
        # give score=5, total=6 -> round(5/6, 2) == 0.83 (the achievable max).
        profile = {
            "fullname": "John Doe",
            "location": "New York",
            "bio": "osint and python expert",
            "website": "https://example.com",
            "followers": 150,
        }
        result = score_profile(
            profile,
            fullname="john",
            location="york",
            keywords=["osint", "python"],
            domain="example.com",
        )
        self.assertEqual(result, 0.83)

    def test_keywords_partial_match_contributes_fraction(self):
        # 1 of 2 keywords matches -> score = 0.5, total = 2 -> round(0.5/2, 2) == 0.25.
        profile = {"bio": "osint expert"}
        result = score_profile(profile, keywords=["osint", "python"])
        self.assertEqual(result, 0.25)

    def test_followers_at_threshold_adds_to_score(self):
        # followers >= 100 -> score = 1, total = 2 -> 0.5.
        self.assertEqual(score_profile({"followers": 100}), 0.5)

    def test_followers_below_threshold_does_not_add(self):
        # followers < 100 -> score = 0, total = 2 -> 0.0.
        self.assertEqual(score_profile({"followers": 99}), 0.0)


if __name__ == "__main__":
    unittest.main()
