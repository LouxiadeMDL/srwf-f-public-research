# SSF F RevB integrated story/reference master — 2026-10-04

Status: `INTEGRATED_REFERENCE_MASTER / TRANSLATION_DRAFT / RUNTIME_UNVERIFIED`

Scope: Super Robot Wars F only; Saturn RevB 21M is the primary story target.

## Integrated checkpoint

- RevB archived story records: **7,182**
- Japanese reading fields present: **7,182 / 7,182**
- Chinese draft fields present: **7,182 / 7,182**
- Normal route/story nodes: **50**
- Excluded structural/non-target records: **447**
- Source-review rows: **51**
- Existing protagonist shared battle-text rows: **396**
- Protagonist video pages: **543**
- Protagonist visible video-text lines: **1,002**
- Protagonist video REVIEW pages: **133**
- Hidden/reference IDs: **35**
- Dynamic protagonist/partner story records: **1,126**

## Video ↔ story reference reconciliation

Candidate alignment counts:
- exact unique: 278
- exact context-resolved: 41
- fuzzy high: 140
- fuzzy medium: 40
- exact but record-ambiguous: 161
- HOLD: 313
- unmapped: 29

High-confidence candidate lines: **459**, touching **282** unique story records.

Two existing source-review rows now have direct visual-text corroboration from the protagonist videos:
- `SSF_P04_R0060`
- `SSF_P22_R0146`

The videos' exact platform/revision is not independently established. These remain visual/reference corroboration and are **not** Saturn RevB runtime promotion.

## Hidden / RouteLocal reconciliation

The same 35 IDs are present in the hidden-elements guide, the story archive hidden index, and the RouteLocal policy draft. This confirms bookkeeping consistency only. Native predicates, addresses and runtime triggers remain separate gates.

## Identity / integrity

The original story XLSX and story SQLite hashes match the previously published artifact hashes. The prior RELEASE ZIP was re-downloaded and passed SHA/ZIP CRC re-check. The integrated Master SQLite passes `PRAGMA integrity_check = ok`.

## Open scope

This checkpoint does not claim full-game all-resource closure. Still open:
- full NPC BMESS / M_DEAD,
- movie/cutscene baked subtitles/text,
- exact execution order and trigger binding for every branch,
- 51 controlled source-review rows,
- 133 video-page visual REVIEW rows,
- PS F / SSF RevA / SSF RevB text reconciliation,
- final in-game pagination/buffer/relocation/all-route runtime QA.

No ROM/BIN/canonical mapping was modified.

Full story text, XLSX, SQLite and release ZIP remain outside the public GitHub research folder.
