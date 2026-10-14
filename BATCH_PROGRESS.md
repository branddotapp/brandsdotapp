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
- uskees — DONE. 46 screens at 375x667 re-read. Fixed this pass: search-row types (Overshirts_cord), welcome card (logo was over a face; now logo on brand colour, applied to all brands). All items pass.
- albaray — DONE. 49 screens at 375x667 re-read (splash checked separately at 900ms: logo fades in, fine). All items pass.
- navygrey — DONE. 45 screens at 375x667 re-read. Shop 'New arrivals' banner now framed at 12% (face whole); all items pass.
- lilyandroo — DONE. 44 screens at 375x667 re-read. Fixed the restock push saying 'back in size A' (initial letter): it now picks a product with a real size option (bracelet Small/Medium). Ring size kept because they sell rings. All items pass.
- dlouise — DONE. 46 screens at 375x667 re-read. Fixed the Account footer showing the raw Instagram URL; it now reads @d.louise (handle normalised in the template). Ring sizes kept (they sell rings); shipping matches their page (free Standard over £75). All items pass.
- justbee — DONE. 46 screens at 375x667 re-read. Fixes: the stacked logo was a speck at wordmark height, so square/stacked logos now get a 'logo-tall' size (header 30px, welcome 52px, card, footer); white-on-dark logos are flattened to pure white (no more inverted purple); duplicate 'All Honey' removed from Popular categories. Free UK delivery over £40 confirmed on justbeehoney.co.uk/pages/just-bee-honey-delivery-information. No size wording. All items pass.
- solebliss — DONE. 44 screens at 375x667 re-read. Fixes: search for 'Trainers' returned no results (product titles don't say 'trainers'), so search now also matches the collections a product sits in, plus simple plurals (100 results); dropped the odd 'Size EU 43' collection from Collections. UK/EU shoe sizes correct. All items pass.
- avo — DONE. 48 screens at 375x667 re-read. Fix: the bag said delivery was 'Free' on a £47 order, but avoactivewear.com/pages/shipping-information says free Royal Mail Tracked 48 only over £90 and doesn't publish the under-£90 price. So the option now shows 'At checkout' below £90 (the template supports unknown prices, price:null) and a spend-£43-more bar. Stacked logo gets the logo-tall sizing. All items pass.
- solebliss (re-check) — the bag also said 'Free' at £189. Corrected from solebliss.com/pages/shipping-returns: UK £5.95, free over £200. Still DONE.
- navygrey (re-check) — the scraped 'UK delivery £60' was wrong. Corrected from navygrey.co/pages/orders-delivery: Royal Mail £5.75 (free over £250), DPD £7.00, DPD Premium £10.00. Still DONE.
- barebiology — DONE. 42 screens at 375x667 re-read. 'Pack' options (no sizes), free Express Royal Mail, real copy. All items pass.
