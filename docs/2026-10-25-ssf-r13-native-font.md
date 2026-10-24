# SSF R13 | registered-scene native Han font and layout unification

Evidence date: **2026-10-24**. Target: **Saturn F**, separate from CN1940 F Final.  
Reported Track1 SHA-256: `e677506ad012373b71eed8693f40bd394462abdf1f4b3f5c73f916aafd425669`.

## Reported scoped engineering model / 全场景字形统一

A shared native-font layout is indexed across **52 physical / 74 logical scenes**, with **2,555** registered scenario cell placements, **6,962** registered text bodies, **155,503** glyph references and **10,898** explicit lines. Relevant Chinese glyph cells use the reported **12 px native Han** form with centered placement, retaining the protagonist's name input/display constraints rather than substituting Saturn/PS addresses. The prelude test set contains **45 lines / 778 characters**.

Eight default-name variants were evaluated under a reported maximum **240 px** width without default-name overflow. Conservative user-defined long-name bounds are not turned into observed bugs. MAIN was reported not to require new instructions or RAM allocation in the named area.

## Historical bounded observation

Saved local **Yabause 0.9.15 HLE** cold-start checks sampled seven natural-path categories, **233** natural frames and **376** labeled pixel samples. They provide bounded visual evidence, **not** exhaustive game-path acceptance.

**178 archived** and **42 opaque whole-line** semantic HOLD entries remain. The separate **36** long custom-name cases are conservative risk upper bounds, not confirmed runtime overflow. Full campaign, every battle/retreat/ending branch, SSF Preview R38, hardware, and artistic image/title translation remain outside this pass.

Source evidence fingerprints **S098/S099/S100**: [RECORD_DIGESTS](../evidence/specialized/2026-10-25/RECORD_DIGESTS.json). No font, translated corpus, screenshot, original resource or patch media is included.