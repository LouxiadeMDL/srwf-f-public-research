#!/usr/bin/env python3
"""Synthetic 90,099/4,857/128,513/1,556 official UETS schema regression.

This does NOT validate the user's private 1.48 GB formal DB or any game runtime.
"""
from argparse import Namespace
import sqlite3
from pathlib import Path
import sys
import tempfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from n02_u1_real_r2_preflight import reconcile, inspect_archive

def kind(i):
    return ("PERSON","UNIT","WEAPON")[i%3]

def main():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        formal=root/"formal.sqlite"
        staged=root/"stage.sqlite"
        out=root/"out"; out.mkdir()
        with sqlite3.connect(formal) as db:
            db.executescript("""
            CREATE TABLE TEXT_SOURCE (
                source_id TEXT PRIMARY KEY, cn_final TEXT,
                authoring_revision TEXT NOT NULL, freeze_status TEXT NOT NULL);
            CREATE TABLE n08_name_binding (
                source_id TEXT PRIMARY KEY, entity_id TEXT NOT NULL,
                name_kind TEXT NOT NULL, approved_cn TEXT NOT NULL);
            CREATE TABLE TEXT_CALLSITE (callsite_id TEXT PRIMARY KEY);
            CREATE TABLE TEXT_ACCEPTANCE (acceptance_id TEXT PRIMARY KEY);
            """)
            db.executemany("INSERT INTO TEXT_SOURCE VALUES(?,?,?,?)",
                           ((f"SSF_SYN_{i:06d}",
                             f"合成实体{i%1392}" if i<4857 else "其他原文",
                             "SYNTHETIC", "NONE") for i in range(90099)))
            db.executemany("INSERT INTO n08_name_binding VALUES(?,?,?,?)",
                           ((f"SSF_SYN_{i:06d}",f"ENT_{i%1392:04d}",
                             kind(i),f"合成实体{i%1392}") for i in range(4857)))
            db.executemany("INSERT INTO TEXT_CALLSITE VALUES (?)",
                           ((f"CALL:{i:06d}",) for i in range(128513)))
            db.executemany("INSERT INTO TEXT_ACCEPTANCE VALUES (?)",
                           ((f"LEDGER:{i:06d}",) for i in range(1556)))
        with sqlite3.connect(staged) as db:
            db.execute("""CREATE TABLE R2_ENTITY(
                entity_id TEXT PRIMARY KEY,entity_type TEXT,canonical_cn TEXT)""")
            db.execute("""CREATE TABLE R2_SOURCE_BINDING(
                original_source_id TEXT PRIMARY KEY,entity_id TEXT,canonical_cn TEXT)""")
            db.executemany("INSERT INTO R2_ENTITY VALUES (?,?,?)",
                           ((f"ENT_{i:04d}",kind(i),f"合成实体{i}")
                            for i in range(1392)))
            db.executemany("INSERT INTO R2_SOURCE_BINDING VALUES (?,?,?)",
                           ((f"SSF_SYN_{i:06d}",f"ENT_{i%1392:04d}",
                             f"合成实体{i%1392}") for i in range(4857)))

        args=Namespace(source_table=None,source_column=None,
                       binding_table=None,binding_source_column=None)
        r=reconcile(formal,staged,out,args)
        assert r["status"]=="REAL_R2_TO_FORMAL_BINDING_PASS_PENDING_OTHER_U1",r
        assert r["checks"]["source_identity"]["pass"],r
        assert r["checks"]["binding_identity"]["pass"],r
        assert r["checks"]["binding_identity"]["exact_four_field_matches"]==4857,r
        assert r["checks"]["registered_callsite_count"]["pass"],r
        assert r["checks"]["speed3_acceptance_count"]["pass"],r
        assert r["checks"]["field_form_review"]["count"]==0,r

        # Bad entity on a valid original ID must fail the four-field gate.
        with sqlite3.connect(formal) as db:
            db.execute("UPDATE n08_name_binding SET entity_id='WRONG_ENTITY' "
                       "WHERE source_id='SSF_SYN_000000'")
        out2=root/"out2";out2.mkdir()
        r=reconcile(formal,staged,out2,args)
        assert r["status"]=="REAL_R2_PREFLIGHT_PARTIAL_OR_BLOCKED",r
        assert r["checks"]["binding_identity"]["entity_conflict"]==1,r

        # A wrong approved Chinese name or category is not an allowed alias.
        with sqlite3.connect(formal) as db:
            db.execute("UPDATE n08_name_binding SET approved_cn='错译' "
                       "WHERE source_id='SSF_SYN_000001'")
            db.execute("UPDATE n08_name_binding SET name_kind='WRONG_KIND' "
                       "WHERE source_id='SSF_SYN_000002'")
        out3=root/"out3";out3.mkdir()
        r=reconcile(formal,staged,out3,args)
        assert r["checks"]["binding_identity"]["canonical_cn_conflict"]==1,r
        assert r["checks"]["binding_identity"]["category_conflict"]==1,r

        # Dynamic/display form differs from R2; must be REVIEW, not rewritten.
        with sqlite3.connect(formal) as db:
            db.execute("UPDATE TEXT_SOURCE SET cn_final='合法短名' "
                       "WHERE source_id='SSF_SYN_000003'")
        out4=root/"out4";out4.mkdir()
        r=reconcile(formal,staged,out4,args)
        assert r["checks"]["field_form_review"]["count"]==1,r
        assert (out4/"SOURCE_CN_FINAL_FORM_REVIEW.tsv").is_file()
        assert r["status"]=="REAL_R2_PREFLIGHT_PARTIAL_OR_BLOCKED"  # other conflicts persist

        # Reject a requested column that isn't actually in official table.
        args.binding_source_column="DOES_NOT_EXIST"
        out5=root/"out5";out5.mkdir()
        r=reconcile(formal,staged,out5,args)
        assert not r["checks"]["binding_identity"]["pass"],r
        args.binding_source_column=None

        with sqlite3.connect(formal) as db:
            db.execute("DELETE FROM TEXT_SOURCE WHERE source_id='SSF_SYN_090098'")
        args.source_table="TEXT_SOURCE"
        out6=root/"out6";out6.mkdir()
        r=reconcile(formal,staged,out6,args)
        assert not r["checks"]["source_identity"]["pass"],r
        args.source_table=None

        with sqlite3.connect(formal) as db:
            db.execute("DELETE FROM TEXT_CALLSITE WHERE callsite_id='CALL:128512'")
            db.execute("DELETE FROM TEXT_ACCEPTANCE WHERE acceptance_id='LEDGER:001555'")
        out7=root/"out7";out7.mkdir()
        r=reconcile(formal,staged,out7,args)
        assert not r["checks"]["registered_callsite_count"]["pass"],r
        assert not r["checks"]["speed3_acceptance_count"]["pass"],r

        fake_zip=root/"fake_r2.zip"
        with zipfile.ZipFile(fake_zip,"w") as z:
            z.writestr("统一简体中文名称.tsv","synthetic")
        try:
            inspect_archive(fake_zip,root)
        except ValueError as ex:
            assert "SHA-256 mismatch" in str(ex)
        else:
            raise AssertionError("Synthetic ZIP bypassed pinned original SHA")
        print("N02-U1 90099 / 4857 / 128513 / 1556 synthetic UETS audit PASS")
        print("Wrong entity, category, approved CN, missing callsite/acceptance,"
              " invalid column and wrong archive: REJECTED")
        print("Real formal SQLite and game runtime: NOT RUN.")

if __name__=="__main__":
    main()
