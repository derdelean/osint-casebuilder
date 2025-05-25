from datetime import datetime
from .modules.username_lookup import run_username_lookup_async
from .modules.github_profile_scraper import scrape_github_profile_async
from .modules.confidence_scorer import score_profile
from .reporter import generate_markdown_report


async def run_case(
    email=None,
    username=None,
    domain=None,
    generate_report=False,
    output_path=None,
    fullname=None,
    location=None,
    keywords=None,
    target_domain=None
):
    session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    findings = []

    if username:
        print(f"\n🔍 Username lookup: {username}")
        username_findings = await run_username_lookup_async(username)
        print(f"🔎 Found: {len(username_findings)} profiles")

        for f in username_findings:
            f["timestamp"] = session_id

            # fallback platform detection from URL
            if "platform" not in f and "source" in f:
                try:
                    f["platform"] = f["source"].split("//")[1].split("/")[0]
                except Exception:
                    f["platform"] = "unknown"

            # score every profile
            if "github.com" in f.get("source", ""):
                f["score"] = 1.0  # fallback
            else:
                f["score"] = 0.2  # generic trust score

        findings.extend(username_findings)

        # GitHub metadata scraping + confidence scoring
        profile = await scrape_github_profile_async(username)
        if profile:
            print("🧠 GitHub Profile:")
            print(profile)
            profile_finding = {
                "type": "username",
                "value": username,
                "source": profile["profile_url"],
                "platform": "GitHub",
                "timestamp": session_id,
                "meta": profile,
                "score": score_profile(profile, fullname, location, keywords, target_domain)
            }
            findings.append(profile_finding)

    if generate_report:
        print("\n📝 Generating report...")
        generate_markdown_report(findings, session_id, output_path)

    return findings
