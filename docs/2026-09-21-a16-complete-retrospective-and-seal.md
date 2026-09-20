# A16 complete retrospective and seal (2026-09-21)

Scope: **Super Robot Wars F only / Sega Saturn / F RevB**.

This is a public-safe retrospective. It publishes process, structural counts, validation outcomes and hashes only. It does not publish ROM/BIN data, disc tracks, commercial assets, font payloads, dialogue dumps, saves, recordings, private paths or third-party tables.

## 1. Starting point

A16 began after the A15 controlled translation test had demonstrated one real end-to-end Saturn text edit through encoding, SCEDATA rebuild, Track1 patching and emulator display.

A16 therefore changed the question from "can one controlled string be shown?" to "can the project support a repeatable production-scale localization workflow with traceable context, translation references, deterministic rebuilding and runtime review?"

The main goals became:

1. align Saturn F RevB Japanese records to PS F Japanese records;
2. attach WGF Chinese references only after Saturn-to-PS record identity was established;
3. classify resources and episode ownership before translation;
4. run a production-scale Episode 1 translation/engineering batch;
5. rebuild from the frozen base rather than stacking canonical patches;
6. validate the exact candidate in both Mednafen and SSF;
7. use runtime defects to refine authoring and mapping policy;
8. close with an explicit font/production architecture decision.

## 2. Reference model

A16 adopted this evidence order:

Saturn F RevB Japanese -> PS F Japanese -> WGF Chinese reference

WGF was treated as translation and terminology evidence, not as authority for Saturn glyph IDs or Unicode identities.

The project also kept these claims separate: record/scene identity, text semantics, token/code identity, glyph identity, Unicode assignment, renderer behavior, and runtime acceptance.

Guide material and Japanese references were used to understand scene ownership and meaning. F-only scope was retained; Final material was not used as F canonical evidence.

## 3. A16-01A: Saturn-to-PS record alignment

The record bridge produced:

- 7,629 Saturn translation-master records;
- 6,388 PLAIN records in the A16-01A scope;
- 5,299 unique exact Japanese matches;
- 208 duplicate-text occurrences resolved by monotonic context anchors;
- 5,507 high-confidence exact Saturn-to-PS rows in total;
- 227 exact-text occurrence-ambiguous rows;
- 654 rows without an exact PS text match.

The resolved 5,507 rows had exact Japanese identity in the bridge and zero monotonic inversions. Streams 27, 41 and 45 remained explicit text-divergent exceptions rather than being forced into false matches.

## 4. A16-01B: three-way translation reference

Only after the Saturn-to-PS bridge was established were WGF records joined.

All 5,507 resolved rows were attached to the PS/WGF bridge. The working WGF reference layer used the then-current 1,108/2,816 effective mapping for reconstruction, while unresolved glyphs remained explicit.

The result was a three-way reference table and roughly 4,943 unique PS/WGF reference pairs.

A useful process lesson emerged: identical Japanese source strings can have different WGF treatment across physical occurrences. Translation references therefore remain record-specific; they are not globally inherited by matching text alone.

## 5. A16-01C through A16-01F: classify before translating

A16 deliberately inserted classification before large-scale translation.

The resource model distinguishes story/scenario dialogue, battlefield/map-event dialogue, mission conditions, system prompts/messages, menu/UI material, battle quotes, death/miscellaneous battle text, name/static tables, encyclopedia candidates, debug/test material, and unresolved material.

A separate episode/scene-phase layer was built for F's 50-episode structure. Global resources were not forced into an episode merely to make the table complete.

Residual/conflict closure was designed not to become an artificial translation blocker. Japanese context determined source meaning; WGF could be retained or edited when its Chinese expression was semantically equivalent.

## 6. A16-02: semantic Episode 1 translation

Episode 1 became the first production-scale translation batch.

The key design decision was to keep two layers separate:

- semantic master: natural approved Chinese;
- engineering/native layer: a technical runtime carrier constrained by the currently released native mapping and fixed-layout rules.

Later coverage review counted 77 Episode 1 semantic Chinese rows. Engineering restrictions were not allowed to overwrite the semantic master.

## 7. A16-03 and A16-04: engineering layer and cumulative build

The engineering ledger contained 63 candidate rows including the inherited mission-condition case. The cumulative candidate applied:

- 51 previously approved A15 edits;
- 62 new Episode 1 edits;
- 113 cumulative edits.

The build was regenerated from the frozen A11/A10 base rather than patching the A15 candidate as the canonical source.

The A16 SCEDATA result was:

- size: 359,768 bytes;
- SHA-256: 77e7a257dd01c62e8bfc370ef2f9bbc32af8481cbdece59d06d093e3735ed590.

Static gates included 52/52 strict stream re-decode, 74/74 pointer-pair validation, deterministic rebuild, and independent validation.

The controlled Track1 patch produced the tested Track1 identity:

daa62054b6e2a567e03e047d883d81e7f421f7ee3f813bb68efba641c1a0693c

The CUE remained:

9b940aa2afea650e86f786623cb4ab3982741cd5cdb59564112cc5ec5d32a870

The patcher also reported 176/176 MODE1 EDC/ECC checks passing.

## 8. Runtime closure

A16 was run in both Mednafen and SSF against the exact Track1/SCEDATA candidate above.

Both runs recorded exit code 0, matched emulator process identity, unchanged candidate identity after exit, unchanged source protection, integrity PASS, and no recorded A16-specific execution errors.

The supplied runtime archives were rehashed at 42/42 files for Mednafen and 37/37 for SSF after accounting for one ZIP-safe encoded filename.

Screen/video review observed in both engines: pre-map engineering text rendering, Episode 1 entering the map/battle phase, continued battle/map progression, post-map engineering text rendering, and clear into Intermission.

The runtime conclusion was therefore closed for the tested Episode 1 engineering scope, not for final linguistic quality or full-game coverage.

## 9. Important defect found by runtime

Runtime exposed a layout artifact that static validation had not made visually obvious.

In 58 of 63 engineering rows, fixed-length padding had been placed before the final closing quote. Both emulators showed the resulting closing quote displaced to the right.

Because the effect reproduced in both engines, it was classified as an authoring/layout artifact rather than a compression, pointer or emulator-divergence failure.

A separate recorder metadata defect was preserved: descriptive expected-text fields still contained stale A15 wording. Candidate identity remained bound by the correct A16 hashes, so historical receipts were retained rather than rewritten.

## 10. A16-05: layout policy refinement

The proposed layout-v2 rule moved declared padding after the closing quote while preserving record length, terminator position, control bytes and non-padding byte order.

Static recalculation covered:

- 63 engineering rows;
- 58 rows with relocated padding;
- 699 relocated padding bytes;
- maximum 42 padding bytes in one row.

For stream 1:

- frozen A16 compressed size: 6,758 bytes;
- layout-v2 temporary compressed size: 6,770 bytes;
- fixed allocation: 7,152 bytes;
- remaining slack: 382 bytes.

Recompression was deterministic and independent decoding returned the expected stream.

This was static only. It did not claim a new runtime pass, and 0x00 was not redefined as an invisible padding instruction.

## 11. A16-06: native-mapping evidence audit

The previously released conservative native-authoring set remained at 1,330 preferred unique mappings.

A16-06 audited the 5,507 exact Saturn-to-PS rows at token boundaries and observed 1,364 storage tokens.

It identified 94 additional single-Unicode token candidates, representing 93 potential additional Unicode values and one additional token alias for an already represented Unicode value. There were zero reference conflicts and zero new canonical Unicode promotions.

The zero-promotion result was deliberate. Inspection showed that the PS and Saturn Japanese labels in the relevant bridge shared the same jp_reference lineage. Repeating a label produced by the same reference source is not independent Unicode evidence.

This corrected an earlier proposed promotion rule and is one of A16's most important methodological improvements.

## 12. A16-07: Episode 1 production coverage

Episode 1 semantic coverage was recalculated from the unchanged semantic master:

- 77 semantic rows;
- 468 unique visible Unicode characters;
- 1,927 visible scalar occurrences.

With the released 1,330 mappings:

- 231 unique characters were directly covered;
- 237 were missing or held;
- 0/77 rows had direct full-string glyph coverage.

With the diagnostic released-plus-candidate set:

- 237 unique characters were directly covered;
- 231 remained missing or held;
- direct full-string coverage remained 0/77.

The 468 characters were further separated into 231 existing preferred, 103 orthographic-production proposals, 6 new positional-reference candidates, 2 duplicate-token-policy cases, 38 reference-table-only not released, and 88 not covered by the audited maps.

These categories explicitly prevent the false conclusion that "237 not released" means "237 new glyphs required."

Two independent non-font issues were also found:

- 12 semantic rows had F6/F7/control topology different from the source record;
- 11 rows exceeded the original record byte budget even under the current strict lower-bound calculation.

## 13. A16-08: final production architecture decision

A16 rejected four premature strategies:

1. native-only final production, because it would force unnatural wording to satisfy today's glyph set;
2. immediate whole-font replacement, because font-bank ownership, capacity and safe-slot policy were not yet proven;
3. automatic WGF-to-Saturn glyph inheritance, because WGF is not independent Saturn glyph authority;
4. automatic variable-length relocation, because the runtime-proven contract through A16 is fixed-layout.

The adopted architecture is:

**hybrid native reuse + selective font extension**

with five layers:

1. natural Chinese semantic master;
2. context-reviewed production orthography;
3. native/extended glyph map;
4. record/control layout;
5. cumulative deterministic build from the frozen base.

## 14. What A16 improved

A16 changed the production methodology:

- from single-platform inference to a Saturn -> PS -> WGF evidence chain;
- from immediate translation to domain/episode/scene classification first;
- from one text layer to semantic, orthographic and engineering layers;
- from patch-on-patch to deterministic cumulative rebuilds;
- from static-only acceptance to exact-hash dual-emulator runtime review;
- from "missing mapping means missing glyph" to evidence-tiered demand analysis;
- from assuming Chinese always fits to explicit byte-budget checks;
- from silent control-code editing to a dedicated F6/F7 review gate;
- from evidence-counting to evidence-lineage auditing.

## 15. Sealed result and limits

A16 is **CLOSED / SEALED**.

Frozen tested candidate:

- Track1 SHA-256: daa62054b6e2a567e03e047d883d81e7f421f7ee3f813bb68efba641c1a0693c
- embedded SCEDATA SHA-256: 77e7a257dd01c62e8bfc370ef2f9bbc32af8481cbdece59d06d093e3735ed590
- CUE SHA-256: 9b940aa2afea650e86f786623cb4ab3982741cd5cdb59564112cc5ec5d32a870

A16 does not claim release-quality final Chinese for Episode 1, all 77 semantic rows directly encodable, runtime validation of layout-v2, canonical promotion of the 94 mapping candidates, complete Saturn font-bank ownership/capacity, completed font expansion, completed renderer/menu modification, runtime-proven variable-length relocation, runtime coverage of all 50 episodes, hardware-Saturn validation, or complete battle-quote translation.

## 16. Next boundary

The sealed next node is:

A17-01_SSF_REVB_FONT_BANK_OWNERSHIP_AND_CAPACITY

It starts with read-only discovery of the actual Saturn RevB font resource, glyph geometry/stride/indexing, token-to-glyph dataflow, and used/unused/duplicate/reclaimable slot policy before any font bytes are modified.

Future findings belong to A17 or to an explicit dated amendment. The A16 frozen candidate, receipts and conclusions are not silently rewritten.
