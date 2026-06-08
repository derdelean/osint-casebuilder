import re
import hashlib
import httpx

print("✅ Modul `email_lookup` keyless async aktiv")

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


async def run_email_lookup_async(email: str) -> list:
    findings = []

    if not EMAIL_REGEX.match(email or ""):
        print(f"⚠️  Ungültiges E-Mail-Format: {email}")
        return []

    domain = email.split("@", 1)[1]
    normalized = email.strip().lower()
    md5 = hashlib.md5(normalized.encode("utf-8")).hexdigest()

    mx_url = f"https://dns.google/resolve?name={domain}&type=MX"
    gravatar_url = f"https://www.gravatar.com/avatar/{md5}?d=404"

    async with httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=10.0,
        follow_redirects=True,
    ) as client:
        # MX records via DNS-over-HTTPS
        mx_records = []
        try:
            resp = await client.get(mx_url)
            if resp.status_code == 200:
                data = resp.json()
                for answer in data.get("Answer", []):
                    parts = answer.get("data", "").split()
                    host = parts[-1].rstrip(".") if parts else ""
                    if host:
                        mx_records.append(host)
        except httpx.RequestError as e:
            print(f"⚠️  MX-Lookup fehlgeschlagen für {domain}: {e}")

        findings.append({
            "type": "email",
            "value": email,
            "source": mx_url,
            "platform": "Email/MX",
            "meta": {
                "valid_format": True,
                "domain": domain,
                "mx_records": mx_records,
            },
        })

        # Gravatar existence check
        try:
            resp = await client.get(gravatar_url)
            if resp.status_code == 200:
                print(f"✅ Gravatar gefunden für {email}")
                findings.append({
                    "type": "email",
                    "value": email,
                    "source": gravatar_url,
                    "platform": "Gravatar",
                    "meta": {"gravatar_url": gravatar_url},
                })
        except httpx.RequestError as e:
            print(f"⚠️  Gravatar-Check fehlgeschlagen für {email}: {e}")

    print(f"✅ {len(findings)} Email findings")
    return findings
