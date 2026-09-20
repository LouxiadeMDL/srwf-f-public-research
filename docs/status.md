# Evidence status

Publication review: 2026-09-12. **Report review, not a new binary or runtime validation.** Numerical observations below are historical report claims with source digests in provenance.md. They are deliberately not labelled newly confirmed facts.

## Dated Saturn observations

The 2026-09-07 Step3A/3B execution report records 75,086 reader-verified rows across RevA, RevB, wp and PS. These labels are dataset-specific; PS is a comparison dataset, not Saturn. Its overall result is PASS_WITH_RESERVATIONS.

The report records 875 distinct token types for each stock Saturn variant and 1,426 for wp. Its wp font layout is 2,775 glyphs at 28 bytes each, 14 rows of 16 bits, in the decompressed interval [0x47705, 0x5A689). The stock reported regions are [0x41742, 0x57742) for RevA and [0x49B73, 0x5FB73) for RevB, each 2,816 glyphs at 32 bytes. These are version-bound observations, not universal offsets.

A later inspected Step3B closure report preserves the reservation: address/range/bitmap checks are not proof of the full runtime reader/renderer. The candidate code-to-glyph expression maps EBFA through EBFF to indices 485 through 490 for the observed wp corpus. No glyph bitmap, raw glyph bytes or reconstructed character table is published here.

EBFF remains a useful discriminating test: historical external readers disagree about invalid-bank fallback. Their behavior does not determine the game's behavior. The 5,989 distinct-string correlation reported for RevB likewise does not prove another project's line-identity algorithm.

The historical Korean RevB comparison report describes 384 logical BMESS slots and 383 physical blocks with shared slots 0/1. It reports that changed block sizes preserved the tested live structure while the older residual classifier left bytes unclassified. Live traversal and orphan/residual classification must therefore be evaluated separately. This release did not reproduce that comparison or redistribute its inputs.

## Separate PlayStation work

The inspected T1 R6 status reports conditional general-register analysis, zero source-generation closures, 18 unknown query cells and full acceptance 0/32. Its validation label is PASS_WITH_RESERVATIONS, advance_allowed is false and unicode_confirmed is zero. This is a snapshot of one PS static-analysis task, not a Saturn status or a claim that all later work stopped.

## Current public conclusions

1. The inspected records contain partial offline and static evidence, with explicit reservations.
2. This release contains no direct runtime proof connecting the entire Saturn pipeline.
3. Resource/version identity, token/glyph addressing, Unicode identification and rendering are different claims.
4. Older project-wide status summaries are not used as current authority: later local control files record different stage states. Publication does not reconcile or advance those stages.

Future updates must add dated evidence rather than silently replacing historical conclusions.

## Later review decision

The inspected R6 review decision (S6) accepts 20 conditional function/variant relations and four call-context relations with reservations, retains 18 unknown game queries and records a user pause. The frozen 0/32 is a capability-acceptance measure, **not a project progress percentage**. Research remains paused under that decision; publishing this repository does not resume it.


## 2026-09-21 A16 production-scale seal

A later reviewed A16 evidence package advances the public-safe process record beyond the earlier historical snapshot above without rewriting it.

For **Saturn F RevB / F only**, A16 records a production-scale Episode 1 engineering validation built around a Saturn-to-PS Japanese record bridge, record-specific WGF translation references, pre-translation domain/episode classification, deterministic cumulative SCEDATA rebuilding, and exact-hash runtime checks in both Mednafen and SSF.

The sealed tested candidate is identified by:

- Track1 SHA-256: `daa62054b6e2a567e03e047d883d81e7f421f7ee3f813bb68efba641c1a0693c`
- embedded SCEDATA SHA-256: `77e7a257dd01c62e8bfc370ef2f9bbc32af8481cbdece59d06d093e3735ed590`
- CUE SHA-256: `9b940aa2afea650e86f786623cb4ab3982741cd5cdb59564112cc5ec5d32a870`

Both emulator runs reached Episode 1 clear and Intermission with normal exit, matched process identity and unchanged candidate identity. The seal remains explicitly limited to the tested engineering scope; it is not a claim of release-quality Chinese, complete font coverage, whole-game runtime coverage or hardware-Saturn validation.

A16 also records a visible fixed-length authoring artifact, a conservative native-mapping evidence audit, and an Episode 1 production-coverage analysis. The final production decision is **hybrid native reuse plus selective font extension**, with font-bank ownership/capacity left for the next read-only gate.

See `docs/2026-09-21-a16-complete-retrospective-and-seal.md` and `evidence/cross_reference/2026-09-21-a16-final-seal.json`.
