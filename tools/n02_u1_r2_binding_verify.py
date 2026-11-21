#!/usr/bin/env python3
"""Independent R2 staging audit; intentionally imports no builder code.

Compares every entity/source binding, input digest and raw TSV row metadata.
Exit 0 means staging source identity only, NOT N02-U1 or N03 runtime PASS.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sqlite3

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        while True:
            data = stream.read(4 * 1024 * 1024)
            if not data:
                break
            h.update(data)
    return h.hexdigest()

def parse_tsv(path):
    with open(path, encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        names = reader.fieldnames
        if not names or len(set(names)) != len(names):
            raise ValueError("Invalid TSV column headers: " + str(path))
        rows = list(reader)
        if any(None in r or any(v is None for v in r.values()) for r in rows):
            raise ValueError("Invalid TSV row length: " + str(path))
        return names, rows

def compare(args):
    inp_names = Path(args.names)
    inp_bindings = Path(args.bindings)
    stage = Path(args.stage)
    for path in (inp_names, inp_bindings, stage):
        if not path.is_file():
            raise FileNotFoundError(path)
    header_names, rows_names = parse_tsv(inp_names)
    header_bindings, rows_bindings = parse_tsv(inp_bindings)
    if not {"实体ID", "类别", "简体中文定名"}.issubset(header_names):
        raise ValueError("Missing R2 names columns")
    if args.source_column not in header_bindings or args.entity_column not in header_bindings:
        raise ValueError("Missing mapped binding source/entity columns")
    name_col = args.binding_name_column
    if name_col is None and "简体中文定名" in header_bindings:
        name_col = "简体中文定名"
    if name_col and name_col not in header_bindings:
        raise ValueError("Selected binding name column is missing")

    result = {
        "status": "BLOCKED_STAGING", "stage": stage.name,
        "inputs": {
            "R2_NAMES": {"basename": inp_names.name, "bytes": inp_names.stat().st_size,
                         "sha256": sha256_file(inp_names)},
            "R2_BINDINGS": {"basename": inp_bindings.name,
                            "bytes": inp_bindings.stat().st_size,
                            "sha256": sha256_file(inp_bindings)},
        },
        "checks": {}, "production_scope": "NOT_RUN",
    }
    def check(key, ok, detail):
        result["checks"][key] = {"pass": bool(ok), "detail": detail}

    expected_entities = sorted((
        r["实体ID"], r["类别"], r["简体中文定名"]) for r in rows_names)
    term_map = {a:c for a,b,c in expected_entities}
    duplicate_entity = len(term_map) != len(expected_entities)
    expected_bindings = sorted((
        row[args.source_column],
        row[args.entity_column],
        term_map.get(row[args.entity_column], ""),
        i,
        json.dumps(row, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":")),
        "R2_IMPORTED_NOT_CALLSITE_PROOF"
    ) for i, row in enumerate(rows_bindings, 2))
    duplicate_source = len({r[0] for r in expected_bindings}) != len(expected_bindings)
    check("r2_names_exact_count", len(expected_entities) == 1392 and not duplicate_entity,
          {"rows": len(expected_entities), "duplicate_identity": duplicate_entity})
    check("r2_bindings_exact_count", len(expected_bindings) == 4857 and not duplicate_source,
          {"rows": len(expected_bindings), "duplicate_source": duplicate_source})
    check("bindings_all_identified",
          all(row[2] and row[1] in term_map for row in expected_bindings),
          "Every source binding must link to an existing R2 entity")
    if name_col:
        check("bindings_same_canonical_name",
              all(row[name_col] == term_map.get(row[args.entity_column])
                  for row in rows_bindings),
              "Binding TSV name column must match the R2 master name")
    else:
        check("binding_name_column_available", True,
              "Absent: names joined by entity ID only; no original name-column claim")
    with sqlite3.connect(stage.resolve().as_uri() + "?mode=ro", uri=True) as db:
        check("sqlite_integrity",
              db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
              and db.execute("PRAGMA foreign_key_check").fetchone() is None,
              "SQLite integrity and foreign keys")
        actual_entities = db.execute(
            "SELECT entity_id,entity_type,canonical_cn FROM R2_ENTITY ORDER BY entity_id"
        ).fetchall()
        actual_bindings = db.execute(
            "SELECT original_source_id,entity_id,canonical_cn,source_file_line,"
            "raw_row_json,evidence_status FROM R2_SOURCE_BINDING "
            "ORDER BY original_source_id"
        ).fetchall()
        actual_receipts = {
            r[0]: (r[1],r[2],r[3])
            for r in db.execute("SELECT role,basename,bytes,sha256 FROM R2_INPUT")
        }
    check("entity_rows_exact", actual_entities == expected_entities,
          {"expected": len(expected_entities), "observed": len(actual_entities)})
    check("source_binding_rows_exact", actual_bindings == expected_bindings,
          {"expected": len(expected_bindings), "observed": len(actual_bindings)})
    receipt_valid = (
        set(actual_receipts) == set(result["inputs"]) and all(
            actual_receipts[k] == (
                v["basename"], v["bytes"], v["sha256"]
            ) for k,v in result["inputs"].items()
        )
    )
    check("input_receipts_exact", receipt_valid,
          {"roles": sorted(actual_receipts), "matches": receipt_valid})
    check("not_claimed_as_runtime",
          all(r[-1] == "R2_IMPORTED_NOT_CALLSITE_PROOF" for r in actual_bindings),
          "Staged R2 mapping must never claim N03 static or runtime proof")
    result["passed"] = all(x["pass"] for x in result["checks"].values())
    result["status"] = ("VERIFIED_STAGING_NOT_N02_U1_PASS"
                        if result["passed"] else "BLOCKED_STAGING")
    return result

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--names", required=True)
    p.add_argument("--bindings", required=True)
    p.add_argument("--stage", required=True)
    p.add_argument("--report", required=True)
    p.add_argument("--source-column", default="原始来源ID")
    p.add_argument("--entity-column", default="实体ID")
    p.add_argument("--binding-name-column", default=None)
    args = p.parse_args()
    path = Path(args.report)
    if path.exists():
        raise FileExistsError("Refuse to overwrite an existing report: " + str(path))
    result = compare(args)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    print(json.dumps({"status": result["status"],
                      "checks": len(result["checks"])}, ensure_ascii=False))
    raise SystemExit(0 if result["passed"] else 2)

if __name__ == "__main__":
    main()
