"""Build a new SQLite metadata index from a hash-checked public handoff packet."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    packet = args.input.resolve()
    root = packet.parent.parent
    manifest = json.loads((packet / 'MANIFEST.json').read_text(encoding='utf-8'))
    required = ['claims.json', 'leads.json', 'sources.json', 'database_catalog.json']
    for name in required:
        rel = (packet / name).relative_to(root).as_posix()
        if rel not in manifest['files']:
            raise ValueError('Required input missing from reviewed manifest: ' + name)
    for rel, expected in manifest['files'].items():
        path = (root / rel).resolve()
        if root not in path.parents or path.is_symlink():
            raise ValueError('Unsafe manifest path: ' + rel)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Digest mismatch: ' + rel)
    if args.output.exists():
        raise FileExistsError('Refusing to overwrite an existing output')
    data = {name: json.loads((packet / name).read_text(encoding='utf-8')) for name in required}
    with sqlite3.connect(args.output) as db:
        db.executescript('''
        CREATE TABLE claims(id TEXT PRIMARY KEY,domain TEXT,title TEXT,evidence_class TEXT,result TEXT,limitations TEXT,source_ids TEXT);
        CREATE TABLE leads(id TEXT PRIMARY KEY,priority TEXT,domain TEXT,status TEXT,title TEXT,next_check TEXT,source_ids TEXT);
        CREATE TABLE sources(id TEXT PRIMARY KEY,name TEXT,size INTEGER,sha256 TEXT,read_level TEXT);
        CREATE TABLE databases(id TEXT PRIMARY KEY,name TEXT,sha256 TEXT,size INTEGER,integrity TEXT,role TEXT);
        CREATE TABLE table_counts(database_id TEXT,table_name TEXT,rows INTEGER,PRIMARY KEY(database_id,table_name));
        ''')
        for r in data['claims.json']:
            db.execute('INSERT INTO claims VALUES (?,?,?,?,?,?,?)',tuple(r[k] for k in ['id','domain','title','evidence_class','result','limitations'])+(json.dumps(r['source_ids']),))
        for r in data['leads.json']:
            db.execute('INSERT INTO leads VALUES (?,?,?,?,?,?,?)',tuple(r[k] for k in ['id','priority','domain','status','title','next_check'])+(json.dumps(r['source_ids']),))
        for r in data['sources.json']:
            db.execute('INSERT INTO sources VALUES (?,?,?,?,?)',tuple(r[k] for k in ['id','name','size','sha256','read_level']))
        for r in data['database_catalog.json']:
            db.execute('INSERT INTO databases VALUES (?,?,?,?,?,?)',tuple(r[k] for k in ['id','name','sha256','size','integrity','role']))
            for t in r['tables']:
                db.execute('INSERT INTO table_counts VALUES (?,?,?)',(r['id'],t['name'],t['rows']))
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError('Generated database failed integrity check')
    db.close()
    print(json.dumps({'status':'PASS_METADATA_INDEX_ONLY','claims':len(data['claims.json']),
                      'leads':len(data['leads.json']),'sources':len(data['sources.json']),
                      'databases':len(data['database_catalog.json']),
                      'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
