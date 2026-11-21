#!/usr/bin/env python3
"""Stage an exact R2 source-ID -> entity-ID mapping without touching game databases.

Private-data tool, standard-library only (Python 3.10+).
A successful stage is NOT N02-U1 completion, N03 callsite proof, or game validation.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile

EXPECTED_ENTITIES = 1392
EXPECTED_BINDINGS = 4857

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE R2_INPUT(
    role TEXT PRIMARY KEY, basename TEXT NOT NULL,
    bytes INTEGER NOT NULL CHECK(bytes>0), sha256 TEXT NOT NULL
);
CREATE TABLE R2_ENTITY(
    entity_id TEXT PRIMARY KEY, entity_type TEXT NOT NULL,
    canonical_cn TEXT NOT NULL CHECK(length(canonical_cn)>0)
);
CREATE TABLE R2_SOURCE_BINDING(
    original_source_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL REFERENCES R2_ENTITY(entity_id),
    canonical_cn TEXT NOT NULL,
    source_file_line INTEGER NOT NULL CHECK(source_file_line>=2),
    raw_row_json TEXT NOT NULL,
    evidence_status TEXT NOT NULL
       CHECK(evidence_status='R2_IMPORTED_NOT_CALLSITE_PROOF')
);
CREATE INDEX idx_r2_source_entity ON R2_SOURCE_BINDING(entity_id);
"""

def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def read_tsv(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        headers = reader.fieldnames
        if not headers or len(set(headers)) != len(headers) or None in headers:
            raise ValueError("Missing, repeated or invalid TSV headers: " + str(path))
        rows = list(reader)
        for index, row in enumerate(rows, 2):
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f"Invalid TSV column count at input row {index}")
    return headers, rows

def checked_key(value, label, row):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Blank {label} in input row {row}")
    if value != value.strip() or any(c in value for c in "\x00\t\r\n"):
        raise ValueError(f"Unsafe or noncanonical {label} in input row {row}")
    return value

def render_row(row):
    # Stable transcript for independent verification; original file is retained.
    return json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

def stage(names_path, bindings_path, target, receipt, *,
          source_col="原始来源ID", entity_col="实体ID",
          name_col=None, names_pin=None, bindings_pin=None):
    names_path, bindings_path = Path(names_path), Path(bindings_path)
    target, receipt = Path(target), Path(receipt)
    for path in (names_path, bindings_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    resolutions = [p.resolve() for p in (names_path, bindings_path, target, receipt)]
    if len(set(resolutions)) != 4:
        raise ValueError("Input, output and receipt must all have distinct paths")
    if target.exists() or receipt.exists():
        raise FileExistsError("Never overwrite an existing staging database or receipt")

    name_headers, name_rows = read_tsv(names_path)
    if not {"实体ID", "类别", "简体中文定名"}.issubset(name_headers):
        raise ValueError("R2 names file must contain 实体ID / 类别 / 简体中文定名")
    if len(name_rows) != EXPECTED_ENTITIES:
        raise ValueError(f"R2 name count {len(name_rows)} != {EXPECTED_ENTITIES}")
    entities = {}
    for i, row in enumerate(name_rows, 2):
        entity = checked_key(row["实体ID"], "entity ID", i)
        kind = checked_key(row["类别"], "entity type", i)
        cn = row["简体中文定名"]
        if not isinstance(cn, str) or not cn.strip() or "\x00" in cn:
            raise ValueError(f"Invalid canonical name in row {i}")
        if entity in entities:
            raise ValueError(f"Duplicate R2 entity: {entity}")
        entities[entity] = (kind, cn)

    binding_headers, binding_rows = read_tsv(bindings_path)
    for column in (source_col, entity_col):
        if column not in binding_headers:
            raise ValueError(f"Missing binding column {column!r}; actual headers={binding_headers}")
    if name_col is None and "简体中文定名" in binding_headers:
        name_col = "简体中文定名"
    if name_col is not None and name_col not in binding_headers:
        raise ValueError(f"Requested binding name column missing: {name_col!r}")
    if len(binding_rows) != EXPECTED_BINDINGS:
        raise ValueError(f"R2 binding count {len(binding_rows)} != {EXPECTED_BINDINGS}")

    mappings = []
    seen = set()
    for i, row in enumerate(binding_rows, 2):
        source = checked_key(row[source_col], "original source ID", i)
        entity = checked_key(row[entity_col], "binding entity ID", i)
        if source in seen:
            raise ValueError(f"Duplicate original source ID: {source}")
        if entity not in entities:
            raise ValueError(f"Binding row {i} references unknown entity: {entity}")
        cn = entities[entity][1]
        if name_col is not None and row[name_col] != cn:
            raise ValueError(f"Binding row {i} disagrees with R2 canonical name")
        seen.add(source)
        mappings.append((source, entity, cn, i, render_row(row),
                         "R2_IMPORTED_NOT_CALLSITE_PROOF"))

    hash_names = sha256_file(names_path)
    hash_bindings = sha256_file(bindings_path)
    for label, actual, pinned in (("names", hash_names, names_pin),
                                  ("bindings", hash_bindings, bindings_pin)):
        if pinned is not None and actual.lower() != pinned.lower():
            raise ValueError(f"Pinned R2 {label} SHA-256 mismatch")
    target.parent.mkdir(parents=True, exist_ok=True)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".n02_u1_r2_", suffix=".sqlite",
                                    dir=target.parent)
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        with sqlite3.connect(tmp) as db:
            db.executescript(SCHEMA)
            db.executemany("INSERT INTO R2_ENTITY VALUES(?,?,?)",
                           [(entity, kind, cn) for entity,(kind,cn) in entities.items()])
            db.executemany("INSERT INTO R2_SOURCE_BINDING VALUES(?,?,?,?,?,?)", mappings)
            db.executemany("INSERT INTO R2_INPUT VALUES(?,?,?,?)", [
                ("R2_NAMES", names_path.name, names_path.stat().st_size, hash_names),
                ("R2_BINDINGS", bindings_path.name, bindings_path.stat().st_size,
                 hash_bindings),
            ])
            db.commit()
            if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("Stage integrity_check not ok")
            if db.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise RuntimeError("Stage foreign_key_check found a violation")
            if db.execute("SELECT count(*) FROM R2_SOURCE_BINDING").fetchone()[0] != EXPECTED_BINDINGS:
                raise RuntimeError("Stage row count mismatch")
        os.replace(tmp, target)
        report = {
            "status": "STAGED_NOT_N02_U1_PASS",
            "evidence": "R2 source binding only, not N03 callsite or runtime evidence",
            "entities": len(entities), "source_bindings": len(mappings),
            "binding_source_column": source_col, "binding_entity_column": entity_col,
            "binding_name_column": name_col,
            "input_pins": {
                "R2_NAMES": bool(names_pin), "R2_BINDINGS": bool(bindings_pin)
            },
            "inputs": {
                "R2_NAMES": {"basename": names_path.name,
                             "bytes": names_path.stat().st_size, "sha256": hash_names},
                "R2_BINDINGS": {"basename": bindings_path.name,
                                "bytes": bindings_path.stat().st_size,
                                "sha256": hash_bindings},
            },
            "stage": {"basename": target.name, "bytes": target.stat().st_size,
                      "sha256": sha256_file(target)},
            "known_gaps": [
                "No reconciliation to N03 actual source-ID table",
                "No N08/N09 latest approved manuscript text reconciliation",
                "No source callsite or dynamic-display verification",
                "No semantic review of ambiguous entity identity",
            ],
        }
        fd2, temp_receipt = tempfile.mkstemp(prefix=".n02_u1_receipt_",
                                            suffix=".json", dir=receipt.parent)
        os.close(fd2)
        temp_receipt = Path(temp_receipt)
        try:
            temp_receipt.write_text(
                json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8")
            os.replace(temp_receipt, receipt)
        finally:
            temp_receipt.unlink(missing_ok=True)
        return report
    finally:
        tmp.unlink(missing_ok=True)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--names", required=True, help="R2 1,392-entry TSV")
    p.add_argument("--bindings", required=True, help="R2 4,857-source TSV")
    p.add_argument("--out", required=True, help="New private SQLite sidecar path")
    p.add_argument("--receipt", required=True, help="New private JSON receipt path")
    p.add_argument("--source-column", default="原始来源ID")
    p.add_argument("--entity-column", default="实体ID")
    p.add_argument("--binding-name-column", default=None)
    p.add_argument("--expected-names-sha256", default=None)
    p.add_argument("--expected-bindings-sha256", default=None)
    a = p.parse_args()
    report = stage(a.names, a.bindings, a.out, a.receipt,
                   source_col=a.source_column, entity_col=a.entity_column,
                   name_col=a.binding_name_column,
                   names_pin=a.expected_names_sha256,
                   bindings_pin=a.expected_bindings_sha256)
    print(json.dumps({"status": report["status"],
                      "entities": report["entities"],
                      "source_bindings": report["source_bindings"]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
