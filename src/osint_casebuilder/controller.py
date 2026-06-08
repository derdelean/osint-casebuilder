from datetime import datetime
from osint_casebuilder.modules.username_lookup import run_username_lookup_async
from osint_casebuilder.modules.github_profile_scraper import scrape_github_profile_async
from osint_casebuilder.modules.email_lookup import run_email_lookup_async
from osint_casebuilder.modules.domain_lookup import run_domain_lookup_async
from osint_casebuilder.modules.confidence_scorer import score_profile
from osint_casebuilder.modules.correlation import correlate, export_graph_html
from osint_casebuilder.modules.case_store import save_case as store_case
from osint_casebuilder.modules.social_enrich import run_social_enrichment_async
from osint_casebuilder.reporter import generate_markdown_report


def _merge_or_add(findings, enrichment, score_args, session_id):
    """Merge an enrichment finding into the same-platform finding (filling only
    empty meta fields), else append it. Re-scores the affected finding."""
    match = next(
        (f for f in findings if f.get("platform", "").lower() == enrichment["platform"].lower()),
        None,
    )
    if match:
        meta = match.setdefault("meta", {})
        for k, v in (enrichment.get("meta") or {}).items():
            if v not in (None, "") and not meta.get(k):
                meta[k] = v
        match["score"] = score_profile(meta, *score_args)
    else:
        enrichment["timestamp"] = session_id
        enrichment["score"] = score_profile(enrichment.get("meta", {}), *score_args)
        findings.append(enrichment)


_PIVOT_CAPS = {"username": 5, "email": 3}


def _harvest_pivot_seeds(findings, searched):
    """Collect new, unseen pivot seeds per type (username, email), capped. Uses the
    correlation entity extractor so e.g. an email embedded in a profile's metadata
    becomes an email seed (the email↔username cross-pivot)."""
    from osint_casebuilder.modules.correlation import extract_entities
    seeds = {t: [] for t in _PIVOT_CAPS}
    for f in findings:
        for etype, value in extract_entities(f):
            if etype not in seeds or value in searched[etype] or value in seeds[etype]:
                continue
            if len(seeds[etype]) < _PIVOT_CAPS[etype]:
                seeds[etype].append(value)
    return seeds


async def _lookup_username(username, top_sites, interactive=True):
    """Username engine with graceful degradation:
    in-process maigret (engine venv) → maigret subprocess (any env with a binary)
    → basic HTTP-200 sweep (last resort)."""
    try:
        from osint_casebuilder.modules.maigret_lookup import run_maigret_lookup_async
        return await run_maigret_lookup_async(username, top_sites=top_sites)
    except ImportError:
        pass
    try:
        from osint_casebuilder.modules.maigret_runner import run_maigret_subprocess_async
        result = await run_maigret_subprocess_async(username, top_sites=top_sites)
        if interactive:
            print(f"🧩 maigret (subprocess): {len(result)} Profile für '{username}'")
        return result
    except FileNotFoundError:
        pass
    if interactive:
        print("⚠️  maigret nicht verfügbar – nutze einfachen HTTP-Lookup")
    return await run_username_lookup_async(username)


async def run_case(
    email=None,
    username=None,
    domain=None,
    generate_report=False,
    output_path=None,
    fullname=None,
    location=None,
    keywords=None,
    target_domain=None,
    phone=None,
    phone_region=None,
    top_sites=500,
    pivot_depth=0,
    infra=False,
    save=True,
    db_path="cases.db",
    interactive=True
):
    session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    findings = []

    if username:
        if interactive:
            print(f"\n🔍 Username lookup: {username}")

        # Primary engine: maigret (3000+ sites, real per-site detection + on-page
        # metadata), via in-process import or subprocess, falling back to the basic
        # HTTP sweep. See _lookup_username.
        username_findings = await _lookup_username(username, top_sites, interactive)

        if interactive:
            print(f"🔎 Found: {len(username_findings)} profiles")

        for f in username_findings:
            f["timestamp"] = session_id

            # fallback platform detection from URL
            if "platform" not in f and "source" in f:
                try:
                    f["platform"] = f["source"].split("//")[1].split("/")[0]
                except Exception:
                    f["platform"] = "unknown"

            # Apply confidence score to each profile
            f["score"] = score_profile(
                f.get("meta", {}),
                fullname,
                location,
                keywords or [],
                target_domain
            )

        findings.extend(username_findings)

        # Deep enrichment: dedicated public-API scrapers add richer metadata than
        # maigret extracts (GitHub bio/website; Reddit/HN karma + account age).
        # Each is merged into the matching platform finding, else appended.
        score_args = (fullname, location, keywords or [], target_domain)

        profile = await scrape_github_profile_async(username)
        if profile:
            if interactive:
                print("🧠 GitHub Profile gefunden")
            _merge_or_add(findings, {
                "type": "username", "value": username,
                "source": profile["profile_url"], "platform": "GitHub", "meta": profile,
            }, score_args, session_id)

        for enrichment in await run_social_enrichment_async(username):
            _merge_or_add(findings, enrichment, score_args, session_id)

    if email:
        if interactive:
            print(f"\n🔍 Email lookup: {email}")
        email_findings = await run_email_lookup_async(email)

        # holehe: which of ~121 sites is this email registered on? (engine venv)
        try:
            from osint_casebuilder.modules.holehe_lookup import run_holehe_lookup_async
            email_findings += await run_holehe_lookup_async(email)
        except ImportError:
            if interactive:
                print("⚠️  holehe nicht installiert – überspringe Registrierungs-Check")

        # optional breach intel (off by default; needs HIBP_API_KEY)
        if infra:
            from osint_casebuilder.modules.breach_lookup import run_hibp_lookup_async
            email_findings += await run_hibp_lookup_async(email)

        if interactive:
            print(f"🔎 Found: {len(email_findings)} email findings")
        for f in email_findings:
            f["timestamp"] = session_id
        findings.extend(email_findings)

    if phone:
        if interactive:
            print(f"\n🔍 Phone lookup: {phone}")
        try:
            from osint_casebuilder.modules.phone_lookup import run_phone_lookup
            phone_findings = run_phone_lookup(phone, phone_region)
        except ImportError:
            if interactive:
                print("⚠️  phonenumbers nicht installiert – überspringe Phone-Lookup")
            phone_findings = []

        # phone → social accounts via ignorant (Instagram/Amazon/Snapchat, engine venv)
        if phone_findings:
            meta0 = phone_findings[0]["meta"]
            try:
                from osint_casebuilder.modules.phone_accounts_lookup import run_ignorant_lookup_async
                phone_findings += await run_ignorant_lookup_async(
                    meta0["country_code"], meta0["national_number"])
            except ImportError:
                if interactive:
                    print("⚠️  ignorant nicht installiert – überspringe Phone-Accounts")

        for f in phone_findings:
            f["timestamp"] = session_id
        findings.extend(phone_findings)
        if interactive:
            print(f"🔎 Found: {len(phone_findings)} phone findings")

    if domain:
        if interactive:
            print(f"\n🔍 Domain lookup: {domain}")
        domain_findings = await run_domain_lookup_async(domain)

        # optional infra intel (off by default): keyless crt.sh + key-gated
        # Shodan/Censys (each skips cleanly without its env-var API key).
        if infra:
            from osint_casebuilder.modules.infra_lookup import (
                run_crtsh_subdomains_async, run_shodan_domain_async, run_censys_hosts_async)
            domain_findings += await run_crtsh_subdomains_async(domain)
            domain_findings += await run_shodan_domain_async(domain)
            domain_findings += await run_censys_hosts_async(domain)

        if interactive:
            print(f"🔎 Found: {len(domain_findings)} domain findings")
        for f in domain_findings:
            f["timestamp"] = session_id
        findings.extend(domain_findings)

    # Auto-pivot: recursively search newly discovered usernames AND emails
    # (cross-type), depth-limited and deduped against already-searched seeds.
    if pivot_depth > 0:
        searched = {
            "username": {username.lower()} if username else set(),
            "email": {email.lower()} if email else set(),
        }
        for round_n in range(pivot_depth):
            seeds = _harvest_pivot_seeds(findings, searched)
            if not any(seeds.values()):
                break
            if interactive:
                desc = ", ".join(f"{t}={v}" for t, v in seeds.items() if v)
                print(f"\n🔁 Pivot {round_n + 1}: {desc}")

            for u in seeds["username"]:
                searched["username"].add(u)
                pivoted = await _lookup_username(u, top_sites, interactive=False)
                for f in pivoted:
                    f["timestamp"] = session_id
                    f["pivoted_from"] = u
                    f["score"] = score_profile(
                        f.get("meta", {}), fullname, location, keywords or [], target_domain
                    )
                findings.extend(pivoted)

            for e in seeds["email"]:
                searched["email"].add(e)
                pivoted = await run_email_lookup_async(e)
                try:
                    from osint_casebuilder.modules.holehe_lookup import run_holehe_lookup_async
                    pivoted += await run_holehe_lookup_async(e)
                except ImportError:
                    pass
                for f in pivoted:
                    f["timestamp"] = session_id
                    f["pivoted_from"] = e
                findings.extend(pivoted)

    # Correlate everything into an entity graph.
    summary = correlate(findings)
    if interactive:
        print(f"\n🔗 Correlation: {summary['distinct_entities']} entities, "
              f"{len(summary['corroborated'])} corroborated across platforms, "
              f"{summary['clusters']} cluster(s)")

    # Persist the investigation.
    if save:
        seed = {k: v for k, v in {
            "username": username, "email": email, "domain": domain, "phone": phone,
            "fullname": fullname, "location": location, "keywords": keywords,
            "target_domain": target_domain,
        }.items() if v}
        try:
            case_id = store_case(seed, findings, summary, db_path, created_at=session_id)
            if interactive:
                print(f"💾 Case #{case_id} gespeichert in {db_path}")
        except Exception as e:
            if interactive:
                print(f"⚠️  Case speichern fehlgeschlagen: {e}")

    if generate_report:
        if interactive:
            print("\n📝 Generating report...")
        report_path = generate_markdown_report(findings, session_id, output_path, summary)
        # best-effort interactive graph next to the report (needs pyvis)
        if report_path:
            graph_path = report_path.rsplit(".", 1)[0] + "_graph.html"
            if export_graph_html(findings, graph_path) and interactive:
                print(f"🕸️  Graph: {graph_path}")

    return findings
