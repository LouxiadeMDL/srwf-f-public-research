#!/usr/bin/env python3
"""N02-U1: real private R2 ZIP / formal SQLite preflight. Python 3.10+, stdlib.

NO writes to input SQLite, ISO, BIN, CUE or N08/N09 manuscripts.
Result is a new staging SQLite + independent report + source/version diffs.
HOLD is not PASS. Never publish private results to public CI/GitHub.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import zipfile

EXPECTED_ZIP_SHA = "1f4f99dd1271dd64c149d283624cfa6c5404f260372f124267c36c0f6da17eb7"
EXPECTED_MEMBERS = {
    "统一简体中文名称.tsv": "ea5bdc2a6e1557d149247e1b37a7464f27eb88126d1a91face16933af09de693",
    "工程来源定名绑定.tsv": "459bbb24db91e97b313e20ce99a3490dd93f430df78d15208c414046bf1d1c18",
}
SRC_ALIASES = ("source_id", "original_source_id", "source_record_id", "源ID", "原始来源ID")
ENT_ALIASES = ("entity_id", "canonical_entity_id", "实体ID")
REL_WORDS = ("relation", "edge", "xref", "call", "storage", "relation")
ACC_WORDS = ("acceptance", "验收")
ROOT = Path(__file__).resolve().parent

def file_sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()

def quoted(name):
    return '"' + name.replace('"', '""') + '"'

def member_data(z, name):
    matches = [m for m in z.infolist()
               if not m.is_dir() and m.filename.rsplit("/", 1)[-1] == name]
    if len(matches) != 1:
        raise ValueError(f"R2 ZIP expected one {name!r}, found {len(matches)}")
    m = matches[0]
    if m.file_size > 8_000_000:
        raise ValueError("Unexpected oversized R2 member")
    content = z.read(m)  # zipfile checks per-file CRC32
    if len(content) != m.file_size:
        raise ValueError(f"R2 member length mismatch: {name}")
    return content

def parse_tsv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        hdr = reader.fieldnames
        if hdr is None or len(set(hdr)) != len(hdr):
            raise ValueError("Bad R2 TSV headers")
        rows = list(reader)
        if any(None in row or any(v is None for v in row.values()) for row in rows):
            raise ValueError("Bad R2 TSV column count")
    return hdr, rows

def inspect_archive(archive, work):
    if file_sha(archive) != EXPECTED_ZIP_SHA:
        raise ValueError("R2 ZIP SHA-256 mismatch; stop rather than silently using another R2")
    with zipfile.ZipFile(archive, "r") as z:
        corrupt = z.testzip()
        if corrupt:
            raise ValueError("Corrupt R2 ZIP member: " + corrupt)
        manifest = member_data(z, "SHA256SUMS.txt").decode("utf-8")
        expected_in_manifest = {}
        for line in manifest.splitlines():
            if line.strip():
                digest, name = line.split("  ", 1)
                expected_in_manifest[name] = digest
        for name, pinned in EXPECTED_MEMBERS.items():
            if expected_in_manifest.get(name) != pinned:
                raise ValueError("R2 ZIP embedded manifest mismatch: " + name)
            path = work / name
            path.write_bytes(member_data(z, name))
            if file_sha(path) != pinned:
                raise ValueError("R2 ZIP member SHA mismatch: " + name)
        receipt = json.loads(member_data(z, "检查结果.json").decode("utf-8"))
    if (receipt.get("unique_entity_ids") != 1392
            or receipt.get("source_binding_count") != 4857
            or receipt.get("final_tsv_sha256") != EXPECTED_MEMBERS["统一简体中文名称.tsv"]
            or receipt.get("binding_tsv_sha256") != EXPECTED_MEMBERS["工程来源定名绑定.tsv"]):
        raise ValueError("R2 ZIP receipt contradicts source files")
    return work / "统一简体中文名称.tsv", work / "工程来源定名绑定.tsv"

def audit_subprocess(script, args):
    r = subprocess.run([sys.executable, str(ROOT/script), *map(str, args)],
                       text=True, capture_output=True)
    if r.returncode:
        raise RuntimeError(f"{script} failed rc={r.returncode}\n" + r.stderr[-4500:])
    return r.stdout[-1000:]

def choose_table(db, tables, *, kind, requested=None, column=None, count=None):
    """Only select when unequivocal; never infer join from equal row counts alone."""
    keys = SRC_ALIASES if kind == "source" else SRC_ALIASES
    candidates = []
    for table in tables:
        if table.startswith("sqlite_"):
            continue
        cols = [r[1] for r in db.execute(f"PRAGMA table_info({quoted(table)})")]
        # An explicit column is authoritative; never fall back silently.
        src = (column if column in cols else None) if column else next(
            (x for x in keys if x in cols), None)
        ent = next((x for x in ENT_ALIASES if x in cols), None)
        if kind == "binding" and not ent:
            continue
        if not src:
            continue
        if requested and table != requested:
            continue
        # Count only plausible tables; pinning the expected number is not proof
        n = db.execute(f"SELECT count(*) FROM {quoted(table)}").fetchone()[0]
        candidates.append({"table":table,"source_col":src,
                           "entity_col":ent,"rows":n})
    eligible = [c for c in candidates if c["rows"] == count]
    if requested:
        if len(candidates) != 1:
            return None, candidates
        return candidates[0], candidates
    # A row count alone is insufficient. Restrict automatic discovery by name.
    words = ("source", "原始", "来源") if kind == "source" else ("binding", "name_map", "绑定")
    favored = [c for c in eligible if any(w in c["table"].lower() for w in words)]
    return (favored[0] if len(favored) == 1 else None), candidates

def write_rows(path, columns, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(columns)
        writer.writerows(rows)

def reconcile(formal, staged, out, args):
    report = {"db":formal.name,"bytes":formal.stat().st_size,
              "sha256":file_sha(formal),
              "read_only":True,"checks":{},"schema_candidates":{},
              "notes":["A source-to-entity binding is not a consumer/callsite proof",
                       "N09 R2 P045 392 HOLD is historical; Speed3 acceptance is separate"]}
    with sqlite3.connect(formal.resolve().as_uri()+"?mode=ro",uri=True) as db:
        db.execute("PRAGMA query_only=ON")
        report["checks"]["integrity"] = db.execute("PRAGMA integrity_check").fetchone()[0]
        report["checks"]["foreign_keys"] = len(db.execute("PRAGMA foreign_key_check").fetchall())
        tables = [r[0] for r in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        src,sc = choose_table(db,tables,kind="source",
                              requested=args.source_table or "TEXT_SOURCE",column=args.source_column,
                              count=90099)
        bind,bc = choose_table(db,tables,kind="binding",
                               requested=args.binding_table or "n08_name_binding",column=args.binding_source_column,
                               count=4857)
        report["schema_candidates"]["source"] = sc
        report["schema_candidates"]["binding"] = bc
        with sqlite3.connect(staged.resolve().as_uri()+"?mode=ro",uri=True) as st:
            expected = {
                sid: (eid, cn, kind) for sid, eid, cn, kind in st.execute(
                    "SELECT b.original_source_id,b.entity_id,b.canonical_cn,e.entity_type "
                    "FROM R2_SOURCE_BINDING b JOIN R2_ENTITY e USING(entity_id)")
            }
        if src:
            sids = {str(r[0]) for r in db.execute(
                f"SELECT {quoted(src['source_col'])} FROM {quoted(src['table'])}")}
            missing = sorted(set(expected)-sids)
            write_rows(out/"SOURCE_IDS_MISSING.tsv",("original_source_id",),
                       ((sid,) for sid in missing))
            report["checks"]["source_identity"] = {
                "table":src["table"],"column":src["source_col"],
                "real_source_rows":src["rows"],"unique_source_ids":len(sids),
                "r2_checked":len(expected),"missing_count":len(missing),
                "pass":len(missing)==0 and len(sids)==src["rows"]
                       and src["rows"]==90099}
        else:
            report["checks"]["source_identity"] = {
                "pass":False,"reason":"HOLD_SCHEMA: explicit/unique 90,099 source table not established"}
        if bind:
            # UETS catalog/schema.sql is authoritative. It defines all four
            # identity fields, not merely source_id/entity_id.
            columns = {r[1] for r in db.execute(
                f"PRAGMA table_info({quoted(bind['table'])})")}
            required = {bind["source_col"],bind["entity_col"],
                        "name_kind","approved_cn"}
            if not required.issubset(columns):
                report["checks"]["binding_identity"] = {
                    "pass":False,"reason":"HOLD_SCHEMA: actual name_kind/approved_cn absent",
                    "missing_columns":sorted(required-columns)}
            else:
                actual = {}
                for sid,eid,kind,cn in db.execute(
                    f"SELECT {quoted(bind['source_col'])},{quoted(bind['entity_col'])},"
                    f"name_kind,approved_cn FROM {quoted(bind['table'])}"):
                    actual.setdefault(str(sid),[]).append(
                        (str(eid),str(kind),str(cn)))
                unmatched,entity_conflicts,kind_conflicts,cn_conflicts,duplicates = (
                    [],[],[],[],[])
                for sid,(eid,cn,kind) in expected.items():
                    got=actual.get(sid)
                    if not got:
                        unmatched.append((sid,eid,kind,cn))
                    elif len(got)!=1:
                        duplicates.append((sid,eid,";".join(str(v) for v in got)))
                    else:
                        observed_eid,observed_kind,observed_cn=got[0]
                        if observed_eid!=eid:
                            entity_conflicts.append((sid,eid,observed_eid))
                        if observed_kind!=kind:
                            kind_conflicts.append((sid,kind,observed_kind))
                        if observed_cn!=cn:
                            cn_conflicts.append((sid,cn,observed_cn))
                write_rows(out/"BINDINGS_MISSING.tsv",
                           ("source_id","entity_id","kind","canonical_cn"),unmatched)
                write_rows(out/"BINDINGS_CONFLICT.tsv",
                           ("source_id","r2_entity_id","formal_entity_id"),
                           entity_conflicts)
                write_rows(out/"BINDINGS_CATEGORY_CONFLICT.tsv",
                           ("source_id","r2_category","formal_category"),kind_conflicts)
                write_rows(out/"BINDINGS_CN_CONFLICT.tsv",
                           ("source_id","r2_canonical_cn","formal_approved_cn"),cn_conflicts)
                write_rows(out/"BINDINGS_DUPLICATE.tsv",
                           ("source_id","r2_entity_id","formal_entries"),duplicates)
                extra=sorted(set(actual)-set(expected))
                write_rows(out/"FORMAL_BINDINGS_EXTRA.tsv",("source_id",),
                           ((sid,) for sid in extra))
                report["checks"]["binding_identity"]={
                    "table":bind["table"],"column":bind["source_col"],
                    "formal_bindings_rows":bind["rows"],
                    "missing":len(unmatched),"entity_conflict":len(entity_conflicts),
                    "category_conflict":len(kind_conflicts),
                    "canonical_cn_conflict":len(cn_conflicts),
                    "duplicate":len(duplicates),"extra":len(extra),
                    "exact_four_field_matches":(
                        len(expected)-len(unmatched)-len(duplicates)-
                        len({sid for sid,_,_ in entity_conflicts+kind_conflicts+
                             cn_conflicts})),
                    "pass":bind["rows"]==4857
                           and not(unmatched or entity_conflicts or kind_conflicts
                                   or cn_conflicts or duplicates or extra)}
                # N08 R2 canonical name is a semantic target; source.cn_final
                # can have controlled per-field variants. Report, never replace.
                source_cols={r[1] for r in db.execute(
                    "PRAGMA table_info(TEXT_SOURCE)")}
                required_source={"source_id","cn_final","authoring_revision",
                                 "freeze_status"}
                if required_source.issubset(source_cols):
                    form_review=[]
                    for sid,actual_cn,revision,freeze in db.execute(
                        "SELECT s.source_id,s.cn_final,s.authoring_revision,"
                        "s.freeze_status FROM TEXT_SOURCE s "
                        "JOIN n08_name_binding b USING(source_id)"):
                        entry=expected.get(str(sid))
                        if entry and actual_cn!=entry[1]:
                            form_review.append((sid,entry[1],actual_cn,revision,freeze))
                    write_rows(out/"SOURCE_CN_FINAL_FORM_REVIEW.tsv",
                               ("source_id","r2_approved_cn","source_cn_final",
                                "authoring_revision","freeze_status"),
                               form_review)
                    report["checks"]["field_form_review"]={
                        "count":len(form_review),
                        "status":"REVIEW_LEGAL_VARIANT_NOT_AUTOMATIC_ERROR",
                        "writes_to_formal_database":0}
                else:
                    report["checks"]["field_form_review"]={
                        "count":None,"status":"HOLD_SCHEMA_FIELD_FORM",
                        "missing_columns":sorted(required_source-source_cols)}
        else:
            report["checks"]["binding_identity"]={
                "pass":False,"reason":"HOLD_SCHEMA: n08_name_binding not established"}
        # Use exact source-schema table names. A count alone is not natural
        # gameplay evidence; only validates a formal ledger's record inventory.
        if "TEXT_CALLSITE" in tables:
            callsites=db.execute("SELECT count(*) FROM TEXT_CALLSITE").fetchone()[0]
        else:
            callsites=None
        report["checks"]["registered_callsite_count"]={
            "pass":callsites==128513,
            "rows":callsites,"evidence_status":"REGISTERED_RELATIONS_NOT_RUNTIME"}
        if "TEXT_ACCEPTANCE" in tables:
            acceptance=db.execute("SELECT count(*) FROM TEXT_ACCEPTANCE").fetchone()[0]
        else:
            acceptance=None
        report["checks"]["speed3_acceptance_count"]={
            "pass":acceptance==1556,"table":"TEXT_ACCEPTANCE"
                   if acceptance is not None else None,
            "row_count":acceptance,
            "scope":"LEDGER_COUNT_ONLY_NOT_RUNTIME_REEXECUTION"}
        report["schema_candidates"]["speed3_acceptance"] = (
            [{"table":"TEXT_ACCEPTANCE","rows":acceptance}]
            if acceptance is not None else [])
    report["status"] = (
        "REAL_R2_TO_FORMAL_BINDING_PASS_PENDING_OTHER_U1"
        if report["checks"]["integrity"]=="ok"
        and report["checks"]["foreign_keys"]==0
        and report["checks"]["source_identity"]["pass"]
        and report["checks"]["binding_identity"]["pass"]
        and report["checks"]["registered_callsite_count"]["pass"]
        and report["checks"]["speed3_acceptance_count"]["pass"]
        else "REAL_R2_PREFLIGHT_PARTIAL_OR_BLOCKED"
    )
    return report

SPEED3_MERGE_SHA256 = "2c86c086adcc8a6a10fc11fb4cb5344eb75f43fee2ff569a1c54ecf4ac526810"
SPEED3_ACCEPTANCE_TSV_SHA256 = "313f9c150118b60a98eba2411bc20cae26f03ce5311b7ca995a669ffbf5334c4"


def verify_speed3_seven(formal, merge, acceptance_tsv):
    """Independent seven-acceptance identity/evidence check, not runtime replay."""
    fields=("acceptance_id","revision","axis","outcome","chronology","evidence_sha256")
    if file_sha(acceptance_tsv) != SPEED3_ACCEPTANCE_TSV_SHA256:
        raise ValueError("Speed3 seven-acceptance TSV differs from pinned CONTENTS.json")
    with Path(acceptance_tsv).open("r", encoding="utf-8-sig", newline="") as fp:
        reader=csv.DictReader(fp, delimiter="\t")
        if not reader.fieldnames or not set(fields).issubset(reader.fieldnames):
            raise ValueError("Speed3 source TSV has missing acceptance/evidence columns")
        source_rows=list(reader)
        if len(source_rows)!=7 or len({r["acceptance_id"] for r in source_rows})!=7:
            raise ValueError("Speed3 acceptance TSV must have exactly seven unique IDs")
    incoming=merge.get("mapping")
    if not isinstance(incoming,list) or len(incoming)!=7:
        raise ValueError("Speed3 merge receipt missing its seven mapping rows")
    expected_map={r["acceptance_id"]:(r["revision"],bool(r["historical_only"]))
                  for r in incoming}
    if len(expected_map)!=7 or set(expected_map)!={r["acceptance_id"] for r in source_rows}:
        raise ValueError("Speed3 merge receipt and acceptance TSV disagree")
    if sum(not historical for _,historical in expected_map.values())!=6:
        raise ValueError("Speed3 expected six current plus one historical acceptance")
    with sqlite3.connect(Path(formal).resolve().as_uri()+"?mode=ro",uri=True) as db:
        db.execute("PRAGMA query_only=ON")
        if db.execute("SELECT count(*) FROM TEXT_ACCEPTANCE").fetchone()[0]!=1556:
            raise ValueError("Speed3 formal acceptance count is not 1,556")
        found={}
        for row in db.execute(
            "SELECT a.acceptance_id,a.revision,a.axis,a.outcome,a.chronology,"
            "f.sha256 FROM TEXT_ACCEPTANCE a "
            "JOIN evidence_file f ON a.evidence_id=f.evidence_id "
            "WHERE a.acceptance_id IN ("+",".join("?" for _ in source_rows)+")",
            [r["acceptance_id"] for r in source_rows]):
            found[row[0]]=row[1:]
    failed=[]
    for row in source_rows:
        key=row["acceptance_id"]
        requested=(row["revision"],row["axis"],row["outcome"],
                   row["chronology"],row["evidence_sha256"])
        observed=found.get(key)
        revision,historical=expected_map[key]
        if revision!=row["revision"]:
            failed.append({"acceptance_id":key,"problem":"RECEIPT_REVISION_MISMATCH"})
        if historical!=(row["outcome"]=="HISTORICAL_PASS"):
            failed.append({"acceptance_id":key,"problem":"HISTORY_SCOPE_MISMATCH"})
        if observed!=requested:
            failed.append({"acceptance_id":key,
                           "problem":"FORMAL_ACCEPTANCE_OR_EVIDENCE_MISMATCH",
                           "expected":requested, "observed":observed})
    return {"pass":not failed,"verified_rows":7-len({
                x["acceptance_id"] for x in failed}),
            "source_rows":len(source_rows),"historical_rows":1,
            "speed3_current_rows":6,"mismatches":failed,
            "evidence_status":"EXACT_DB_ROWS_NOT_RUNTIME_REEXECUTION"}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--r2-zip",required=True,help="Original 97,628-byte R2 ZIP")
    p.add_argument("--formal-db",required=True,help="Current formal SQLite (read-only)")
    p.add_argument("--out-dir",required=True,help="MUST NOT exist")
    p.add_argument("--source-table")
    p.add_argument("--source-column")
    p.add_argument("--binding-table")
    p.add_argument("--binding-source-column")
    p.add_argument("--expected-formal-db-sha256",
                   help="Optional pinned SHA-256 of known official formal DB")
    p.add_argument("--speed3-merge-receipt",
                   help="Optional UETS_SPEED3_FORMAL_MERGE.json")
    p.add_argument("--speed3-acceptance-tsv",
                   help="Optional pinned seven-row UETS_SPEED3_FORMAL_ACCEPTANCE.tsv")
    args=p.parse_args()
    archive,dbpath,out=Path(args.r2_zip),Path(args.formal_db),Path(args.out_dir)
    if not archive.is_file() or not dbpath.is_file():
        raise FileNotFoundError("R2 archive and formal SQLite must both exist")
    if out.exists() or out.resolve() in (archive.resolve(),dbpath.resolve()):
        raise FileExistsError("Refuse to overwrite or share output/input path")
    out.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="n02_u1_real_r2_") as tmp:
        names,bindings=inspect_archive(archive,Path(tmp))
        staged=out/"N02_U1_R2_BINDINGS_STAGING.sqlite"
        report=out/"STAGING_RECEIPT.json"
        audit_subprocess("n02_u1_r2_binding_stage.py",[
            "--names",names,"--bindings",bindings,
            "--out",staged,"--receipt",report,
            "--expected-names-sha256",EXPECTED_MEMBERS["统一简体中文名称.tsv"],
            "--expected-bindings-sha256",EXPECTED_MEMBERS["工程来源定名绑定.tsv"],
        ])
        independent=out/"R2_INDEPENDENT_AUDIT.json"
        audit_subprocess("n02_u1_r2_binding_verify.py",[
            "--names",names,"--bindings",bindings,
            "--stage",staged,"--report",independent])
        recon=reconcile(dbpath,staged,out,args)
        if args.expected_formal_db_sha256:
            pin_ok = (recon["sha256"].lower() ==
                      args.expected_formal_db_sha256.lower())
            recon["checks"]["formal_sha256_pin"] = {
                "pass": pin_ok, "expected": args.expected_formal_db_sha256,
                "actual": recon["sha256"]}
            if not pin_ok:
                recon["status"] = "REAL_R2_PREFLIGHT_PARTIAL_OR_BLOCKED"
        if args.speed3_acceptance_tsv and not args.speed3_merge_receipt:
            raise ValueError("Speed3 acceptance TSV requires original merge receipt")
        if args.speed3_merge_receipt:
            if file_sha(Path(args.speed3_merge_receipt)) != SPEED3_MERGE_SHA256:
                raise ValueError("Speed3 merge receipt SHA-256 differs from pinned original")
            merged = json.loads(Path(args.speed3_merge_receipt).read_text(
                encoding="utf-8-sig"))
            merge_ok = (merged.get("status")=="PASS_FORMAL_MERGE"
                        and merged.get("total_acceptance_rows")==1556
                        and merged.get("conflicts")==0
                        and merged.get("database_sha256")==recon["sha256"]
                        and recon["checks"]["speed3_acceptance_count"]["pass"])
            recon["checks"]["speed3_formal_merge_receipt"]={
                "pass":merge_ok,"new_acceptance_rows":merged.get("inserted"),
                "total_acceptance_rows":merged.get("total_acceptance_rows"),
                "database_hash_matches":merged.get("database_sha256")==recon["sha256"]}
            if not merge_ok:
                recon["status"]="REAL_R2_PREFLIGHT_PARTIAL_OR_BLOCKED"
            if args.speed3_acceptance_tsv:
                exact_seven = verify_speed3_seven(
                    dbpath,merged,Path(args.speed3_acceptance_tsv))
                recon["checks"]["speed3_seven_exact_evidence"] = exact_seven
                if not exact_seven["pass"]:
                    recon["status"]="REAL_R2_PREFLIGHT_PARTIAL_OR_BLOCKED"
            else:
                recon["checks"]["speed3_seven_exact_evidence"] = {
                    "pass":False,"status":"NOT_RUN_NO_SPEED3_SEVEN_TSV",
                    "note":"Summary receipt only; seven actual acceptance rows not separately checked"}
        recon["r2_archive"]={"filename":archive.name,"sha256":EXPECTED_ZIP_SHA,
                              "binding_rows":4857,"canonical_entities":1392}
        (out/"REAL_PREFLIGHT_STATUS.json").write_text(
            json.dumps(recon,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({"status":recon["status"],
                          "checks":recon["checks"],
                          "report":str(out/"REAL_PREFLIGHT_STATUS.json")},
                         ensure_ascii=False,indent=2))
        if recon["status"]!="REAL_R2_TO_FORMAL_BINDING_PASS_PENDING_OTHER_U1":
            raise SystemExit(2)

if __name__=="__main__":
    main()
