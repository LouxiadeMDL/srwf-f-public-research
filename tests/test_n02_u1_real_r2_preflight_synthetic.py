#!/usr/bin/env python3
"""Synthetic formal-DB reconciliation, not production R2 approval."""
from argparse import Namespace
import sqlite3
from pathlib import Path
import sys
import tempfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from n02_u1_real_r2_preflight import reconcile, inspect_archive

def main():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        formal=root/"formal.sqlite"
        stage=root/"stage.sqlite"
        out=root/"out"
        out.mkdir()
        with sqlite3.connect(formal) as db:
            db.executescript("""
            CREATE TABLE source_record(source_id TEXT PRIMARY KEY);
            CREATE TABLE r2_source_binding(original_source_id TEXT PRIMARY KEY, entity_id TEXT);
            CREATE TABLE formal_acceptance(id INTEGER PRIMARY KEY);
            """)
            db.executemany("INSERT INTO source_record VALUES (?)",
                           ((f"SSF_SYN_{i:06d}",) for i in range(90099)))
            db.executemany("INSERT INTO r2_source_binding VALUES (?,?)",
                           ((f"SSF_SYN_{i:06d}",f"ENT_{i%1392:04d}")
                            for i in range(4857)))
            db.executemany("INSERT INTO formal_acceptance VALUES (?)",
                           ((i,) for i in range(1556)))
        with sqlite3.connect(stage) as db:
            db.execute("""CREATE TABLE R2_SOURCE_BINDING(
                        original_source_id TEXT,entity_id TEXT,canonical_cn TEXT)""")
            db.executemany("INSERT INTO R2_SOURCE_BINDING VALUES (?,?,?)",
                           ((f"SSF_SYN_{i:06d}",f"ENT_{i%1392:04d}",
                             f"合成实体{i%1392}") for i in range(4857)))
        args=Namespace(source_table=None,source_column=None,
                       binding_table=None,binding_source_column=None)
        r=reconcile(formal,stage,out,args)
        assert r["status"]=="REAL_R2_TO_FORMAL_BINDING_PASS_PENDING_OTHER_U1",r
        assert r["checks"]["source_identity"]["pass"],r
        assert r["checks"]["binding_identity"]["pass"],r
        assert r["checks"]["speed3_acceptance_count"]["pass"],r
        with sqlite3.connect(formal) as db:
            db.execute("""UPDATE r2_source_binding SET entity_id='WRONG_ENTITY'
                       WHERE original_source_id='SSF_SYN_000000'""")
        out2=root/"out2";out2.mkdir()
        r=reconcile(formal,stage,out2,args)
        assert r["status"]=="REAL_R2_PREFLIGHT_PARTIAL_OR_BLOCKED",r
        assert r["checks"]["binding_identity"]["conflict"]==1,r
        args.binding_source_column="DOES_NOT_EXIST"
        out3=root/"out3";out3.mkdir()
        r=reconcile(formal,stage,out3,args)
        assert not r["checks"]["binding_identity"]["pass"],r
        assert r["status"]!="REAL_R2_TO_FORMAL_BINDING_PASS_PENDING_OTHER_U1"
        args.binding_source_column=None
        with sqlite3.connect(formal) as db:
            db.execute("DELETE FROM source_record WHERE source_id='SSF_SYN_090098'")
        args.source_table="source_record"
        out4=root/"out4";out4.mkdir()
        r=reconcile(formal,stage,out4,args)
        assert not r["checks"]["source_identity"]["pass"],r
        # Private R2 pinned original must not accept synthetic substitute data.
        fakezip=root/"fake_r2.zip"
        with zipfile.ZipFile(fakezip,"w") as z:
            z.writestr("统一简体中文名称.tsv","synthetic data")
        try:
            inspect_archive(fakezip,root)
        except ValueError as ex:
            assert "SHA-256 mismatch" in str(ex)
        else:
            raise AssertionError("Unpinned synthetic ZIP was accepted")
        print("N02-U1 formal 90099/4857/1556 synthetic reconciliation PASS")
        print("Wrong identity, invalid explicit schema, missing 90099 source, "
              "and fake R2 ZIP were rejected.")
        print("Real user-local formal SQLite execution: NOT RUN")

if __name__=="__main__":
    main()
