#!/usr/bin/env python3
"""
Generates stats.svg from the GitHub API.

The usual profile-README stats cards are hotlinked from someone else's free
service. They rate-limit, they 503, and when a host retires its free tier the
image just disappears from your profile with no warning -- which is exactly
what happened here: the streak card pointed at a Heroku dyno that stopped
existing in 2022, and the stats cards were returning 503.

So this renders the card locally and commits it as a static file. A GitHub
Action refreshes it on a schedule. The card cannot go down, because it is not
a request -- it is a file in the repo.

Stdlib only. Auth comes from GITHUB_TOKEN in the environment.

    GITHUB_TOKEN=... python3 .github/scripts/stats.py --user Syedomershah99
"""

import argparse
import json
import os
import urllib.request
from datetime import datetime, timedelta

API = "https://api.github.com/graphql"

QUERY = """
query($login: String!, $from: DateTime!) {
  user(login: $login) {
    followers { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes { stargazerCount primaryLanguage { name color } }
    }
    contributionsCollection(from: $from) {
      totalCommitContributions
      totalPullRequestContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""

# GitHub's own dark palette, so the card sits flush in a dark-theme profile.
BG = "#0d1117"
BORDER = "#30363d"
INK = "#e6edf3"
MUTED = "#8b949e"
ACCENT = "#58a6ff"
CELL = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]


def fetch(login, token):
    frm = (datetime.utcnow() - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = json.dumps({"query": QUERY, "variables": {"login": login, "from": frm}})
    req = urllib.request.Request(
        API, data=body.encode(),
        headers={"Authorization": "bearer " + token,
                 "Content-Type": "application/json",
                 "User-Agent": "profile-stats"})
    with urllib.request.urlopen(req, timeout=45) as r:
        payload = json.load(r)
    if "errors" in payload:
        raise SystemExit("GitHub API: %s" % payload["errors"])
    return payload["data"]["user"]


def streaks(days):
    """Current and longest run of consecutive days with at least one contribution."""
    longest = current = run = 0
    for d in days:
        if d["contributionCount"] > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    # Walk backwards for the current streak. Today counts as unbroken if it is
    # still empty -- the day is not over yet, and a card that resets at
    # midnight every night would be lying about the streak.
    for i in range(len(days) - 1, -1, -1):
        if days[i]["contributionCount"] > 0:
            current += 1
        elif i != len(days) - 1:
            break
    return current, longest


def languages(nodes, top=5):
    tally = {}
    for n in nodes:
        lang = n.get("primaryLanguage")
        if not lang:
            continue
        k = (lang["name"], lang["color"] or ACCENT)
        tally[k] = tally.get(k, 0) + 1
    ranked = sorted(tally.items(), key=lambda kv: -kv[1])[:top]
    total = sum(v for _, v in ranked) or 1
    return [(name, color, count / total) for (name, color), count in ranked]


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def render(user, login):
    repos = user["repositories"]
    stars = sum(n["stargazerCount"] for n in repos["nodes"])
    cc = user["contributionsCollection"]
    cal = cc["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    cur, longest = streaks(days)
    langs = languages(repos["nodes"])

    W, H = 840, 340
    o = []
    a = o.append
    a('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
      'viewBox="0 0 %d %d" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">'
      % (W, H, W, H))
    a('<rect width="%d" height="%d" rx="12" fill="%s" stroke="%s"/>' % (W, H, BG, BORDER))

    a('<text x="32" y="46" fill="%s" font-size="15" font-weight="600" '
      'letter-spacing="0.3">%s</text>' % (MUTED, esc(login)))
    a('<text x="%d" y="46" fill="%s" font-size="13" text-anchor="end">last 12 months</text>'
      % (W - 32, MUTED))

    # Headline numbers. Four, not twelve -- the ones that mean something.
    figures = [
        (cal["totalContributions"], "contributions"),
        (cc["totalCommitContributions"], "commits"),
        (repos["totalCount"], "repositories"),
        (stars, "stars earned"),
    ]
    x = 32
    for value, label in figures:
        a('<text x="%d" y="112" fill="%s" font-size="40" font-weight="700">%s</text>'
          % (x, INK, format(value, ",")))
        a('<text x="%d" y="134" fill="%s" font-size="13">%s</text>' % (x, MUTED, label))
        x += 200

    # Contribution heatmap: 53 weeks x 7 days, the real calendar.
    a('<text x="32" y="176" fill="%s" font-size="13">contribution activity</text>' % MUTED)
    size, gap, x0, y0 = 11, 3, 32, 188
    for wi, week in enumerate(cc["contributionCalendar"]["weeks"]):
        for di, day in enumerate(week["contributionDays"]):
            n = day["contributionCount"]
            level = 0 if n == 0 else 1 if n < 3 else 2 if n < 6 else 3 if n < 10 else 4
            a('<rect x="%d" y="%d" width="%d" height="%d" rx="2" fill="%s"/>'
              % (x0 + wi * (size + gap), y0 + di * (size + gap), size, size, CELL[level]))

    # Streaks, right-aligned against the heatmap.
    a('<text x="%d" y="176" fill="%s" font-size="13" text-anchor="end">streak</text>'
      % (W - 32, MUTED))
    a('<text x="%d" y="214" fill="%s" font-size="30" font-weight="700" text-anchor="end">%d</text>'
      % (W - 32, ACCENT, cur))
    a('<text x="%d" y="234" fill="%s" font-size="12" text-anchor="end">current</text>'
      % (W - 32, MUTED))
    a('<text x="%d" y="268" fill="%s" font-size="20" font-weight="600" text-anchor="end">%d</text>'
      % (W - 32, INK, longest))
    a('<text x="%d" y="286" fill="%s" font-size="12" text-anchor="end">longest</text>'
      % (W - 32, MUTED))

    # Language bar: one line, proportional, no pie chart.
    y = 300
    a('<text x="32" y="%d" fill="%s" font-size="13">most used</text>' % (y, MUTED))
    bar_x, bar_w = 130, W - 130 - 32 - 90
    cx = bar_x
    for name, color, frac in langs:
        seg = max(4, bar_w * frac)
        a('<rect x="%.1f" y="%d" width="%.1f" height="8" fill="%s"/>'
          % (cx, y - 9, seg, color))
        cx += seg
    labels = "  ".join(n for n, _, _ in langs)
    a('<text x="32" y="%d" fill="%s" font-size="11">%s</text>' % (y + 20, MUTED, esc(labels)))

    a('</svg>')
    return "\n".join(o)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default="Syedomershah99")
    ap.add_argument("--out", default="stats.svg")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("set GITHUB_TOKEN")

    user = fetch(args.user, token)
    svg = render(user, args.user)
    with open(args.out, "w") as fh:
        fh.write(svg)
    print("wrote %s (%d bytes)" % (args.out, len(svg)))


if __name__ == "__main__":
    main()
