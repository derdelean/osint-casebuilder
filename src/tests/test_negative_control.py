import asyncio
import unittest
from unittest import mock

try:
    from osint_casebuilder import controller
    HAS_CONTROLLER = True
except ImportError:
    HAS_CONTROLLER = False


def _hit(username, platform):
    return {"type": "username", "value": username, "platform": platform}


async def _fake_lookup(username, top_sites, interactive=True):
    """Two sites claim every name (unreliable); GitHub only claims 'alice'."""
    hits = [_hit(username, "CNET"), _hit(username, "fixya")]
    if username == "alice":
        hits.append(_hit(username, "GitHub"))
    return hits


@unittest.skipUnless(HAS_CONTROLLER, "controller deps (httpx) not installed")
class TestNegativeControl(unittest.TestCase):
    def test_drops_sites_that_claim_a_random_handle(self):
        with mock.patch.object(controller, "_lookup_username", side_effect=_fake_lookup):
            found = asyncio.run(controller._lookup_username_checked("alice", 500, {}, False))
        self.assertEqual([f["platform"] for f in found], ["GitHub"])

    def test_control_runs_once_and_is_reused_for_pivots(self):
        control = {}
        with mock.patch.object(controller, "_lookup_username", side_effect=_fake_lookup) as lk:
            asyncio.run(controller._lookup_username_checked("alice", 500, control, False))
            self.assertEqual(lk.call_count, 2)  # seed + control
            found = asyncio.run(controller._lookup_username_checked("bob", 500, control, False))
            self.assertEqual(lk.call_count, 3)  # pivot reuses the cached control
        self.assertEqual(found, [])
        self.assertEqual(control["platforms"], {"cnet", "fixya"})

    def test_control_handle_is_random(self):
        with mock.patch.object(controller, "_lookup_username", side_effect=_fake_lookup) as lk:
            asyncio.run(controller._lookup_username_checked("alice", 500, {}, False))
            asyncio.run(controller._lookup_username_checked("alice", 500, {}, False))
        controls = [c.args[0] for c in lk.call_args_list if c.args[0] != "alice"]
        self.assertEqual(len(set(controls)), 2)


if __name__ == "__main__":
    unittest.main()
