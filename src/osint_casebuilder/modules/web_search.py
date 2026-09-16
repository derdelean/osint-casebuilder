"""Name → open-web search (keyless, DuckDuckGo's HTML endpoint).

Every other discovery module here is *selector*-based: hand it a username, email,
phone or domain and it enumerates accounts. Nothing turned a person's *name* into
a selector, so a name-only case found nothing at all and the pivot engine started
with no seeds — which is why a plain web search beat the tool on the one input
people naturally start from.

This searches the open web for the name, and extracts profile handles from the
results into `ids_usernames`, the same pivot channel maigret uses. A hit on
`instagram.com/some.handle` therefore becomes a username seed and the existing
pipeline takes over from there.

Keyless and httpx-only, so it runs in every environment. This scrapes an HTML
endpoint rather than calling an API: it rate-limits, and its markup can change
without notice, so the result count is reported rather than assumed.
"""

import re
import sys
import urllib.parse

import httpx
from bs4 import BeautifulSoup

print("✅ Modul `web_search` (keyless Name→Web) aktiv", file=sys.stderr)

_ENDPOINT = "https://html.duckduckgo.com/html/"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
}

# Only URL shapes whose first path segment IS the account handle. Anything looser
# (github.com/owner/repo, linkedin.com/company/...) would manufacture handles that
# were never there, and the pivot engine would then search for them as if real.
_PROFILE_PATTERNS = (
    ("GitHub", re.compile(r"^https?://(?:www\.)?github\.com/([A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?)/?$", re.I)),
    ("Instagram", re.compile(r"^https?://(?:www\.)?instagram\.com/([A-Za-z0-9._]{1,30})/?$", re.I)),
    ("LinkedIn", re.compile(r"^https?://(?:[a-z]{2}\.)?linkedin\.com/in/([A-Za-z0-9-]{3,100})", re.I)),
    ("X", re.compile(r"^https?://(?:www\.)?(?:twitter|x)\.com/([A-Za-z0-9_]{1,15})/?$", re.I)),
    ("Reddit", re.compile(r"^https?://(?:www\.)?reddit\.com/u(?:ser)?/([A-Za-z0-9_-]{3,20})", re.I)),
    ("Telegram", re.compile(r"^https?://t\.me/([A-Za-z0-9_]{5,32})/?$", re.I)),
    ("Medium", re.compile(r"^https?://medium\.com/@([A-Za-z0-9._-]{1,50})/?$", re.I)),
)

# First-segment paths on those hosts that are site furniture, not people.
_NOT_HANDLES = {
    "about", "home", "login", "signup", "session", "search", "explore", "help",
    "legal", "privacy", "terms", "features", "pricing", "enterprise", "settings",
    "jobs", "careers", "blog", "news", "events", "pulse", "learning", "share",
}


def _unwrap(href: str) -> str:
    """DuckDuckGo sometimes returns results via its /l/?uddg= redirector."""
    if "duckduckgo.com/l/" in href:
        target = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("uddg")
        if target:
            return target[0]
    return href


def _host_of(url: str) -> str:
    return urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")


def extract_handle(url: str):
    """(platform, handle) if the URL is a personal profile page, else None."""
    for platform, pattern in _PROFILE_PATTERNS:
        m = pattern.match(url or "")
        if m and m.group(1).lower() not in _NOT_HANDLES:
            return platform, m.group(1)
    return None


def parse_results(html: str, query: str, max_results: int) -> list:
    """Map the SERP HTML onto finding dicts. Separate from the fetch so the
    parser can be tested without network."""
    soup = BeautifulSoup(html, "html.parser")
    findings = []
    for result in soup.select("div.result")[:max_results]:
        anchor = result.select_one("a.result__a")
        if not anchor or not anchor.get("href"):
            continue
        url = _unwrap(anchor["href"])
        if not url.startswith("http"):
            continue
        snippet_el = result.select_one(".result__snippet")
        finding = {
            "type": "web",
            "value": anchor.get_text(strip=True) or url,
            "source": url,
            "platform": _host_of(url) or "web",
            "meta": {
                "title": anchor.get_text(strip=True),
                "snippet": snippet_el.get_text(" ", strip=True) if snippet_el else "",
                "query": query,
            },
        }
        handle = extract_handle(url)
        if handle:
            platform, name = handle
            finding["meta"]["handle"] = f"{platform}: {name}"
            # same pivot channel maigret populates → _harvest_pivot_seeds picks it up
            finding["ids_usernames"] = {name: platform}
        findings.append(finding)
    return findings


async def run_web_search_async(query: str, max_results: int = 20, stats: dict | None = None) -> list:
    """Search the open web for `query`; one finding per result, handles extracted."""
    print(f"🌐 web_search: suche '{query}'")
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            response = await client.post(_ENDPOINT, data={"q": query}, headers=_HEADERS)
        response.raise_for_status()
    except Exception as exc:
        # Scraped endpoint: blocked or reshaped is a normal outcome, not a crash.
        print(f"⚠️  web_search: Suche fehlgeschlagen ({type(exc).__name__}) – übersprungen")
        if stats is not None:
            stats.update(results=0, handles=0, ok=False)
        return []

    findings = parse_results(response.text, query, max_results)
    handles = sum(1 for f in findings if f.get("ids_usernames"))
    if stats is not None:
        stats.update(results=len(findings), handles=handles, ok=True)
    print(f"✅ web_search: {len(findings)} Treffer, {handles} Profil-Handle(s) als Pivot-Seed")
    return findings
