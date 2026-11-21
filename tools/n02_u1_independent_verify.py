#!/usr/bin/env python3
"""N02-U1 independent, fail-closed source-preservation audit.

Read-only: does not alter games, original SQLite or candidate SQLite.
Python 3.10+ stdlib. Do not publish its output if local paths are sensitive.
"""
import argparse
import csv
import hashlib
import json
import sqlite3
from pathlib import Path


def quoted(name):
    return '"' + name.replace('"', '""') + '"'


def connect_ro(path):
    return sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)


def sha(path):
    d = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b""):
            d.update(b)
    return d.hexdigest()


def tables(db):
    return {
        row[0]: row[1] for row in db.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    }


def digest_rows(db, table):
    """Type-preserving digest over all rows in reproducible rowid order.

    SQLite backup preserves the row storage for ordinary tables. If a virtual
    table does not expose rowid, fall back to column-order sorting.
    """
    cols = [r[1] for r in db.execute("PRAGMA table_info(" + quoted(table) + ")")]
    if not cols:
        raise ValueError(f"No visible columns: {table}")
    q = "SELECT * FROM " + quoted(table)
    try:
        it = db.execute(q + " ORDER BY rowid")
    except sqlite3.OperationalError:
        it = db.execute(q + " ORDER BY " + ",".join(quoted(c) for c in cols))
    d = hashlib.sha256()
    count = 0
    for row in it:
        count += 1
        for cell in row:
            if cell is None:
                tag, b = b"N", b""
            elif isinstance(cell, bytes):
                tag, b = b"B", cell
            elif isinstance(cell, str):
                tag, b = b"S", cell.encode("utf-8", "surrogatepass")
            elif isinstance(cell, int):
                tag, b = b"I", str(cell).encode("ascii")
            else:
                tag, b = b"F", repr(cell).encode("ascii")
            d.update(tag + len(b).to_bytes(8, "big") + b)
        d.update(b"\xff")
    return count, d.hexdigest()


def check_sqlite(db):
    integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
    fk = db.execute("PRAGMA foreign_key_check").fetchall()
    return integrity, len(fk)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--parent", required=True, help="Unmodified N03 parent SQLite")
    p.add_argument("--candidate", required=True, help="New N02-U1 candidate SQLite")
    p.add_argument("--r2", required=True, help="R2 TSV with exact 3-column header")
    p.add_argument("--guide-f", required=True)
    p.add_argument("--guide-ff", required=True)
    p.add_argument("--report", required=True)
    args = p.parse_args()
    inp = {k: Path(v) for k, v in {
        "parent": args.parent, "candidate": args.candidate, "r2": args.r2,
        "guide_f": args.guide_f, "guide_ff": args.guide_ff,
    }.items()}
    for role, path in inp.items():
        if not path.is_file():
            raise FileNotFoundError(f"{role}: {path}")
    out = Path(args.report)
    if out.exists():
        raise FileExistsError(f"Refuse to overwrite report: {out}")
    result = {
        "node": "N02-U1", "audit_kind": "independent_full_table",
        "inputs": {k: {"basename": v.name, "size": v.stat().st_size, "sha256": sha(v)}
                   for k, v in inp.items()},
        "checks": {}, "original_tables": {}, "scope_limitations": [],
    }
    passed = True

    def assertion(key, valid, detail):
        nonlocal passed
        result["checks"][key] = {"pass": bool(valid), "detail": detail}
        if not valid:
            passed = False

    with connect_ro(inp["parent"]) as src, connect_ro(inp["candidate"]) as dst:
        for label, conn in (("parent", src), ("candidate", dst)):
            integrity, fk = check_sqlite(conn)
            assertion(label + "_integrity", integrity == "ok" and fk == 0,
                      {"integrity_check": integrity, "foreign_key_errors": fk})
        parent_tables = tables(src)
        target_tables = tables(dst)
        missing = sorted(set(parent_tables) - set(target_tables))
        assertion("parent_table_names_preserved", not missing, {"missing": missing})
        for name, sql in parent_tables.items():
            if name not in target_tables:
                continue
            same_schema = sql == target_tables[name]
            sc, sd = digest_rows(src, name)
            dc, dd = digest_rows(dst, name)
            result["original_tables"][name] = {
                "source_rows": sc, "candidate_rows": dc,
                "source_digest": sd, "candidate_digest": dd,
                "schema_equal": same_schema, "rows_equal": (sc == dc and sd == dd),
            }
            if not (same_schema and sc == dc and sd == dd):
                passed = False
        assertion("legacy_table_byte_semantics_preserved",
                  all(x["schema_equal"] and x["rows_equal"]
                      for x in result["original_tables"].values()),
                  "Type-preserving full row digests and schema SQL; not raw SQLite page hashes")

        with open(inp["r2"], encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f, delimiter="\t"))
        expected = {(r["实体ID"], r["类别"], r["简体中文定名"]) for r in rows}
        actual = set()
        if {"CANONICAL_ENTITY", "CANONICAL_TERM"} <= set(target_tables):
            actual = set(dst.execute(
                "SELECT e.entity_id,e.entity_type,t.canonical_cn "
                "FROM CANONICAL_ENTITY e JOIN CANONICAL_TERM t USING(entity_id)"
            ).fetchall())
        assertion("r2_exact_names", len(rows) == 1392 and len(expected) == len(rows)
                  and actual == expected,
                  {"r2_rows": len(rows), "unique_input": len(expected),
                   "actual": len(actual), "only_in_input": len(expected - actual),
                   "only_in_output": len(actual - expected)})
        have_guide = {"GUIDE_DOCUMENT", "GUIDE_PAGE", "GUIDE_TEXT_NORMALIZED"} <= set(target_tables)
        assertion("guide_tables_present", have_guide, "Guide normalized layer required")
        if have_guide:
            for k, path in (("F_v0.2", inp["guide_f"]), ("FF_v1.0.2", inp["guide_ff"])):
                with connect_ro(path) as guide:
                    ig, fk = check_sqlite(guide)
                    pages = guide.execute("SELECT count(*) FROM pages").fetchone()[0]
                    lines = guide.execute("SELECT count(*) FROM page_lines").fetchone()[0]
                pcount = dst.execute(
                    "SELECT count(*) FROM GUIDE_PAGE WHERE guide_key LIKE ?", (k + "::%",)
                ).fetchone()[0]
                lcount = dst.execute(
                    "SELECT count(*) FROM GUIDE_TEXT_NORMALIZED WHERE guide_key LIKE ?",
                    (k + "::%",)
                ).fetchone()[0]
                assertion(k + "_pages_lines", ig == "ok" and fk == 0
                          and pcount == pages and lcount == lines
                          and pages == (1062 if k == "F_v0.2" else 812),
                          {"source_pages": pages, "copied_pages": pcount,
                           "source_lines": lines, "copied_lines": lcount,
                           "source_fk_errors": fk})
            with connect_ro(inp["guide_ff"]) as guide:
                ff_qa = guide.execute("SELECT count(*) FROM qa_resolution").fetchone()[0]
                ff_facts = guide.execute("SELECT count(*) FROM crosscheck_facts").fetchone()[0]
            qa = dst.execute("SELECT count(*) FROM FF_GUIDE_QA_RESOLUTION").fetchone()[0] if "FF_GUIDE_QA_RESOLUTION" in target_tables else -1
            facts = dst.execute("SELECT count(*) FROM FF_GUIDE_CROSSCHECK").fetchone()[0] if "FF_GUIDE_CROSSCHECK" in target_tables else -1
            assertion("ff_qa44_inherited", ff_qa == 44 and qa == ff_qa and facts == ff_facts,
                      {"source_qa": ff_qa, "candidate_qa": qa,
                       "source_facts": ff_facts, "candidate_facts": facts})

        rev = dst.execute("SELECT count(*) FROM TEXT_REVISION").fetchone()[0] if "TEXT_REVISION" in target_tables else -1
        result["text_revision_rows"] = rev
        result["scope_limitations"] = [
            "No independent semantic verification of entity identities",
            "No proof of N08/N09 current approved text reconciliation",
            "No proof of 4,857 R2 source bindings until source TSV is imported",
            "No N03 dynamic callsite or all-branch runtime completion proof",
            "Guide page/line count equality does not prove normalized substitutions",
            "No 35-category full semantic and runtime signoff",
        ]
    result["baseline_pass"] = passed
    result["status"] = "N02_U1_PARTIAL" if passed else "N02_U1_BLOCKED"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "report": str(out),
                      "checks": len(result["checks"])}, ensure_ascii=False))
    raise SystemExit(0 if passed else 2)


if __name__ == "__main__":
    main()
