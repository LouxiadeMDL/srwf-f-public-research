# SS35 F Final Guide QA44 Cross-check — 2026-10-08

Scope: **Sega Saturn `Super Robot Wars F Final` / SS35 guide reference only**.

This checkpoint records the public-safe result of resolving the 44 blocking QA records in the private SS35 guide corpus. It does **not** publish the scanned guide, page images, full OCR/text corpus, SQLite database, or reconstructive copyrighted payload.

## Result

- Source family: 3 SS35 PDF parts / 812 scan pages
- Original blocking QA records: 44
- Information-layer resolutions: 44/44
- Blocking QA remaining: 0
- Public-source conflicts retained: 1
- Canonical scope in the private project: `PRIMARY_FF_REFERENCE`

`RESOLVED` here means the page's information role, normalized title/entities and relevant game facts were cross-checked. It does **not** mean every glyph or dense table cell was manually retyped. For exact printed wording and SS-specific numeric cells, the source scan remains authoritative.

## Cross-check policy

1. The SS35 scan controls the guide's printed wording, layout, diagrams and table cells.
2. Japanese Saturn F Final databases are used to normalize scenario numbering/titles and to cross-check event/hidden-condition claims.
3. Traditional-Chinese F Final databases are used for names, stage indexes and context. Mixed SS/PS numeric data is never allowed to overwrite an SS scan blindly.
4. Secondary/community sources are corroborative only.
5. Conflicting public conditions are preserved as conflicts instead of being flattened into one guessed value.

## Public files

- `source_fingerprints.csv` — hashes, sizes and page counts for the three source PDFs; no PDF bytes.
- `qa44_resolution_summary.csv` — one metadata-only row per resolved QA page.
- `conflicts.csv` — unresolved public-source condition disagreements.
- `web_sources.md` — cross-check source registry and publication notes.

## Known conflict

`FF_PART2A:p0163` / フォウ・ムラサメ rescue boundary:

- Tuzigiri hidden-pilot database: defeat Bask within 7 turns.
- SRW Wiki compilation: defeat Bask by the end of 8PP.

The private corpus records the disagreement and does not overwrite the scan/ROM condition. This remains a ROM/script validation item.

## Publication boundary

The complete private package contains page/line text, source images, SQLite/FTS and page-level corrections. Those are intentionally excluded from this public repository. This checkpoint publishes only fingerprints, metadata, normalized identifiers, source relationships and non-reconstructive conclusions.
