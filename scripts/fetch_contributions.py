"""Fetch the public contribution calendar for a GitHub user (no token needed).

Writes data/contributions.json with per-day counts and derived stats.
"""
from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_USER", "khaledmnejja")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"

COUNT_RE = re.compile(r"^(\d[\d,]*) contributions?")


def fetch_days(username: str) -> list[dict]:
    url = f"https://github.com/users/{username}/contributions"
    resp = requests.get(url, timeout=30, headers={"User-Agent": "profile-art-bot"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # The count lives in a <tool-tip for="cell-id"> next to each cell.
    counts: dict[str, int] = {}
    for tip in soup.find_all("tool-tip"):
        target = tip.get("for")
        match = COUNT_RE.match(tip.get_text(strip=True))
        if target:
            counts[target] = int(match.group(1).replace(",", "")) if match else 0

    days = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        days.append(
            {
                "date": cell["data-date"],
                "level": int(cell.get("data-level", 0)),
                "count": counts.get(cell.get("id", ""), 0),
            }
        )
    days.sort(key=lambda d: d["date"])
    return days


def streaks(days: list[dict]) -> tuple[int, int]:
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)

    # Current streak: an empty "today" doesn't break it yet.
    current = 0
    seq = list(reversed(days))
    if seq and seq[0]["count"] == 0 and seq[0]["date"] == date.today().isoformat():
        seq = seq[1:]
    for d in seq:
        if d["count"] == 0:
            break
        current += 1
    return current, longest


def main() -> None:
    days = fetch_days(USERNAME)
    if not days:
        raise SystemExit("No contribution cells found; GitHub markup may have changed.")

    current, longest = streaks(days)
    best = max(days, key=lambda d: d["count"])
    monthly: dict[str, int] = defaultdict(int)
    for d in days:
        monthly[d["date"][:7]] += d["count"]

    data = {
        "username": USERNAME,
        "generated": date.today().isoformat(),
        "total": sum(d["count"] for d in days),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": dict(sorted(monthly.items())),
        "days": days,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"{len(days)} days, {data['total']} contributions -> {OUT}")


if __name__ == "__main__":
    main()
