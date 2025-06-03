def validate_inputs(username: str, fullname: str, location: str, keywords: list, target_domain: str) -> bool:
    return any([
        bool(username and username.strip()),
        bool(fullname and fullname.strip()),
        bool(location and location.strip()),
        bool(keywords and any(k.strip() for k in keywords)),
        bool(target_domain and target_domain.strip())
    ])
