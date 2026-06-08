import unittest

try:
    from osint_casebuilder.modules.phone_accounts_lookup import _map_results
    HAS_IGNORANT = True
except ImportError:
    HAS_IGNORANT = False


@unittest.skipUnless(HAS_IGNORANT, "ignorant not installed")
class TestMapResults(unittest.TestCase):
    def test_keeps_only_confirmed(self):
        raw = [
            {"name": "instagram", "exists": True, "rateLimit": False},
            {"name": "amazon", "exists": False, "rateLimit": False},
            {"name": "snapchat", "exists": True, "rateLimit": True},  # rate-limited → drop
        ]
        out = _map_results(raw, "+41791234567")
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["platform"], "ignorant:instagram")
        self.assertEqual(out[0]["type"], "phone")
        self.assertEqual(out[0]["value"], "+41791234567")
        self.assertTrue(out[0]["meta"]["registered"])

    def test_empty(self):
        self.assertEqual(_map_results([], "+41791234567"), [])


if __name__ == "__main__":
    unittest.main()
