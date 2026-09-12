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
