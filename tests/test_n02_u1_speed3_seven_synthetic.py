#!/usr/bin/env python3
"""Synthetic checks for exact seven-row Speed3 formal ledger reconciliation.

No private game files, original acceptance TSV, or personal SQLite.
"""
import csv
import hashlib
from pathlib import Path
import sqlite3
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import n02_u1_real_r2_preflight as preflight

def make(tmp):
    formal=tmp/"formal.sqlite"
    evidence_ids=[f"EV:{i}" for i in range(7)]
    realids=[f"UETS_LEDGER:P045-S3-0{i}" for i in range(1,7)]
    ids=realids+["UETS_LEDGER:P045-S2-HISTORY"]
    rows=[]
    merge=[]
    for i,sid in enumerate(ids):
        history=(i==6)
        rev=("SSF_N09_R2_P045_UETS_SPEED2" if history else
             "SSF_N09_R2_P045_UETS_SPEED3")
        axis="GLYPH" if history else ("WINDOW" if i<3 else "COLD_READ")
        outcome="HISTORICAL_PASS" if history else "PASS"
        chronology="INHERITED_SPEED2_FULL_REGRESSION" if history else "SPEED3_VERIFIED_RECEIPT_MERGE"
        digest=hashlib.sha256(f"synthetic-evidence-{i}".encode()).hexdigest()
        rows.append({"delta_id":f"SYN_{i}","acceptance_id":sid,"revision":rev,
                     "axis":axis,"outcome":outcome,"chronology":chronology,
                     "evidence_sha256":digest})
        merge.append({"acceptance_id":sid,"revision":rev,"historical_only":history})
    with sqlite3.connect(formal) as db:
        db.executescript("""
          CREATE TABLE evidence_file(evidence_id TEXT PRIMARY KEY,sha256 TEXT);
          CREATE TABLE TEXT_ACCEPTANCE(
              acceptance_id TEXT PRIMARY KEY,revision TEXT,axis TEXT,
              outcome TEXT,chronology TEXT,evidence_id TEXT);
        """)
        db.execute("INSERT INTO evidence_file VALUES(?,?)",("EV:DUMMY","f"*64))
        db.executemany("INSERT INTO TEXT_ACCEPTANCE VALUES (?,?,?,?,?,?)",
                       ((f"ARCHIVE:{i:04d}","OLD","STATIC","PASS","OLD","EV:DUMMY")
                        for i in range(1549)))
        db.executemany("INSERT INTO evidence_file VALUES (?,?)",
                       ((eid,row["evidence_sha256"])
                        for eid,row in zip(evidence_ids,rows)))
        db.executemany("INSERT INTO TEXT_ACCEPTANCE VALUES(?,?,?,?,?,?)",
                       ((row["acceptance_id"],row["revision"],row["axis"],
                         row["outcome"],row["chronology"],eid)
                        for row,eid in zip(rows,evidence_ids)))
    tsv=tmp/"seven.tsv"
    with tsv.open("w",encoding="utf-8-sig",newline="") as fp:
        w=csv.DictWriter(fp,fieldnames=list(rows[0]),delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    preflight.SPEED3_ACCEPTANCE_TSV_SHA256=preflight.file_sha(tsv)
    return formal,tsv,merge,rows

def main():
    with tempfile.TemporaryDirectory() as t:
        tmp=Path(t)
        formal,tsv,mapping,rows=make(tmp)
        merged={"mapping":mapping}
        report=preflight.verify_speed3_seven(formal,merged,tsv)
        assert report["pass"] and report["verified_rows"]==7,report
        assert report["historical_rows"]==1
        with sqlite3.connect(formal) as db:
            db.execute("UPDATE TEXT_ACCEPTANCE SET outcome='FAIL' WHERE acceptance_id=?",
                       (rows[0]["acceptance_id"],))
        report=preflight.verify_speed3_seven(formal,merged,tsv)
        assert not report["pass"] and report["verified_rows"]==6,report
        with sqlite3.connect(formal) as db:
            db.execute("UPDATE TEXT_ACCEPTANCE SET outcome='PASS' WHERE acceptance_id=?",
                       (rows[0]["acceptance_id"],))
            db.execute("UPDATE evidence_file SET sha256=? WHERE evidence_id=?",
                       ("0"*64,"EV:1"))
        report=preflight.verify_speed3_seven(formal,merged,tsv)
        assert not report["pass"] and report["verified_rows"]==6,report
        bad_merge={"mapping":[dict(x) for x in mapping]}
        bad_merge["mapping"][6]["historical_only"]=False
        try:
            preflight.verify_speed3_seven(formal,bad_merge,tsv)
        except ValueError:
            pass
        else:
            raise AssertionError("Historical/Speed3 revision count accepted incorrectly")
        with tsv.open("a",encoding="utf-8") as fp:
            fp.write("\n")
        try:
            preflight.verify_speed3_seven(formal,merged,tsv)
        except ValueError:
            pass
        else:
            raise AssertionError("Changed seven-row source SHA accepted")
        print("N02-U1 Speed3 1,556-row synthetic evidence/identity check PASS")
        print("Swapped outcome, evidence digest, historical flag and TSV SHA: REJECTED")
        print("No actual private formal SQLite in CI.")

if __name__=="__main__":
    main()
