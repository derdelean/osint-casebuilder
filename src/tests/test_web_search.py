import unittest

try:
    from osint_casebuilder.modules import web_search
    HAS_WEB_SEARCH = True
except ImportError:
    HAS_WEB_SEARCH = False


SERP = """
<div class="result">
  <a class="result__a" href="https://ch.linkedin.com/in/denniserdelean/en">Dennis E - Cyber Security</a>
  <a class="result__snippet">Cyber Security | AI Agent Security</a>
</div>
<div class="result">
  <a class="result__a" href="https://www.instagram.com/dennis.erdelean/">(@dennis.erdelean) Instagram</a>
</div>
<div class="result">
  <a class="result__a" href="https://github.com/derdelean">derdelean</a>
</div>
<div class="result">
  <a class="result__a" href="https://github.com/derdelean/some-repo">a repository</a>
</div>
<div class="result">
  <a class="result__a" href="https://www.eliteprospects.com/player/41194/dennis-erdelean">Elite Prospects</a>
</div>
<div class="result">
  <a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Ft.me%2Fsomehandle&amp;rut=x">Telegram</a>
</div>
"""


@unittest.skipUnless(HAS_WEB_SEARCH, "web_search deps (httpx/bs4) not installed")
class TestWebSearchParsing(unittest.TestCase):
    def setUp(self):
        self.findings = web_search.parse_results(SERP, "Dennis Erdelean", 20)

    def test_every_result_becomes_a_finding(self):
        self.assertEqual(len(self.findings), 6)
        self.assertTrue(all(f["type"] == "web" for f in self.findings))

    def test_platform_is_the_result_host(self):
        hosts = [f["platform"] for f in self.findings]
        self.assertIn("ch.linkedin.com", hosts)
        self.assertIn("instagram.com", hosts)
        self.assertIn("eliteprospects.com", hosts)

    def test_profile_urls_become_pivot_seeds(self):
        seeds = {}
        for f in self.findings:
            seeds.update(f.get("ids_usernames") or {})
        self.assertEqual(
            seeds, {"denniserdelean": "LinkedIn",
                    "dennis.erdelean": "Instagram",
                    "derdelean": "GitHub",
                    "somehandle": "Telegram"}
        )

    def test_a_repo_url_is_not_mistaken_for_a_handle(self):
        repo = next(f for f in self.findings if f["source"].endswith("some-repo"))
        self.assertNotIn("ids_usernames", repo)

    def test_a_non_profile_result_yields_no_handle(self):
        ep = next(f for f in self.findings if f["platform"] == "eliteprospects.com")
        self.assertNotIn("ids_usernames", ep)

    def test_duckduckgo_redirector_is_unwrapped(self):
        tg = next(f for f in self.findings if "t.me" in f["source"])
        self.assertEqual(tg["source"], "https://t.me/somehandle")

    def test_snippet_is_captured(self):
        li = next(f for f in self.findings if f["platform"] == "ch.linkedin.com")
        self.assertIn("AI Agent Security", li["meta"]["snippet"])

    def test_site_furniture_is_not_a_handle(self):
        self.assertIsNone(web_search.extract_handle("https://github.com/features"))
        self.assertIsNone(web_search.extract_handle("https://www.instagram.com/explore/"))

    def test_max_results_is_honoured(self):
        self.assertEqual(len(web_search.parse_results(SERP, "q", 2)), 2)


if __name__ == "__main__":
    unittest.main()
