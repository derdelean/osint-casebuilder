from .cli import run_cli
from utils.validation import validate_inputs
import sys

def main():
    args = run_cli(return_args=True)  # Modify run_cli to return args if needed

    if not validate_inputs(
        args.username,
        args.fullname,
        args.location,
        args.keywords,
        args.target_domain
    ):
        print("❌ Please provide at least one valid input (username, fullname, location, keywords, or target domain).")
        sys.exit(1)

    run_cli()

if __name__ == "__main__":
    main()
