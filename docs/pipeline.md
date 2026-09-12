# Technical route and open questions

The following is a proposed investigation order. None of the arrows alone claims a verified runtime relationship.

| Step | Question | Evidence needed |
| --- | --- | --- |
| Identity | Which platform, revision and modification is tested? | SHA-256, size and precisely defined resource/track representation |
| Loading | Which file/resource and range is requested? | Call arguments and source-to-buffer provenance |
| Decoding | Is this resource compressed; what are the boundaries? | Decoder input/output sizes, termination and independent validation |
| Reading | How does control flow reach a text span? | Reachable references, cursor updates and token consumption |
| Mapping | How does each token select a glyph? | Version-specific table/formula and boundary tests |
| Rendering | Which buffer and drawing routine consume it? | Traceable glyph data and drawing parameters through to screen |

Keep BMESS battle messages separate from SCEDATA scenario scripts and TSR/font assets. Keep Saturn and PlayStation implementations separate. A PS MIPS address or delay-slot analysis cannot identify Saturn code.

Priorities for discussion:

- Where is the Saturn SCEDATA decompression boundary, and what establishes the output buffer's consumer?
- Does the game consume EBFF as a two-byte token for the relevant modified Saturn build?
- Can font selection or dynamic remapping change the apparent code-to-glyph relationship?
- How are speaker/name prefixes distinguished from ordinary message text?
- Which renderer entry point consumes the resolved glyph, and with what stride and dimensions?

For any future runtime work, first agree the exact scope, test image and method. This publication task performed no runtime experiments and produced no patch.

The existing project route uses WGF text mechanisms as a bridge to PS F, then Saturn F and YZZL. This is an investigation strategy, not demonstrated semantic equivalence. Public Saturn questions remain the destination while each bridge requires its own evidence.
