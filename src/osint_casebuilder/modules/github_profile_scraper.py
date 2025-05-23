import requests

def scrape_github_profile(username: str) -> dict:
    """
    Holt öffentlich sichtbare Metadaten eines GitHub-Profils über die GitHub Public API.
    """
    url = f"https://api.github.com/users/{username}"
    headers = {"User-Agent": "OSINT-CaseBuilder"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"❌ GitHub API: Benutzer '{username}' nicht gefunden (Status {response.status_code})")
            return {}

        data = response.json()

        return {
            "username": username,
            "profile_url": data.get("html_url"),
            "fullname": data.get("name"),
            "bio": data.get("bio"),
            "location": data.get("location"),
            "website": data.get("blog"),
            "joined": data.get("created_at"),
            "followers": data.get("followers"),
        }

    except Exception as e:
        print(f"⚠️ Fehler bei GitHub API-Aufruf: {e}")
        return {}
