# WP-C2 — ROOT0 179-RUN / 610-BYTE SEMANTIC CLOSURE

Project: `SRWF_F_WP_REVERSE`
Status: `PASS_WITH_POLICY_AND_RUNTIME_HOLDS`

## Physical identity
The paired root0 delta remains:
- 179 changed runs
- 610 changed bytes

Do not inflate the total by adding branch-local review rows.

## R046 — MAP_MAP single-stream dependency
The paired Japanese base has 95 objects with two streams per object.
WP has 239 objects with one stream per object.

WP changes the second decode source so the first stream is reused. Under the old second-source formula, WP objects resolve beyond their own object end. Selected base objects contain genuinely different first/second streams, so this is not a universal “harmless deduplication”.

Safe conclusion:
`MAP_MAP loader/decoder path was changed to support WP single-stream object layout.`

Do not restore only the reader while keeping the WP single-stream resource.

## R047 — TSR34 -> BBACK background lookup
The expanded table is now consumer-bound:
- three groups
- 120 rows -> 159 rows per group
- 4 bytes per row
- group stride 480 -> 636
- selected fields feed runtime work records and are later consumed as BBACK subobject indices

The first three groups also contain modified pre-existing rows; this is not merely “append 39 rows”.

Safe conclusion:
`TSR[34] lookup expansion participates in battle-background selection feeding BBACK.`

Runtime reachability/safety of all possible selectors remains a separate question.

## Historical ownership correction
28 runs that had carried ENDING-only / strong-restore metadata are not accepted as current ownership merely because of nearby historical labels.

Protected corrected ranges:
- R032
- R033
- R068..R079
- R128..R141

Current rule:
nearby file names, moved tables, or unchanged shared handlers are not enough to infer ownership or restoration policy.

## Policy
Every root0 run may be displayed with its current mechanism class.
`restore_to_base` is a historical clean-RevB strategy field, **not** an automatic editor action.

## OPEN / HOLD
- runtime safety for selected mechanisms
- portability to another build
- whether a business feature should be retained/removed
- production write recipe for mechanisms that span code + changed resource payload
