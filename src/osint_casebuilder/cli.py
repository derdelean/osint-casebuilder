import argparse
from .controller import run_case

def run_cli():
    parser = argparse.ArgumentParser(description="OSINT CaseBuilder CLI")

    parser.add_argument("--username", type=str, help="Ziel-Benutzername")
    parser.add_argument("--email", type=str, help="Ziel-E-Mail-Adresse")
    parser.add_argument("--domain", type=str, help="Ziel-Domain")

    parser.add_argument("--fullname", type=str, help="Vollständiger Name der Zielperson")
    parser.add_argument("--location", type=str, help="Standort (z. B. Stadt, Land)")
    parser.add_argument("--keywords", type=str, help="Komma-getrennte Schlüsselwörter (z. B. OSINT, ETH, Schweiz)")
    parser.add_argument("--target-domain", type=str, help="Website/Domain der Person")

    parser.add_argument("--report", action="store_true", help="Markdown-Report erstellen")
    parser.add_argument("--out", type=str, help="Pfad für Output-Ordner")

    args = parser.parse_args()

    run_case(
        email=args.email,
        username=args.username,
        domain=args.domain,
        generate_report=args.report,
        output_path=args.out,
        target_profile={
            "fullname": args.fullname,
            "location": args.location,
            "keywords": args.keywords.split(",") if args.keywords else [],
            "domain": args.target_domain
        }
    )
