# Design brief: murrayrothbard.com

Written before any CSS, per the Elevate website skill's design-brief step (adapted for a library, not a practice).

- **Direction:** "Apple-clean, text-first." A calm, fast reading library; the writing is the product.
- **Palette:** white and #F5F5F7 (black and #1C1C1E in dark mode), near-black text, one accent blue used only for the primary button and links. No gradients, textures or decoration.
- **Type:** a serif (Iowan Old Style / Charter / Georgia) for titles and reading text; the system sans for interface. No web fonts, so first paint is instant.
- **Hero:** one short headline, one sentence of support, one search box. Search is the primary action.
- **Shapes:** pill search and buttons, 20px borderless gray fact cards, hairline dividers.
- **Signature:** a single searchable index where every work is one line, with year and type.
- **Efficiency:** no framework, about 10 lines of JS, inline CSS, one request per page.
- **Difference check:** vs. the Elevate client sites in `elevate-agents/sites/_shared/DESIGNS.md`, which are practice sites with photo heroes, this is a text library with no photography. Matches Ence/Glen Rose only on "Apple-clean"; type, hero and signature all differ.

## Content and licensing policy

Rothbard's writings are not public domain and licenses vary (CC BY, CC BY-NC, CC BY-NC-ND, all rights reserved). Each record has a `license` and a `hosting` field. Default `hosting` is `link`. Only set `hosting: full` after verifying the license permits republishing (and NonCommercial only if the site stays noncommercial). Otherwise get written permission from the rights holder.

## Data

`data/works.json`: one record per work (`slug`, `title`, `year`, `type`, `source_url`, `source_name`, `license`, `hosting`, `description`). The seed list is the major books; the full catalog should be imported from Tyler Kubik's "Murray N. Rothbard Bibliography: 1940-2019" (Property and Freedom Journal) and the Mises Institute's Rothbard library, verifying each source URL and license.
