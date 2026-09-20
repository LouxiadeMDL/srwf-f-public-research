# SRW F — A14 cross-check of the external DIC codec against Saturn scenario streams

Record date: 2026-09-20  
Scope: **Super Robot Wars F only**. This is a follow-up to the [source-level DIC codec audit](2026-09-20-dic-codec-source-audit.md).

## Source identity

The reviewed external sources matched the previously recorded fingerprints exactly:

| Source | Size | SHA-256 |
| --- | ---: | --- |
| `dic-comp.c` | 15,856 bytes | `8fed6eafc947f67a11f0c00346af956745ab811f34f5f3b5c6c16193c2cde8b7` |
| `dic-dec.c` | 12,976 bytes | `99458e895dfe15f331cdf6feddefd95b9c65acd27bf94c070095a50a9654c787` |

The original source files are **not redistributed** here. Their redistribution/license status is not established by this repository, and the publication policy excludes unknown-license third-party code. This page publishes the technical results of reviewing and testing them.

## Source-level grammar retained

The source audit recovered an MSB-first LZ-style stream with:

- literal: control `1` + one byte;
- short back-reference: `00xx` + 8-bit offset, length 2..5;
- long back-reference: `01` + packed big-endian 16-bit distance/length;
- extended length when the low 3 length bits are zero;
- semantic maximum match length `0x100` (256 bytes);
- long window `0x2000` and short window `0x100`;
- end marker represented by long-form zero packed value plus zero extension;
- a greedy longest-match compressor.

Compressed-byte identity is not required for semantic roundtrip. The meaningful condition is equality of decoded bytes after recompression.

## Real Saturn F RevB cross-implementation result

A14 tested the external codec against **52 actual Saturn F RevB SCEDATA stream payloads** from the already-reviewed fixed-layout pipeline.

| Check | Result |
| --- | ---: |
| strict A10 decode of the 52 baseline streams | **52/52 exact** |
| external `dic-comp.c` output -> strict A10 decode | **52/52 exact** |
| A10 recompress -> strict redecode | **52/52 exact** |
| A10 deterministic recompression | **52/52 byte-identical to its frozen stream** |
| legacy `dic-dec.c` -> expected decoded stream | **51/52 exact** |
| legacy compressor + legacy decoder self-roundtrip | **51/52 exact** |

This provides direct cross-implementation evidence that the DIC codec grammar is compatible with the tested Saturn SCEDATA compression layer. It does **not** promote BMESS or every other SRW F resource to this codec.

## The 256-byte legacy decoder defect was reproduced on real data

Exactly one tested stream contained extended back-references with a decoded length of 256 bytes: **two such operations** were observed in that stream.

The legacy decompressor stores the calculated extended length in an 8-bit variable. For extension byte `255`, the mathematical length is `256`, but an 8-bit value wraps to zero. In the affected real stream the legacy decoder therefore omitted two 256-byte copies and produced output **512 bytes short**, while still returning success.

That behavior turns the previous source-audit warning into an observed compatibility limitation:

`dic-dec.c = reference decoder, not strict acceptance authority`

The strict project decoder uses full-width arithmetic and fail-closed bounds/EOF handling.

## Negative fixtures

Synthetic negative tests also preserved two source-audit reservations:

- truncated literal/long forms are rejected by the strict decoder while the legacy decoder can terminate successfully at end-of-input;
- a back-reference before the start of output is rejected by the strict decoder and was intentionally not executed through the unsafe legacy path.

A public, clean-room synthetic checker implementing only the documented grammar is provided as `tools/check_dic_codec_vectors.py`. It contains no game bytes and does not copy the third-party C source.

## Public conclusion

For the tested corpus:

`SATURN_SCEDATA_EXTERNAL_CODEC_COMPATIBILITY = PASS_FOR_TESTED_52_STREAM_SCOPE`

with:

`LEGACY_DIC_DECODER = REFERENCE_ONLY_WITH_EXT256_AND_FAIL_CLOSED_RESERVATIONS`

Not established by this result:

- BMESS codec identity;
- every Saturn/PlayStation resource framing;
- record ownership or pointer rules;
- post-decompression token semantics;
- Unicode/glyph identity;
- renderer behavior;
- byte-identical equivalence between independent compressors.
