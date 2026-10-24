# SSFF CN1940 R5 R15 RC1 | five scoped fixes / 五项修复

Evidence: 2026-10-22; independent failure capture: 2026-10-23.  
Target: **Saturn F Final**, CN1940 R5 family, parent R14 UI_TEXT_HANGARFIX.  
Reported Track1 SHA-256: `a863fae9ac32e929f6a79c330ea35dd34423aafe58cbdc857e353c5667be4dc8`.

## Bounded five-fix acceptance

1. **主人公设定** — Seven native menu labels and cursor locations realigned; incorrect “编/键” glyph selection corrected; three-line guidance. No new menu option inferred.
2. **保存/读取界面** — Reproduced eight-pixel drift accumulating per subsequent row and corrected two line-end positions. Ordinary 04/07 card paths were cold-loaded. User saves were not overwritten.
3. **反击光标** — R animation-toggle preview redraw lost action-window text context, leaving green highlight displaced. The context is preserved across redraw; attack, weapon, evade, defend and B/menu-return routes were checked after three toggles.
4. **Ex-S 反射 INCOM** — The dedicated three-image body used the ν Gundam silhouette. The existing Ex-S body outline and palette were selected for that slot; ν Gundam's own battle sequence remained unchanged. The recorded cold battle and map return passed; the observed damage 5352 and recorded combat data remained baseline-equivalent.
5. **等级/技能说明** — A parameter-length vs Chinese text-length mismatch caused following window controls to be read as glyphs. Scoped fixes covered level gain, Newtype, shield defense, a new spirit command and a new skill path using controlled save copies.

## Failures preserved, not miscredited

**R15-03** B-viewer frame/HP-EN; **R15-05** sortie/system/turn menu borders; **R15-07** ability-page frame/field overlap all remained unresolved in this R15 candidate. [R16 RC2](2026-10-25-ssff-r16-rc2-windows.md) is the later, version-specific repair.

The Oct 23 **unchanged Ymir 0.4.1 core** with a Linux checkpoint frontend reproduced B/system/ability failures. A master SH-2 DMA-fed VDP2 pattern-state change was recorded; restoring the affected CYCB registers and shadow words in a copied failed checkpoint recovered borders and HP/EN after 90 emulated frames. This was a **controlled causal experiment**, *not* repaired R15 media or cold-boot repair acceptance. The ship-list fault had not yet been reproduced in that diagnostic.

## Runtime boundary

The R15 five-fix acceptance ran under **Yabause/libretro 0.9.15 HLE**. SSF Preview R38 did not enter the game under the local Wine configuration and must not be credited. No full-campaign, all-animations or physical-Saturn claim follows from this milestone.

Sources: private report fingerprints **S107/S108/S109** in [the digest ledger](../evidence/specialized/2026-10-25/RECORD_DIGESTS.json). No game-derived graphics, binary code, save or video is redistributed.