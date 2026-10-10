# brandsdotapp tools

Turn a brand's website into a clickable concept shopping app (static HTML/CSS/JS, hosted on GitHub Pages).

```
_template/          shared app code: app.js, app.css, index.html (one copy for every brand)
_template/config.json  shared defaults merged under every brand (e.g. the desktop "Why an app" stats)
tools/build_brand.py  generator: scrapes a site and writes <slug>/
tools/smoke_test.py   headless Chrome click-through test + screenshots
<slug>/brand.json             everything scraped for the brand (products, theme, pages, copy, report)
<slug>/brand.overrides.json   optional hand-written copy, merged on top of brand.json
<slug>/assets/brand.js        brand.json as window.BRAND (generated, don't edit)
<slug>/assets/app.js|app.css  copied from _template/ at build time
<slug>/assets/img/, hero.mp4/.webm  logo (dark + light), favicon, hero poster, campaign image, hero video
```

## Requirements

Python 3.9+, plus:

```
pip install beautifulsoup4 pillow playwright
```

- `ffmpeg` on PATH (hero video transcode + poster frame). Without it the hero is a still image.
- Google Chrome at `/usr/bin/google-chrome` (used for the rendered-page pass, SVG logo rasterising and the smoke test).
  `--no-render` skips the Chrome pass if you don't have it.

## Build a brand

```
cd brandsdotapp
python3 tools/build_brand.py https://raith-clo.com raith
python3 -m http.server 8000      # then open http://localhost:8000/raith/
```

The run prints a ✓ / ✗ line for every thing it looked for and finishes with a **Missing / placeholder** list.
The same report is saved in `<slug>/brand.json` under `report`. Nothing missing is invented: features with no
data are hidden (e.g. no review score → no social proof block, no season collection → no Drops tab).

Options:

| flag | what it does |
|---|---|
| `--refetch-video SLUG` | re-download just the hero video at the best quality available, re-encode it with the settings below, then rebuild |
| `--rebuild SLUG` | re-render from the saved `brand.json` + `brand.overrides.json` without touching the network (use after editing overrides or `_template/`) |
| `--no-render` | skip headless Chrome (no announcement bar / Trustpilot widget data) |
| `--max-products N` | cap the catalogue (default 400 products from the nav collections) |
| `--root DIR` | write somewhere other than the repo root, e.g. `--root /tmp/try` for a dry run |

## What it scrapes

| | source |
|---|---|
| Products, prices, compare-at prices, sizes + stock, images | Shopify `/products.json` and `/collections/<handle>/products.json` |
| Collections, nav order, categories vs edits | Shopify `/collections.json` + the site's header nav |
| Currency | `/cart.js` |
| Logo (dark + light), favicon | header logo `<img>` / inline SVG, `<link rel=icon>` |
| Colours, font | site CSS custom properties / most frequent colours; Google Fonts if the font is on it |
| Hero video / poster / campaign image | homepage `<video>` (Shopify's original upload when it's public, otherwise the best transcode) and large images. See **Hero video** below |
| Help, About, Legal pages + summaries | links in nav/footer matched by name (shipping, returns, FAQs, contact, about, sustainability, stockists, privacy, terms, refund, cookies) |
| Delivery options, cut-offs, free-delivery threshold | the shipping page (first region listed) |
| Returns copy | the returns page |
| Instagram handle | footer / social links |
| Instagram feed (followers, bio, latest 9 posts) | **not scraped**: collected separately in a browser and stored in `brand.overrides.json`, see **Instagram feed** below |
| Review score | Trustpilot widget data (only if the site embeds a Trustpilot widget) |
| Marquee perks | announcement bar / cart USP slider in the rendered page, plus delivery and returns facts |
| Whether pages can be shown in an iframe | `X-Frame-Options` / CSP `frame-ancestors`. If blocked, the in-app browser shows the page summary with "Open on site" |
| Next drop | the newest season collection (e.g. "AW26") that isn't the current hero; drop number from `XX26D6`-style tags |

Things that are always placeholders (they don't exist on a website): the drop date/time (rolling: app early access
Wednesday 19:00, website Thursday 19:00), the rewards balance and barcode, login/sign-up (demo only, nothing saved
or sent), checkout (no real order) and the APP10 code.

**Non-Shopify sites** build without crashing: no products/collections, Drops and size features hidden, theme/logo/pages
taken from whatever can be found, and every gap listed in the report.

## Hero video

Every brand's hero video is encoded the same way (`HERO` in `build_brand.py`):

- source: for each homepage `<video>`, the Shopify original upload (`/cdn/shop/videos/c/o/v/<id>.mp4|.mov`) is tried before
  the transcode; portrait / 4:5 sources win, then the most pixels
- cropped to the app hero's shape (0.63, i.e. 390x620) and scaled to **1080 px on the long side** (never upscaled), Lanczos
- **H.264** high profile, **CRF 23**, preset slow, keyframe every 2s, yuv420p, **faststart** (moov atom first), **no audio**
- **seamless 8–12s loop**: it ends exactly on a hard cut (nearest 10s) so jumping back to frame 0 reads as a normal cut;
  with no cut in range the tail is cross-faded into the head
- optional **WebM/VP9** copy (`hero.webm`, CRF 34) as a second `<source>`; poster = first frame of the loop, same crop, JPEG q2

In the app the `<video>` has `autoplay muted loop playsinline preload="auto"`, `object-fit:cover`, is created once and kept
across Home re-renders (so it never restarts), and pauses when scrolled off screen or the tab is hidden. Nothing over it uses
`backdrop-filter` (re-blurring every video frame made playback stutter).

## Instagram feed

Home shows an Instagram block directly below the Trustpilot block: `@handle`, follower count, bio line and a **Follow** button
(opens the profile in a new tab), then a 3x3 square grid of the latest posts. Each tile opens its post in a new tab and reels / carousels
get a small corner icon. The block is hidden when the brand has no posts.

Instagram can't be scraped (login wall), so the scraper only finds the handle. The posts are **collected separately via a browser**
(open `https://www.instagram.com/<handle>/`, note the follower count, bio and the first 9 posts' URLs and types, save each
thumbnail) and **stored in `<slug>/brand.overrides.json`**, so `--rebuild` and full re-scrapes keep them:

```json
"instagram": {"handle": "raithclothing", "url": "https://www.instagram.com/raithclothing/", "followers": "111K",
  "bio": "Stocked in Selfridges & Harvey Nichols", "collected": "2026-10-09",
  "posts": [{"url": "https://www.instagram.com/reel/Dd7QBkYt1xl/", "type": "reel", "image": "assets/ig/1.jpg"}, ...]}
```

- `type` is `reel`, `carousel` or `photo`; `posts` is a list, so the override replaces it whole (refresh all 9 at once)
- thumbnails go in `<slug>/assets/ig/N.jpg`: square crop (slightly above centre), max 600px, JPEG q80 progressive
- the build logs the feed status and skips posts whose URL isn't an instagram.com post or whose thumbnail file is missing

## Desktop layout

On desktop (over 1000px wide) the page is three columns with the phone centred in the window: on the left the brand pitch
(logo, "X APP, CONCEPT", headline, copy, feature lines) and the "Try it: send a push to the phone" demo buttons; on the right
a **"Why an app"** column of four stat boxes (big number, label, one-line explanation, source link opening in a new tab).
`fit()` in `app.js` scales the phone to the window height and each side column towards the phone if it doesn't fit.
Between 1001 and 1099px the stats move under the pitch as a compact 2x2 (explanation kept as the box tooltip); at 1000px and
below only the phone shows (Demo button in the app), and the phone-only mobile view is unchanged.

The stats live in `_template/config.json` → `stats` (`heading`, `items: [{num, label, copy, source, url}]`), so they are
edited once for every brand. A brand can override them in `brand.overrides.json` (`"stats": {"heading": "..."}` merges;
`"stats": {"items": [...]}` replaces the list; `"stats": false` hides the column). The boxes use the brand's font and theme
colours; brand-level styling goes in `<slug>/brand.css` (Yelir: square corners, bold numbers).

## Hand-tuning a brand

Put copy you want to keep across re-scrapes in `<slug>/brand.overrides.json`. Objects merge, lists and strings replace,
keys starting with `_` are comments. Example (`raith/brand.overrides.json`):

```json
{ "pitch": { "title": "Timeless menswear,<br>one tap away." },
  "home": { "hero": { "title": "PRE FALL 26", "cta": "Shop Pre Fall" } },
  "perks": ["Free UK delivery over £150", "Over 300,000 happy customers"] }
```

Then `python3 tools/build_brand.py --rebuild raith`. Useful keys: `name`, `short`, `pitch`, `home.hero`, `home.tiles`,
`home.editorial`, `home.feature`, `instagram`, `perks`, `scrape.extraCollections` (menu collections the static HTML doesn't expose), `scrape.colours` (colour names to split off the end of product titles like "Hybrid High Waisted Leggings Mahogany", so colourways share a name and show as swatches), `search.trending`, `drop` (set `drop.opensAt` to an ISO date for a real
drop time), `discount` (`{"code":"APP10","pct":10}`), `theme` colours, `copy`.

## Test

```
python3 -m http.server 8765 &
python3 tools/smoke_test.py raith --shots raith-shots/v11
python3 tools/layout_check.py raith            # 390x844, 1280x720, 1440x800, 1920x1080 by default; -v lists notes, --shots DIR
```

Clicks through every tab and feature at 390x844, 1280x720, 1440x800 and 1920x1080 (plus a prefers-reduced-motion pass), fails on console errors, failed requests, broken images
and missing sections. Also checks the Home header band (status bar area + perks marquee + header) is one translucent tint with edge-faded marquee, the hero video is playing, not upscaled and has the right attributes, that the review block
sits near the bottom of Home, that the Instagram feed sits directly below it (3x3 square tiles, every tile a valid instagram.com post URL with `target=_blank`, reel/carousel icons, Follow button, hover state, hidden with no posts; section screenshot `instagram.png`), and that the welcome pop-up shows again on reload. Motion/interaction checks (v11): the segmented control's white pill slides (transform + width, 0.28s cubic-bezier, sampled mid-flight) and the content swaps; segment kept after back; tab cross-fade and active-icon spring; push/pop slide with parallax and shade (no `filter`); button press scale ~0.97 and hover; heart pop + ring; add to bag → "Added" + check, header bag count bump, sheet after; sheet drag-handle dismiss; image fade-in + shimmer; rail snap; switch knob transition; PDP title bar; Escape back/close; bag quantity totals; checkout Change buttons; Demo button hidden on product pages and under toasts; reduced motion turns it all instant. Desktop stage (v12): three centred columns that fit the window with no overlap or page scroll; the "Why an app" column has 4 boxes matching `BRAND.stats`, each with a valid https source link (`target=_blank`, `rel=noopener`) that opens a new tab, a fade-in and a hover lift; source URLs are fetched once (401/403/429 bot walls are noted, not failed). Screenshots land in `<slug>-shots/` (git-ignored).

`tools/layout_check.py` visits every screen and state and flags, inside the phone screen: horizontal overflow, clipped text (overflow without ellipsis/clamp), WCAG AA contrast failures, overlapping siblings in rows, header icons off-centre, the Demo button over a toast or buy bar, non-brand fonts, broken images, console errors, and (desktop) a stage that doesn't fit the viewport, an off-centre phone, overlapping columns, and stat boxes that are missing, overlapping, clipped, off-brand, low-contrast or have an invalid source link.

## Motion

All motion is transform/opacity only and switched off by `prefers-reduced-motion` (CSS block at the end of `app.css`; JS animations go through `anim()`, which checks the same media query). Easing tokens: `--ease` (iOS push/sheet), `--ease-out`, `--spring` (badges, toasts, switches, welcome card), `--seg-ease` (segmented pill).

## App URL parameters

`?nosplash` skip the splash · `?nowelcome` (the welcome pop-up shows on every page load; dismissing it only hides it until the next load) · `?nopush` · `?tab=drops` · `?p=<product-handle>`
