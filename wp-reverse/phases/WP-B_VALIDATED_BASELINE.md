# WP-B — VALIDATED LEGACY BASELINE

Project: `SRWF_F_WP_REVERSE`  
Status: `COMPLETE_WITH_RESERVATIONS`  
Role: validated import layer for historical WP/YZZL F reverse-engineering results.

This phase replaces the old conversation/task numbering as the current project vocabulary. Old IDs are retained only in `legacy_id` fields for provenance.

## Closed or strongly bounded results

### VM level query safety
`C0/10` success returns the pilot runtime level byte. Lookup failure sets the condition failure bit but preserves the previous accumulator value. A following comparison therefore cannot be interpreted as a complete “pilot exists and is above level N” contract unless lookup success/presence is separately proven.

### Fatima / BE chain
The scene45 collector has four local `C0/10` level queries in its bound route; no Amuro-15 query is present in that route. `F2 = Amuro15` is rejected. The pending flag `BE` is produced by more than one scene; in the scene45 path it participates in a later Fatima inventory increment. `C1/0E 02AA` is a common join action, not the Fatima reward.

### CA/02 deployment record
The native record stride is 12 bytes. The validated structure includes X/Y, packed pilot selector+level, packed unit selector+weapon-upgrade nibble, drop/reward selector, signed same-SCEDATA secondary pointer, five body-upgrade nibbles, and one additional runtime-unit field nibble. Placement routing is native-bound but its AI/side/faction business names remain reserved.

The scene71 Sety1 selector is derived from the full packed word, not from byte3 alone.

### AB13 private state
AB13 physically overlaps pilot runtime slot127 byte2/mask0x10. Direct D0 set producers are gated by flag017B in scene1/51. Scene26 uses AB13 to select deployment tables that preserve entities/positions while increasing upgrade modifiers, supporting a high-confidence `difficulty/enemy-upgrade state` business label. WP ordinary pilot-clear and fieldwise reconstruction skip slot127; raw snapshot/restore includes the slot. Full save/load backend ordering and cold-boot initial value remain open.

## Import rule

WP-B facts may seed WP-C only within their documented scope. Cross-platform code, MDB/BNE2, guides, dialogue references and FF data remain lower-authority evidence classes.
