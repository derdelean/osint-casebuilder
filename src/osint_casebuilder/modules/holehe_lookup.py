import sys
import httpx
from holehe.core import import_submodules, get_functions

print("✅ Modul `holehe_lookup` (121 Seiten Email-Registrierung) aktiv", file=sys.stderr)

# Discover the ~121 site-check coroutines once at import time.
_SITE_CHECKS = get_functions(import_submodules("holehe.modules"))


async def _run_check(fn, email, client, out):
    try:
        await fn(email, client, out)
    except Exception:
        # individual site failures (timeouts, layout changes) must not abort the sweep
        pass


async def run_holehe_lookup_async(email: str, stats: dict | None = None) -> list:
    """Check which of holehe's ~121 sites this email is registered on. Returns a
    finding per CONFIRMED registration (rate-limited/unknown results are dropped).

    Pass `stats` to also receive coverage counts. Most checks never give a usable
    answer — sites rate-limit or block enumeration on purpose, and some are simply
    broken against the current layout — so a bare hit count silently overstates how
    much of the internet was actually looked at."""
    import asyncio

    print(f"🧠 holehe: prüfe {len(_SITE_CHECKS)} Seiten für '{email}'")

    raw = []
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*(_run_check(fn, email, client, raw) for fn in _SITE_CHECKS))

    findings = []
    answered = 0
    for r in raw:
        if r.get("rateLimit"):
            continue
        answered += 1  # the site gave a usable yes/no
        if not r.get("exists"):
            continue
        domain = r.get("domain") or r.get("name")
        findings.append({
            "type": "email",
            "value": email,
            "source": f"https://{domain}" if domain else r.get("name"),
            "platform": f"holehe:{r.get('name')}",
            "meta": {
                "registered": True,
                "emailrecovery": r.get("emailrecovery"),
                "phoneNumber": r.get("phoneNumber"),
                "others": r.get("others"),
            },
        })

    if stats is not None:
        stats["checked"] = len(_SITE_CHECKS)
        stats["answered"] = answered
        stats["inconclusive"] = len(_SITE_CHECKS) - answered
        stats["confirmed"] = len(findings)

    print(f"✅ holehe: {len(findings)} bestätigte Registrierungen "
          f"({answered}/{len(_SITE_CHECKS)} Seiten haben geantwortet)")
    return findings
