import asyncio

import httpx
from ignorant.core import import_submodules, get_functions

print("✅ Modul `phone_accounts_lookup` (ignorant: Phone→Social) aktiv")

# Discover ignorant's site-check coroutines once (Instagram, Amazon, Snapchat).
_CHECKS = get_functions(import_submodules("ignorant.modules"))


def _map_results(raw, e164: str) -> list:
    """Pure: map ignorant result dicts to findings (CONFIRMED registrations only)."""
    findings = []
    for r in raw:
        if not r.get("exists") or r.get("rateLimit"):
            continue
        findings.append({
            "type": "phone",
            "value": e164,
            "source": f"https://{r.get('name')}",
            "platform": f"ignorant:{r.get('name')}",
            "meta": {"registered": True},
        })
    return findings


async def _run_check(fn, phone, country_code, client, out):
    try:
        await fn(phone, country_code, client, out)
    except Exception:
        pass


async def run_ignorant_lookup_async(country_code, national_number) -> list:
    """Check which of ignorant's sites (Instagram/Amazon/Snapchat) a phone number is
    registered on. `country_code`/`national_number` come from the parsed phone."""
    cc, nn = str(country_code), str(national_number)
    e164 = f"+{cc}{nn}"
    print(f"🧠 ignorant: prüfe {len(_CHECKS)} Seiten für {e164}")

    raw = []
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*(_run_check(fn, nn, cc, client, raw) for fn in _CHECKS))

    findings = _map_results(raw, e164)
    print(f"✅ ignorant: {len(findings)} bestätigte Phone-Registrierungen")
    return findings
