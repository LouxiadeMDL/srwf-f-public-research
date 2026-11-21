#!/usr/bin/env python3
"""Synthetic acceptance tests for N02-U1 data-preservation tools.

No private database/game/guide content. CI must not claim U1 production PASS.
"""
import csv
import json
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path


def run(*cmd, ok=0):
    result = subprocess.run([sys.executable, *map(str, cmd)],
                            capture_output=True, text=True)
    if result.returncode != ok:
        raise AssertionError(
            f"Unexpected exit {result.returncode} expected {ok}: {cmd}\n"
            + result.stdout + "\n" + result.stderr
        )
    return result


def make_parent(path):
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE example_source(source_id TEXT PRIMARY KEY, original_text TEXT, raw_bytes BLOB)")
        db.executemany("INSERT INTO example_source VALUES(?,?,?)", [
            ("SSF:STORY:1", "母舰抵达", b"\x00\xff"),
            ("SSFF:STORY:2", "敌机撤退", b"\x01\x02"),
        ])


def make_guide(path, ff=False):
    with sqlite3.connect(path) as db:
        db.executescript("""
          CREATE TABLE sources(source_id TEXT PRIMARY KEY, title TEXT,
              pdf_sha256 TEXT, page_count INTEGER);
          CREATE TABLE pages(page_id TEXT PRIMARY KEY, source_id TEXT,
              page_number INTEGER, transcript_text TEXT, canonical_text TEXT, qa_state TEXT);
          CREATE TABLE page_lines(line_id TEXT PRIMARY KEY, page_id TEXT, source_id TEXT,
              page_number INTEGER, line_number INTEGER, line_text TEXT);
          CREATE TABLE qa_resolution(page_id TEXT PRIMARY KEY, original_flag TEXT,
              resolution_status TEXT, information_status TEXT, exact_text_status TEXT);
          CREATE TABLE crosscheck_facts(id INTEGER PRIMARY KEY, page_id TEXT);
        """)
        sections = [("FF", 812)] if ff else [("F", 210), ("FF_OLD", 812), ("SFC4", 40)]
        for section, pages in sections:
            db.execute("INSERT INTO sources VALUES(?,?,?,?)",
                       (section, section, "a" * 64, pages))
            for page in range(1, pages + 1):
                pid = f"{section}:{page}"
                db.execute("INSERT INTO pages VALUES(?,?,?,?,?,?)",
                           (pid, section, page, "原始记录", "原始记录", "APPROVED"))
                db.execute("INSERT INTO page_lines VALUES(?,?,?,?,?,?)",
                           (pid, pid, section, page, 1, "示例文字"))
        if ff:
            for i in range(44):
                db.execute("INSERT INTO qa_resolution VALUES(?,?,?,?,?)",
                           (f"FF:{i+1}", "FLAG", "RESOLVED", "CLOSED", "UNVERIFIED"))
            for i in range(109):
                db.execute("INSERT INTO crosscheck_facts VALUES(?,?)", (i + 1, "FF:1"))


def make_r2(path):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["实体ID", "类别", "简体中文定名"])
        for i in range(1392):
            w.writerow([f"ENTITY:{i:04d}", "机体", f"实体{i}"])


def main():
    root = Path(__file__).resolve().parents[1]
    builder = root / "tools" / "n02_u1_baseline_builder.py"
    auditor = root / "tools" / "n02_u1_independent_verify.py"
    with tempfile.TemporaryDirectory() as tmp:
        w = Path(tmp)
        parent, guide_f, guide_ff = w / "parent.sqlite", w / "f.sqlite", w / "ff.sqlite"
        r2, candidate, report = w / "r2.tsv", w / "new.sqlite", w / "audit.json"
        make_parent(parent)
        make_guide(guide_f)
        make_guide(guide_ff, ff=True)
        make_r2(r2)
        run(builder, "--n03", parent, "--guide-f", guide_f,
            "--guide-ff", guide_ff, "--r2", r2, "--out", candidate)
        run(auditor, "--parent", parent, "--candidate", candidate,
            "--r2", r2, "--guide-f", guide_f, "--guide-ff", guide_ff,
            "--report", report)
        obj = json.loads(report.read_text(encoding="utf-8"))
        assert obj["status"] == "N02_U1_PARTIAL", obj
        assert obj["baseline_pass"], obj
        assert obj["checks"]["r2_exact_names"]["pass"], obj
        assert obj["checks"]["ff_qa44_inherited"]["pass"], obj
        assert obj["checks"]["legacy_table_byte_semantics_preserved"]["pass"], obj
        with sqlite3.connect(candidate) as db:
            db.execute("UPDATE example_source SET original_text='被篡改' WHERE source_id='SSF:STORY:1'")
        bad_report = w / "bad_audit.json"
        run(auditor, "--parent", parent, "--candidate", candidate,
            "--r2", r2, "--guide-f", guide_f, "--guide-ff", guide_ff,
            "--report", bad_report, ok=2)
        failed = json.loads(bad_report.read_text(encoding="utf-8"))
        assert failed["status"] == "N02_U1_BLOCKED", failed
        assert not failed["checks"]["legacy_table_byte_semantics_preserved"]["pass"], failed
        print("N02-U1 synthetic tests PASS: untouched data preserved, tamper detected.")
        print("NOTE: synthetic PASS is not a production-database acceptance.")


if __name__ == "__main__":
    main()
