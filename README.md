# 🕵️‍♂️ OSINT CaseBuilder

## 🚀 What is OSINT CaseBuilder?

OSINT CaseBuilder is a modular, extensible tool that helps investigators, cybersecurity professionals, and journalists rapidly collect and analyze public data on people, usernames, and digital footprints across the web.

It supports:

✅ Username enumeration across 10+ platforms
✅ GitHub metadata scraping (followers, bio, location, etc.)
✅ Smart confidence scoring using NLP & metadata
✅ Beautiful markdown + JSON reports
✅ PyQt5 desktop interface (with progress spinner + sortable table)
✅ Easy CLI interface for headless environments
✅ Built with async Python and a scalable architecture

## 🔍 Why OSINT CaseBuilder?

Because finding the right digital footprint shouldn’t require 100 tabs, a million tools, and your sanity.
Whether you're verifying a suspect's identity, mapping aliases, or preparing a digital profile for court or internal review — this tool helps you build a case file you can trust.

## ✨ Features

- Username Variant Generator: Creates dozens of smart variations (john.doe → johnd, jdoe, johndoe1990, etc.)
- Multi-platform Lookup: GitHub, Reddit, TikTok, Instagram, Twitter, Steam, Pinterest, and more
- Confidence Scoring: Automatically rates profile relevance based on name, location, bio & domain
- Reports: Generate Markdown + JSON reports, exportable to PDF (planned)
- Fast & Async: Built on httpx and asyncio for blazing speed
- GUI Option: Run the tool with a slick PyQt5 interface
- CLI Option: Use it in scripts or headless servers

## ⚙️ Getting Started

```bash
git clone https://github.com/yourusername/osint-casebuilder.git
cd osint-casebuilder
python -m venv venv
source venv/bin/activate # or .\\venv\\Scripts\\activate on Windows
pip install -r requirements.txt
```

## 🧪 Run the CLI

```bash
python -m osint_casebuilder.main --username johndoe --fullname "John Doe" --location "Berlin" --keywords "python,infosec" --target-domain "johndoe.dev" --report

```

## 🖱️ Run the GUI

```bash
python -m osint_casebuilder.gui
```

## 🧱 Architecture Overview

- main.py / cli.py: Entry points
- modules/: All functional units (username lookup, scoring, etc.)
- reporter.py: Report generation logic
- controller.py: Orchestrates everything
- gui.py: PyQt5 interface

## 🔐 Disclaimer

This tool is for educational and ethical use only. Use responsibly and only on targets you are legally allowed to investigate.

## 🧠 Future Ideas

- Browserless scraping for TikTok/Instagram bios
- Confidence scoring for Reddit, Steam, Twitter
- PDF report export
- Threat actor detection modules
- Saved investigations database

## 👨‍💻 Author

Built with ❤️ by derdelean. Inspired by Sherlock, recon-ng, and the needs of real OSINT analysts.
