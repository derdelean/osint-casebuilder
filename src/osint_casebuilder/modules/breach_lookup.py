import os

import httpx

print("✅ Modul `breach_lookup` (HaveIBeenPwned, API-Key) aktiv")

_HIBP_URL = "https://haveibeenpwned.com/api/v3/breachedaccount/{}"


def _map_breaches(breaches, email: str) -> list:
    """Pure: map HIBP breach objects to findings."""
    return [{
        "type": "breach",
        "value": email,
        "source": "https://haveibeenpwned.com/",
        "platform": f"HIBP:{b.get('Name')}",
        "meta": {
            "breach": b.get("Name"),
            "domain": b.get("Domain"),
            "breach_date": b.get("BreachDate"),
            "pwn_count": b.get("PwnCount"),
            "data_classes": b.get("DataClasses"),
        },
    } for b in breaches]


async def run_hibp_lookup_async(email: str, api_key: str = None) -> list:
    """Look up breaches for `email` via HaveIBeenPwned. Paid: needs an API key in
    the HIBP_API_KEY env var (or passed in). Skips cleanly (returns []) without one."""
    api_key = api_key or os.environ.get("HIBP_API_KEY")
    if not api_key:
        print("⚠️  HIBP übersprungen: kein HIBP_API_KEY gesetzt")
        return []

    url = _HIBP_URL.format(email) + "?truncateResponse=false"
    headers = {"hibp-api-key": api_key, "user-agent": "osint-casebuilder"}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
    except httpx.RequestError as e:
        print(f"⚠️  HIBP-Fehler: {e}")
        return []

    if resp.status_code == 404:
        print(f"✅ HIBP: keine Breaches für {email}")
        return []
    if resp.status_code == 401:
        print("⚠️  HIBP: ungültiger API-Key")
        return []
    if resp.status_code == 429:
        print("⚠️  HIBP: Rate-Limit erreicht")
        return []
    if resp.status_code != 200:
        print(f"⚠️  HIBP: unerwarteter Status {resp.status_code}")
        return []

    findings = _map_breaches(resp.json(), email)
    print(f"✅ HIBP: {len(findings)} Breaches für {email}")
    return findings
