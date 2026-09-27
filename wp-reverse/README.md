# SRWF_F_WP_REVERSE

Independent reverse-engineering track for the WP/YZZL modification of **Super Robot Wars F**.

This directory uses its own phase names (`WP-B`, `WP-C`, ...). Historical task/conversation names are retained only as provenance and are not the current project structure.

## Objective

Reverse WP as a modification system:
- code changes
- TSR extensions
- SCEDATA scripting
- menus/options
- data tables
- state/save behavior
- text/font/input
- resource additions and format/index extensions
- gameplay/private modifications
- reproducible modification methods

## Current state

- `WP-B`: validated historical baseline — complete with reservations
- `WP-C0`: evidence consolidation — complete
- `WP-C1`: state/save/private-bank closure — pass with save/cold-boot reservations
- `WP-C2`: root0 semantic closure — pass with policy/runtime holds
- `WP-C3`: menu/UI number-domain closure — pass with business/lifecycle holds
- `WP-C4`: name editor/input/serialization — pass with cancel/save-load/second-editor holds
- `WP-C5`: scenario + guide matrix closure — **active**

## Start here

1. `PROJECT_CHARTER.md`
2. `SOURCE_AUTHORITY.csv`
3. `phases/WP-B_VALIDATED_BASELINE.md`
4. `phases/WP-C_START_CONTRACT.md`
5. `phases/WP-C0_CONSOLIDATION_REPORT.md`
6. `data/reference_dataset_registry.csv`
7. `data/wp_b_validated_claims.csv`
8. `data/wp_c_phase_map.csv`
9. `WP_C_STATE.json`

## Evidence rule

Target-native Saturn WP bytes/handlers/CFG outrank all historical, cross-platform, static-editor, MDB/BNE2, guide and external-dialogue evidence.

Historical sources are used to generate candidates and semantic hypotheses; they cannot silently promote a Saturn WP claim.

## Public-safe scope

No game image, ROM/BIN, font, dialogue dump, save image, legacy EXE/DLL or unknown-license source is included. Historical database identities and table counts are catalogued, not republished wholesale.

F is canonical. FF-related material is reference-only.
