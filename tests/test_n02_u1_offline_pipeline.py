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
                raw = "FF原始OCR扫描" if ff else "原始记录"
                corrected = "FF已校对的文字" if ff else raw
                db.execute("INSERT INTO pages VALUES(?,?,?,?,?,?)",
                           (pid, section, page, raw, corrected, "APPROVED"))
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
        assert obj["checks"]["builder_input_receipts_match_actual_files"]["pass"], obj
        assert obj["checks"]["FF_v1.0.2_corrected_source_identity"]["pass"], obj
        assert obj["checks"]["legacy_table_byte_semantics_preserved"]["pass"], obj
        for check in ("F_v0.2_pages_original_identity",
                      "F_v0.2_lines_original_identity",
                      "FF_v1.0.2_pages_original_identity",
                      "FF_v1.0.2_lines_original_identity",
                      "FF_v1.0.2_qa_original_identity",
                      "FF_v1.0.2_facts_original_identity"):
            assert obj["checks"][check]["pass"], (check, obj["checks"][check])
        with sqlite3.connect(candidate) as db:
            raw, normalized = db.execute(
                "SELECT original_transcript,normalized_transcript "
                "FROM GUIDE_PAGE WHERE guide_key='FF_v1.0.2::FF' LIMIT 1").fetchone()
            assert raw == "FF原始OCR扫描", (raw, normalized)
            assert normalized == "FF已校对的文字", (raw, normalized)
            corrected = db.execute(
                "SELECT corrected_source_text FROM GUIDE_PAGE_CORRECTION_SOURCE "
                "WHERE guide_key='FF_v1.0.2::FF' LIMIT 1").fetchone()[0]
            assert corrected == normalized
            assert db.execute(
                "SELECT status FROM QA_RESULT WHERE qa_key='U1_ORIGINAL_PRESERVED'"
            ).fetchone()[0] == "PENDING_INDEPENDENT_AUDIT"
            # Old 812-page FF guide remains historical; only FF v1.0.2 is canonical.
            fpol = db.execute(
                "SELECT policy FROM GUIDE_DOCUMENT WHERE guide_key='F_v0.2::FF_OLD'"
            ).fetchone()[0]
            ffpol = db.execute(
                "SELECT policy FROM GUIDE_DOCUMENT WHERE guide_key='FF_v1.0.2::FF'"
            ).fetchone()[0]
            assert fpol == "ARCHIVAL_SUPERSEDED_BY_FF_v1.0.2"
            assert ffpol == "CANONICAL_FF_REFERENCE"
        with sqlite3.connect(candidate) as db:
            db.execute("UPDATE example_source SET original_text='被篡改' WHERE source_id='SSF:STORY:1'")
        bad_report = w / "bad_audit.json"
        run(auditor, "--parent", parent, "--candidate", candidate,
            "--r2", r2, "--guide-f", guide_f, "--guide-ff", guide_ff,
            "--report", bad_report, ok=2)
        failed = json.loads(bad_report.read_text(encoding="utf-8"))
        assert failed["status"] == "N02_U1_BLOCKED", failed
        assert not failed["checks"]["legacy_table_byte_semantics_preserved"]["pass"], failed
        # A mutated guide original_text must fail even when page and line counts match.
        with sqlite3.connect(candidate) as db:
            db.execute(
                "UPDATE GUIDE_TEXT_NORMALIZED SET original_text='原文被篡改' "
                "WHERE rowid=(SELECT rowid FROM GUIDE_TEXT_NORMALIZED "
                "WHERE guide_key='F_v0.2::F' ORDER BY rowid LIMIT 1)")
        guide_report = w / "guide_tamper_audit.json"
        run(auditor, "--parent", parent, "--candidate", candidate,
            "--r2", r2, "--guide-f", guide_f, "--guide-ff", guide_ff,
            "--report", guide_report, ok=2)
        guide_failed = json.loads(guide_report.read_text(encoding="utf-8"))
        assert not guide_failed["checks"]["F_v0.2_lines_original_identity"]["pass"], guide_failed
        # Changing an imported historical QA record must also fail closed.
        with sqlite3.connect(candidate) as db:
            db.execute(
                "UPDATE FF_GUIDE_QA_RESOLUTION SET raw_json='{}' "
                "WHERE rowid=(SELECT rowid FROM FF_GUIDE_QA_RESOLUTION LIMIT 1)")
        qa_report = w / "qa_tamper_audit.json"
        run(auditor, "--parent", parent, "--candidate", candidate,
            "--r2", r2, "--guide-f", guide_f, "--guide-ff", guide_ff,
            "--report", qa_report, ok=2)
        qa_failed = json.loads(qa_report.read_text(encoding="utf-8"))
        assert not qa_failed["checks"]["FF_v1.0.2_qa_original_identity"]["pass"], qa_failed
        # A changed reviewed FF correction must be detected independently,
        # even if all raw pages and historical QA records are still present.
        with sqlite3.connect(candidate) as db:
            db.execute(
                "UPDATE GUIDE_PAGE_CORRECTION_SOURCE SET corrected_source_text='错误的校对文字' "
                "WHERE rowid=(SELECT rowid FROM GUIDE_PAGE_CORRECTION_SOURCE LIMIT 1)")
        corr_report = w / "correction_tamper_audit.json"
        run(auditor, "--parent", parent, "--candidate", candidate,
            "--r2", r2, "--guide-f", guide_f, "--guide-ff", guide_ff,
            "--report", corr_report, ok=2)
        corr_failed = json.loads(corr_report.read_text(encoding="utf-8"))
        assert not corr_failed["checks"]["FF_v1.0.2_corrected_source_identity"]["pass"]
        # Input identity cannot be certified from a stale or fabricated receipt.
        with sqlite3.connect(candidate) as db:
            db.execute(
                "UPDATE U1_BUILD_INPUT SET sha256=? WHERE role='GUIDE_FF_V102'",
                ("f" * 64,))
        receipt_report = w / "receipt_tamper_audit.json"
        run(auditor, "--parent", parent, "--candidate", candidate,
            "--r2", r2, "--guide-f", guide_f, "--guide-ff", guide_ff,
            "--report", receipt_report, ok=2)
        receipt_failed = json.loads(receipt_report.read_text(encoding="utf-8"))
        assert not receipt_failed["checks"]["builder_input_receipts_match_actual_files"]["pass"]
        print("N02-U1 synthetic tests PASS: raw OCR, corrected FF source, receipts, "
              "parent/guide/QA tampering rejected.")
        print("NOTE: synthetic PASS is not a production-database acceptance.")


if __name__ == "__main__":
    main()
