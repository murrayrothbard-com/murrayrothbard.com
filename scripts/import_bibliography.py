#!/usr/bin/env python3
"""Import the Rothbard catalog from the Mises Institute's online copy of the
chronological bibliography in David Gordon's "The Essential Rothbard" (1949-1995).

Runs in GitHub Actions (import.yml), writes data/imported.json. Stdlib only.
We keep only factual bibliographic fields (title, year, type, publication, date);
links to full texts are added in a later step. Existing hand-written records in
data/works.json always win over imported ones.
"""
import json
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "https://mises.org/online-book/essential-rothbard/15-bibliography"
UA = "murrayrothbard.com catalog builder (+https://github.com/murrayrothbard-com/murrayrothbard.com)"


class Paras(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ps, self.cur = [], None

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.cur = []

    def handle_endtag(self, tag):
        if tag == "p" and self.cur is not None:
            self.ps.append(re.sub(r"\s+", " ", "".join(self.cur)).strip())
            self.cur = None

    def handle_data(self, data):
        if self.cur is not None:
            self.cur.append(data)


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "x"


def key(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())[:22]


def parse(entry, year, section):
    head = entry.split(" (")[0] if " (" in entry else entry
    m_date = re.search(r"\(([^()]*\d{4}[^()]*)\)", entry)
    date = m_date.group(1) if m_date else str(year)
    if entry.startswith("Review of"):
        i = head.rfind(". ")
        title, pub = (head[:i], head[i + 2:]) if i > 0 else (head, "")
        typ = "Review"
    else:
        m = re.match(r"[“\"](.+?)[”\"]\s*,?\s*(.*)$", entry)
        if m:
            title = m.group(1)
            rest = m.group(2).split(" (")[0]
            pub = rest.strip(" .,")
            typ = "Chapter" if pub.lower().startswith("in ") else ("Article" if "ARTICLE" in section or "SCHOLARLY" in section else "Other")
        else:
            title, pub = head, ""
            typ = "Book" if "BOOK" in section else "Other"
    title = title.strip(" .,")
    return title, pub.strip(" .,"), typ, date


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    p = Paras()
    p.feed(html)
    works_path = ROOT / "data" / "works.json"
    seed = json.loads(works_path.read_text())
    seed_keys = {key(w["title"]) for w in seed}
    used = {w["slug"] for w in seed}

    out, year, section, seen = [], None, "", {}
    started = False
    for t in p.ps:
        if re.fullmatch(r"(19|20)\d\d", t):
            year, started = int(t), True
            continue
        if not started:
            continue
        if t.startswith("The Mises Institute is"):
            break
        if t.endswith(":") and t.upper() == t:
            section = t
            seen[t] = seen.get(t, 0) + 1
            continue
        if not re.search(r"\d{4}", t) or len(t) < 8:
            continue
        title, pub, typ, date = parse(t, year, section)
        if not title or key(title) in seed_keys:
            continue
        slug = f"{slugify(title)[:70]}-{year}"
        n, base = 2, slug
        while slug in used:
            slug, n = f"{base}-{n}", n + 1
        used.add(slug)
        out.append({"slug": slug, "title": title, "year": year, "type": typ, "publication": pub, "date": date,
                    "source_url": None, "source_name": "Mises Institute", "license": "Check at source", "hosting": "link"})

    print("sections seen:", seen)
    print("records:", len(out), "of", len(p.ps), "paragraphs")
    by = {}
    for r in out:
        by[r["type"]] = by.get(r["type"], 0) + 1
    print("by type:", by)
    if len(out) < 300:
        sys.exit("too few records; the page layout may have changed")
    (ROOT / "data" / "imported.json").write_text(json.dumps(out, ensure_ascii=False, indent=0) + "\n")


if __name__ == "__main__":
    main()
