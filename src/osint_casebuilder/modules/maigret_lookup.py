import logging

import maigret
from maigret.db_updater import resolve_db_path
from maigret.result import MaigretCheckStatus

from .maigret_common import normalize_meta as _normalize_meta

print("✅ Modul `maigret_lookup` (3000+ Seiten Engine) aktiv")

_DB = None


def _get_db():
    """Load the maigret site database once and cache it. Uses maigret's own
    auto-update (the same as its CLI): a cached ~/.maigret/data.json refreshed from
    upstream at most every 24h, else the bundled copy. The bundled DB goes stale
    fast and stale site checks report CLAIMED for any username."""
    global _DB
    if _DB is None:
        _DB = maigret.MaigretDatabase().load_from_path(
            resolve_db_path("resources/data.json", color=False))
    return _DB


async def run_maigret_lookup_async(username: str, top_sites: int = 500, timeout: int = 8) -> list:
    """Search `username` across the top-N maigret sites with real per-site detection
    and on-page metadata parsing. Returns a list of finding dicts (CLAIMED accounts only)."""
    db = _get_db()
    site_dict = db.ranked_sites_dict(top=top_sites, disabled=False)

    logger = logging.getLogger("maigret")
    logger.setLevel(logging.CRITICAL)

    print(f"🧠 maigret: prüfe {len(site_dict)} Seiten für '{username}'")

    results = await maigret.search(
        username=username,
        site_dict=site_dict,
        logger=logger,
        timeout=timeout,
        is_parsing_enabled=True,
        no_progressbar=True,
        max_connections=50,
    )

    findings = []
    for site_name, info in results.items():
        status = info.get("status")
        if not status or status.status != MaigretCheckStatus.CLAIMED:
            continue

        findings.append({
            "type": "username",
            "value": username,
            "source": status.site_url_user,
            "platform": site_name,
            "meta": _normalize_meta(status.ids_data or {}),
            # pivot material for the correlation phase:
            "ids_usernames": info.get("ids_usernames") or {},
            "ids_links": info.get("ids_links") or [],
        })

    print(f"✅ maigret: {len(findings)} bestätigte Profile")
    return findings
