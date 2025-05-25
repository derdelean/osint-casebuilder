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

    if keywords and profile.get("bio"):
        total += 1
        matches = sum(1 for kw in keywords.split(",") if kw.lower().strip() in profile["bio"].lower())
        if matches:
            score += matches / len(keywords.split(","))

    if domain and profile.get("website"):
        total += 1
        if domain.lower() in profile["website"].lower():
            score += 1

    if profile.get("followers") is not None:
        total += 1
        if profile["followers"] >= 100:
            score += 1

    return round(score / total, 2)
