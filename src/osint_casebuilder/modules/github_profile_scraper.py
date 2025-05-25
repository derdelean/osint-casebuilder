import httpx

async def scrape_github_profile_async(username: str) -> dict:
    url = f"https://api.github.com/users/{username}"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "username": data.get("login"),
                    "profile_url": data.get("html_url"),
                    "fullname": data.get("name"),
                    "bio": data.get("bio"),
                    "location": data.get("location"),
                    "website": data.get("blog"),
                    "joined": data.get("created_at"),
                    "followers": data.get("followers")
                }
    except Exception as e:
        print(f"❌ GitHub scraping error: {e}")
    return None
