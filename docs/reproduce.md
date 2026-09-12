# Reproduction

## Checks shipped here

Requirements: Python 3.10+, standard library only. No network access is used by these utilities.

```sh
python tools/check_layout.py --self-test
python tools/check_layout.py --start 0x47705 --end 0x5A689 --count 2775 --stride 28
python tools/fingerprint.py /path/to/your/local/input --label saturn-f-resource
python tools/check_publication.py
```

The layout command checks only that end-start equals count*stride. It neither opens game data nor verifies a font. The fingerprint command reads one user-selected local file in chunks and prints only a user-supplied label, size and SHA-256, never its path or bytes. Review labels before sharing. It writes no files and makes no uploads.

## Historical experiments

The historical parsers, decoder implementation, reader-range export and image corpus are **not distributed**. Consequently the historical token counts and glyph checks cannot be reproduced from this checkout alone. This is an explicit limitation, not a missing download link.

A future full reproduction should independently obtain authorized local inputs, record platform and representation, verify their identities, review a publishable parser, establish structural text ranges, and compare outputs without publishing text or glyph payloads. Separate reachable structure from residual/orphan classification. Compare resource-specific outputs rather than conflating whole-disc and extracted-file hashes.

The identity records in provenance.md were transcribed from inspected reports. Their source data was not rehashed during this publication task. An input mismatch must stop a reproduction, not select a convenient substitute.

Use examples/evidence-record.json as a synthetic template. Keep local paths, traces, game bytes, Unicode tables derived from fonts and screenshots out of public attachments.
