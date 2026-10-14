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
