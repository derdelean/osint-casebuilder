from datetime import datetime

# Später: echte Module importieren
from .modules.username_lookup import run_username_lookup

# from .modules.email_lookup import run_email_lookup
# from .modules.domain_lookup import run_domain_lookup

def run_case(email=None, username=None, domain=None, generate_report=False, output_path=None):
    session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    findings = []

    if username:
      print(f"\n🔍 Benutzername-Recherche: {username}")
      username_findings = run_username_lookup(username)
      print(f"🔎 Ergebnisse von run_username_lookup(): {len(username_findings)}")
    for f in username_findings:
        f["timestamp"] = session_id
    findings.extend(username_findings)

    if email:
        print(f"\n📧 E-Mail-Recherche: {email}")
        # TODO

    if domain:
        print(f"\n🌐 Domain-Recherche: {domain}")
        # TODO

    if generate_report:
        print("\n📝 Report-Generierung aktiviert")
        from .reporter import generate_markdown_report
        generate_markdown_report(findings, session_id, output_path)

    return findings
