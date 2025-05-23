import argparse
from .controller import run_case

def run_cli():
    parser = argparse.ArgumentParser(description="🕵️ OSINT CaseBuilder CLI")
    parser.add_argument('--email', type=str, help='Email address to investigate')
    parser.add_argument('--username', type=str, help='Username to investigate')
    parser.add_argument('--domain', type=str, help='Domain to investigate')
    parser.add_argument('--report', action='store_true', help='Generate report after run')
    parser.add_argument('--out', type=str, help='Speicherort für Report-Dateien')


    args = parser.parse_args()
    
    print("CLI funktioniert ✅")
    print(f"E-Mail: {args.email}")
    print(f"Benutzername: {args.username}")
    print(f"Domain: {args.domain}")
    print(f"Report generieren: {args.report}")

    run_case(
        email=args.email,
        username=args.username,
        domain=args.domain,
        generate_report=args.report,
        output_path=args.out
    )

