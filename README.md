# 🕵️‍♂️ OSINT CaseBuilder

OSINT CaseBuilder collects public data on a target from a **username, email,
phone, or domain** (plus optional identity hints), correlates everything into an
entity graph, and emits Markdown/JSON reports. Three frontends — CLI, PyQt5
desktop GUI, and Streamlit — funnel into one async orchestrator.

## 🔍 What it does

Give it any combination of inputs and it will, where applicable:

- **Username discovery via Maigret** — real per-site detection across 4500+ sites
  (top 500 by default, all with `--all-sites`), keeping only claimed accounts and
  parsing on-page metadata into each finding. The site database auto-refreshes,
  and every run also searches a random control handle: sites that report *that*
  as found are discarded, which removes most false positives.
- **Deep profile enrichment** — GitHub (bio/website via the API) and Hacker News
  (karma/about), richer than Maigret's generic extraction. Reddit (karma/age) is
  best-effort: Reddit currently blocks most keyless requests.
- **Email intelligence** — keyless MX (DNS-over-HTTPS) + Gravatar, then `holehe`
  to find which of ~121 sites the email is *registered* on (recovery hints
  captured where exposed).
- **Phone intelligence** — offline `libphonenumber` (validity, carrier, region,
  line type, timezones), then `ignorant` for phone→social registration checks
  (Instagram/Amazon/Snapchat).
- **Domain intelligence** — RDAP/WHOIS + A/NS records via DNS-over-HTTPS.
- **Optional infra/breach intel** (`--infra`, off by default) — crt.sh subdomain
  enumeration (keyless), plus Shodan/Censys hosts and Have I Been Pwned breaches
  when the relevant API keys are present in the environment.
- **Correlation** — extracts typed entities from every finding and reports the
  attributes corroborated across multiple sources, identity clusters, and an edge
  list (interactive pyvis graph export when available).
- **Auto-pivot** (`--pivot-depth N`) — recursively searches usernames and emails
  discovered mid-run (the email↔username pivot).
- **Confidence scoring** — rates each profile's relevance against the supplied
  name/location/keywords/domain so the real owner rises above lookalikes.
- **Persistence** — every run auto-saves to a SQLite case database; list and
  reload past cases from the CLI.
- **Reports** — Markdown + JSON, with a correlation summary, written to
  `reports/`.

## ⚙️ Getting started

The Maigret engine pulls a heavy, tightly-pinned dependency tree that conflicts
with the Streamlit/PyQt pins, so it lives in its **own Python 3.12 venv**.

```bash
git clone https://github.com/derdelean/osint-casebuilder.git
cd osint-casebuilder

# Engine venv (Maigret) — Python 3.12, reliable wheels for the C-extension deps
~/.pyenv/versions/3.12.13/bin/python -m venv .venv
./.venv/bin/pip install -r requirements-engine.txt
```

> **All commands run from `src/`.** The package imports the top-level `utils`
> package, so imports fail elsewhere. Reports are written CWD-relative to
> `reports/`, i.e. `src/reports/`.

The Streamlit/PyQt frontends use a separate environment (`requirements.txt`) and
can't import Maigret directly, but they still reach the real engine through a
subprocess bridge as long as `.venv/bin/maigret` exists (or `$MAIGRET_BIN` is
set); otherwise they degrade to a basic HTTP-200 sweep.

## 🧪 Run the CLI

```bash
cd src

# Any combination of --username / --email / --phone / --domain + identity hints.
../.venv/bin/python -m osint_casebuilder.main \
  --username johndoe --fullname "John Doe" --location "Berlin" \
  --keywords "python,infosec" --target-domain johndoe.dev \
  --phone "+41441234567" --top-sites 500 --pivot-depth 1 --report

# Optional infra/breach intel. Paid sources run only if their env keys are set.
HIBP_API_KEY=xxx SHODAN_API_KEY=yyy ../.venv/bin/python -m osint_casebuilder.main \
  --domain example.com --email a@example.com --infra --report

# Case management (no target inputs needed; works in any environment)
../.venv/bin/python -m osint_casebuilder.main --list-cases
../.venv/bin/python -m osint_casebuilder.main --load-case 1
```

Key flags: `--all-sites` (full Maigret sweep), `--pivot-depth N`
(recursive pivots), `--infra` (subdomain/breach intel), `--db PATH` /
`--no-save` (case persistence), `--phone-region XX` (for national numbers).

## 🖱️ Run the GUI / web app

```bash
# PyQt5 desktop interface
python -m osint_casebuilder.gui

# Streamlit web frontend (run from src/)
streamlit run app_streamlit.py
```

## 🧱 Architecture

All three frontends call `controller.run_case()` — the single async entry point.
Data flows as a list of `finding` dicts through discovery → scoring → reporting.

- `main.py` / `cli.py` — CLI entry + argument parsing
- `controller.py` — orchestrates discovery, enrichment, pivot, correlation, save
- `modules/` — discovery and analysis units (Maigret, email/phone/domain, holehe,
  ignorant, social enrichment, infra/breach, correlation, scoring, case store)
- `reporter.py` — Markdown/HTML/JSON report rendering
- `gui.py` / `app_streamlit.py` — PyQt5 and Streamlit frontends
- `utils/validation.py` — input gating (requires at least one non-empty field)

## ✅ Tests

Stdlib `unittest`. The full suite runs in the engine venv; engine-dependency
tests skip elsewhere.

```bash
cd src && ../.venv/bin/python -m unittest discover -s tests -p "test_*.py"
```

## 🔐 Disclaimer

This tool is for educational and ethical use only. Use responsibly and only on
targets you are legally allowed to investigate.

## 👨‍💻 Author

Built by derdelean. Inspired by Maigret, holehe, Sherlock, and recon-ng.
