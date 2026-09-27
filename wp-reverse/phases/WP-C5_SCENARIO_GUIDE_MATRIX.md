# WP-C5 — Scenario / Guide Matrix Closure

Date: 2026-09-27  
Project: `SRWF_F_WP_REVERSE`  
State: **ACTIVE — batch 1 closed**

## Scope

This phase binds F guide/event candidates to:

`SCEDATA / TSR / BMESS -> opcode / flag / selector -> TARGET native handler -> business effect`.

Guide text is never sufficient for native promotion.

## Baseline

The historical 71-item matrix entered WP-C5 with:
- BOUND 34
- PARTIAL 4
- OPEN 32
- HOLD 1

After this batch the working classification is:
- BOUND: 37
- BOUND_WITH_NAME_CONFLICT: 1
- PARTIAL: 5
- OPEN: 20
- HOLD: 1
- OPTIONAL_VARIANT_REFERENCE: 6
- REFERENCE_CONFLICT: 1

The two BOUND classes together represent 38 bounded target features. Optional variants are not counted as unresolved baseline WP functions.

## New native opcode contracts

- `C0/0F @ 0x06021338`: count selected actor/entity instances inside an inclusive map rectangle.
- `C1/00 @ 0x06025DB8`: create/add a runtime pilot in the first free pilot slot.
- `C1/02`: remove runtime pilot.
- `C1/04 @ 0x060260B0`: associate an existing runtime pilot with an existing runtime unit definition.
- `C1/05 @ 0x06026130`: detach a pilot from any runtime unit while keeping the pilot record.
- `C2/00 @ 0x060287A4`: remove/deactivate runtime unit by definition selector.
- `C2/04 @ 0x06028BC8`: create/add runtime unit by definition selector.
- `C2/0F @ 0x060291EC`: replace runtime unit definition and rebuild derived state.

These primitives are now the canonical basis for recruitment, co-pilot, unit acquisition and transformation closure.

## Scene 18 exact-position reward chain

TARGET call:

`C0 0F 00 0A 02 04 02 04`

Native semantics:
- selector `0x000A`
- exact coordinate X=2, Y=4
- rectangle query succeeds only when a matching entity is present there.

The local producer also requires the observed flag-state conditions including AB13 clear and AB1B set, then sets `00E9`.

The `00E9` consumer executes:
- `C2/0F 0001 -> 0009`
- `C2/0E 0E` -> Fatima inventory +1
- four money increments of 50,000 -> +200,000
- set `016F`

Historical PS F labels call unit0001 `ガンダム` and unit0009 `νガンダム`, while the guide calls the feature `高达R`. These are lower-authority naming sources; WP-C5 keeps the name conflict instead of overwriting the TARGET physical effect.

## Fatima cleanup

### Closed
- scene45 qualification collector -> BE -> scene12 Fatima inventory consumer.
- scene71 Sety1 deployment drop selector `0x0D`.
- scene18 exact-position reward -> Fatima +1.
- scene30/67 Haman/Qubeley deployment records use drop selector `0x0D`, matching the already-bound Fatima selector.

### Partial
Zeub deployment records use selectors `0x09 / 0x0A / 0x1E`, not the known Fatima selector `0x0D`.

TARGET helper `0x0602A88C` proves CA/02 byte+6 selects a weighted drop table. It is **not a raw item ID**. Zeub therefore remains drop-table-bound until the selected table contents are decoded.

## DLC separation

The YZZL F guide describes machine DLC conditionally ("if machine DLC is supported") and lists six groups:
- Sazabi
- Tallgeese III
- Master/Toho Fuhai
- Haman/Qubeley
- Maba
- Grays/Grays II wording in the guide set

The prior matrix also merged Shuu/Granzon into the same stage-DLC group. The same source instead places Shuu in later Masoukishin story conditions.

TARGET SCEDATA scene6 is independently bound to `エヴァンゲリオン、始動`. Its stage-end script does not contain six ordinary pilot/unit roster-add chains. Therefore:
- six machine-DLC rows are `OPTIONAL_VARIANT_REFERENCE / TARGET_VARIANT_UNBOUND`;
- Shuu/Granzon is removed from the baseline DLC group and retained only as historical provenance.

## Current holds

- target-native unit name for definition 0009 in the scene18 transform;
- exact weighted drop-table contents for Zeub;
- remaining plot/recruitment consumers;
- some reward/weapon final-write consumers;
- optional DLC variant binaries/configuration are outside the current baseline target.

## Next batch

1. Resolve weighted drop-table resource/table if the exact TARGET data becomes available.
2. Use C1/00/02/04/05 to bind remaining recruitment/co-pilot rows.
3. Group remaining plot flags by shared consumer rather than auditing guide rows one-by-one.
4. Regenerate the feature matrix under WP-C naming after the next closure batch.
