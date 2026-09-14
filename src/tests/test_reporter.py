import unittest

# reporter imports no third-party packages → always importable.
from osint_casebuilder.reporter import render_markdown_report

LINKED = {"type": "username", "value": "soxoj", "platform": "GitHub",
          "source": "https://github.com/soxoj", "score": 0.5,
          "meta": {"location": "Amsterdam"},
          "evidence": ["location `amsterdam` also on Twitter", "matches location hint"]}
HANDLE_ONLY = {"type": "username", "value": "soxoj", "platform": "Codewars",
               "source": "https://www.codewars.com/users/soxoj", "score": 0.0, "meta": {}}
PHONE = {"type": "phone", "value": "+41446681800", "platform": "Phone/libphonenumber",
         "source": "tel:+41446681800", "meta": {"region": "Zurich"}}
SUMMARY = {"distinct_entities": 5, "clusters": 3,
           "corroborated": [{"type": "location", "value": "amsterdam", "count": 2,
                             "platforms": ["GitHub", "Twitter"]}]}


class TestEvidenceTiers(unittest.TestCase):
    def setUp(self):
        self.md = render_markdown_report([HANDLE_ONLY, PHONE, LINKED], SUMMARY)

    def _section(self, title):
        start = self.md.index(title)
        nxt = self.md.find("\n## ", start + 1)
        return self.md[start:] if nxt == -1 else self.md[start:nxt]

    def test_tier_counts(self):
        self.assertIn("- **Linked by evidence**: 1", self.md)
        self.assertIn("- **Handle exists only**: 1", self.md)
        self.assertNotIn("Identity clusters", self.md)

    def test_linked_hit_rendered_in_full_with_evidence(self):
        sec = self._section("## ✅ Linked by evidence")
        self.assertIn("### 🔹 GitHub", sec)
        self.assertIn("location `amsterdam` also on Twitter; matches location hint", sec)
        self.assertIn("**Location**: Amsterdam", sec)
        self.assertNotIn("Codewars", sec)

    def test_handle_only_hit_listed_compactly(self):
        sec = self._section("## ❔ Handle exists only")
        self.assertIn("- **Codewars** `soxoj` — https://www.codewars.com/users/soxoj", sec)
        self.assertNotIn("GitHub", sec)

    def test_other_findings_keep_their_type_label(self):
        sec = self._section("## 📇 Other findings")
        self.assertIn("### 🔹 Phone/libphonenumber", sec)
        self.assertIn("- **Phone**: `+41446681800`", sec)
        self.assertIn("**Region**: Zurich", sec)

    def test_corroborated_section_kept(self):
        self.assertIn("- **location** `amsterdam` — 2× (GitHub, Twitter)", self.md)

    def test_without_summary_or_username_hits(self):
        md = render_markdown_report([PHONE])
        self.assertNotIn("Linked by evidence", md)
        self.assertNotIn("Handle exists only", md)
        self.assertIn("## 📇 Other findings", md)


if __name__ == "__main__":
    unittest.main()
