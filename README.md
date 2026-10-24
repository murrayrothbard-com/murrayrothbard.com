# murrayrothbard.com

A free, searchable index of the writings of Murray N. Rothbard. Static site, Python standard library only, deployed to GitHub Pages.

```
python3 scripts/build.py     # builds dist/
python3 -m http.server -d dist 8000
```

- Data: `data/works.json`
- Design brief and licensing policy: `DESIGN.md`
- Deploy: `.github/workflows/deploy.yml` (push to `main`). In the repo's Settings > Pages, set Source to "GitHub Actions".
- Domain: `CNAME` is `murrayrothbard.com`. Point DNS at GitHub Pages (A records for the apex, or CNAME `www`).
