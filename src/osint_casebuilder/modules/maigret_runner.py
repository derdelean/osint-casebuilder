"""Run Maigret as a subprocess and parse its JSON report. This bridges the
dependency-tree split: any environment (Streamlit/PyQt, which can't import
maigret) can still use the real engine as long as a maigret binary is reachable.

Binary resolution order: $MAIGRET_BIN → the repo's `.venv/bin/maigret` → PATH."""

import asyncio
import glob
import json
import os
import shutil
import tempfile

from .maigret_common import normalize_meta, ids_to_pivots

print("✅ Modul `maigret_runner` (subprocess bridge) aktiv")


def find_maigret_bin():
    """Locate a maigret executable, or return None."""
    env = os.environ.get("MAIGRET_BIN")
    if env and os.path.exists(env):
        return env
    here = os.path.dirname(os.path.abspath(__file__))
    venv_bin = os.path.normpath(os.path.join(here, "..", "..", "..", ".venv", "bin", "maigret"))
    if os.path.exists(venv_bin):
        return venv_bin
    return shutil.which("maigret")


async def run_maigret_subprocess_async(username: str, top_sites: int = 500, timeout: int = 8) -> list:
    """Search via the maigret CLI (JSON report) and map to finding dicts. Raises
    FileNotFoundError if no maigret binary is available (so the caller can fall back)."""
    binary = find_maigret_bin()
    if not binary:
        raise FileNotFoundError("maigret binary not found (set MAIGRET_BIN or create .venv)")

    tmp = tempfile.mkdtemp(prefix="maigret_")
    try:
        cmd = [
            binary, username,
            "--top-sites", str(top_sites),
            "--timeout", str(timeout),
            "--json", "simple", "-fo", tmp,
            "--no-recursion", "--no-color", "--no-progressbar", "--no-autoupdate",
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )
        await proc.wait()

        reports = glob.glob(os.path.join(tmp, "*simple.json"))
        if not reports:
            return []
        with open(reports[0]) as fh:
            data = json.load(fh)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    findings = []
    for site_name, info in data.items():
        status = info.get("status") or {}
        if status.get("status") != "Claimed":
            continue
        ids = status.get("ids") or {}
        usernames, links = ids_to_pivots(ids)
        findings.append({
            "type": "username",
            "value": username,
            "source": info.get("url_user") or status.get("url"),
            "platform": site_name,
            "meta": normalize_meta(ids),
            "ids_usernames": usernames,
            "ids_links": links,
        })
    return findings
