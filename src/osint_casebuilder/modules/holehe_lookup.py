import httpx
from holehe.core import import_submodules, get_functions

print("✅ Modul `holehe_lookup` (121 Seiten Email-Registrierung) aktiv")

# Discover the ~121 site-check coroutines once at import time.
_SITE_CHECKS = get_functions(import_submodules("holehe.modules"))


async def _run_check(fn, email, client, out):
    try:
        await fn(email, client, out)
    except Exception:
        # individual site failures (timeouts, layout changes) must not abort the sweep
        pass


async def run_holehe_lookup_async(email: str) -> list:
    """Check which of holehe's ~121 sites this email is registered on. Returns a
    finding per CONFIRMED registration (rate-limited/unknown results are dropped)."""
    import asyncio

    print(f"🧠 holehe: prüfe {len(_SITE_CHECKS)} Seiten für '{email}'")

    raw = []
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*(_run_check(fn, email, client, raw) for fn in _SITE_CHECKS))

    findings = []
    for r in raw:
        if not r.get("exists") or r.get("rateLimit"):
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

    print(f"✅ holehe: {len(findings)} bestätigte Registrierungen")
    return findings
