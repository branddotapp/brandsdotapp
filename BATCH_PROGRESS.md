# Outreach mockup batch (Oct 2026) — round 1 shipped; round 2 review in progress
Skipped: Holland Cooper (dropped), Olivia Rubin (~250K IG, deliberately shrinking), Story mfg (~243K IG, Mr Porter/Selfridges/DSM), Damson Madder, Ancient + Brave, Kestin, Edge of Ember, Motion Nutrition (3 staff, stalled), Lola Starr (too small).
Live (10): wawwa, uskees, albaray, navygrey, lilyandroo, dlouise, justbee, solebliss, avo, barebiology.
Template: home.heroSlides carousel (Lily & Roo only: the only brand with a real multi-slide hero; others are single hero/video or product sliders). One-size auto-select. Tests skip size/drop checks when a brand has none.
QA: smoke passes for all 10; layout passes at 375x667/393x852/430x932 (one transient DEMO-button contrast reading on Just Bee checkout).

## Review round 2 (14 Oct, Lewis feedback) — in progress
Tools: tools/screens.py (every screen, 393x852 + 375x667, simulated safe areas, contact sheets in /workspace/review/<slug>/), tools/visual_check.py (text-edge/clip detector, OCR crop warnings on cover images/posters/backgrounds, size-wording check for no-size verticals, logo-is-not-a-photo check).
Template: vertical-aware option labels and wording (no "size" for food/supplements; NOUN products vs pieces), one-option products hide the picker, wrapped feature/hero titles, editorial fit:natural, hero.baked (artwork with its own lettering: no overlay, whole hero taps through), welcome card avoids baked artwork, packshot mode (contain, no label crop) for food/supplements/footwear, generated square app icon for pushes + apple-touch-icon, product-type codes hidden (BLAZERS_TWILL -> Blazers), drop subtitle de-duplicated, fixed .app class collision that put the push icon over the title.
Builder: compare-at from same variant, option names, perks filter (carousel button labels, CSS fragments), opt-in menu count stripping.
Found in round 1 and fixed: wrong logos on 6 brands (BB product thumb, Uskees icon, Albaray/Navygrey photos, D.Louise sliver, Sole Bliss globe) -> official header logos.

Checklist key: L logo/splash/icon/push · V vertical features · T text padding/overflow · I images with text uncropped · F faces · P no placeholder/leaks/odd badges · C real copy/prices · S spacing

| brand | L | V | T | I | F | P | C | S | status |
|---|---|---|---|---|---|---|---|---|---|
| wawwa | fixed (official) | pass (clothing sizes) | pass | fixed (editorial natural, hero swapped) | OPEN: welcome card logo sits over face | fixed (Previous/Next announcement perks, "ф" name) | fixed (shipping £3.50/free £80) | pass | not done |
| uskees | fixed (official SVG) | pass | pass | pass | pass | fixed (BLAZERS_TWILL types, code search chips) | fixed (shipping free £90) | pass | needs final 375 pass |
| albaray | fixed (official) | pass (UK 8-18) | pass | fixed (baked hero video: no overlay) | pass | fixed (View All category, CSS perk) | fixed (free £99) | pass | needs final 375 pass |
| navygrey | fixed (official SVG) | pass | pass | fixed (split hero swapped) | OPEN: Shop "New arrivals" banner crops a forehead | pass | fixed (free £250) | pass | not done |
| lilyandroo | pass | fixed (rings now included; Ring size only, filter only on sized collections) | pass | pass (3-slide hero) | fixed (editorial removed) | pass | pass | pass | needs final 375 pass |
| dlouise | fixed (official) | fixed (ring sizes) | pass | fixed (editorial matches image) | pass | fixed (menu counts "Bracelets 79", CSS perks) | fixed (UK shipping, free £75 now applied in bag) | pass | needs final 375 pass |
| justbee | fixed (light logo for splash) | fixed (no size anywhere, packshot) | pass | fixed (editorial natural, jars uncropped) | pass | pass | OPEN: free-delivery threshold not verified | pass | not done |
| solebliss | fixed (official, was a globe) | pass (UK/EU shoe sizes) | pass | fixed (packshot: shoes uncropped) | pass (legs-only hero is intentional) | fixed (Size EU 43 as feature) | pass | pass | needs final 375 pass |
| avo | pass | pass | pass | fixed (baked hero: no overlay, welcome uses product) | pass | fixed (heading-as-about) | pass | pass | needs final 375 pass |
| barebiology | fixed (real SVG wordmark, app icon) | fixed (Pack not Size, no size wording, packshot) | pass | fixed (editorial natural) | pass | fixed (cookie table page, -83% badges) | fixed (free delivery on all orders) | pass | needs final 375 pass |
Automated: visual_check.py 0 fail / 0 crop warnings on all 10 (393x852 + 375x667) as of 09:15.

## Final 375x667 sign-off (14 Oct)
- wawwa — DONE. All 45 screens re-read at 375x667. Fixed in this pass: welcome card now their rear-view product shot (logo was sitting on a face; the framing change *was* applied, the subject's head just sat under the centred logo), Shop kicker "WAWWA Ф" glyph. All checklist items pass.
