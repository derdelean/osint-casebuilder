"""Deep enrichment for high-value social platforms via keyless public APIs
(Reddit, Hacker News). These return richer profile metadata (karma, account age,
bio) than maigret's generic extraction; the controller merges them into the
matching maigret finding. httpx-only → runs in any environment."""

import asyncio
from datetime import datetime, timezone

import httpx

print("✅ Modul `social_enrich` (Reddit + HackerNews, keyless) aktiv")

_UA = "osint-casebuilder/1.0 (research)"


def _utc_date(ts):
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def _reddit_finding(data, username):
    """Pure: map a Reddit about.json `data` object to a finding."""
    sub = data.get("subreddit") or {}
    return {
        "type": "username",
        "value": username,
        "source": f"https://www.reddit.com/user/{data.get('name', username)}",
        "platform": "Reddit",
        "meta": {
            "username": data.get("name"),
            "karma": data.get("total_karma"),
            "link_karma": data.get("link_karma"),
            "comment_karma": data.get("comment_karma"),
            "joined": _utc_date(data.get("created_utc")),
            "verified": data.get("verified"),
            "is_gold": data.get("is_gold"),
            "bio": sub.get("public_description") or None,
        },
    }


def _hn_finding(data, username):
    """Pure: map a Hacker News user object to a finding."""
    return {
        "type": "username",
        "value": username,
        "source": f"https://news.ycombinator.com/user?id={data.get('id', username)}",
        "platform": "HackerNews",
        "meta": {
            "username": data.get("id"),
            "karma": data.get("karma"),
            "joined": _utc_date(data.get("created")),
            "bio": data.get("about") or None,
        },
    }


async def _reddit(client, username):
    try:
        resp = await client.get(f"https://www.reddit.com/user/{username}/about.json")
        if resp.status_code == 200:
            data = (resp.json() or {}).get("data") or {}
            if data.get("name"):
                return _reddit_finding(data, username)
    except (httpx.RequestError, ValueError):
        pass
    return None


async def _hackernews(client, username):
    try:
        resp = await client.get(f"https://hacker-news.firebaseio.com/v0/user/{username}.json")
        if resp.status_code == 200 and resp.text.strip() not in ("", "null"):
            data = resp.json() or {}
            if data.get("id"):
                return _hn_finding(data, username)
    except (httpx.RequestError, ValueError):
        pass
    return None


async def run_social_enrichment_async(username: str) -> list:
    """Fetch richer profile data for `username` on Reddit + Hacker News (keyless)."""
    async with httpx.AsyncClient(timeout=12.0, follow_redirects=True,
                                 headers={"User-Agent": _UA}) as client:
        results = await asyncio.gather(_reddit(client, username), _hackernews(client, username))
    findings = [f for f in results if f]
    print(f"✅ social_enrich: {len(findings)} angereicherte Profile")
    return findings
