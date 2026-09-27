# WP-C4 — NAME EDITOR / INPUT / SERIALIZATION CLOSURE

Project: `SRWF_F_WP_REVERSE`
Status: `PASS_WITH_CANCEL_SAVELOAD_AND_SECOND_EDITOR_REACHABILITY_HOLDS`

## Serialized field contract
Validated for the main editor path:
- two payloads
- each payload max: 6 encoded bytes
- one delimiter byte
- one terminal FF byte
- total maximum serialized field: 14 bytes

Therefore:
`6 bytes != 6 Unicode characters`

All editing tools must enforce the budget after encoding.

## Delimiter
Paired change:
- base delimiter: `E3`
- target delimiter: `40`

Reader/writer behavior must be treated as a paired format change. Changing only one side is unsafe.

## Main special-key mapping
Native dispatch establishes:
- base special keys: 122..126
- target main 9B/02 special keys: 117..121

The earlier 120..124 -> 115..119 interpretation is superseded.

## Validation
A bounded validation matrix of 144 cases was executed in the historical late checkpoint.
Observed return classes include:
- empty/duplicate -> 1
- legal new value -> 2

The main field can be written before validation completes, so a clean offline editor should validate first and commit second rather than copying the runtime prewrite behavior blindly.

## Second-editor conflict
A distinct 9B/03 consumer still subtracts 122 and therefore expects special keys 122..126.
The target shared descriptor used by the associated route has valid indices only through 121.

A target script route binds callback44, descriptor11 and the input loop to 9B/03. Shortcut row 121 reaches an ordinary-character path rather than the historical special-key confirm path.

This is a real `OPEN_REACHABILITY` / contract conflict, not a typo to normalize away.

## OPEN
- cancel/re-entry behavior
- actual save/load persistence
- cold boot / old-save migration
- end-to-end reachability and intended visible behavior of the second editor
