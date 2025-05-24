import httpx

GITHUB_API_URL = "https://api.github.com/users/{}"

async def scrape_github_profile_async(username: str) -> dict:
    url = GITHUB_API_URL.format(username)
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "OSINT-Tool/1.0"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                return {
                    "username": data.get("login"),
                    "profile_url": data.get("html_url"),
                    "fullname": data.get("name"),
                    "bio": data.get("bio"),
                    "location": data.get("location"),
                    "website": data.get("blog"),
                    "joined": data.get("created_at"),
                    "followers": data.get("followers"),
                }
    except httpx.RequestError as e:
        print(f"❌ GitHub profile lookup failed: {e}")
    return None
