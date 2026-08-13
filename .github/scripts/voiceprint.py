#!/usr/bin/env python3
"""
Draws voiceprint.svg -- a fingerprint of how I write, measured by being-human.

Every profile README shows the same three things: commits, languages, streak.
This shows something no other profile can, because the numbers come from a tool
I wrote and a corpus that is mine: sentence rhythm, casing, punctuation rates,
and the words this model uses with me that I never use.

Run locally against a being-human corpus and commit the output. It is
deliberately NOT a scheduled action -- the corpus is private prompt history and
has no business on a CI runner.

    python3 .github/scripts/voiceprint.py \\
        --metrics ~/Desktop/projects/being-human/.being-human/metrics.json \\
        --corpus  ~/Desktop/projects/being-human/.being-human/corpus.jsonl \\
        --out voiceprint.svg

Only aggregate statistics reach the SVG. No prompt text is ever written out.
"""

import argparse
import json
import os
import random
import re

BG = "#0d1117"
BORDER = "#30363d"
INK = "#e6edf3"
MUTED = "#8b949e"
ACCENT = "#58a6ff"
GOOD = "#3fb950"
BAD = "#f85149"

WORD = re.compile(r"[A-Za-z']+")
SENT = re.compile(r"[.!?]+|\n+")


def sentence_lengths(corpus_path, limit=120, seed=11):
    """
    Real sentence lengths, sampled, for the rhythm strip.

    The strip is the honest version of "vary your sentence length": each bar is
    one actual sentence. A generated paragraph would draw as a picket fence.
    """
    lens = []
    if not corpus_path or not os.path.exists(corpus_path):
        return lens
    with open(corpus_path) as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            for s in SENT.split(row.get("text", "")):
                n = len(WORD.findall(s))
                if n:
                    lens.append(n)
    rng = random.Random(seed)
    if len(lens) > limit:
        start = rng.randrange(0, len(lens) - limit)
        lens = lens[start:start + limit]
    return lens


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(m, lens):
    metrics = m["metrics"]
    p = metrics["punct_per_1k"]
    mean = metrics["sentence_len_mean"] or 1
    burst = metrics["sentence_len_sd"] / float(mean)
    avoid = [w for w, _, _, _ in m.get("slop_candidates", [])][:8]

    W, H = 840, 286
    o = []
    a = o.append
    a('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
      'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">'
      % (W, H, W, H))
    a('<rect width="%d" height="%d" rx="12" fill="%s" stroke="%s"/>' % (W, H, BG, BORDER))

    a('<text x="32" y="42" fill="%s" font-size="15" font-weight="600">voiceprint</text>' % INK)
    a('<text x="32" y="62" fill="%s" font-size="12">how i actually write, measured from %s of my own words</text>'
      % (MUTED, format(metrics["words"], ",")))
    a('<text x="%d" y="42" fill="%s" font-size="11.5" text-anchor="end">being-human</text>'
      % (W - 32, ACCENT))

    # Rhythm strip: one bar per real sentence, height = word count.
    a('<text x="32" y="92" fill="%s" font-size="11.5">sentence rhythm</text>' % MUTED)
    if lens:
        top = max(lens) or 1
        bw, gap, x0, base, maxh = 4, 2, 32, 148, 46
        for i, n in enumerate(lens):
            if x0 + i * (bw + gap) > W - 40:
                break
            h = max(2, (n / top) * maxh)
            a('<rect x="%d" y="%.1f" width="%d" height="%.1f" rx="1" fill="%s" opacity="0.85">'
              '<animate attributeName="height" from="0" to="%.1f" dur="0.5s" begin="%.3fs" fill="freeze"/>'
              '<animate attributeName="y" from="%d" to="%.1f" dur="0.5s" begin="%.3fs" fill="freeze"/>'
              '</rect>'
              % (x0 + i * (bw + gap), base - h, bw, h, ACCENT, h, 0.004 * i, base, base - h, 0.004 * i))
    a('<text x="32" y="168" fill="%s" font-size="11">%.0f words average, deviating %.0f. '
      'ratio %.2f, and the flat ones are the tell.</text>'
      % (MUTED, mean, metrics["sentence_len_sd"], burst))

    # Measured habits.
    facts = [
        ('lowercase "i"', "%.0f%%" % metrics["lowercase_i_pct"]),
        ("em dash", "%.1f/1k" % p["em_dash"]),
        ("exclamation", "%.2f/1k" % p["exclaim"]),
        ("hedging", "%.1f/1k" % metrics.get("hedge_per_1k", 0)),
    ]
    x = 32
    for k, v in facts:
        a('<text x="%d" y="200" fill="%s" font-size="19" font-weight="600">%s</text>' % (x, INK, v))
        a('<text x="%d" y="216" fill="%s" font-size="11">%s</text>' % (x, MUTED, k))
        x += 132

    # The personal avoid-list: words the model uses with me that I never use.
    if avoid:
        a('<text x="32" y="250" fill="%s" font-size="11">'
          'words this model uses with me that i never do</text>' % MUTED)
        cx = W - 32
        for w in reversed(avoid[:7]):
            wid = 9 + len(w) * 6.6
            cx -= wid + 6
            a('<rect x="%.1f" y="256" width="%.1f" height="20" rx="10" fill="#21262d" stroke="%s" stroke-opacity="0.4"/>'
              % (cx, wid, BAD))
            a('<text x="%.1f" y="270" fill="%s" font-size="11" text-anchor="middle">%s</text>'
              % (cx + wid / 2, BAD, esc(w)))
    a('</svg>')
    return "\n".join(o)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metrics", required=True)
    ap.add_argument("--corpus")
    ap.add_argument("--out", default="voiceprint.svg")
    args = ap.parse_args()
    with open(args.metrics) as fh:
        m = json.load(fh)
    svg = render(m, sentence_lengths(args.corpus))
    with open(args.out, "w") as fh:
        fh.write(svg)
    print("wrote %s (%d bytes)" % (args.out, len(svg)))


if __name__ == "__main__":
    main()
