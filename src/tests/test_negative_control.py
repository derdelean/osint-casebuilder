import asyncio
import unittest
from unittest import mock

try:
    from osint_casebuilder import controller
    HAS_CONTROLLER = True
except ImportError:
    HAS_CONTROLLER = False

try:
    from osint_casebuilder.modules import holehe_lookup
    HAS_HOLEHE = True
except ImportError:
    HAS_HOLEHE = False


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


def _mail(email, platform):
    return {"type": "email", "value": email, "platform": platform}


async def _fake_holehe(email, stats=None):
    """protonmail confirms any @proton.me address (catch-all); office365 only the
    real one. A gmail.com address gets no catch-all at all."""
    hits = []
    if email.endswith("@proton.me"):
        hits.append(_mail(email, "holehe:protonmail"))
    if email.startswith("real@"):
        hits.append(_mail(email, "holehe:office365"))
    if stats is not None:
        stats.update(checked=121, answered=47, inconclusive=74, confirmed=len(hits))
    return hits


@unittest.skipUnless(HAS_CONTROLLER and HAS_HOLEHE, "holehe not installed")
class TestEmailNegativeControl(unittest.TestCase):
    def setUp(self):
        self.patch = mock.patch.object(
            holehe_lookup, "run_holehe_lookup_async", side_effect=_fake_holehe
        )
        self.lookup = self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_drops_sites_that_confirm_a_random_address(self):
        found = asyncio.run(
            controller._lookup_holehe_checked("real@proton.me", {}, False)
        )
        self.assertEqual([f["platform"] for f in found], ["holehe:office365"])

    def test_control_address_shares_the_target_domain(self):
        asyncio.run(controller._lookup_holehe_checked("real@proton.me", {}, False))
        controls = [c.args[0] for c in self.lookup.call_args_list
                    if c.args[0] != "real@proton.me"]
        self.assertEqual(len(controls), 1)
        self.assertTrue(controls[0].endswith("@proton.me"))

    def test_control_is_cached_per_domain(self):
        control = {}
        asyncio.run(controller._lookup_holehe_checked("real@proton.me", control, False))
        self.assertEqual(self.lookup.call_count, 2)  # seed + control
        asyncio.run(controller._lookup_holehe_checked("other@proton.me", control, False))
        self.assertEqual(self.lookup.call_count, 3)  # same domain reuses the control
        asyncio.run(controller._lookup_holehe_checked("real@gmail.com", control, False))
        self.assertEqual(self.lookup.call_count, 5)  # new domain needs its own control
        self.assertEqual(control["proton.me"], {"holehe:protonmail"})
        self.assertEqual(control["gmail.com"], set())

    def test_a_clean_domain_keeps_every_hit(self):
        found = asyncio.run(
            controller._lookup_holehe_checked("real@gmail.com", {}, False)
        )
        self.assertEqual([f["platform"] for f in found], ["holehe:office365"])

    def test_coverage_stats_are_reported_for_the_target_not_the_control(self):
        stats = {}
        asyncio.run(
            controller._lookup_holehe_checked("real@proton.me", {}, False, stats)
        )
        self.assertEqual(stats["checked"], 121)
        self.assertEqual(stats["answered"], 47)
        self.assertEqual(stats["inconclusive"], 74)


if __name__ == "__main__":
    unittest.main()
