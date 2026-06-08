import httpx

print("✅ Modul `domain_lookup` keyless async aktiv")


def _extract_dns_records(data: dict) -> list:
    records = []
    for answer in data.get("Answer", []):
        value = answer.get("data", "").rstrip(".")
        if value:
            records.append(value)
    return records


async def run_domain_lookup_async(domain: str) -> list:
    registrar = None
    created = None
    expires = None
    nameservers = []
    a_records = []

    rdap_url = f"https://rdap.org/domain/{domain}"
    a_url = f"https://dns.google/resolve?name={domain}&type=A"
    ns_url = f"https://dns.google/resolve?name={domain}&type=NS"

    async with httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=10.0,
        follow_redirects=True,
    ) as client:
        # RDAP / WHOIS
        try:
            resp = await client.get(rdap_url)
            if resp.status_code == 200:
                data = resp.json()

                for entity in data.get("entities", []):
                    if "registrar" in entity.get("roles", []):
                        for item in entity.get("vcardArray", [[], []])[1]:
                            if item and item[0] == "fn":
                                registrar = item[3]
                                break
                        if registrar:
                            break

                for event in data.get("events", []):
                    action = event.get("eventAction")
                    if action == "registration":
                        created = event.get("eventDate")
                    elif action == "expiration":
                        expires = event.get("eventDate")

                for ns in data.get("nameservers", []):
                    name = ns.get("ldhName")
                    if name:
                        nameservers.append(name)
        except httpx.RequestError as e:
            print(f"⚠️  RDAP-Lookup fehlgeschlagen für {domain}: {e}")

        # DNS A records
        try:
            resp = await client.get(a_url)
            if resp.status_code == 200:
                a_records = _extract_dns_records(resp.json())
        except httpx.RequestError as e:
            print(f"⚠️  A-Lookup fehlgeschlagen für {domain}: {e}")

        # DNS NS records (fallback if RDAP had none)
        try:
            resp = await client.get(ns_url)
            if resp.status_code == 200:
                ns_records = _extract_dns_records(resp.json())
                if not nameservers:
                    nameservers = ns_records
        except httpx.RequestError as e:
            print(f"⚠️  NS-Lookup fehlgeschlagen für {domain}: {e}")

    finding = {
        "type": "domain",
        "value": domain,
        "source": rdap_url,
        "platform": "RDAP/WHOIS",
        "meta": {
            "registrar": registrar,
            "created": created,
            "expires": expires,
            "nameservers": nameservers,
            "a_records": a_records,
        },
    }

    print(f"✅ Domain findings für {domain}: registrar={registrar}, {len(a_records)} A-records")
    return [finding]
