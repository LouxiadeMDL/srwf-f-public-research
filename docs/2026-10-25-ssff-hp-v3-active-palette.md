# SSFF V3 | restore native result-window colors after effective HP display

Evidence date: **2026-10-15**. Parent chain: **CN02R2 + BD01 + pre-existing P6B title + ACTIVE_PALETTE V3**.  
V3 Track1 SHA-256: `abbb3e754083888a5d8683d05987601b487e1444b0a5aa777c70e5808a5c12c8`.

## Cause and fix / 故障成因

Effective-HP drawing changed ColorRAM and did not fully restore the native money/experience result-window palette. The normal **dark background, light letters and gold border** became wrong. An initial **B17** attempt restored an empty working cache and produced a black window; this failed candidate is kept as negative evidence, not counted as a repair.

V3 saves the **currently active ColorRAM when the HP pathway begins** and restores the same state through the native color-cache/upload chain when finishing. This is a preservation of original presentation, **not** a redesigned window or modified combat calculation.

## Bounded V3 runtime acceptance

A new V3 cold start, ordinary Continue, and candidate-native preview states covered **six** ON/OFF/Start early/middle/late/extra-input display paths. **48** recorded window samples, each **5,264 pixels**, matched corresponding original Japanese regions within the stored comparison. HP transitions, single ammo/EN costs, queue cleanup, and normal return were checked.

An additional R input during an OFF route led to a **native counterattack MISS**; no fake extra HP loss was inserted. A 900-frame tail-stage input and later 1020-frame HP-display input were recorded as different cases, not conflated as instant animation speed-up.

The earlier **D8** baseline covered toggle, HP=0, MAP/repair/supply and randomized cases; **V3 did not newly rerun all D8 cases**. The new palette result is limited to observed **mode0 ordinary battles**; mode1 uses the earlier HP path.

## Code and public limits

The private package includes source/rebuild work, a **1,470-byte** animation component and a **1,628-byte** HP component, and historical exact Track1 rebuild checks. Components depend on this F Final UI/font/control chain and are **not** presented as plug-and-play for Saturn F or PS F. No compiled module, game code seed, code archive, full track, screenshot, save, or copyrighted P6B art is distributed.

Source fingerprints **S128/S129**: [RECORD_DIGESTS](../evidence/specialized/2026-10-25/RECORD_DIGESTS.json).