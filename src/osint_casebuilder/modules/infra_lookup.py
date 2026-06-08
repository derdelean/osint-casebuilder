import asyncio
import os

import httpx

print("✅ Modul `infra_lookup` (crt.sh keyless + Shodan/Censys key-gated) aktiv")

_SUBDOMAIN_CAP = 200


def _extract_subdomains(data, domain: str) -> list:
    """Pure: pull unique subdomains of `domain` out of a crt.sh JSON response."""
    dom = domain.lower().strip()
    subs = set()
    for entry in data:
        for field in ("name_value", "common_name"):
            raw = entry.get(field) or ""
            for name in str(raw).split("\n"):
                name = name.strip().lower().lstrip("*.")
                if name and (name == dom or name.endswith("." + dom)):
                    subs.add(name)
    return sorted(subs)


async def run_crtsh_subdomains_async(domain: str, retries: int = 2) -> list:
    """Enumerate subdomains of `domain` from certificate-transparency logs (crt.sh).
    Keyless. Returns one `domain`-type finding per discovered subdomain. crt.sh is
    frequently overloaded (HTTP 503), so transient failures are retried."""
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    print(f"🧠 crt.sh: Subdomain-Enumeration für {domain}")

    subdomains = None
    async with httpx.AsyncClient(timeout=25.0, follow_redirects=True,
                                 headers={"User-Agent": "osint-casebuilder"}) as client:
        for attempt in range(retries + 1):
            try:
                resp = await client.get(url)
            except httpx.RequestError as e:
                if attempt < retries:
                    await asyncio.sleep(2.0)
                    continue
                print(f"⚠️  crt.sh fehlgeschlagen für {domain}: {e}")
                return []

            if resp.status_code == 200:
                try:
                    subdomains = _extract_subdomains(resp.json(), domain)
                except ValueError:
                    print(f"⚠️  crt.sh: ungültige JSON-Antwort für {domain}")
                    return []
                break

            # non-200 (usually 503 overload) → retry, then give up clearly
            if attempt < retries:
                await asyncio.sleep(2.0)
                continue
            print(f"⚠️  crt.sh nicht verfügbar (HTTP {resp.status_code}) für {domain} – "
                  f"später erneut versuchen")
            return []

    total = len(subdomains)
    if total > _SUBDOMAIN_CAP:
        print(f"ℹ️  crt.sh: {total} Subdomains gefunden, auf {_SUBDOMAIN_CAP} begrenzt")
        subdomains = subdomains[:_SUBDOMAIN_CAP]

    findings = [{
        "type": "domain",
        "value": sub,
        "source": f"https://crt.sh/?q=%25.{domain}",
        "platform": "crt.sh",
        "meta": {"parent_domain": domain},
    } for sub in subdomains]

    print(f"✅ crt.sh: {len(findings)} Subdomains")
    return findings


# --- Shodan (key-gated): domain DNS intel (subdomains + hosts/ports) -----------

def _map_shodan(data, domain: str) -> list:
    """Pure: map a Shodan /dns/domain response to findings."""
    parent = domain.lower().strip()
    findings = []
    for sub in data.get("subdomains", []):
        fqdn = f"{sub}.{parent}" if sub else parent
        findings.append({
            "type": "domain", "value": fqdn.lower(),
            "source": f"https://www.shodan.io/domain/{parent}",
            "platform": "Shodan", "meta": {"parent_domain": parent},
        })
    for rec in data.get("data", []):
        ports = rec.get("ports") or []
        ip = rec.get("value")
        if rec.get("type") in ("A", "AAAA") and ip and ports:
            sub = rec.get("subdomain")
            fqdn = f"{sub}.{parent}" if sub else parent
            findings.append({
                "type": "host", "value": ip,
                "source": f"https://www.shodan.io/host/{ip}",
                "platform": "Shodan",
                "meta": {"domain": parent, "hostname": fqdn.lower(), "ports": ports},
            })
    return findings


async def run_shodan_domain_async(domain: str, api_key: str = None) -> list:
    """Shodan domain intel (subdomains + open ports). Paid: needs SHODAN_API_KEY env
    var, skips cleanly without it."""
    api_key = api_key or os.environ.get("SHODAN_API_KEY")
    if not api_key:
        print("⚠️  Shodan übersprungen: kein SHODAN_API_KEY gesetzt")
        return []
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(f"https://api.shodan.io/dns/domain/{domain}",
                                    params={"key": api_key})
    except httpx.RequestError as e:
        print(f"⚠️  Shodan-Fehler: {e}")
        return []
    if resp.status_code == 401:
        print("⚠️  Shodan: ungültiger API-Key")
        return []
    if resp.status_code != 200:
        print(f"⚠️  Shodan: unerwarteter Status {resp.status_code}")
        return []
    findings = _map_shodan(resp.json(), domain)
    print(f"✅ Shodan: {len(findings)} Einträge für {domain}")
    return findings


# --- Censys (key-gated): host search ------------------------------------------

def _map_censys(hits, domain: str) -> list:
    """Pure: map Censys hosts-search hits to host findings."""
    dom = domain.lower().strip()
    findings = []
    for hit in hits:
        ip = hit.get("ip")
        if not ip:
            continue
        services = hit.get("services") or []
        findings.append({
            "type": "host", "value": ip,
            "source": f"https://search.censys.io/hosts/{ip}",
            "platform": "Censys",
            "meta": {
                "domain": dom,
                "ports": [s.get("port") for s in services if s.get("port")],
                "services": [s.get("service_name") for s in services if s.get("service_name")],
            },
        })
    return findings


async def run_censys_hosts_async(domain: str, api_id: str = None, api_secret: str = None) -> list:
    """Censys host search for a domain. Paid: needs CENSYS_API_ID + CENSYS_API_SECRET
    env vars, skips cleanly without them."""
    api_id = api_id or os.environ.get("CENSYS_API_ID")
    api_secret = api_secret or os.environ.get("CENSYS_API_SECRET")
    if not (api_id and api_secret):
        print("⚠️  Censys übersprungen: kein CENSYS_API_ID/SECRET gesetzt")
        return []
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get("https://search.censys.io/api/v2/hosts/search",
                                    params={"q": domain, "per_page": 25},
                                    auth=(api_id, api_secret))
    except httpx.RequestError as e:
        print(f"⚠️  Censys-Fehler: {e}")
        return []
    if resp.status_code in (401, 403):
        print("⚠️  Censys: ungültige Credentials")
        return []
    if resp.status_code != 200:
        print(f"⚠️  Censys: unerwarteter Status {resp.status_code}")
        return []
    hits = resp.json().get("result", {}).get("hits", [])
    findings = _map_censys(hits, domain)
    print(f"✅ Censys: {len(findings)} Hosts für {domain}")
    return findings
