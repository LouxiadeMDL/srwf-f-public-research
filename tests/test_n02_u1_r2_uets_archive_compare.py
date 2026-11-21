#!/usr/bin/env python3
"""Synthetic four-field R2 / UETS archive comparison tests (no private strings)."""
import copy
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from n02_u1_r2_uets_archive_compare import compare_rows, EXPECTED_ROWS

def fixtures():
    r2,uets=[],[]
    for i in range(EXPECTED_ROWS):
        sid=f"SSF_SYN_{i:06d}" if i%2==0 else f"SSFF_SYN_{i:06d}"
        entity=f"ENTITY:{i%1392:04d}"
        kind=("PERSON","UNIT","WEAPON")[i%3]
        cn=f"合成译名{i%1392}"
        r2.append({"原始来源ID":sid,"实体ID":entity,
                   "类别":kind,"简体中文定名":cn})
        uets.append({"source_id":sid,"entity_id":entity,
                     "name_kind":kind,"approved_cn":cn,
                     "differs_from_authoring":"1" if i<1265 else "0",
                     "field_guard":"SHORT_FORM_NATIVE_CONSUMER_AND_LAYOUT_REQUIRED"
                                    if i<396 else "CURRENT_IMAGE_SOURCE_GLYPH_AND_LAYOUT_REQUIRED",
                     "image_write_state":"NOT_INSTALLED_BY_THIS_CATALOG_IMPORT"})
    return r2,uets

def main():
    r2,uets=fixtures()
    report=compare_rows(r2,uets)
    assert report["status"]=="PASS_TWO_REAL_SOURCE_ARCHIVES_NOT_FORMAL_SQLITE",report
    assert report["exact_four_field_matches"]==4857
    assert report["authoring_name_different_count"]==1265
    assert report["field_guard_counts"]["SHORT_FORM_NATIVE_CONSUMER_AND_LAYOUT_REQUIRED"]==396
    assert report["image_write_state_counts"]["NOT_INSTALLED_BY_THIS_CATALOG_IMPORT"]==4857
    assert report["formal_speed3_db_readback"]=="NOT_RUN"

    for field,value,label in [
        ("entity_id","ENTITY:9999","entity_id"),
        ("name_kind","WRONG_KIND","entity_type"),
        ("approved_cn","错误译名","canonical_cn"),
    ]:
        changed=copy.deepcopy(uets)
        changed[0][field]=value
        result=compare_rows(r2,changed)
        assert result["status"]=="BLOCKED_SOURCE_SNAPSHOT_DIFFERENCE"
        assert label in result["identity_name_category_differences"][0]["fields"]
        assert result["exact_four_field_matches"]==4856

    changed=copy.deepcopy(uets)
    changed[0]["source_id"]="SSFF_SYN_UNEXPECTED"
    result=compare_rows(r2,changed)
    assert len(result["r2_sources_missing_in_uets"])==1
    assert len(result["uets_sources_extra_to_r2"])==1
    assert result["status"]=="BLOCKED_SOURCE_SNAPSHOT_DIFFERENCE"

    changed=copy.deepcopy(uets)
    changed[0]["source_id"]=changed[1]["source_id"]
    try:
        compare_rows(r2,changed)
        raise AssertionError("Duplicate UETS source accepted")
    except ValueError:
        pass

    changed=copy.deepcopy(r2)
    changed[0]["实体ID"]=""
    result=compare_rows(changed,uets)
    assert result["status"]=="BLOCKED_SOURCE_SNAPSHOT_DIFFERENCE"

    changed=copy.deepcopy(uets)
    changed[0]["differs_from_authoring"]="MAYBE"
    result=compare_rows(r2,changed)
    assert result["invalid_authoring_change_flags"]==1
    assert result["status"]=="BLOCKED_SOURCE_SNAPSHOT_DIFFERENCE"

    try:
        compare_rows(r2[:4856],uets)
        raise AssertionError("Short source accepted")
    except ValueError:
        pass
    print("N02-U1 synthetic 4,857 R2/UETS archive four-field comparison: PASS")
    print("Entity/category/name mismatch, missing/extra source, duplicate, "
          "blank identity, invalid flags and incomplete source: REJECTED")
    print("Note: no private UETS/Speed3 SQLite used in this test.")

if __name__=="__main__":
    main()
