# 2026-10-25 | 机战 F / F 完结篇专项研究公开索引

Publication date: 2026-10-25 (Sydney). Source evidence dates: 2026-10-14–24. This is a **public-safe technical supplement**, not a game/translation/patch release.

本索引汇集 10 月 8 日之后完成的限定范围研究。每个 PASS 只对应该版本明确验证的路径；本次公开没有重新执行游戏、镜像构建或模拟器测试。

| Branch | Date | Research | Report |
| --- | --- | --- | --- |
| SSF RevB R13 | Oct 24 | Native Han font/layout across registered scenes | [SSF R13](2026-10-25-ssf-r13-native-font.md) |
| SSF G3 R4→R5 | Oct 18–19 | Four-form S/Ex-S integration; map icon alpha fix | [SSF G3](2026-10-25-ssf-g3-s-exs-r4-r5.md) |
| SSFF S/Ex-S V1 | Oct 18 | Four-form parameters, defense labels, transformation | [SSFF S/Ex-S](2026-10-25-ssff-s-exs-v1.md) |
| SSFF CN02 R2 BD01 | Oct 14 | R animation toggle, Start skip, effective damage/HP | [BD01](2026-10-25-ssff-animation-hp-bd01.md) |
| SSFF BD01/P6B V3 | Oct 15 | Restore native result-window colors | [V3](2026-10-25-ssff-hp-v3-active-palette.md) |
| SSFF CN1940 R5 R15 RC1 | Oct 22–23 | Five UI/combat fixes; separate VDP failure diagnosis | [R15](2026-10-25-ssff-r15-rc1-five-fixes.md) |
| SSFF CN1940 R5 R16 RC2 | Oct 24 | Map/B/ability/sortie windows and deployment layout | [R16](2026-10-25-ssff-r16-rc2-windows.md) |

## Boundaries / 版本与证据规则

- Saturn **F** and **F Final** are different game/program families; their addresses, units and runtime test results are not interchangeable.
- **R15** solved five issues but did not yet solve the three frameless-window categories. **R16 RC2** is the later scoped window/deployment successor, superseding the R16 RC1 layout candidate.
- **SSF G3 R4 combat** evidence is historical to R4; R5's new acceptance only covers the map outline and ordinary-card compatibility.
- **BD01**, historical **D8**, and **V3** represent different combat/HP test generations; V3 has not independently rerun every older randomized/MAP case.
- Listed Track1 SHA-256 values identify reported release candidates; they are not download links or fresh binary readbacks.

The saved source-report SHA-256 references are in [RECORD_DIGESTS.json](../evidence/specialized/2026-10-25/RECORD_DIGESTS.json). Only rewritten descriptions, narrow facts and fingerprints are published. No ROM/ISO/BIN, disc tracks, translated dialogue, font, unit graphics, emulator BIOS, user saves, video/screenshots, compiled patch or unreviewed third-party source is included.

The underlying work was reviewed from the 2026-10-24 read-only research ledger, not replayed at publication. Older background and separate PS/SFC comparisons remain in the [cross-game handoff](2026-09-22-cross-game-research-handoff.md).