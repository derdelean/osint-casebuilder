import unittest

try:
    from osint_casebuilder.modules.maigret_lookup import _normalize_meta
    HAS_MAIGRET = True
except ImportError:
    HAS_MAIGRET = False


@unittest.skipUnless(HAS_MAIGRET, "maigret engine not installed (see requirements-engine.txt)")
class TestNormalizeMeta(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(_normalize_meta({}), {})

    def test_preserves_raw_fields(self):
        raw = {"uid": "123", "image": "http://x/y.jpg"}
        meta = _normalize_meta(raw)
        self.assertEqual(meta["uid"], "123")
        self.assertEqual(meta["image"], "http://x/y.jpg")

    def test_name_maps_to_fullname(self):
        meta = _normalize_meta({"name": "Linus Torvalds"})
        self.assertEqual(meta["fullname"], "Linus Torvalds")

    def test_existing_fullname_not_overwritten(self):
        meta = _normalize_meta({"name": "Alias", "fullname": "Real Name"})
        self.assertEqual(meta["fullname"], "Real Name")

    def test_description_maps_to_bio(self):
        meta = _normalize_meta({"description": "kernel hacker"})
        self.assertEqual(meta["bio"], "kernel hacker")

    def test_created_at_maps_to_joined(self):
        meta = _normalize_meta({"created_at": "2011-09-03T15:26:22Z"})
        self.assertEqual(meta["joined"], "2011-09-03T15:26:22Z")

    def test_follower_count_string_becomes_int(self):
        meta = _normalize_meta({"follower_count": "306213"})
        self.assertEqual(meta["followers"], 306213)
        self.assertIsInstance(meta["followers"], int)

    def test_non_numeric_follower_count_ignored(self):
        meta = _normalize_meta({"follower_count": "many"})
        self.assertNotIn("followers", meta)


if __name__ == "__main__":
    unittest.main()
