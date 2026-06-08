from .cli import run_cli
from utils.validation import validate_inputs
import sys

def main():
    args = run_cli(return_args=True)  # Modify run_cli to return args if needed

    # Case-management commands short-circuit (no target inputs needed).
    if args.list_cases:
        from osint_casebuilder.modules.case_store import list_cases
        cases = list_cases(args.db)
        if not cases:
            print("Keine Cases gespeichert.")
        for c in cases:
            print(f"#{c['id']}  {c['created_at']}  findings={c['n_findings']}  seed={c['seed']}")
        return
    if args.load_case is not None:
        import json
        from osint_casebuilder.modules.case_store import load_case
        case = load_case(args.load_case, args.db)
        if not case:
            print(f"❌ Case #{args.load_case} not found")
            sys.exit(1)
        print(json.dumps(case, indent=2, default=str, ensure_ascii=False))
        return

    if not validate_inputs(
        args.username,
        args.fullname,
        args.location,
        args.keywords.split(",") if args.keywords else [],
        args.target_domain,
        args.email,
        args.domain,
        args.phone
    ):
        print("❌ Please provide at least one valid input (username, fullname, location, keywords, target domain, email, phone, or domain).")
        sys.exit(1)

    run_cli()

if __name__ == "__main__":
    main()
