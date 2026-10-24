# SSFF CN02 R2 + BD01 | battle animation switch and effective HP

Evidence date: **2026-10-14**; target: **Saturn F Final RevA10M CN02R2**.  
Accepted parent: BD01 candidate05; candidate04 was rejected.  
BD01 Track1 SHA-256: `6cd32afffad06391da48b463263bd109af3a82fb4c6d7bdf8424f00e117bf40e`.

## Native function / 用户操作

- During battle preview, **R** switches `省略影像`: **否** = play battle animation; **有** = omit it. Cold start defaults to animation enabled.
- **Start** skips the active animation through the original return sequence without changing the chosen animation setting.
- **ON**, **OFF** and **Start** all return to the map showing **actual effective damage and HP**. Map damage display is independent of animation toggle, and is not separately switchable.
- HP, EN and ammunition are committed **once** by the game's own combat ledger, not by the overlay. Aborted/precomputed counterattack values are never a substitute for actual hits.

## Bounded test paths

The saved report describes **24,138 frames** of Yabause/libretro HLE cold-start execution with native controller inputs, no instant-state load and no manual guest-memory writes. Repeated R changes, Start early/middle/late and successful return-to-map were captured.

One important negative test: a lethal first hit reduced the defender from **1665 → 0**, so the overlay showed **−1665** and the native HP=0 cancellation prevented a predicted but nonexistent **−1704** retaliation. That false retaliation was the reason candidate04 was rejected. An ordinary Save → process exit → fresh Continue also checked **12,624** payload bytes and **119 unit HP/EN** entries.

## Version-scoped reservation

BD01 acceptance is for **ordinary bilateral battles plus one standard save roundtrip**. It does not certify MAP weapons, repair/supply, randomized tests, entire gameplay, desktop GUI, SSF Preview R38 or real hardware. Subsequent D8 regression testing and [V3 palette repair](2026-10-25-ssff-hp-v3-active-palette.md) must be evaluated by their own identities; later results cannot be retroactively assigned to BD01.

Private evidence digest: **S126** in [RECORD_DIGESTS](../evidence/specialized/2026-10-25/RECORD_DIGESTS.json). No binary code, image, ROM, translated payload or save is published.