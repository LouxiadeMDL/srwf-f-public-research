# WP-C3 — MENU / UI NUMBER-DOMAIN CLOSURE

Project: `SRWF_F_WP_REVERSE`
Status: `PASS_FOR_NUMBER_DOMAIN_SEPARATION_WITH_BUSINESS_LIFECYCLE_HOLDS`

## Core rule
The following are distinct typed domains and must not be collapsed into one `menu_id`:
- callback number
- template number
- descriptor number
- pane
- selection group/runtime group state
- row/page
- mapped action
- 9B action/subaction

## Corrected interpretation
For `51 04 01 xx`:
- operand `01` selects pane 1
- it is not “group1”
- group/selection state is separate

## Shortcut-row flow
The shortcut row setter does not directly invoke a 9B/02 action.

Observed structure:
`51/09 set row -> return to input/wait loop -> later action dispatch`

A second route reaches 9B/03 instead, proving that shortcut row, input handling and business action are separate steps.

## Engineering rule
UI/editor data models must use separate fields for each namespace. Never store callback/template/descriptor/pane/group/row/action in one generic integer without an explicit type.

## Remaining holds
- full top-level UI lifecycle
- some callback business names
- some action reachability and cancel/re-entry behavior
- renderer-visible labels for selected template routes
