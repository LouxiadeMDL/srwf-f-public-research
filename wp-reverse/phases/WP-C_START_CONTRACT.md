# WP-C — CONSOLIDATED REVERSE / MODIFICATION METHOD CLOSURE

Project: `SRWF_F_WP_REVERSE`  
Phase: `WP-C`  
State: `ACTIVE`

## Goal

Complete the reverse engineering of WP/YZZL F as a modification system, not merely as a translation patch.

The end product must explain:
- every meaningful WP change in program code, TSR, SCEDATA and changed resources;
- the runtime consumer and business effect of each change;
- how WP adds/changes menus, options, scenarios, names, resources, data tables, state and save-related behavior;
- which mechanisms are localization support vs gameplay/private additions;
- how to reproduce supported modifications with new, auditable tools without relying on old unknown executables.

F is canonical. FF/PSFF/WPFF are reference-only and must never silently enter F canonical conclusions.

## Work packages

### WP-C0 — Evidence consolidation
Status: COMPLETE in this publication.
- unified source registry
- authority model
- GitHub historical DB catalog
- guide/modifier/static-editor/cross-code dataset registry
- WP-B validated overlay

### WP-C1 — State/save/private-bank closure
Status: ACTIVE.
Primary target:
- AB5C full producer/consumer/lifecycle
- slot127 cold boot / new game / snapshot / fieldwise pack-unpack / actual save-load call order
- distinguish storage semantics, observed business semantics and lifecycle
- legacy Save/RAM candidates may generate hypotheses only

### WP-C2 — root0 179-run / 610-byte semantic closure
- every changed run assigned to code/data owner
- consumer/dataflow
- localization-support vs gameplay/private vs resource relocation vs state/save vs audio/graphics
- no “ENDING because nearby file name” or similar proximity labeling
- R046/R047 and all prior HOLDs revisited under current authority rules

### WP-C3 — Menu/UI extension system
- menu builder
- callback namespace
- descriptor/pane/group/action namespaces
- opcode51/53
- mapped actions
- callbacks 2/11/32/37/47/49
- 9B/02 and related consumers
- produce reusable menu/option modification method

### WP-C4 — Name editor / input / serialization
- special-key remapping
- input buffer ownership
- delimiter/serialized format
- validation/rollback/cancel
- save/load compatibility
- maximum field contract
- reusable editor/input modification method

### WP-C5 — Scenario + guide matrix closure
- import guide dataset registry (227 events) as candidates
- bind only F events
- map candidate -> SCEDATA/TSR/BMESS -> opcode/flag/selector -> native handler -> business effect
- rebuild a new WP feature matrix under WP-C naming

### WP-C6 — Resource/data extension closure
- FACE/C_ROBOT/MAP_MAP/MAP_BANK/BBACK/EFFECT and other changed resources
- added portraits/images/maps/data tables
- loader/format/index extension methods
- resource relocation and size-growth rules

### WP-C7 — Reusable modification method/toolchain
For each subsystem:
`locate -> decode -> edit -> validate -> encode/rebuild -> verify`
No ROM/patch generation is required for research closure unless separately authorized.

### WP-C8 — Final reverse-engineering closeout
Exit only when:
- all known WP code/data/resource modifications are classified;
- unresolved items are explicit and narrow;
- each accepted semantic claim has provenance/evidence class;
- reusable modification recipes/tools exist for supported subsystems;
- F canonical is not contaminated by FF reference data.

## Current next action

Start `WP-C1` with AB5C producer/consumer/snapshot/save-lifecycle audit, using:
1. TARGET native bytes/handlers/CFG first;
2. WP-B storage/snapshot contracts second;
3. historical Save/RAM/static-editor/cross-code databases as candidate sources only.
