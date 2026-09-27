# WP-C5B — OPTIONAL MACHINE-DLC INTEGRATION RECLASSIFICATION

Project: `SRWF_F_WP_REVERSE`  
Date: 2026-09-27  
Status: `PASS_FOR_CURRENT_TARGET_NEGATIVE_BINDING_WITH_EXTERNAL_DLC_PROTOCOL_HOLD`

## Scope

This node reviews the guide-described optional machine-DLC integration associated with
`シナリオ6「エヴァンゲリオン、始動」`.

The historical guide lists six front-half DLC additions:
- Sazabi
- Tallgeese III
- Master Asia / Master Gundam
- Haman / Qubeley
- 魔霸
- Mekibos / 灰羚羊II

The same guide says the specific DLC support method should be obtained from the author.
The old feature matrix contained a seventh row, Shu / 真古兰森, in the same group.
That seventh row is not supported by the cited front-half DLC list and is remanded to
independent provenance review.

Guide source:
https://kxb4u.com/yzzl/viewthread.php?action=printable&tid=115347

## Scenario identity

TARGET SCEDATA text directly identifies scene 6 as:
`シナリオ6「エヴァンゲリオン、始動」`.

## Native creation contracts used

TARGET root0 handler tracing establishes:

- `C1/00`: create/initialize pilot runtime record.
- `C1/06`: advanced pilot-create/init variant using the same pilot allocator.
- `C2/00`: remove/reset runtime unit by unit-definition ID.
- `C2/04`: create/add runtime unit by unit-definition ID.
- `C2/05`: advanced runtime-unit create/add variant.
- `C2/0F`: replace an existing runtime unit definition and rebuild derived state.
- `C0/13`: write body/weapon upgrade modifiers to a runtime unit.

## Current TARGET negative binding

TARGET scene6 decoded SHA-256:
`ebc58649d929e6662549466fe30b80a878fdd1560280dcede8464ccb29432ead`

Its stage-clear prefix rebuilds unit definitions `0002/0003` with
`C2/00 -> C2/04`; this is not a six-DLC grant sequence.

Deferred-grant checks:
- scene7: no reachable pilot/unit-create grant sequence
- scene57: no reachable create sequence
- scene75: repeats the `0002/0003` rebuild only
- scene1/common return roots: no reachable six-unit create sequence
- full `1 -> 41 -> 44 -> 42 -> 43 -> 45 -> 1` route: no six-unit grant group

## Reclassification

For the six guide-supported rows:

`EXTERNAL_DLC_INTEGRATION_POINT`

Substatus:

`GUIDE_BOUND / CURRENT_TARGET_DIRECT_GRANT_NOT_FOUND / EXTERNAL_PROTOCOL_HOLD`

For Shu / 真古兰森:

`PROVENANCE_MISMATCH_REMAND`

The cited front-half DLC list does not contain that seventh item.

## Safe conclusion

In the current target build, the documented EVA-stage six-machine DLC grants are not
encoded as direct pilot/unit grant operations in the stage-clear path, immediate
transition scenes, or the checked common/0079-return paths. The remaining dependency is
the external DLC support protocol/package.

This does not prove that no compatible external DLC package exists.
