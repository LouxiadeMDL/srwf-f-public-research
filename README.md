# SRW F — Saturn text pipeline research

A small, curated research companion for understanding how **Super Robot Wars F on Sega Saturn** turns script data into characters on screen. This is an early research project, shared for technical discussion and collaboration. It is not a translation release or a complete decoder.

## The question

How does the game locate a message, read its bytes, decompress where needed, interpret tokens, select glyphs, and render them? Battle messages and scenario scripts must be traced separately. A working offline parser does not establish what the game executes.

```text
Disc resource -> loader -> resource-specific decoding -> text reader
             -> token interpretation -> glyph lookup -> drawing -> screen
```

This is a research roadmap, not a verified execution graph. In particular, TSR/font decompression does not establish SCEDATA scenario-text decompression.

## Progress and limits

A [2026-09-13 update](docs/2026-09-13-baseline-and-patch-experiment.md) records fresh baseline checks and a failed direct-patch experiment; F2/F3 clean-image inputs remain incomplete.

A [2026-09-20 A14 update](docs/2026-09-20-a14-pre-formal-translation-batch.md) records a constrained pre-formal translation dry-run, while a separate [DIC/Saturn cross-check](docs/2026-09-20-dic-codec-a14-crosscheck.md) reports 52/52 strict roundtrips for the external compressor against tested Saturn scenario streams and documents a reproduced 256-byte legacy-decoder defect. The public repository keeps only safe summaries, hashes and synthetic tooling; game-derived text/mapping payloads remain private.

The publication was assembled on 2026-09-12 from dated research reports. Later dated updates add scoped evidence without silently rewriting the earlier reports. See [evidence and status](docs/status.md) and [source provenance](docs/provenance.md).

| Area | What the inspected reports support | What remains open |
| --- | --- | --- |
| Saturn BMESS | Historical offline structure and reader-range validation across identified variants | Complete runtime reader/control semantics |
| Saturn TSR/font | Historical decompression, layout and glyph-range checks | Runtime font selection and full renderer connection |
| wp/YZZL code-to-glyph | Candidate addressing matches the observed token set in historical checks | Unicode identity, dynamic remapping, boundary behavior |
| Saturn SCEDATA | Later private engineering work adds scoped codec/rebuild/runtime evidence; public-safe A14 summaries are linked above | Full translated-content acceptance and any scope-expanding changes |
| PlayStation comparison | Separate static-analysis work remains partial | No automatic transfer of PS/MIPS findings to Saturn |

The complete Saturn script-to-screen path is **not established by the original public package alone**. No completed Unicode mapping, translation release or patch is published here. Mechanical validation and semantic proof remain separate.

## Start here

- [Research status and dated observations](docs/status.md)
- [A14 pre-formal translation batch update](docs/2026-09-20-a14-pre-formal-translation-batch.md)
- [DIC codec A14 cross-check](docs/2026-09-20-dic-codec-a14-crosscheck.md)
- [DIC codec source audit and Saturn scenario-text provenance](docs/2026-09-20-dic-codec-source-audit.md)
- [Pipeline questions and technical route](docs/pipeline.md)
- [Reproduction guide](docs/reproduce.md)
- [Evidence provenance and hashes](docs/provenance.md)
- [Publication scope](docs/publication-policy.md)

```text
docs/       rewritten research notes and reproduction instructions
tools/      original, dependency-free metadata and arithmetic checks
examples/   synthetic evidence-record template
```

Run the synthetic checks with Python 3.10 or later:

```sh
python tools/check_layout.py --self-test
python tools/check_dic_codec_vectors.py --self-test
python tools/check_publication.py
```

These checks need no game data. They test the supplied utilities, not the game's runtime. Third-party/legacy source code is excluded unless redistribution rights are clear; public results use rewritten descriptions, fingerprints and original synthetic utilities.

## Collaboration

Feedback from Asakim and other researchers is welcome, particularly on Saturn resource loading, scenario decompression, boundary token behavior, font selection and the renderer call path. A small, independently checkable observation is more useful than an unqualified completion claim. Please include platform/version, input digest, observation method and limitations. Do not attach game data or private correspondence. See [CONTRIBUTING](CONTRIBUTING.md).

## 中文说明

这个公开副本用于交流《超级机器人大战 F》Saturn 版“脚本数据到屏幕字符”的完整路径。公开版只保留重新整理的说明、哈希、限定范围的验证摘要和不含游戏数据的通用/合成测试工具；不包含游戏、字库位图、对话转储、完整字符映射、第三方未知许可源码或私人工作记录。

Original materials in this repository use the [MIT License](LICENSE). No rights to game assets or third-party materials are granted. This is an independent, unofficial project; product names identify the subject of research and do not imply endorsement.
