#!/usr/bin/env python3
"""
Draws stats.svg from the GitHub API.

The usual profile cards are hotlinked from someone else's free service. They
rate-limit, they 503, and when a host retires its free tier the image silently
vanishes -- which is what happened here: the streak card pointed at a Heroku
dyno that stopped existing in 2022. This renders locally and commits the result,
so the card cannot go down, because it is not a request.

No contribution heatmap on purpose. The snake animation below it in the README
is the contribution grid, and showing the same twelve months twice is just
clutter wearing two hats.

Stdlib only. Auth from GITHUB_TOKEN.

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
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes { stargazerCount primaryLanguage { name color } }
    }
    contributionsCollection(from: $from) {
      totalCommitContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""

BG = "#0d1117"
BORDER = "#30363d"
INK = "#e6edf3"
MUTED = "#8b949e"
ACCENT = "#58a6ff"
FLAME = "#f78166"


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
    longest = current = run = 0
    for d in days:
        if d["contributionCount"] > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    # Today being empty does not break the streak -- the day is not over.
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
    return [(n, c, v / total) for (n, c), v in ranked]


def render(user, login):
    repos = user["repositories"]
    stars = sum(n["stargazerCount"] for n in repos["nodes"])
    cc = user["contributionsCollection"]
    cal = cc["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    cur, longest = streaks(days)
    langs = languages(repos["nodes"])

    W, H = 840, 172
    o = []
    a = o.append
    a('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
      'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">'
      % (W, H, W, H))
    a('<rect width="%d" height="%d" rx="12" fill="%s" stroke="%s"/>' % (W, H, BG, BORDER))

    figures = [
        (format(cal["totalContributions"], ","), "contributions"),
        (format(cc["totalCommitContributions"], ","), "commits"),
        (format(repos["totalCount"], ","), "repositories"),
        (format(stars, ","), "stars"),
    ]
    x = 32
    for i, (value, label) in enumerate(figures):
        # Staggered fade-in, so the eye lands on them left to right.
        # opacity starts at 1 so a renderer that ignores SMIL still shows the
        # number. The animation only supplies the entrance.
        a('<g opacity="1"><animate attributeName="opacity" values="0;0;1" '
          'keyTimes="0;%.3f;1" dur="0.8s" fill="freeze"/>' % min(0.9, 0.12 * i + 0.01))
        a('<text x="%d" y="72" fill="%s" font-size="38" font-weight="700">%s</text>'
          % (x, INK, value))
        a('<text x="%d" y="94" fill="%s" font-size="12.5">%s</text>' % (x, MUTED, label))
        a('</g>')
        x += 172

    # Streak, right-hand column.
    a('<g opacity="1"><animate attributeName="opacity" values="0;0;1" '
      'keyTimes="0;0.5;1" dur="0.8s" fill="freeze"/>')
    a('<text x="%d" y="58" fill="%s" font-size="30" font-weight="700" text-anchor="end">%d</text>'
      % (W - 32, FLAME, cur))
    a('<text x="%d" y="76" fill="%s" font-size="11.5" text-anchor="end">day streak</text>'
      % (W - 32, MUTED))
    a('<text x="%d" y="98" fill="%s" font-size="11.5" text-anchor="end">best %d</text>'
      % (W - 32, MUTED, longest))
    a('</g>')

    # Language bar. Widths grow from zero, which reads as the bar filling up.
    a('<text x="32" y="128" fill="%s" font-size="12.5">most used</text>' % MUTED)
    bar_x, bar_w, bar_y = 32, W - 64, 138
    cx = bar_x
    for i, (name, color, frac) in enumerate(langs):
        seg = max(6, bar_w * frac)
        rx = 4 if i == 0 or i == len(langs) - 1 else 0
        a('<rect x="%.1f" y="%d" width="%.1f" height="9" rx="%d" fill="%s">'
          '<animate attributeName="width" from="0" to="%.1f" dur="0.7s" '
          'begin="%.2fs" fill="freeze"/></rect>'
          % (cx, bar_y, seg, rx, color, seg, 0.5 + 0.08 * i))
        cx += seg
    a('<text x="32" y="164" fill="%s" font-size="11">%s</text>'
      % (MUTED, "   ".join(n for n, _, _ in langs)))

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
    svg = render(fetch(args.user, token), args.user)
    with open(args.out, "w") as fh:
        fh.write(svg)
    print("wrote %s (%d bytes)" % (args.out, len(svg)))


if __name__ == "__main__":
    main()
