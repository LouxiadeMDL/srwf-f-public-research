# WGF Full-Corpus Unicode Sweep — 2026-09-18

Scope: **Super Robot Wars F only**.

> **Scoped status correction, 2026-09-18:** The original daily snapshot is retained in Git history. Later read-only verification established the **native Saturn F RevB TSR font-bank layout**, so the original blanket statement that the font location was unconfirmed is superseded for layout only. Token consumers, dynamic remapping, the full renderer/runtime binding, recompression and reinsertion remain separate, unclosed obligations. Also, **1108 effective mapped slots include mixed evidence classes and candidates/HOLD; this is not a strict-confirmed Unicode count**. This public page is a sanitized reference, not the private project's operational controller or full evidence backup.

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
- Effective mapped slots after local review merge: 1108/2816, with mixed evidence classes retained
- Remaining slots without a current value: 1708; not 1708 unidentified common Chinese characters
- Original daily validator: 15 PASS / 0 FAIL, within that checkpoint's validation scope

`A_STRONG` requires multiple distinct WGF text contexts in this checkpoint. `B_SUPPORTED` is kept separate for strong single-context cases. Japanese reference values are corroborative only and are not inherited automatically. These labels do not automatically become a different strict Unicode-confirmation model.

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

The local Saturn F RevB SCEDATA decompression checkpoint recovers 52 explicitly terminated streams and records 52/52 unique exact PS F JP-window matches. This is decompression/read-path evidence, not full stable-ID or writeback closure.

Later source-bound verification reproduced the native RevB TSR bank layout: decoded interval `[0x49B73,0x5FB73)`, 90,112 bytes, 2816 cells of 32 bytes, 16x16. This does not establish slot identity across platforms or complete consumer/renderer/runtime behavior. Recompression and reinsertion remain unclosed.

A later local test of the separately pinned TSR CLI recorded **14 PASS / 1 FAIL**: the native source/layout positive path passed, but the literal branch did not enforce its configured output-size limit. This is not a GitHub Actions pass, and the positive result must not be presented as full tool validation.

## Publication boundary

This public checkpoint contains only sanitized metadata and conclusions. Full text, game assets, raw binaries, glyph payloads, and reconstruction-capable datasets remain offline/private. Historical evidence is retained; updates supersede only specifically identified status claims.
