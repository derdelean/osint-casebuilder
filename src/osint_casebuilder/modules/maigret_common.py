"""Shared helpers for the maigret integrations. Imports NO third-party packages
(in particular not `maigret`), so it is safe to import from any environment —
both the in-process engine path and the subprocess bridge use it."""


def normalize_meta(ids: dict) -> dict:
    """Map maigret's extracted ids_data onto the keys confidence_scorer expects,
    while preserving every raw field maigret found."""
    meta = dict(ids or {})

    if ids.get("name") and not meta.get("fullname"):
        meta["fullname"] = ids["name"]
    if ids.get("description") and not meta.get("bio"):
        meta["bio"] = ids["description"]
    if ids.get("created_at") and not meta.get("joined"):
        meta["joined"] = ids["created_at"]

    fc = ids.get("follower_count")
    if fc is not None:
        try:
            meta["followers"] = int(fc)
        except (ValueError, TypeError):
            pass

    return meta


def ids_to_pivots(ids: dict):
    """Derive (ids_usernames, ids_links) pivot material from an ids_data dict."""
    ids = ids or {}
    usernames = {
        v: "username"
        for k, v in ids.items()
        if "username" in str(k).lower() and isinstance(v, str) and v
    }
    links = [v for v in ids.values() if isinstance(v, str) and v.startswith("http")]
    return usernames, links
