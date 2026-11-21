#!/usr/bin/env python3
"""Compare original R2 source bindings with the archived UETS N08 R2 snapshot.

Production source ZIPs stay private. No game text or database is modified.
A pass proves archived snapshot identity, NOT Speed3 current SQLite identity.
Python 3.10+, standard library only. Public CI uses synthetic rows only.
"""
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

R2_ZIP_SHA256 = "1f4f99dd1271dd64c149d283624cfa6c5404f260372f124267c36c0f6da17eb7"
UETS_ZIP_SHA256 = "f799d05d290fcd7313a4f0dd1824d7f4f43956cd804df74d72b9b60db825ca34"
R2_MEMBER_SHA256 = "459bbb24db91e97b313e20ce99a3490dd93f430df78d15208c414046bf1d1c18"
EXPECTED_ROWS = 4857

R2_COLUMNS = ("原始来源ID", "实体ID", "类别", "简体中文定名")
UETS_COLUMNS = ("source_id", "entity_id", "name_kind", "approved_cn",
                "differs_from_authoring", "field_guard", "image_write_state")
R2_MEMBER = "工程来源定名绑定.tsv"
UETS_MEMBER = "UETS/catalog/N08_R2定名绑定.tsv"


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as fp:
        for chunk in iter(lambda: fp.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_member(path, member, pinned_zip_hash, pinned_member_hash=None):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    if file_sha256(path) != pinned_zip_hash:
        raise ValueError(f"ZIP SHA-256 mismatch: {path.name}")
    with zipfile.ZipFile(path, "r") as z:
        if z.testzip() is not None:
            raise ValueError(f"ZIP has a failed CRC: {path.name}")
        names = [i for i in z.infolist() if not i.is_dir() and i.filename == member]
        if len(names) != 1:
            raise ValueError(f"Expected exactly one member {member}, got {len(names)}")
        info = names[0]
        if info.file_size > 2_000_000:
            raise ValueError(f"Member too large: {member}")
        data = z.read(info)
    if pinned_member_hash and sha256_bytes(data) != pinned_member_hash:
        raise ValueError(f"TSV member SHA-256 mismatch: {member}")
    return data


def parse_tsv(data, required):
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline=""),
                            delimiter="\t")
    headers = reader.fieldnames
    if not headers or len(set(headers)) != len(headers) or not set(required).issubset(headers):
        raise ValueError("TSV missing columns, invalid or repeated header")
    rows = list(reader)
    if any(None in r or any(v is None for v in r.values()) for r in rows):
        raise ValueError("Malformed TSV row width")
    return rows


def compare_rows(r2_rows, uets_rows):
    if len(r2_rows) != EXPECTED_ROWS or len(uets_rows) != EXPECTED_ROWS:
        raise ValueError(f"Unexpected record count: R2={len(r2_rows)}, UETS={len(uets_rows)}")
    r2, uets = {}, {}
    for row in r2_rows:
        sid = row["原始来源ID"]
        if not sid or sid != sid.strip() or sid in r2:
            raise ValueError(f"Blank, malformed or duplicated R2 source ID: {sid!r}")
        r2[sid] = row
    for row in uets_rows:
        sid = row["source_id"]
        if not sid or sid != sid.strip() or sid in uets:
            raise ValueError(f"Blank, malformed or duplicated UETS source ID: {sid!r}")
        uets[sid] = row

    missing = sorted(set(r2) - set(uets))
    unexpected = sorted(set(uets) - set(r2))
    columns = (
        ("实体ID", "entity_id", "entity_id"),
        ("类别", "name_kind", "entity_type"),
        ("简体中文定名", "approved_cn", "canonical_cn"),
    )
    differences = []
    exact = 0
    for sid in sorted(set(r2) & set(uets)):
        left, right = r2[sid], uets[sid]
        diff = {label: {"r2": left[a], "uets": right[b]}
                for a, b, label in columns if left[a] != right[b]}
        if diff:
            differences.append({"source_id": sid, "fields": diff})
        else:
            exact += 1
    field_guard = Counter(x["field_guard"] for x in uets_rows)
    image_status = Counter(x["image_write_state"] for x in uets_rows)
    changed = sum(x["differs_from_authoring"] == "1" for x in uets_rows)
    bad_changed_flags = sum(x["differs_from_authoring"] not in ("0", "1")
                            for x in uets_rows)
    # No null values, illegal control characters or empty identity fields.
    blank_r2_keys = [sid for sid,row in r2.items()
                     if any(not row[k] or "\x00" in row[k] for k in R2_COLUMNS)]
    blank_uets_keys = [sid for sid,row in uets.items()
                       if any(not row[k] or "\x00" in row[k]
                              for k in ("source_id", "entity_id", "name_kind", "approved_cn"))]
    accepted = (exact == EXPECTED_ROWS and not missing and not unexpected
                and not differences and not bad_changed_flags and
                not blank_r2_keys and not blank_uets_keys)
    return {
        "status": ("PASS_TWO_REAL_SOURCE_ARCHIVES_NOT_FORMAL_SQLITE"
                   if accepted else "BLOCKED_SOURCE_SNAPSHOT_DIFFERENCE"),
        "r2_rows": len(r2_rows),
        "uets_rows": len(uets_rows),
        "exact_four_field_matches": exact,
        "r2_sources_missing_in_uets": missing,
        "uets_sources_extra_to_r2": unexpected,
        "identity_name_category_differences": differences,
        "authoring_name_different_count": changed,
        "invalid_authoring_change_flags": bad_changed_flags,
        "field_guard_counts": dict(sorted(field_guard.items())),
        "image_write_state_counts": dict(sorted(image_status.items())),
        "malformed_r2_sources": blank_r2_keys,
        "malformed_uets_sources": blank_uets_keys,
        "formal_speed3_db_readback": "NOT_RUN",
        "version_scope": ("Archive R2 2026-11-19 vs UETS design-source snapshot "
                          "2026-11-21, not Speed3 merged SQLite file."),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--r2-zip", required=True, help="Unmodified original R2 delivery ZIP")
    ap.add_argument("--uets-source-zip", required=True,
                    help="Unmodified 2026-11-21 UETS design source archive")
    ap.add_argument("--report", required=True, help="New private JSON report")
    a = ap.parse_args()
    dest = Path(a.report)
    if dest.exists() or dest.resolve() in (
            Path(a.r2_zip).resolve(), Path(a.uets_source_zip).resolve()):
        raise FileExistsError("Do not overwrite a report or any source ZIP")
    r2_data = read_member(a.r2_zip, R2_MEMBER, R2_ZIP_SHA256, R2_MEMBER_SHA256)
    uets_data = read_member(a.uets_source_zip, UETS_MEMBER, UETS_ZIP_SHA256)
    result = compare_rows(parse_tsv(r2_data, R2_COLUMNS),
                          parse_tsv(uets_data, UETS_COLUMNS))
    result["input_identity"] = {
        "r2_zip_sha256": R2_ZIP_SHA256,
        "r2_member_sha256": R2_MEMBER_SHA256,
        "uets_zip_sha256": UETS_ZIP_SHA256,
        "uets_member_sha256": sha256_bytes(uets_data),
    }
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "matched": result["exact_four_field_matches"],
        "r2_rows": result["r2_rows"], "uets_rows": result["uets_rows"],
        "report": str(dest),
    }, ensure_ascii=False))
    raise SystemExit(0 if result["status"].startswith("PASS_TWO_REAL") else 2)


if __name__ == "__main__":
    main()
