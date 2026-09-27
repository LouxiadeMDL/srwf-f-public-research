# WP-C1 — STATE / SAVE / PRIVATE-BANK CLOSURE

Project: `SRWF_F_WP_REVERSE`
Status: `PASS_WITH_SAVE_COLD_BOOT_RESERVATIONS`

## AB5C storage
- flag: `0xAB5C`
- state offset: `0x1A9F`
- mask: `0x08`
- physical owner: pilot runtime slot 127, byte 11

## Direct TARGET references
Validated late checkpoint:
- direct SET: 1
- direct CLEAR: 0
- direct TEST: 13
- rooted/CFG-bound consumers: 6
- raw-only TEST patterns: 7

The sole direct SET is in scene45 at `0x1640`, on the experience-return route.

## Observed business semantics
Safe business gloss:
`0079 experience-return / later-content eligibility latch`

Do **not** rename it globally as a cross-save “0079 completed flag”.

Bound consumers include:
- anti-replay gate at scene1 entry;
- return initialization behavior in scene1 / scene51;
- hidden-route gate in scene30 / scene67 together with ordinary flag `0x0107`;
- scene72 eligibility gate before two level checks and a later choice/scene transition.

## Lifecycle
WP deliberately skips slot127 in several ordinary pilot/state loops:
- ordinary clear path
- fieldwise reconstruction/unpack path
- related bounded refresh loops

Raw snapshot/restore is a different contract:
- snapshot copies state `[0x5A0,0x1AA0)`
- restore copies the same range back
- therefore the complete slot127/private bank, including AB5C, is included

This proves snapshot persistence for that helper pair, **not** persistence in the actual disk save format.

## OPEN
- cold-boot establishment of slot127
- new-game ordering
- actual disk save backend ordering
- actual disk load backend ordering
- warm restart ordering
- old WP save compatibility/migration
- indirect/non-D0 producers beyond the bounded set

## Modification implication
A static editor may expose AB5C as a condition/state bit only if it also shows the lifecycle warning. Editing the bit and editing save persistence are separate features.
