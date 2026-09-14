import unittest

from osint_casebuilder.modules.correlation import extract_entities, correlate, evidence_links

GITHUB = {
    "type": "username", "value": "torvalds", "platform": "GitHub",
    "meta": {"fullname": "Linus Torvalds", "location": "Portland, OR",
             "website": "https://kernel.org", "followers": 300000},
    "ids_usernames": {"torvalds": "username"},
}
SOUNDCLOUD = {
    "type": "username", "value": "torvalds", "platform": "SoundCloud",
    "meta": {"fullname": "Linus Torvalds"},
}
EMAIL = {
    "type": "email", "value": "linus@kernel.org", "platform": "Email/MX",
    "meta": {"domain": "kernel.org", "mx_records": ["mx"]},
}
PHONE = {
    "type": "phone", "value": "+41446681800", "platform": "Phone/libphonenumber",
    "meta": {"region": "Zurich"},
}


class TestExtractEntities(unittest.TestCase):
    def test_username_finding(self):
        ents = extract_entities(GITHUB)
        self.assertIn(("username", "torvalds"), ents)
        self.assertIn(("name", "linus torvalds"), ents)
        self.assertIn(("location", "portland, or"), ents)
        self.assertIn(("domain", "kernel.org"), ents)  # from website

    def test_email_domain_extracted(self):
        self.assertIn(("domain", "kernel.org"), extract_entities(EMAIL))

    def test_dedupe(self):
        ents = extract_entities(GITHUB)
        self.assertEqual(len(ents), len(set(ents)))

    def test_breach_links_to_email(self):
        breach = {"type": "breach", "value": "linus@kernel.org",
                  "platform": "HIBP:Adobe", "meta": {"breach": "Adobe", "domain": "adobe.com"}}
        ents = extract_entities(breach)
        self.assertIn(("email", "linus@kernel.org"), ents)
        self.assertIn(("domain", "adobe.com"), ents)

    def test_subdomain_links_to_parent(self):
        sub = {"type": "domain", "value": "mail.kernel.org",
               "platform": "crt.sh", "meta": {"parent_domain": "kernel.org"}}
        ents = extract_entities(sub)
        self.assertIn(("domain", "mail.kernel.org"), ents)
        self.assertIn(("domain", "kernel.org"), ents)

    def test_email_in_meta_extracted(self):
        # an email embedded in a profile's metadata enables username→email pivot
        prof = {"type": "username", "value": "torvalds", "platform": "SomeSite",
                "meta": {"email": "linus@kernel.org"}}
        self.assertIn(("email", "linus@kernel.org"), extract_entities(prof))

    def test_host_links_to_domain(self):
        host = {"type": "host", "value": "1.2.3.4", "platform": "Shodan",
                "meta": {"domain": "example.com", "ports": [443]}}
        ents = extract_entities(host)
        self.assertIn(("host", "1.2.3.4"), ents)
        self.assertIn(("domain", "example.com"), ents)

    def test_site_extracted_for_account_presence(self):
        # a maigret username hit and a holehe email-registration on the same site
        # both yield the same ("site", host) bridge entity
        uname = {"type": "username", "value": "derdelean", "platform": "Replit",
                 "source": "https://replit.com/@derdelean", "meta": {}}
        holehe = {"type": "email", "value": "x@gmail.com", "platform": "holehe:replit",
                  "source": "https://replit.com", "meta": {"registered": True}}
        self.assertIn(("site", "replit.com"), extract_entities(uname))
        self.assertIn(("site", "replit.com"), extract_entities(holehe))

    def test_site_not_extracted_for_resolver_lookup(self):
        # the Email/MX finding's source is a DoH resolver, not the target's site
        self.assertNotIn(
            ("site", "dns.google"),
            extract_entities({"type": "email", "value": "linus@kernel.org",
                              "platform": "Email/MX",
                              "source": "https://dns.google/resolve?name=kernel.org&type=MX",
                              "meta": {"domain": "kernel.org"}}),
        )


class TestCorrelate(unittest.TestCase):
    def setUp(self):
        self.summary = correlate([GITHUB, SOUNDCLOUD, EMAIL, PHONE])

    def test_domain_links_email_to_profile(self):
        # kernel.org appears in GitHub (website) and Email/MX (email domain)
        dom = [c for c in self.summary["corroborated"]
               if c["type"] == "domain" and c["value"] == "kernel.org"]
        self.assertEqual(len(dom), 1)
        self.assertEqual(dom[0]["count"], 2)
        self.assertEqual(sorted(dom[0]["platforms"]), ["Email/MX", "GitHub"])

    def test_name_corroborated(self):
        names = [c for c in self.summary["corroborated"] if c["type"] == "name"]
        self.assertTrue(any(c["value"] == "linus torvalds" and c["count"] == 2 for c in names))

    def test_domain_starting_with_w_links_website_to_email(self):
        # only a leading "www." is stripped — "wolfgang.dev" must not become "olfgang.dev"
        prof = {"type": "username", "value": "wolf", "platform": "GitHub",
                "source": "https://www.github.com/wolf", "meta": {"website": "https://wolfgang.dev"}}
        mail = {"type": "email", "value": "a@wolfgang.dev", "platform": "Email/MX",
                "meta": {"domain": "wolfgang.dev"}}
        self.assertIn(("site", "github.com"), extract_entities(prof))
        summary = correlate([prof, mail])
        self.assertIn(("domain", "wolfgang.dev"),
                      [(c["type"], c["value"]) for c in summary["corroborated"]])
        self.assertEqual(summary["clusters"], 1)

    def test_clusters(self):
        # GitHub+SoundCloud+Email share entities; phone is alone → 2 clusters
        self.assertEqual(self.summary["clusters"], 2)

    def test_empty(self):
        s = correlate([])
        self.assertEqual(s["distinct_entities"], 0)
        self.assertEqual(s["clusters"], 0)
        self.assertEqual(s["corroborated"], [])


class TestSiteBridge(unittest.TestCase):
    """A username hit and an email/phone registration on the SAME site must merge
    into one identity cluster (the username↔email cross-type link)."""

    UNAME_REPLIT = {"type": "username", "value": "derdelean", "platform": "Replit",
                    "source": "https://replit.com/@derdelean", "meta": {}}
    HOLEHE_REPLIT = {"type": "email", "value": "x@gmail.com", "platform": "holehe:replit",
                     "source": "https://replit.com", "meta": {"registered": True}}

    def test_username_and_email_merge_via_site(self):
        # alone the two share no entity (username vs email) — only the site bridges
        s = correlate([self.UNAME_REPLIT, self.HOLEHE_REPLIT])
        self.assertEqual(s["clusters"], 1)

    def test_shared_site_is_corroborated(self):
        s = correlate([self.UNAME_REPLIT, self.HOLEHE_REPLIT])
        site = [c for c in s["corroborated"]
                if c["type"] == "site" and c["value"] == "replit.com"]
        self.assertEqual(len(site), 1)
        self.assertEqual(site[0]["count"], 2)
        self.assertEqual(sorted(site[0]["platforms"]), ["Replit", "holehe:replit"])

    def test_different_sites_do_not_merge(self):
        # username on replit + email registered on twitter → no bridge, 2 clusters
        holehe_tw = {"type": "email", "value": "x@gmail.com", "platform": "holehe:twitter",
                     "source": "https://twitter.com", "meta": {"registered": True}}
        s = correlate([self.UNAME_REPLIT, holehe_tw])
        self.assertEqual(s["clusters"], 2)


def _hit(platform, handle="soxoj", **meta):
    return {"type": "username", "value": handle, "platform": platform,
            "source": f"https://{platform.lower()}.com/{handle}", "meta": meta}


class TestSearchedValuesAreNotEvidence(unittest.TestCase):
    """The searched handle existing on many sites (or a display name equal to it)
    is the query, not corroboration."""

    SEARCHED = {"username": {"soxoj"}}

    def test_seed_not_corroborated(self):
        s = correlate([_hit("GitHub"), _hit("Twitter")], self.SEARCHED)
        self.assertEqual(s["corroborated"], [])
        self.assertEqual(s["clusters"], 2)

    def test_name_equal_to_handle_not_corroborated(self):
        s = correlate([_hit("GitHub", fullname="Soxoj"), _hit("Twitter", fullname="soxoj")],
                      self.SEARCHED)
        self.assertEqual(s["corroborated"], [])

    def test_real_attribute_still_corroborated(self):
        s = correlate([_hit("GitHub", location="Amsterdam"), _hit("Twitter", location="amsterdam")],
                      self.SEARCHED)
        self.assertEqual([(c["type"], c["value"]) for c in s["corroborated"]],
                         [("location", "amsterdam")])
        self.assertEqual(s["clusters"], 1)

    def test_two_handles_on_same_site_not_corroborated_or_merged(self):
        # seed soxoj and pivot soxoj1 both on github.com: same host, different accounts
        fs = [_hit("GitHub"), _hit("GitHub", handle="soxoj1")]
        s = correlate(fs, {"username": {"soxoj", "soxoj1"}})
        self.assertEqual(s["corroborated"], [])
        self.assertEqual(s["clusters"], 2)

    def test_without_searched_behaviour_unchanged(self):
        s = correlate([_hit("GitHub"), _hit("Twitter")])
        self.assertEqual(s["clusters"], 1)


class TestEvidenceLinks(unittest.TestCase):
    SEARCHED = {"username": {"soxoj"}}

    def test_shared_location_links_both_hits(self):
        fs = [_hit("GitHub", location="Amsterdam"), _hit("Twitter", location="Amsterdam"),
              _hit("Codewars")]
        ev = evidence_links(fs, self.SEARCHED)
        self.assertEqual(ev[0], ["location `amsterdam` also on Twitter"])
        self.assertEqual(ev[1], ["location `amsterdam` also on GitHub"])
        self.assertNotIn(2, ev)  # handle only

    def test_handle_and_name_equal_to_handle_are_not_evidence(self):
        fs = [_hit("GitHub", fullname="soxoj"), _hit("Twitter", fullname="soxoj")]
        self.assertEqual(evidence_links(fs, self.SEARCHED), {})

    def test_email_registration_on_same_site_links_username_hit(self):
        uname = TestSiteBridge.UNAME_REPLIT
        holehe = TestSiteBridge.HOLEHE_REPLIT
        ev = evidence_links([uname, holehe], {"username": {"derdelean"}, "email": {"x@gmail.com"}})
        self.assertEqual(ev[0], ["same site (replit.com) as holehe:replit"])
        self.assertEqual(ev[1], ["same site (replit.com) as Replit"])

    def test_two_handles_on_same_site_are_not_evidence(self):
        fs = [_hit("GitHub"), _hit("GitHubPivot", handle="sox0j")]
        fs[1]["source"] = "https://github.com/sox0j"
        fs[0]["source"] = "https://github.com/soxoj"
        self.assertEqual(evidence_links(fs, {"username": {"soxoj", "sox0j"}}), {})


if __name__ == "__main__":
    unittest.main()
