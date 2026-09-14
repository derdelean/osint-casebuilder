def score_profile(profile, fullname=None, location=None, keywords=None, domain=None) -> float:
    score = 0
    total = 1  # to avoid division by zero

    if not profile:
        return 0.0

    if fullname and profile.get("fullname"):
        total += 1
        if fullname.lower() in profile["fullname"].lower():
            score += 1

    if location and profile.get("location"):
        total += 1
        if location.lower() in profile["location"].lower():
            score += 1

    # Blank entries (an empty form field, "a,,b") would match every bio via `"" in bio`.
    keywords = [k.strip() for k in (keywords or []) if k.strip()]
    if keywords and profile.get("bio"):
        total += 1
        bio_lower = profile["bio"].lower()
        matches = sum(1 for kw_item in keywords if kw_item.lower() in bio_lower)
        score += matches / len(keywords)

    if domain and profile.get("website"):
        total += 1
        if domain.lower() in profile["website"].lower():
            score += 1

    if profile.get("followers") is not None:
        total += 1
        if profile["followers"] >= 100:
            score += 1

    return round(score / total, 2)


def matched_hints(profile, fullname=None, location=None, keywords=None, domain=None) -> list:
    """Names of the operator-supplied identity hints this profile's meta matches.
    Same comparisons as score_profile, minus followers: popularity isn't identity."""
    profile = profile or {}
    hits = [name for name, hint, key in (("fullname", fullname, "fullname"),
                                          ("location", location, "location"))
            if hint and profile.get(key) and hint.lower() in str(profile[key]).lower()]
    keywords = [k.strip() for k in (keywords or []) if k.strip()]
    if keywords and profile.get("bio") and any(k.lower() in profile["bio"].lower() for k in keywords):
        hits.append("keywords")
    if domain and profile.get("website") and domain.lower() in str(profile["website"]).lower():
        hits.append("domain")
    return hits
