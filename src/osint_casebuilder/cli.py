import argparse
import asyncio
from .controller import run_case

def run_cli(return_args=False):
    parser = argparse.ArgumentParser(description="OSINT CaseBuilder CLI")

    parser.add_argument("--username", type=str, help="Ziel-Benutzername")
    parser.add_argument("--email", type=str, help="Ziel-E-Mail-Adresse")
    parser.add_argument("--domain", type=str, help="Ziel-Domain")
    parser.add_argument("--phone", type=str, help="Ziel-Telefonnummer (z. B. +41441234567)")
    parser.add_argument("--phone-region", type=str,
                        help="2-Buchstaben-Region für nationale Nummern (z. B. CH, US)")

    parser.add_argument("--fullname", type=str, help="Vollständiger Name der Zielperson")
    parser.add_argument("--location", type=str, help="Standort (z. B. Stadt, Land)")
    parser.add_argument("--keywords", type=str, help="Komma-getrennte Schlüsselwörter (z. B. OSINT, ETH, Schweiz)")
    parser.add_argument("--target-domain", type=str, help="Website/Domain der Person")

    parser.add_argument("--report", action="store_true", help="Markdown-Report erstellen")
    parser.add_argument("--out", type=str, help="Pfad für Output-Ordner")
    parser.add_argument("--top-sites", type=int, default=500,
                        help="Anzahl der (nach Popularität) geprüften Seiten (mehr = gründlicher, langsamer)")
    parser.add_argument("--all-sites", action="store_true",
                        help="Alle ~2500 maigret-Seiten prüfen (maximale Abdeckung, deutlich langsamer)")
    parser.add_argument("--pivot-depth", type=int, default=0,
                        help="Auto-Pivot-Tiefe: entdeckte Benutzernamen rekursiv weitersuchen (0 = aus)")
    parser.add_argument("--infra", action="store_true",
                        help="Optionale Infra-/Breach-Intel: crt.sh Subdomains (keyless) + "
                             "HIBP Breaches (benötigt HIBP_API_KEY). Standard: aus")

    parser.add_argument("--db", type=str, default="cases.db", help="SQLite-Case-Datenbank")
    parser.add_argument("--no-save", action="store_true", help="Case nicht in der DB speichern")
    parser.add_argument("--list-cases", action="store_true", help="Gespeicherte Cases auflisten und beenden")
    parser.add_argument("--load-case", type=int, help="Gespeicherten Case (per ID) ausgeben und beenden")

    args = parser.parse_args()

    if return_args:
        return args

    asyncio.run(run_case(
        email=args.email,
        username=args.username,
        domain=args.domain,
        generate_report=args.report,
        output_path=args.out,
        fullname=args.fullname,
        location=args.location,
        keywords=args.keywords.split(",") if args.keywords else [],
        target_domain=args.target_domain,
        phone=args.phone,
        phone_region=args.phone_region,
        top_sites=(100000 if args.all_sites else args.top_sites),
        pivot_depth=args.pivot_depth,
        infra=args.infra,
        save=not args.no_save,
        db_path=args.db
    ))
