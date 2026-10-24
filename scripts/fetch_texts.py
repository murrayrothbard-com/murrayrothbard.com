#!/usr/bin/env python3
"""Download Mises EPUBs (cdn.mises.org), detect license from front matter,
and extract chapter text ONLY for permissive (CC BY, no NC/ND) works.
Writes data/licenses.json (report) and data/texts/<slug>.json."""
import json, re, sys, zipfile, io, urllib.request, html, os
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
books = json.load(open(ROOT/"data/mises_books.json"))
(ROOT/"data/texts").mkdir(exist_ok=True)
report = {}

def strip(x):
    x = re.sub(r"(?is)<(script|style).*?</\1>", "", x)
    x = re.sub(r"(?i)</(p|h[1-6]|div|li|blockquote)>", "\n\n", x)
    x = re.sub(r"(?i)<br\s*/?>", "\n", x)
    return html.unescape(re.sub(r"<[^>]+>", "", x))

def detect(txt):
    t = re.sub(r"\s+", " ", txt)
    m = re.search(r"creativecommons\.org/licenses/([a-z\-]+)/([0-9.]+)", t, re.I)
    if m: return "CC " + m.group(1).upper() + " " + m.group(2)
    m = re.search(r"Attribution[^.]{0,60}(NonCommercial|Non-Commercial)[^.]{0,60}", t, re.I)
    if m: return "CC BY-NC (text)"
    if re.search(r"all rights reserved", t, re.I): return "All rights reserved"
    if re.search(r"public domain", t, re.I): return "Public domain (stated)"
    return "unknown"

# Licenses verified by hand on each book's Mises page (EPUB front matter was not machine-readable)
OVERRIDE = {"economic-controversies": "CC BY 3.0", "betrayal-american-right": "CC BY-NC-ND 4.0"}
ONLY = os.environ.get("ONLY", "").split(",") if os.environ.get("ONLY") else None
for slug, path in books.items():
    if ONLY and slug not in ONLY: continue
    url = "https://cdn.mises.org/" + path
    try:
        data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "murrayrothbard.com-archiver (+https://murrayrothbard.com)"}), timeout=120).read()
        z = zipfile.ZipFile(io.BytesIO(data))
        names = [n for n in z.namelist() if re.search(r"\.(x?html?)$", n, re.I)]
        names.sort()
        parts = [(n, strip(z.read(n).decode("utf8", "ignore"))) for n in names]
        front = " ".join(p[1] for p in parts[:6])
        raw_front = " ".join(z.read(n).decode("utf8", "ignore") for n in names[:6])
        lic = OVERRIDE.get(slug) or detect(raw_front + " " + front)
        report[slug] = {"license": lic, "bytes": len(data), "sections": len(parts)}
        if lic.startswith("CC BY"):
            chapters = [{"title": (re.search(r"[^\n]+", t.strip()) or [""])[0][:120] if t.strip() else "", "text": t.strip()} for _, t in parts if len(t.strip()) > 200]
            json.dump({"slug": slug, "license": lic, "source": url, "chapters": chapters}, open(ROOT/f"data/texts/{slug}.json", "w"))
        print(slug, lic, file=sys.stderr)
    except Exception as e:
        report[slug] = {"error": str(e)[:100]}
        print(slug, "ERR", e, file=sys.stderr)
old = json.load(open(ROOT/"data/licenses.json")) if (ROOT/"data/licenses.json").exists() else {}
old.update(report)
json.dump(old, open(ROOT/"data/licenses.json", "w"), indent=1)
