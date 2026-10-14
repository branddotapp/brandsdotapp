# Outreach mockup batch (Oct 2026)
Skipped: Holland Cooper (dropped by Lewis), Olivia Rubin (~250K IG, shrinking "Benjamin Button" by founder's words, 4 staff), Story mfg (~243K IG, stocked Mr Porter/Selfridges/DSM - too established), Damson Madder (£31m, 700K IG), Ancient + Brave (£54m), Kestin (90+ stockists).
Built (overrides in each brand.overrides.json): wawwa, uskees, albaray, navygrey, lilyandroo, dlouise, justbee, solebliss
Status: smoke tests pass (justbee: only "no sizes" check, correct for honey). Layout: contrast fix in build_brand normalise_theme; solebliss long size labels pending.
Pushed 4d0cf5d (all 8 live). Next: remaining 2 slots (fitness/wellbeing).
- In progress: avo (Avo Activewear, 36K IG), barebiology (51K IG, 60%/yr growth, subscriptions)
- 14 Oct 01:45: avo + barebiology built (overrides done). Template: hero carousel (home.heroSlides) added, enabled for lilyandroo (3 real slides). Tests: skip size/drop checks when brand has none. Pending: QA run, commit, push.
- 01:58 fixes: one-size auto-select (template), test harness drop/size skips, justbee/barebiology/avo overrides. Re-running QA.
- 02:25 barebiology hero -> still (2.3s video). Final QA running for all 10.
