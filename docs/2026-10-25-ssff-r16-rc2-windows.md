# SSFF CN1940 R5 R16 RC2 | windows and sortie-layout repair

Evidence date **2026-10-24**. Saturn **F Final**, RevA10M-derived CN1940 R5.  
Version ancestry: **R15 RC1 → R16 RC1 window candidate → R16 RC2 layout**.  
Track1 SHA-256: `b7c042778f6e48d76368406909605ea82924742d6022d86aaab233e0f9489123`.  
Stored result: `PASS_SCOPED_WINDOW_AND_DEPLOYMENT_LAYOUT`.

## Observed repaired categories

- After battle: map/turn-menu, B pilot viewer and ability-page **borders**, with missing HP/EN elements restored.
- Reinforcement: ship/unit list frames; second-row selection no longer hides the selected icon.
- Sortie list: Japanese **Rev A 10M** runtime reference established the original column positions: **icon x16; unit x32; pilot x184; level x248**. Morale and sorting headings return inside their native separators with font and icons at original size.
- “等级排序” is verified against “レベル順” in the actual level-sort mode; the separate morale-sort label/mode is retained. The sorter itself was not changed.

## Scoping and runtime evidence

Saved test used **official Ymir 0.4.1 unmodified core**, Linux capture front-end and an actual Saturn BIOS. From a fresh BIOS startup and **ordinary in-game 00 card**: natural F91 **OFF** attack → two enemy turns → reinforcement ship list → all four deployment pages. It also checked row selection, confirmation/return to map, B viewer and ability view. No old instant-state loading or manual guest-memory repair was used in the accepted route.

The scope-limited media audit preserved other ISO resources and Track2/Track3 identity; Track1/2 EDC/ECC checks reported zero errors. Media validity does not imply real-console acceptance.

**R16 RC2 supersedes R16 RC1 for layout/window work** while keeping R15's other stage-specific repairs. Oct 23 controlled RAM diagnostics are not themselves the release. Unverified: full campaign, all menus, ending subtitles, SSF Preview R38 and physical Saturn.

Evidence fingerprints **S103/S104/S105** are registered in [RECORD_DIGESTS.json](../evidence/specialized/2026-10-25/RECORD_DIGESTS.json). No ROM, original capture or translated media is distributed.