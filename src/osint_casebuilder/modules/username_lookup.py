import asyncio
import httpx
from .username_mutator import generate_username_variants
from asyncio import Semaphore
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    TaskID
)

print("✅ Modul `username_lookup` async mit rich-Progressbar aktiv")

# Platforms with ULR templates
PLATFORMS = {
    "GitHub": "https://github.com/{}",
    "Twitter": "https://twitter.com/{}",
    "Instagram": "https://www.instagram.com/{}",
    "Reddit": "https://www.reddit.com/user/{}",
    "TikTok": "https://www.tiktok.com/@{}",
    "Pinterest": "https://www.pinterest.com/{}",
    "Tumblr": "https://{}.tumblr.com",
    "Steam": "https://steamcommunity.com/id/{}",
    "SoundCloud": "https://soundcloud.com/{}",
    "Replit": "https://replit.com/@{}",
}

MAX_CONCURRENT_REQUESTS = 10
RETRY_COUNT = 2

async def fetch_profile(client, url, platform, variant, sem: Semaphore, progress: Progress, task_id: TaskID):
    async with sem:
        for attempt in range(RETRY_COUNT + 1):
            try:
                response = await client.get(url, timeout=5.0)
                progress.advance(task_id)
                if response.status_code == 200:
                    return {
                        "type": "username",
                        "value": variant,
                        "source": url,
                        "timestamp": "auto"
                    }
                return None
            except httpx.RequestError as e:
                if attempt < RETRY_COUNT:
                    await asyncio.sleep(1.0)  # Retry-Backoff
        progress.advance(task_id)
        return None

async def run_username_lookup_async(username: str):
    findings = []
    all_variants = generate_username_variants(username)
    total_tasks = len(all_variants) * len(PLATFORMS)

    print(f"🧠 {len(all_variants)} Varianten generiert")

    sem = Semaphore(MAX_CONCURRENT_REQUESTS)

    async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"}) as client:
        with Progress(
            SpinnerColumn(style="bold magenta"),
            TextColumn("[bold cyan]🔍 Suche:"),
            BarColumn(bar_width=None, style="green"),
            TaskProgressColumn(),
            TimeElapsedColumn()
        ) as progress:

            task_id = progress.add_task("Benutzername-Plattform-Kombis prüfen...", total=total_tasks)

            tasks = [
                fetch_profile(client, template.format(variant), platform, variant, sem, progress, task_id)
                for variant in all_variants
                for platform, template in PLATFORMS.items()
            ]
            results = await asyncio.gather(*tasks)
            findings = [r for r in results if r]

    print(f"✅ {len(findings)} Fundstellen insgesamt (async)")
    return findings

def run_username_lookup(username: str):
    return asyncio.run(run_username_lookup_async(username))
