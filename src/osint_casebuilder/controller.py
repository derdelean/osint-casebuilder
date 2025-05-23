from datetime import datetime
from .modules.username_lookup import run_username_lookup
from .modules.github_profile_scraper import scrape_github_profile
from .modules.confidence_scorer import score_profile
from .reporter import generate_markdown_report

def run_case(email=None, username=None, domain=None, target_profile=None, generate_report=False, output_path=None):
    session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    findings = []

    def is_profile_empty(profile: dict) -> bool:
        return not profile or all(not v for v in profile.values())

    # Interaktive Zielprofil-Eingabe wenn leer
    if is_profile_empty(target_profile):
        print("🧠 Kein vollständiges Zielprofil übergeben – bitte Angaben machen (ENTER = überspringen):")
        target_profile = {}

        try:
            target_profile["fullname"] = input("Vollständiger Name: ").strip()
            target_profile["location"] = input("Standort (z. B. Stadt, Land): ").strip()

            keywords = input("Schlüsselwörter (Komma, z. B. osint,eth,cybersecurity): ").strip()
            target_profile["keywords"] = [kw.strip() for kw in keywords.split(",")] if keywords else []

            target_profile["domain"] = input("Website/Domain (optional): ").strip()
            print("✅ Zielprofil erstellt.\n")
        except KeyboardInterrupt:
            print("\n⚠️ Eingabe abgebrochen. Zielprofil wird ignoriert.")
            target_profile = {}

    if username:
        print(f"\n🔍 Benutzername-Recherche: {username}")
        try:
            username_findings = run_username_lookup(username)
            print(f"🔎 Ergebnisse von run_username_lookup(): {len(username_findings)}")
        except Exception as e:
            print(f"❌ Fehler bei Username-Lookup: {e}")
            username_findings = []

        for f in username_findings:
            f["timestamp"] = session_id

            if "github.com" in f.get("source", ""):
                gh_username = f["source"].split("/")[-1]
                try:
                    gh_profile = scrape_github_profile(gh_username)
                    if gh_profile:
                        f["meta"] = gh_profile
                        if not is_profile_empty(target_profile):
                            score = score_profile(gh_profile, target_profile)
                            print("DEBUG", f)  # zeigt ob 'score' wirklich drin ist
                            f["score"] = score
                            print(f"📊 Score für {gh_username}: {score}")
                except Exception as e:
                    print(f"⚠️ Fehler beim GitHub-Scraping: {e}")

        findings.extend(username_findings)

    if email:
        print(f"\n📧 E-Mail-Recherche: {email}")
        # TODO: späteres Modul

    if domain:
        print(f"\n🌐 Domain-Recherche: {domain}")
        # TODO: späteres Modul

    if generate_report:
        print("\n📝 Report-Generierung aktiviert")
        try:
            generate_markdown_report(findings, session_id, output_path)
        except Exception as e:
            print(f"❌ Fehler bei der Report-Generierung: {e}")

    return findings
