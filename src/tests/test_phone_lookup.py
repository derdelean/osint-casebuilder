import unittest

try:
    from osint_casebuilder.modules.phone_lookup import run_phone_lookup
    HAS_PHONE = True
except ImportError:
    HAS_PHONE = False


@unittest.skipUnless(HAS_PHONE, "phonenumbers not installed")
class TestPhoneLookup(unittest.TestCase):
    def test_international_number(self):
        findings = run_phone_lookup("+1 650-253-0000")
        self.assertEqual(len(findings), 1)
        meta = findings[0]["meta"]
        self.assertTrue(meta["valid"])
        self.assertEqual(meta["country_code"], 1)
        self.assertEqual(meta["e164"], "+16502530000")
        self.assertEqual(meta["line_type"], "fixed_line_or_mobile")
        self.assertIn("America/Los_Angeles", meta["timezones"])
        self.assertIn("Mountain View", meta["region"])

    def test_national_number_needs_region(self):
        # without a region this national-format number can't be parsed
        self.assertEqual(run_phone_lookup("044 668 18 00"), [])
        # with the region it resolves to the Swiss E.164 form
        findings = run_phone_lookup("044 668 18 00", "CH")
        self.assertEqual(len(findings), 1)
        meta = findings[0]["meta"]
        self.assertEqual(meta["e164"], "+41446681800")
        self.assertEqual(meta["country_code"], 41)
        self.assertEqual(meta["region"], "Zurich")
        self.assertEqual(meta["line_type"], "fixed_line")

    def test_finding_shape(self):
        f = run_phone_lookup("+16502530000")[0]
        self.assertEqual(f["type"], "phone")
        self.assertEqual(f["value"], "+16502530000")
        self.assertEqual(f["source"], "tel:+16502530000")
        self.assertEqual(f["platform"], "Phone/libphonenumber")

    def test_garbage_returns_empty(self):
        self.assertEqual(run_phone_lookup("not-a-number"), [])
        self.assertEqual(run_phone_lookup(""), [])


if __name__ == "__main__":
    unittest.main()
