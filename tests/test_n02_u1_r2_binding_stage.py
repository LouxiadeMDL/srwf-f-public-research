#!/usr/bin/env python3
"""Entirely synthetic R2 mapping tests. No game data or guide text."""
import csv
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "tools" / "n02_u1_r2_binding_stage.py"
VERIFY = ROOT / "tools" / "n02_u1_r2_binding_verify.py"

def run(tool, *args, rc=0):
    p = subprocess.run([sys.executable, str(tool), *map(str, args)],
                       capture_output=True, text=True)
    if p.returncode != rc:
        raise AssertionError(
            f"{tool.name} exit={p.returncode} expected={rc}\n"
            + p.stdout + "\n" + p.stderr
        )
    return p

def make_names(path):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["实体ID", "类别", "简体中文定名"])
        for i in range(1392):
            w.writerow([f"ENTITY:{i:04d}", "PERSON" if i%2 else "UNIT",
                        f"合成实体{i}"])

def make_bindings(path, *, bad=None):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["原始来源ID", "实体ID", "类别", "简体中文定名", "窗口"])
        for i in range(4857):
            ent = i % 1392
            sid = f"SSF:NAME:{i:06d}" if i%2 else f"SSFF:NAME:{i:06d}"
            cn = f"合成实体{ent}"
            if bad == "duplicate" and i == 4856:
                sid = "SSFF:NAME:000000"
            if bad == "unbound" and i == 4856:
                ent = 99999
            if bad == "wrong_name" and i == 4856:
                cn = "错误的合成名"
            if bad == "bad_source" and i == 4856:
                sid = sid + " "
            typ = "PERSON" if ent % 2 else "UNIT"
            if bad == "wrong_type" and i == 4856:
                typ = "PERSON" if typ == "UNIT" else "UNIT"
            w.writerow([sid, f"ENTITY:{ent:04d}", typ, cn, "测试字段"])

def stage_args(names, bindings, out, receipt):
    return ("--names", names, "--bindings", bindings,
            "--out", out, "--receipt", receipt)

def verify_args(names, bindings, staged, report):
    return ("--names", names, "--bindings", bindings,
            "--stage", staged, "--report", report)

def main():
    with tempfile.TemporaryDirectory() as t:
        folder = Path(t)
        names = folder / "r2_names.tsv"
        mappings = folder / "r2_bindings.tsv"
        target = folder / "r2_stage.sqlite"
        receipt = folder / "receipt.json"
        make_names(names)
        make_bindings(mappings)
        run(STAGE, *stage_args(names, mappings, target, receipt))
        summary = json.loads(receipt.read_text(encoding="utf-8"))
        assert summary["status"] == "STAGED_NOT_N02_U1_PASS"
        assert summary["entities"] == 1392
        assert summary["source_bindings"] == 4857
        run(VERIFY, *verify_args(
            names, mappings, target, folder / "verify_ok.json"))
        checks = json.loads((folder/"verify_ok.json").read_text(encoding="utf-8"))
        assert checks["status"] == "VERIFIED_STAGING_NOT_N02_U1_PASS"
        assert checks["passed"]
        assert all(x["pass"] for x in checks["checks"].values())

        # Valid FK but silently altered mapping must fail independently.
        with sqlite3.connect(target) as db:
            db.execute(
                "UPDATE R2_SOURCE_BINDING SET entity_id='ENTITY:0300' "
                "WHERE original_source_id='SSFF:NAME:000000'")
        bad_sql = folder / "verify_database_tamper.json"
        run(VERIFY, *verify_args(names, mappings, target, bad_sql), rc=2)
        x = json.loads(bad_sql.read_text(encoding="utf-8"))
        assert not x["checks"]["source_binding_rows_exact"]["pass"]
        assert x["status"] == "BLOCKED_STAGING"

        # Repair DB from original staged snapshot by rebuilding on a new path.
        stage2 = folder / "stage2.sqlite"
        receipt2 = folder / "receipt2.json"
        run(STAGE, *stage_args(names, mappings, stage2, receipt2))
        # Source file changes after build must be rejected (SHA and rows).
        with mappings.open("a", encoding="utf-8") as f:
            f.write("\n")
        tamper_file_report = folder / "verify_source_tamper.json"
        run(VERIFY, *verify_args(
            names, mappings, stage2, tamper_file_report), rc=2)
        x = json.loads(tamper_file_report.read_text(encoding="utf-8"))
        assert not x["checks"]["input_receipts_exact"]["pass"]

        # Read-only inputs and output overwrite protection.
        try:
            run(STAGE, *stage_args(names, mappings, stage2, receipt2), rc=0)
            raise AssertionError("overwriting should be refused")
        except AssertionError as e:
            if "overwriting should" in str(e):
                raise
        # Independent negative input fixtures: stage must refuse and leave no DB.
        for case in ("duplicate", "unbound", "wrong_name", "wrong_type", "bad_source")
            b = folder / f"bindings_{case}.tsv"
            out = folder / f"rejected_{case}.sqlite"
            rcpt = folder / f"rejected_{case}.json"
            make_bindings(b, bad=case)
            failed = subprocess.run(
                [sys.executable, str(STAGE),
                 *map(str, stage_args(names, b, out, rcpt))],
                capture_output=True, text=True)
            assert failed.returncode != 0, (case, failed.stdout, failed.stderr)
            assert not out.exists() and not rcpt.exists(), case
        # Hash pin mismatch rejects a file without a partially published result.
        out = folder / "wrong_pin.sqlite"
        rcpt = folder / "wrong_pin.json"
        p = subprocess.run(
            [sys.executable, str(STAGE),
             *map(str, stage_args(names, mappings, out, rcpt)),
             "--expected-bindings-sha256", "0"*64],
            capture_output=True, text=True)
        assert p.returncode != 0 and not out.exists() and not rcpt.exists()
        print("N02-U1 R2 4,857 synthetic binding identities: PASS")
        print("Tampered DB, tampered source, duplicate/missing identities, "
              "wrong name, unsafe key and wrong hash pin: REJECTED")
        print("Production source import and N03 callsite verification: NOT RUN")

if __name__ == "__main__":
    main()
