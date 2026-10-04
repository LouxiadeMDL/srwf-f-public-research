# SSF F RevB story/dialogue translation checkpoint — 2026-10-04

Status: `TRANSLATION_DRAFT / SOURCE_ISSUES_OPEN / ORDER_RUNTIME_UNVERIFIED`

Scope: Super Robot Wars F only, Saturn RevB 21M target.

This public checkpoint summarizes the current per-scenario story/dialogue translation work. It intentionally excludes ROM/BIN files and excludes the full dialogue XLSX/SQLite/ZIP from the public repository.

## Current scope

- Source records: 7,629
- Included translation/reference records: 7,182
- Excluded structural/non-target records: 447
- Normal story/route nodes: 50
- Normal story records: 6,978
- Ending-preview records: 29
- Unassigned/test residual records: 123
- Birthday-candidate residual records: 52
- Existing protagonist shared battle-text reference: 396 unique lines
- Hidden-reference items: 35
- Semantic candidate links to hidden conditions: 467 record links

Translation provenance:
- 5,811 records translated in the current pass
- 1,321 records reused from identical source text
- 50 records inherited from the reviewed A17 R7P protagonist translation set

## Organization

The material is grouped by scenario semantics plus route branches, including Real/Super protagonist routes, Golawn/Gran Garan branches, and direct/detour route nodes. Storage order is kept as a stable index, but not all records are yet bound to exact runtime event order.

Mutually exclusive protagonist personality/sex branches, hidden-condition success/failure branches, and route-exclusive records are preserved separately rather than concatenated as if they occur in one playthrough.

## Verification state

Automated checks currently pass for:
- complete/disjoint source partition
- non-empty Chinese translation field
- original Japanese text unchanged
- raw-length consistency
- F9 dynamic parameter occurrence preservation
- XLSX translation readback
- zero formula-error cells
- SQLite integrity = ok

Runtime status remains `NOT_TESTED_THIS_TURN`.

The project does **not** claim complete all-resource/all-route runtime coverage yet.

## Remaining gaps

1. Full NPC BMESS / M_DEAD and other dialogue resources outside the current SCEDATA archive.
2. Baked-in movie/cutscene text and other story-description resources.
3. Exact event execution order and trigger conditions for every route/hidden branch.
4. 10 records with unresolved source glyph/code markers and 41 additional context/name/typo review items.
5. Continued PS F / SSF RevA / SSF RevB text-difference reconciliation.
6. Final game-insertion QA for glyphs, line width, F6/F7 pagination, buffers and relocation.

## Evidence policy

External guides are used as scenario/navigation/semantic references only. Target-version ROM/archive records determine source text; script/control-flow determines reachability and conditions; runtime evidence is the final display check.

Full dialogue text, XLSX, SQLite and full ZIP are intentionally not included in this public folder.

## Integrated master addendum

The 2026-10-04 checkpoint has now been cross-integrated with:
- the 543-page / 1,002-line protagonist event-video reference,
- the 35-item hidden-elements guide and RouteLocal policy layer,
- the external PS F / SSF RevA / SSF RevB dialogue-reference layer.

See:
- `MASTER_INTEGRATION_2026-10-04.md`
- `master_validation_summary.json`
- `master_artifact_hashes.txt`

The full integrated XLSX/SQLite/release ZIP remain private/non-public artifacts. Public files contain sanitized research metadata only.
