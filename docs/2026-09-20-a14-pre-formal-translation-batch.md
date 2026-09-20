# SRW F — A14 pre-formal translation batch update

Record date: 2026-09-20  
Scope: **Super Robot Wars F only / Sega Saturn F RevB**.  
Publication treatment: public-safe engineering summary only. No game image, dialogue dump, font data, save data, translation table, glyph map, or patch is distributed here.

## Purpose

A14 moves the project from isolated controlled text edits toward a constrained translation-authoring workflow. It does **not** build or publish a translated disc image. The tested authoring scope remains deliberately narrow:

- Saturn F RevB only;
- records already accepted by the PLAIN storage profile;
- existing native glyphs only;
- same-length record replacement;
- no new control-code semantics;
- no font-bank, renderer or variable-length relocation changes.

Any future work outside those limits requires a separate gate rather than inheriting this result.

## A14 authority inputs

The private engineering package pinned the already-reviewed A05/A08/A09/A10/A11/A12 chain and the external DIC codec reference. Relevant public-safe fingerprints include:

| Item | SHA-256 |
| --- | --- |
| A08 storage codec source | `893663bfcaf8984c9e0be7902a4540ac587623b1dc29a71a50978846abac8fcd` |
| A10 compressor source | `8390b1cfa7994f11f3db7ae1972e6a13d1220151de7cbda36644f20f51ab70a9` |
| A10 independent decoder | `21b05790a999ad44541358caf69b8d4becb921f5944098e62b4aa15347dec850` |
| Asakim `dic-comp.c` | `8fed6eafc947f67a11f0c00346af956745ab811f34f5f3b5c6c16193c2cde8b7` |
| Asakim `dic-dec.c` | `99458e895dfe15f331cdf6feddefd95b9c65acd27bf94c070095a50a9654c787` |
| external reference table used only as a cross-check | `b052c394b9ca04c8c16faf28d1d2f96fff3bb40ce67dad24c9b30f957a2df0e0` |

The external table was not accepted as a Unicode or Saturn mapping authority by itself.

## Conservative RevB authoring whitelist

A14 joined **6,388** accepted PLAIN records to the existing RevB record authority. The join had:

- missing record IDs: **0**;
- raw-hash mismatches: **0**;
- storage-decode errors: **0**.

An external reference rendering exactly agreed with the RevB Japanese reference for **3,623** of those records. Only token mappings actually observed inside those exact-agreement records were admitted into the private authoring whitelist.

Private whitelist summary:

- rows: **1,336**;
- preferred unique mappings: **1,330**;
- duplicate-Unicode token rows held: **6**;
- preferred CJK Unified Ideograph mappings: **1,105**.

The whitelist itself is intentionally not published because this repository excludes game-derived character tables and translation data. The counts are a scope record, not a complete Unicode claim.

## Engineering Batch01

A14 selected a deliberately narrow same-length engineering fixture that occurred in **51 distinct SCEDATA streams**. The private translation text and exact storage bytes are not published here.

Results:

- accepted engineering rows: **51**;
- distinct modified streams: **51**;
- A08 record encode/decode roundtrip: **51/51 PASS**;
- control/terminator preservation: **51/51 PASS**;
- fixed-allocation capacity: **52/52 PASS**;
- strict independent whole-stream redecode: **52/52 PASS**;
- deterministic A10 rerun: **52/52 PASS**;
- external DIC compressor -> strict decode: **52/52 PASS**;
- minimum remaining fixed-allocation slack: **10 bytes**.

No SCEDATA candidate, Track1, CUE, patch, or translated game image was published or persisted as an A14 deliverable.

## HOLD isolation

All A09 candidate records remained accounted for:

| Class | Count | A14 treatment |
| --- | ---: | --- |
| engineering Batch01 | 51 | accepted for dry-run only |
| untranslated PLAIN | 6,337 | future translation work |
| DYNAMIC_PRESERVE | 1,146 | outside Batch01 |
| unsupported-control records | 95 | fail-closed HOLD |
| **total** | **7,629** | fully accounted |

A HOLD is not an A14 failure and is not automatically promoted later.

## Validation

Private A14 validation reported:

- primary checks: **29 PASS / 0 FAIL**;
- independent checks: **117 PASS / 0 FAIL**;
- package SHA-256: `481dcd62798fec7b836d9587eed44ddad44c597cb18a1a0650141f274554c953`.

Final scoped status:

`A14_PRE_FORMAL_TRANSLATION_BATCH = PASS_FOR_ENGINEERING_BATCH01_SCOPE_WITH_RESERVATIONS`

The main reservation before a formal translated candidate is linguistic/content approval. A14 proves the constrained machinery, not a completed translation.

## What remains private

The private package contains record inventories, translation master rows, a native glyph/token whitelist, dry-run tables and toolchain snapshots. Those files can contain game-derived text or mapping data and are not copied to this public repository. Public evidence is limited to hashes, counts, generic algorithms, synthetic utilities and scope statements.
