from datetime import datetime

from .modules.username_lookup import run_username_lookup
from .modules.github_profile_scraper import scrape_github_profile
from .reporter import generate_markdown_report

def run_case(email=None, username=None, domain=None, generate_report=False, output_path=None):
    session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    findings = []

    if username:
        print(f"\n🔍 Benutzername-Recherche: {username}")
        username_findings = run_username_lookup(username)
        print(f"🔎 Ergebnisse von run_username_lookup(): {len(username_findings)}")

        for f in username_findings:
            f["timestamp"] = session_id

            # GitHub-Profile erkennen und Metadaten extrahieren
            if "github.com" in f["source"]:
                gh_username = f["source"].split("/")[-1]
                gh_profile = scrape_github_profile(gh_username)
                if gh_profile:
                    print(f"🧠 GitHub-Metadaten für '{gh_username}' geladen")
                    f["meta"] = gh_profile

        findings.extend(username_findings)

    if email:
        print(f"\n📧 E-Mail-Recherche: {email}")
        # TODO

    if domain:
        print(f"\n🌐 Domain-Recherche: {domain}")
        # TODO

    if generate_report:
        print("\n📝 Report-Generierung aktiviert")
        generate_markdown_report(findings, session_id, output_path)

    return findings
