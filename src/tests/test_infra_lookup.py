import asyncio
import os
import unittest
from unittest import mock

try:
    from osint_casebuilder.modules.infra_lookup import (
        _extract_subdomains, _map_shodan, _map_censys,
        run_shodan_domain_async, run_censys_hosts_async)
    HAS_INFRA = True
except ImportError:
    HAS_INFRA = False


@unittest.skipUnless(HAS_INFRA, "infra_lookup deps not installed")
class TestExtractSubdomains(unittest.TestCase):
    DATA = [
        {"name_value": "www.example.com\nexample.com", "common_name": "example.com"},
        {"name_value": "*.api.example.com", "common_name": "api.example.com"},
        {"name_value": "mail.example.com", "common_name": "mail.other.com"},
    ]

    def test_extracts_and_dedupes(self):
        subs = _extract_subdomains(self.DATA, "example.com")
        self.assertEqual(subs, ["api.example.com", "example.com",
                                "mail.example.com", "www.example.com"])

    def test_strips_wildcard(self):
        self.assertIn("api.example.com", _extract_subdomains(self.DATA, "example.com"))
        self.assertNotIn("*.api.example.com", _extract_subdomains(self.DATA, "example.com"))

    def test_excludes_other_domains(self):
        subs = _extract_subdomains(self.DATA, "example.com")
        self.assertNotIn("mail.other.com", subs)

    def test_empty(self):
        self.assertEqual(_extract_subdomains([], "example.com"), [])


@unittest.skipUnless(HAS_INFRA, "infra_lookup deps not installed")
class TestShodanCensysMappers(unittest.TestCase):
    def test_map_shodan(self):
        data = {"subdomains": ["www", "mail"],
                "data": [{"subdomain": "www", "type": "A", "value": "1.2.3.4", "ports": [80, 443]}]}
        out = _map_shodan(data, "example.com")
        domains = [f["value"] for f in out if f["type"] == "domain"]
        hosts = [f for f in out if f["type"] == "host"]
        self.assertIn("www.example.com", domains)
        self.assertIn("mail.example.com", domains)
        self.assertEqual(hosts[0]["value"], "1.2.3.4")
        self.assertEqual(hosts[0]["meta"]["ports"], [80, 443])

    def test_map_censys(self):
        hits = [{"ip": "9.9.9.9", "services": [{"port": 443, "service_name": "HTTP"},
                                               {"port": 22, "service_name": "SSH"}]}]
        out = _map_censys(hits, "example.com")
        self.assertEqual(out[0]["type"], "host")
        self.assertEqual(out[0]["value"], "9.9.9.9")
        self.assertEqual(out[0]["meta"]["ports"], [443, 22])
        self.assertEqual(out[0]["meta"]["services"], ["HTTP", "SSH"])

    def test_shodan_no_key_skips(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(asyncio.run(run_shodan_domain_async("example.com")), [])

    def test_censys_no_key_skips(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(asyncio.run(run_censys_hosts_async("example.com")), [])


if __name__ == "__main__":
    unittest.main()
