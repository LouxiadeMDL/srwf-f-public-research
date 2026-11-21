#!/usr/bin/env python3
# N02-U1 public-safe offline baseline and guide-layer builder.
# Does not distribute or modify source games, scans, OCR, or private corpora.
# Requires Python 3.10+; standard library only.
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS U1_BUILD_INPUT (
  role TEXT PRIMARY KEY, path_hint TEXT NOT NULL,
  sha256 TEXT NOT NULL, size_bytes INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS CANONICAL_ENTITY (
  entity_id TEXT PRIMARY KEY, entity_type TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'R2_INHERITED'
);
CREATE TABLE IF NOT EXISTS CANONICAL_TERM (
  entity_id TEXT PRIMARY KEY REFERENCES CANONICAL_ENTITY(entity_id),
  canonical_cn TEXT NOT NULL CHECK(length(canonical_cn)>0),
  evidence_status TEXT NOT NULL DEFAULT 'R2_INHERITED',
  revision_scope TEXT NOT NULL DEFAULT 'SSF_SSFF'
);
CREATE TABLE IF NOT EXISTS LEGAL_NAME_FORM (
  entity_id TEXT NOT NULL REFERENCES CANONICAL_ENTITY(entity_id),
  field_context TEXT NOT NULL, display_text TEXT NOT NULL,
  evidence_ref TEXT, status TEXT NOT NULL DEFAULT 'REQUIRES_REVIEW',
  PRIMARY KEY (entity_id,field_context,display_text)
);
CREATE TABLE IF NOT EXISTS SOURCE_REFERENCE (
  reference_id TEXT PRIMARY KEY, source_kind TEXT NOT NULL,
  version TEXT NOT NULL, relative_path TEXT,
  original_id TEXT, sha256 TEXT, status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS GUIDE_DOCUMENT (
  guide_key TEXT PRIMARY KEY, guide_version TEXT NOT NULL,
  source_id TEXT NOT NULL, title TEXT, pdf_sha256 TEXT,
  original_pages INTEGER, policy TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS GUIDE_PAGE (
  guide_key TEXT NOT NULL REFERENCES GUIDE_DOCUMENT(guide_key),
  page_id TEXT NOT NULL, page_number INTEGER NOT NULL,
  original_transcript TEXT NOT NULL, normalized_transcript TEXT NOT NULL,
  normalized_status TEXT NOT NULL DEFAULT 'IDENTITY_PENDING_ENTITY_BINDING',
  source_qa_state TEXT,
  PRIMARY KEY(guide_key,page_id)
);
CREATE TABLE IF NOT EXISTS GUIDE_TEXT_NORMALIZED (
  guide_key TEXT NOT NULL, line_id TEXT NOT NULL,
  page_id TEXT NOT NULL, page_number INTEGER, line_number INTEGER,
  original_text TEXT NOT NULL, normalized_text TEXT NOT NULL,
  decision TEXT NOT NULL DEFAULT 'NO_REWRITE_PENDING_IDENTITY',
  PRIMARY KEY(guide_key,line_id),
  FOREIGN KEY(guide_key,page_id) REFERENCES GUIDE_PAGE(guide_key,page_id)
);
CREATE TABLE IF NOT EXISTS TERM_OCCURRENCE (
  occurrence_id INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_id TEXT NOT NULL REFERENCES CANONICAL_ENTITY(entity_id),
  source_kind TEXT NOT NULL, source_record_id TEXT NOT NULL,
  guide_key TEXT, page_number INTEGER, field_context TEXT,
  evidence_status TEXT NOT NULL,
  UNIQUE(entity_id,source_kind,source_record_id,field_context)
);
CREATE TABLE IF NOT EXISTS TEXT_REVISION (
  revision_id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_kind TEXT NOT NULL, source_record_id TEXT NOT NULL,
  old_text TEXT NOT NULL, new_text TEXT NOT NULL,
  entity_id TEXT, justification TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'PENDING'
);
CREATE TABLE IF NOT EXISTS SOURCE_CALLSITE (
  evidence_key TEXT PRIMARY KEY, source_record_id TEXT,
  game TEXT NOT NULL, version_hash TEXT,
  resource TEXT, byte_offset TEXT, caller_kind TEXT,
  evidence_status TEXT NOT NULL,
  comments TEXT
);
CREATE TABLE IF NOT EXISTS QA_RESULT (
  qa_key TEXT PRIMARY KEY, status TEXT NOT NULL,
  observed TEXT NOT NULL, requirement TEXT NOT NULL,
  remarks TEXT
);
CREATE TABLE IF NOT EXISTS FF_GUIDE_QA_RESOLUTION (
  page_id TEXT NOT NULL, original_flag TEXT, resolution_status TEXT,
  information_status TEXT, exact_text_status TEXT, raw_json TEXT NOT NULL,
  PRIMARY KEY(page_id, original_flag)
);
CREATE TABLE IF NOT EXISTS FF_GUIDE_CROSSCHECK (
  fact_id TEXT PRIMARY KEY, page_id TEXT, raw_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_u1_occurrence_source
  ON TERM_OCCURRENCE(source_kind,source_record_id);
CREATE INDEX IF NOT EXISTS idx_u1_guide_page
  ON GUIDE_TEXT_NORMALIZED(guide_key,page_number);
"""
def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as fp:
        for block in iter(lambda:fp.read(8*1024*1024),b''):
            h.update(block)
    return h.hexdigest()

def ro(path):
    return sqlite3.connect(Path(path).absolute().as_uri()+'?mode=ro',uri=True)

def record_input(db,role,path):
    path=Path(path)
    db.execute("INSERT INTO U1_BUILD_INPUT VALUES(?,?,?,?)",
               (role,path.name,sha256(path),path.stat().st_size))

def check_db(path):
    with ro(path) as db:
        verdict=db.execute("PRAGMA quick_check").fetchone()[0]
        if verdict!='ok': raise ValueError(f"SQLite quick_check failed: {path}: {verdict}")
        return {name:int(db.execute('SELECT count(*) FROM "'+name+'"').fetchone()[0])
                for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '%_fts%'")}

def import_r2(db,path):
    with open(path,'r',encoding='utf-8-sig',newline='') as fp:
        rows=list(csv.DictReader(fp,delimiter='\t'))
    needed={'实体ID','类别','简体中文定名'}
    if not rows or not needed.issubset(rows[0]): raise ValueError('Missing R2 required headers')
    for row in rows:
        eid=row['实体ID'].strip(); typ=row['类别'].strip(); cn=row['简体中文定名'].strip()
        if not (eid and typ and cn): raise ValueError('Blank R2 identity/type/name')
        db.execute("INSERT INTO CANONICAL_ENTITY(entity_id,entity_type) VALUES (?,?)",(eid,typ))
        db.execute("INSERT INTO CANONICAL_TERM(entity_id,canonical_cn) VALUES (?,?)",(eid,cn))
    return len(rows)

def import_guide(db,path,version,prefer):
    raw=ro(path); data=raw.execute("SELECT * FROM sources").fetchall()
    keys=[x[1] for x in raw.execute("PRAGMA table_info(sources)")]
    sources={str(dict(zip(keys,r))['source_id']):dict(zip(keys,r)) for r in data}
    for sid,src in sources.items():
        guide_key=version+'::'+sid
        is_ff_legacy=(version=='F_v0.2' and int(src.get('page_count') or 0)==812)
        policy=('ARCHIVAL_SUPERSEDED_BY_FF_v1.0.2' if is_ff_legacy
                else 'CANONICAL_FF_REFERENCE' if prefer else 'HISTORICAL_READONLY')
        db.execute("INSERT INTO GUIDE_DOCUMENT VALUES(?,?,?,?,?,?,?)",
            (guide_key,version,sid,src.get('title'),src.get('pdf_sha256'),src.get('page_count'),policy))
    pkeys=[x[1] for x in raw.execute("PRAGMA table_info(pages)")]
    page_rows=0
    for record in raw.execute("SELECT * FROM pages"):
        p=dict(zip(pkeys,record)); sid=str(p['source_id']); guide_key=version+'::'+sid
        original=p.get('canonical_text') if version=='FF_v1.0.2' else p.get('transcript_text')
        db.execute("INSERT INTO GUIDE_PAGE VALUES(?,?,?,?,?,?,?)",
            (guide_key,str(p['page_id']),p['page_number'],original or '',original or '',
             'IDENTITY_PENDING_ENTITY_BINDING',str(p.get('qa_state'))))
        page_rows+=1
    lkeys=[x[1] for x in raw.execute("PRAGMA table_info(page_lines)")]
    line_rows=0
    for record in raw.execute("SELECT * FROM page_lines"):
        r=dict(zip(lkeys,record)); guide_key=version+'::'+str(r['source_id'])
        txt=r.get('line_text') or ''
        db.execute("INSERT INTO GUIDE_TEXT_NORMALIZED VALUES(?,?,?,?,?,?,?,?)",
            (guide_key,str(r['line_id']),str(r['page_id']),r['page_number'],
             r['line_number'],txt,txt,'NO_REWRITE_PENDING_IDENTITY'))
        line_rows+=1
    if version=='FF_v1.0.2':
        qkeys=[x[1] for x in raw.execute("PRAGMA table_info(qa_resolution)")]
        for record in raw.execute("SELECT * FROM qa_resolution"):
            r=dict(zip(qkeys,record))
            db.execute("INSERT INTO FF_GUIDE_QA_RESOLUTION VALUES(?,?,?,?,?,?)",
                (str(r['page_id']),str(r.get('original_flag') or ''),
                 r.get('resolution_status'),r.get('information_status'),
                 r.get('exact_text_status'),json.dumps(r,ensure_ascii=False,default=str)))
        ckeys=[x[1] for x in raw.execute("PRAGMA table_info(crosscheck_facts)")]
        for record in raw.execute("SELECT * FROM crosscheck_facts"):
            r=dict(zip(ckeys,record))
            db.execute("INSERT INTO FF_GUIDE_CROSSCHECK VALUES(?,?,?)",
                (str(r['id']),str(r.get('page_id')),
                 json.dumps(r,ensure_ascii=False,default=str)))
    raw.close()
    return {'pages':page_rows,'lines':line_rows,'sources':len(sources)}

def main():
    ap=argparse.ArgumentParser(description='N02-U1 non-destructive baseline builder')
    for key in ('n03','guide-f','guide-ff','r2','out'):
        ap.add_argument('--'+key,required=True)
    args=ap.parse_args()
    inp={k:Path(v) for k,v in {
        'N03_PARENT':args.n03,'GUIDE_F_V02':args.guide_f,
        'GUIDE_FF_V102':args.guide_ff,'R2_NAMES':args.r2}.items()}
    for role,path in inp.items():
        if not path.is_file():raise FileNotFoundError(f'{role}: {path}')
    out=Path(args.out)
    if out.exists(): raise FileExistsError('Refuse to overwrite any existing output: '+str(out))
    audit={k:check_db(p) for k,p in inp.items() if k!='R2_NAMES'}
    src=ro(inp['N03_PARENT']); db=sqlite3.connect(out)
    try:
        src.backup(db)
        src.close()
        db.executescript(SCHEMA)
        for role,path in inp.items():record_input(db,role,path)
        n=import_r2(db,inp['R2_NAMES'])
        if n!=1392: raise ValueError(f'R2 entity count {n} != 1392')
        f=import_guide(db,inp['GUIDE_F_V02'],'F_v0.2',False)
        ff=import_guide(db,inp['GUIDE_FF_V102'],'FF_v1.0.2',True)
        if f['pages']!=1062 or ff['pages']!=812:raise ValueError('Unexpected guide page count')
        db.execute("INSERT INTO QA_RESULT VALUES(?,?,?,?,?)",
            ('U1_ORIGINAL_PRESERVED','PASS','Original guide text remains byte-for-byte in source files','Never alter input corpus',None))
        db.execute("INSERT INTO QA_RESULT VALUES(?,?,?,?,?)",
            ('U1_AUTOMATIC_GAME_REWRITE','NOT_RUN','0 automatic game text edits','Identity-bound, reviewed changes only','No global replace'))
        db.execute("INSERT INTO QA_RESULT VALUES(?,?,?,?,?)",
            ('U1_GUIDE_ENTITY_BINDING','OPEN','0 guide semantic substitutions','Full page- and line-level bindings','Source data imported; identity review still required'))
        db.commit()
        integrity=db.execute("PRAGMA integrity_check").fetchone()[0]
        foreign=db.execute("PRAGMA foreign_key_check").fetchall()
        if integrity!='ok' or foreign:raise RuntimeError(f'DB validation failed: {integrity}, {len(foreign)} FK')
        result={'status':'BASELINE_IMPORT_ONLY_NOT_U1_COMPLETE',
                'parent_n03':inp['N03_PARENT'].name,
                'r2_entities':n,'guide_f':f,'guide_ff':ff,
                'integrity_check':integrity,'foreign_key_errors':len(foreign),
                'input_sha256':{k:sha256(p) for k,p in inp.items()},
                'known_gaps':['R2 source-binding TSV not imported','N08/N09 current text not reconciled',
                              'UETS links not reconciled','Full 35-category identity review not complete',
                              'No textual rewrites and no runtime tests']}
        out.with_suffix('.audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except:
        db.rollback()
        db.close()
        if out.exists():out.unlink()
        raise
    else: db.close()
if __name__=='__main__':
    main()
