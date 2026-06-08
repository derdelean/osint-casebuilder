def validate_inputs(username: str, fullname: str, location: str, keywords: list, target_domain: str, email: str = None, domain: str = None, phone: str = None) -> bool:
    return any([
        bool(username and username.strip()),
        bool(fullname and fullname.strip()),
        bool(location and location.strip()),
        bool(keywords and any(k.strip() for k in keywords)),
        bool(target_domain and target_domain.strip()),
        bool(email and email.strip()),
        bool(domain and domain.strip()),
        bool(phone and phone.strip())
    ])
