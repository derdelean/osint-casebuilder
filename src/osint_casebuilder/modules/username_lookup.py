import requests
from time import sleep
from .username_mutator import generate_username_variants

print("✅ Modul `username_lookup` aktiv")

PLATFORMS = {
    "GitHub": "https://github.com/{}",
    "Twitter": "https://twitter.com/{}",
    "Instagram": "https://www.instagram.com/{}",
    "Reddit": "https://www.reddit.com/user/{}",
    "TikTok": "https://www.tiktok.com/@{}",
    "Pinterest": "https://www.pinterest.com/{}",
    "Tumblr": "https://{}.tumblr.com",
    "Steam": "https://steamcommunity.com/id/{}",
    "SoundCloud": "https://soundcloud.com/{}",
    "Replit": "https://replit.com/@{}",
}


def run_username_lookup(username: str):
    print(f"🔍 Starte OSINT-Checks für '{username}'")
    findings = []

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    all_variants = generate_username_variants(username)
    print(f"🧠 {len(all_variants)} Varianten generiert:\n{all_variants}\n")

    for variant in all_variants:
        for platform, url_template in PLATFORMS.items():
            url = url_template.format(variant)
            try:
                response = requests.get(url, headers=headers, timeout=5)
                if response.status_code == 200:
                    print(f"[+] {platform} ({variant}): {url}")
                    findings.append({
                        "type": "username",
                        "value": variant,
                        "source": url,
                        "timestamp": "auto"
                    })
                elif response.status_code == 404:
                    print(f"[-] {platform} ({variant}): nicht gefunden")
                else:
                    print(f"[?] {platform} ({variant}): Statuscode {response.status_code}")
            except Exception as e:
                print(f"[!] Fehler bei {platform} ({variant}): {e}")
            sleep(0.5)  # Rate limit freundlich

    print(f"✅ {len(findings)} Fundstellen insgesamt")
    return findings
