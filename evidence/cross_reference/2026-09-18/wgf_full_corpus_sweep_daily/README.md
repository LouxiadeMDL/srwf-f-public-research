# WGF Full-Corpus Unicode Sweep — 2026-09-18

Scope: **Super Robot Wars F only**.

This checkpoint records metadata-only results from a local, read-only analysis of the WGF/JP PS F text corpus. No ROM/BIN bytes, glyph rasters, full dialogue corpus, or reconstructive payload are included here.

## Corpus baseline

- Full text/candidate records: 104,694
- Token occurrences: 1,871,832
- Observed glyph slots: 2656/2816
- Frozen canonical glyph table: unchanged

## Daily reconciliation

- Batch02 checkpoint promotions: 4
- Full-corpus sweep promotions: 358
- Full-corpus tiers: 354 A_STRONG / 4 B_SUPPORTED
- Combined daily additive review rows: 362
- Effective mapped slots after local review merge: 1108/2816
- Remaining unresolved slots: 1708
- Validator: 15 PASS / 0 FAIL

`A_STRONG` requires multiple distinct WGF text contexts in this checkpoint. `B_SUPPORTED` is kept separate for strong single-context cases. Japanese reference values are corroborative only and are not inherited automatically.

## Key corrections

- 0x806: raster-only 棱 -> 梭 (`逃亡的梭罗号` context)
- 0x898: 螟 -> 螺
- 0x885: 芙 -> 荚
- 0x253: temporary 进 inference rejected; keep 增
- 0x7DF: stale 压 hypothesis rejected; keep 搁
- 0x878: stale 迷 hypothesis rejected; keep 腾
- 0x16E: temporary inference corrected to 用
- 0x1FE / 0x27E: corrected to 根 / 本

## Contextual normalization

Primary 0x336 remains `难`. One raw WGF context reads `亲难指挥`; semantic alignment supports normalized `亲自指挥`. This is stored only as a contextual normalization candidate and does not alter the primary glyph mapping.

## Saturn-side status

The current local Saturn F RevB SCEDATA decompression checkpoint independently recovers 52 explicitly terminated streams and validates 52/52 against exact PS F JP windows. This confirms the decompression read path only; recompression and Saturn font location remain unconfirmed.

## Publication boundary

This public checkpoint contains only sanitized metadata and conclusions. Full text, game assets, raw binaries, glyph payloads, and reconstruction-capable datasets remain offline/private.
