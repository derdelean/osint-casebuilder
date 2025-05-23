from difflib import SequenceMatcher

def score_profile(profile: dict, target: dict) -> float:
    score = 0.0
    weight_total = 0

    weights = {
        "fullname": 0.3,
        "location": 0.2,
        "bio_keywords": 0.3,
        "website": 0.1,
        "followers": 0.1
    }

    # Fullname-similarity
    if profile.get("fullname") and target.get("fullname"):
        sim = SequenceMatcher(None, profile["fullname"].lower(), target["fullname"].lower()).ratio()
        score += sim * weights["fullname"]
        weight_total += weights["fullname"]

    # location-similarity
    if profile.get("location") and target.get("location"):
        loc_sim = SequenceMatcher(None, profile["location"].lower(), target["location"].lower()).ratio()
        score += loc_sim * weights["location"]
        weight_total += weights["location"]

    # Bio-Keywords
    if profile.get("bio") and target.get("keywords"):
        bio = profile["bio"].lower()
        hits = sum(1 for kw in target["keywords"] if kw.lower() in bio)
        if target["keywords"]:
            score += (hits / len(target["keywords"])) * weights["bio_keywords"]
            weight_total += weights["bio_keywords"]

    # Website-Domain included?
    if profile.get("website") and target.get("domain"):
        if target["domain"].lower() in profile["website"].lower():
            score += weights["website"]
        weight_total += weights["website"]

    # Followers
    if isinstance(profile.get("followers"), int):
        if profile["followers"] >= 500:
            score += weights["followers"]
        elif profile["followers"] >= 100:
            score += weights["followers"] * 0.5
        weight_total += weights["followers"]

    # Normalize score
    final_score = round(score / weight_total, 2) if weight_total > 0 else 0.0
    return final_score
