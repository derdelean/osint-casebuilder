import asyncio
import os
import unittest
from unittest import mock

try:
    from osint_casebuilder.modules.breach_lookup import _map_breaches, run_hibp_lookup_async
    HAS_BREACH = True
except ImportError:
    HAS_BREACH = False


@unittest.skipUnless(HAS_BREACH, "breach_lookup deps not installed")
class TestBreachLookup(unittest.TestCase):
    def test_map_breaches(self):
        raw = [{"Name": "Adobe", "Domain": "adobe.com", "BreachDate": "2013-10-04",
                "PwnCount": 152445165, "DataClasses": ["Emails", "Passwords"]}]
        f = _map_breaches(raw, "a@b.com")[0]
        self.assertEqual(f["type"], "breach")
        self.assertEqual(f["value"], "a@b.com")
        self.assertEqual(f["platform"], "HIBP:Adobe")
        self.assertEqual(f["meta"]["domain"], "adobe.com")
        self.assertEqual(f["meta"]["data_classes"], ["Emails", "Passwords"])

    def test_no_api_key_skips(self):
        # with no HIBP_API_KEY in the environment, the lookup must skip (no network)
        with mock.patch.dict(os.environ, {}, clear=True):
            result = asyncio.run(run_hibp_lookup_async("a@b.com"))
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
