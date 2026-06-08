import unittest

# maigret_common imports no third-party packages → always importable.
from osint_casebuilder.modules.maigret_common import normalize_meta, ids_to_pivots


class TestNormalizeMeta(unittest.TestCase):
    def test_name_to_fullname_and_followers_int(self):
        meta = normalize_meta({"name": "Linus Torvalds", "follower_count": "306213"})
        self.assertEqual(meta["fullname"], "Linus Torvalds")
        self.assertEqual(meta["followers"], 306213)

    def test_preserves_raw_and_handles_bad_followers(self):
        meta = normalize_meta({"uid": "1", "follower_count": "many"})
        self.assertEqual(meta["uid"], "1")
        self.assertNotIn("followers", meta)

    def test_empty(self):
        self.assertEqual(normalize_meta({}), {})


class TestIdsToPivots(unittest.TestCase):
    def test_extracts_usernames_and_links(self):
        usernames, links = ids_to_pivots(
            {"username": "Bob", "other_username": "bob2", "blog": "http://x.com", "uid": "1"})
        self.assertEqual(usernames, {"Bob": "username", "bob2": "username"})
        self.assertEqual(links, ["http://x.com"])

    def test_empty(self):
        self.assertEqual(ids_to_pivots({}), ({}, []))
        self.assertEqual(ids_to_pivots(None), ({}, []))


if __name__ == "__main__":
    unittest.main()
