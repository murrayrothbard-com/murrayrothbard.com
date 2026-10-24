#!/usr/bin/env python3
"""Build murrayrothbard.com (static, stdlib only, zero tokens per run).

    python3 scripts/build.py   ->  dist/

Reads data/works.json (one record per work) and data/topics.json (keyword rules).
Lookup: search + year/type/topic filters on the home page (linkable via ?query),
plus a static page per year, topic, type and publication under /browse/.
Hosting policy: every record is "link" until its license is verified; see DESIGN.md.
"""
import html
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dist"
SITE = "https://murrayrothbard.com"
LISTING = "https://mises.org/library/murray-n-rothbard-books"
esc = lambda s: html.escape(str(s), quote=True)


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-") or "x"


WORKS = json.loads((ROOT / "data" / "works.json").read_text())
_imp = ROOT / "data" / "imported.json"
if _imp.exists():
    WORKS += json.loads(_imp.read_text())
TOPICS = json.loads((ROOT / "data" / "topics.json").read_text())
WORKS.sort(key=lambda w: (w.get("year") or 9999, w["title"].lower()))

# topic tags = explicit tags + keyword matches (word-start match on title + description)
for w in WORKS:
    text = f"{w['title']} {w.get('description', '')}".lower()
    tags = set(w.get("tags", []))
    for slug, t in TOPICS.items():
        if any(re.search(r"\b" + re.escape(k), text) for k in t["keywords"]):
            tags.add(slug)
    w["_topics"] = sorted(tags)
    w["_type"] = slugify(w["type"])
    w["_pub"] = slugify(w["publication"]) if w.get("publication") else ""

CSS = """
:root{--bg:#fff;--bg2:#f5f5f7;--ink:#1d1d1f;--mute:#6e6e73;--line:#d2d2d7;--acc:#0b57d0;--accink:#fff}
@media (prefers-color-scheme:dark){:root{--bg:#000;--bg2:#1c1c1e;--ink:#f5f5f7;--mute:#a1a1a6;--line:#38383a;--acc:#6ea8ff;--accink:#000}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,sans-serif}
[hidden]{display:none!important}
a{color:var(--acc)}
.wrap{max-width:880px;margin:0 auto;padding:0 20px}
header.top{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);z-index:5}
header.top .wrap{display:flex;align-items:center;justify-content:space-between;height:56px}
.brand{font-weight:650;letter-spacing:-.01em;color:var(--ink);text-decoration:none}
nav a{margin-left:20px;color:var(--mute);text-decoration:none;font-size:15px}
nav a:hover,nav a[aria-current]{color:var(--ink)}
.hero{padding:88px 0 24px}
h1{font-family:"Iowan Old Style","Charter",Georgia,serif;font-weight:600;font-size:clamp(40px,8vw,76px);line-height:1.04;letter-spacing:-.025em;margin:0 0 20px}
h2{font-size:15px;font-weight:600;color:var(--mute);margin:48px 0 12px;letter-spacing:.01em}
.lede{font-size:20px;color:var(--mute);max-width:36em;margin:0 0 32px}
.search,select{font:inherit;border:1px solid var(--line);background:var(--bg2);color:var(--ink)}
.search{width:100%;padding:16px 20px;border-radius:999px}
select{padding:10px 14px;border-radius:999px;font-size:15px;max-width:100%}
.search:focus,select:focus{outline:3px solid var(--acc);outline-offset:2px}
.filters{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px;align-items:center}
.reset{background:none;border:0;color:var(--acc);font:inherit;font-size:15px;cursor:pointer;padding:8px}
.count{color:var(--mute);font-size:14px;margin:14px 4px 0}
ul.list{list-style:none;margin:24px 0 96px;padding:0}
.work{display:flex;gap:16px;justify-content:space-between;align-items:baseline;padding:20px 4px;border-bottom:1px solid var(--line)}
.work a.t{font-family:"Iowan Old Style","Charter",Georgia,serif;font-size:22px;color:var(--ink);text-decoration:none;letter-spacing:-.01em}
.work a.t:hover{text-decoration:underline}
.meta{color:var(--mute);font-size:14px;white-space:nowrap}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:0;padding:0;list-style:none}
.chips a{display:inline-block;background:var(--bg2);color:var(--ink);padding:8px 16px;border-radius:999px;text-decoration:none;font-size:15px}
.chips a:hover{outline:2px solid var(--acc)}
.chips small{color:var(--mute);margin-left:6px}
article{padding:72px 0 96px}
article h1{font-size:clamp(34px,6vw,56px)}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:32px 0}
.fact{background:var(--bg2);border-radius:20px;padding:18px 20px}
.fact b{display:block;font-size:13px;color:var(--mute);font-weight:500;margin-bottom:4px}
.btn{display:inline-block;background:var(--acc);color:var(--accink);padding:14px 26px;border-radius:999px;text-decoration:none;font-weight:600}
.btn:focus{outline:3px solid var(--ink);outline-offset:2px}
.prose{font-family:"Iowan Old Style","Charter",Georgia,serif;font-size:20px;line-height:1.7}
footer{border-top:1px solid var(--line);padding:32px 0 56px;color:var(--mute);font-size:14px}
@media (max-width:600px){.hero{padding-top:56px}.work{flex-direction:column;gap:4px}.meta{white-space:normal}}
"""

JS = """
const $=s=>document.querySelector(s),q=$('#q');
if(q){const fy=$('#fy'),ft=$('#ft'),fo=$('#fo'),c=$('#count'),items=[...document.querySelectorAll('.work')],P=new URLSearchParams(location.search);
q.value=P.get('q')||'';fy.value=P.get('year')||'';ft.value=P.get('type')||'';fo.value=P.get('topic')||'';
const f=()=>{const t=q.value.toLowerCase().trim();let n=0;
items.forEach(e=>{const d=e.dataset,s=(!t||d.s.includes(t))&&(!fy.value||d.year===fy.value)&&(!ft.value||d.type===ft.value)&&(!fo.value||d.topics.split(' ').includes(fo.value));e.hidden=!s;if(s)n++});
c.textContent=n+(n===1?' work':' works');
const u=new URLSearchParams();[['q',q.value],['year',fy.value],['type',ft.value],['topic',fo.value]].forEach(([k,v])=>v&&u.set(k,v));
history.replaceState(null,'',u.toString()?'?'+u:location.pathname)};
[q,fy,ft,fo].forEach(e=>e.addEventListener('input',f));
$('#reset').addEventListener('click',()=>{q.value=fy.value=ft.value=fo.value='';f()});f()}
"""


def page(title, desc, body, path, current=""):
    nav = "".join(
        f'<a href="{h}"{" aria-current=page" if k == current else ""}>{l}</a>'
        for k, h, l in (("works", "/", "Works"), ("browse", "/browse/", "Browse"), ("about", "/about/", "About"))
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{SITE}{path}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website"><meta property="og:url" content="{SITE}{path}">
<style>{CSS}</style></head>
<body><header class="top"><div class="wrap"><a class="brand" href="/">Murray Rothbard</a><nav>{nav}</nav></div></header>
<main class="wrap">{body}</main>
<footer><div class="wrap">An independent index of the writings of Murray N. Rothbard (1926&ndash;1995).
Texts remain the property of their rights holders and are linked at their source.</div></footer>
<script>{JS}</script></body></html>"""


def source_link(w):
    if w.get("source_url"):
        return w["source_url"], f"Read at {w.get('source_name') or 'source'}"
    return LISTING, "Find it in the Mises Institute collection"


def write(rel, text):
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def row(w):
    search = " ".join(str(w.get(k, "")) for k in ("title", "year", "type", "publication", "description")).lower()
    return (
        f'<li class="work" data-s="{esc(search)}" data-year="{esc(w.get("year") or "")}" data-type="{esc(w["_type"])}" '
        f'data-topics="{esc(" ".join(w["_topics"]))}"><a class="t" href="/works/{esc(w["slug"])}/">{esc(w["title"])}</a>'
        f'<span class="meta">{esc(w.get("year") or "n.d.")} &middot; {esc(w["type"])}</span></li>'
    )


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    # ---- facets
    years, types, topics, pubs = defaultdict(list), {}, defaultdict(list), {}
    for w in WORKS:
        if w.get("year"):
            years[w["year"]].append(w)
        types.setdefault(w["_type"], (w["type"], []))[1].append(w)
        for t in w["_topics"]:
            topics[t].append(w)
        if w["_pub"]:
            pubs.setdefault(w["_pub"], (w["publication"], []))[1].append(w)

    # ---- home with filters
    ys = "".join(f'<option value="{y}">{y} ({len(years[y])})</option>' for y in sorted(years))
    ts = "".join(f'<option value="{k}">{esc(v[0])} ({len(v[1])})</option>' for k, v in sorted(types.items()))
    os_ = "".join(f'<option value="{k}">{esc(TOPICS[k]["label"])} ({len(topics[k])})</option>' for k in TOPICS if k in topics)
    home = f"""<section class="hero"><h1>Everything Rothbard wrote, in one place.</h1>
<p class="lede">A free, searchable index of the books, essays, reviews and letters of Murray N. Rothbard, each linked to where it can be read.</p>
<input id="q" class="search" type="search" placeholder="Search {len(WORKS)} works" aria-label="Search works" autocomplete="off">
<div class="filters">
<select id="fy" aria-label="Year"><option value="">Any year</option>{ys}</select>
<select id="ft" aria-label="Type"><option value="">Any type</option>{ts}</select>
<select id="fo" aria-label="Topic"><option value="">Any topic</option>{os_}</select>
<button id="reset" class="reset" type="button">Reset</button></div>
<p id="count" class="count" aria-live="polite"></p></section>
<ul class="list">{''.join(row(w) for w in WORKS)}</ul>"""
    write("index.html", page("Murray Rothbard: the complete writings index",
          "A free, searchable index of every known work by Murray N. Rothbard, linked to its source.", home, "/", "works"))

    # ---- facet pages
    facet_urls = []

    def facet(kind, key, label, ws):
        path = f"/browse/{kind}/{key}/"
        facet_urls.append(path)
        body = (f'<section class="hero"><p class="meta"><a href="/browse/">&larr; Browse</a></p>'
                f'<h1>{esc(label)}</h1><p class="lede">{len(ws)} {"work" if len(ws) == 1 else "works"} by Murray Rothbard.</p></section>'
                f'<ul class="list">{"".join(row(w) for w in ws)}</ul>')
        write(f"browse/{kind}/{key}/index.html",
              page(f"{label} | Murray Rothbard", f"Murray Rothbard's writings: {label}.", body, path, "browse"))

    for y in sorted(years):
        facet("year", y, str(y), years[y])
    for k, ws in topics.items():
        facet("topic", k, TOPICS[k]["label"], ws)
    for k, (label, ws) in types.items():
        facet("type", k, label, ws)
    for k, (label, ws) in pubs.items():
        facet("publication", k, label, ws)

    def chips(kind, items):
        return '<ul class="chips">' + "".join(
            f'<li><a href="/browse/{kind}/{k}/">{esc(label)}<small>{n}</small></a></li>' for k, label, n in items) + "</ul>"

    decades = defaultdict(list)
    for y in sorted(years):
        decades[y // 10 * 10].append((y, str(y), len(years[y])))
    year_html = "".join(f"<h2>{d}s</h2>{chips('year', v)}" for d, v in sorted(decades.items()))
    browse = f"""<article><h1>Browse</h1><p class="prose">Find Rothbard's writings by topic, year, type, or where they were published.</p>
<h2>By topic</h2>{chips('topic', [(k, TOPICS[k]['label'], len(topics[k])) for k in TOPICS if k in topics])}
<h2>By type</h2>{chips('type', [(k, v[0], len(v[1])) for k, v in sorted(types.items())])}
{('<h2>By publication</h2>' + chips('publication', sorted([(k, v[0], len(v[1])) for k, v in pubs.items() if len(v[1]) >= 5], key=lambda x: -x[2]))) if pubs else ''}
<h2>By year</h2>{year_html}</article>"""
    write("browse/index.html", page("Browse | Murray Rothbard", "Browse Murray Rothbard's writings by topic, year, type and publication.", browse, "/browse/", "browse"))

    # ---- work pages
    for w in WORKS:
        url, label = source_link(w)
        desc = w.get("description") or f"{w['title']} by Murray N. Rothbard."
        tchips = "".join(f'<li><a href="/browse/topic/{t}/">{esc(TOPICS[t]["label"])}</a></li>' for t in w["_topics"])
        year = (f'<a href="/browse/year/{w["year"]}/">{w["year"]}</a>' if w.get("year") else "Not dated")
        pub = (f'<div class="fact"><b>Published in</b><a href="/browse/publication/{w["_pub"]}/">{esc(w["publication"])}</a></div>' if w["_pub"] else "")
        body = f"""<article><p class="meta"><a href="/">&larr; All works</a></p>
<h1>{esc(w['title'])}</h1>
<p class="prose">{esc(desc)}</p>
{f'<ul class="chips">{tchips}</ul>' if tchips else ''}
<div class="facts">
<div class="fact"><b>Year</b>{year}</div>
<div class="fact"><b>Type</b><a href="/browse/type/{w['_type']}/">{esc(w['type'])}</a></div>{pub}
<div class="fact"><b>License</b>{esc(w.get('license', 'Check at source'))}</div>
<div class="fact"><b>On this site</b>{'Full text' if w.get('hosting') == 'full' else 'Link to source'}</div></div>
<p><a class="btn" href="{esc(url)}" rel="noopener">{esc(label)}</a></p></article>"""
        write(f"works/{w['slug']}/index.html",
              page(f"{w['title']} | Murray Rothbard", desc, body, f"/works/{w['slug']}/"))

    about = """<article><h1>About this index</h1><div class="prose">
<p>Murray N. Rothbard wrote prolifically between 1949 and 1995. This site aims to be the most complete, easy-to-search list of that work, with each entry linked to a place it can be read.</p>
<p>Rothbard's writings are not in the public domain, and their licenses vary: some are released under Creative Commons licenses, some allow only non-commercial reuse, and some are fully reserved. So this site lists and links first, and hosts full text only where the license clearly allows it.</p>
<p>If you hold rights to a work listed here and want a change, please get in touch.</p></div></article>"""
    write("about/index.html", page("About | Murray Rothbard", "How this index of Rothbard's writings works.", about, "/about/", "about"))
    write("404.html", page("Not found | Murray Rothbard", "Page not found.",
          '<article><h1>Not found.</h1><p class="prose"><a href="/">Back to all works</a></p></article>', "/404.html"))

    urls = ["/", "/browse/", "/about/"] + facet_urls + [f"/works/{w['slug']}/" for w in WORKS]
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"<url><loc>{SITE}{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    write("CNAME", "murrayrothbard.com\n")
    write(".nojekyll", "")
    print(f"built {len(WORKS)} works, {len(urls) + 1} pages -> {OUT}")


if __name__ == "__main__":
    main()
