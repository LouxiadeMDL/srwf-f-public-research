# SRW F — `dic-comp.c` / `dic-dec.c` codec source audit

Record date: 2026-09-20  
Source-review date: 2026-09-12  
Scope: **Super Robot Wars F only**. Public-safe metadata and source-audit conclusions; the tool source itself is not redistributed.

## Why this record exists

Two C sources were reviewed as an external codec reference:

- `dic-comp.c` — source comment identifies it as compression code for SRW F `DIC.BIN`.
- `dic-dec.c` — source comment identifies it as decompression code for SRW F `DIC.BIN`.

Asakim separately stated that, despite the `DIC.BIN` label, the same code can also process **Saturn scenario/story text**. That statement is recorded here as external researcher provenance, not as a substitute for local binary/runtime validation.

There is also public corroboration that Saturn `SCEDATA.BIN` contains compressed scenario text and that an SRW F text de/recompressor exists and works with the game. In the public SegaXtreme thread **“Translating Super Robot Wars F”**, `longsun_zhao` discussed Saturn `SCEDATA.BIN` compression and later credited `abridgewater` with a text de/recompressor that works with the game:

- https://segaxtreme.net/threads/translating-super-robot-wars-f.25557/

This record does **not** assert that the publicly mentioned `abridgewater` tool is byte-for-byte identical to the reviewed `dic-comp.c` / `dic-dec.c` sources.

## Source fingerprints

| File | Lines | Size | SHA-256 |
| --- | ---: | ---: | --- |
| `dic-comp.c` | 494 | 15,856 bytes | `8fed6eafc947f67a11f0c00346af956745ab811f34f5f3b5c6c16193c2cde8b7` |
| `dic-dec.c` | 392 | 12,976 bytes | `99458e895dfe15f331cdf6feddefd95b9c65acd27bf94c070095a50a9654c787` |

The files are fingerprinted for provenance only. They are not included in this public repository.

## Recovered codec grammar

The reviewed implementation uses an **MSB-first control-bit stream**.

```text
token :=
    1      + literal_byte
  | 00xx   + offset8
  | 01     + packed16_be [ + extended_length8 ]
```

### Literal

- control prefix: `1`
- payload: one literal byte

### Short back-reference

- control prefix: `00xx`
- length: `xx + 2`, therefore 2..5 bytes
- offset: 8-bit negative back-reference
- effective window: `0x100` bytes

### Long back-reference

- control prefix: `01`
- payload: big-endian packed 16-bit value
- packed form: 13-bit negative back-reference + 3-bit length field
- effective window: `0x2000` bytes

For low 3 bits `1..7`:

```text
length = low3 + 2
```

therefore ordinary long-match lengths are 3..9 bytes.

For low 3 bits `0`, one extended-length byte follows:

```text
extended != 0  -> length = extended + 1   # 2..256
extended == 0  -> end-of-data marker
```

The semantic EOD form is therefore:

```text
control: 01
packed16: 00 00
extended: 00
```

`dic-comp.c` uses a naïve greedy longest-match search. The maximum encoded match length is `0x100` bytes.

## Validation consequence

Because the compressor is greedy and need not reproduce the original encoder's exact choices, **compressed-byte identity is not the correct roundtrip requirement**.

The meaningful validation is:

```text
original compressed
    -> decode
decoded A
    -> encode
recompressed
    -> decode
decoded B

require: decoded A == decoded B
```

The recompressed byte stream may legitimately differ from the original compressed byte stream.

## Source-audit caveats

The reviewed legacy implementation should not be accepted unchanged as a strict project-canonical decoder:

1. A 256-byte extended match can encounter an 8-bit length-wrap hazard if the length is carried in `uint8_t`.
2. Truncated/EOF input handling can be permissive enough to resemble normal EOD.
3. Back-reference lower-bound validation is insufficient in the legacy decoder.
4. The compressor is greedy and may be non-optimal; byte-identical recompression is not expected.

A hardened implementation should fail closed on malformed input and preserve full-length arithmetic.

## Evidence boundary

This source audit establishes the codec grammar and the behavior of the reviewed compressor/decompressor implementation.

It does **not by itself** establish:

- every Saturn F resource uses this codec or identical framing;
- record boundaries inside `SCEDATA.BIN`;
- token/control semantics after decompression;
- glyph/Unicode identity;
- renderer behavior;
- byte-identical recompression.

Asakim's statement raises Saturn scenario-text applicability from an unattributed guess to an **external researcher claim**, and the SegaXtreme thread supplies independent public corroboration that Saturn scenario text is compressed and that a working SRW F text de/recompressor exists. Project-canonical use should still be tied to exact resource/version fingerprints and independent roundtrip/runtime evidence.

## Publication treatment

The tool source is not public in this repository. Only fingerprints, structural observations, evidence boundaries and public-source references are recorded.

Status label for this record:

`EXTERNAL_INDEPENDENT_CODEC_REFERENCE`
