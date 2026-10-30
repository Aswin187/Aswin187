"""Fetch the public contribution calendar (no token needed) and save stats.

GitHub serves the same HTML fragment the profile page uses at
https://github.com/users/<username>/contributions

Usage: python scripts/fetch_contributions.py [username]
Writes data/contributions.json
"""
import datetime as dt
import json
import os
import re
import sys
from collections import defaultdict

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_USER", "Aswin187")
OUT = "data/contributions.json"


def parse(html: str) -> tuple[list[dict], int | None]:
    soup = BeautifulSoup(html, "html.parser")

    # tooltips carry the counts: "5 contributions on May 3rd." / "No contributions on ..."
    tips = {}
    for tip in soup.find_all("tool-tip"):
        target = tip.get("for")
        text = tip.get_text(" ", strip=True)
        m = re.match(r"([\d,]+|No)\s+contributions?", text)
        if target and m:
            tips[target] = 0 if m.group(1) == "No" else int(m.group(1).replace(",", ""))

    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        date = td["data-date"]
        level = int(td.get("data-level", 0) or 0)
        count = tips.get(td.get("id"))
        if count is None:  # older markup kept the count on the cell itself
            count = int(td.get("data-count", 0) or 0)
        days.append({"date": date, "count": count, "level": level})
    days.sort(key=lambda d: d["date"])

    total = None
    h2 = soup.find(id="js-contribution-activity-description") or soup.find("h2")
    if h2:
        m = re.search(r"([\d,]+)\s+contributions?", h2.get_text(" ", strip=True))
        if m:
            total = int(m.group(1).replace(",", ""))
    return days, total


def stats(days: list[dict], total: int | None) -> dict:
    counts = [d["count"] for d in days]
    longest = run = 0
    for c in counts:
        run = run + 1 if c > 0 else 0
        longest = max(longest, run)
    current = 0
    rev = counts[::-1]
    if rev and rev[0] == 0:  # today may simply not have activity yet
        rev = rev[1:]
    for c in rev:
        if c == 0:
            break
        current += 1
    best = max(days, key=lambda d: d["count"]) if days else None
    monthly = defaultdict(int)
    for d in days:
        monthly[d["date"][:7]] += d["count"]
    return {
        "total": total if total is not None else sum(counts),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": best,
        "active_days": sum(1 for c in counts if c > 0),
        "monthly": dict(sorted(monthly.items())),
    }


def main() -> None:
    user = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    r = requests.get(
        f"https://github.com/users/{user}/contributions",
        headers={"User-Agent": "profile-readme-bot", "Accept": "text/html"},
        timeout=30,
    )
    r.raise_for_status()
    days, total = parse(r.text)
    if not days:
        sys.exit("no contribution cells found — GitHub markup may have changed")
    data = {
        "user": user,
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "days": days,
        "stats": stats(days, total),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    s = data["stats"]
    print(f"{user}: {s['total']} contributions, {len(days)} days, current streak {s['current_streak']}")


if __name__ == "__main__":
    main()
