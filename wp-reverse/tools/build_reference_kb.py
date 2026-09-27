#!/usr/bin/env python3
"""Build the public-safe WP reverse reference SQLite from published CSV/JSON inputs."""
from pathlib import Path
import csv, json, sqlite3

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "WP_REVERSE_REFERENCE_KB_v1.sqlite"

TABLES = {
    "source_registry.csv":"source_registry",
    "historical_database_catalog.csv":"historical_database_catalog",
    "historical_claims.csv":"historical_claims",
    "historical_leads.csv":"historical_leads",
    "reference_dataset_registry.csv":"reference_dataset_registry",
    "wp_b_validated_claims.csv":"wp_b_validated_claims",
    "wp_b_errors.csv":"wp_b_errors",
}

if OUT.exists():
    OUT.unlink()
db = sqlite3.connect(OUT)
db.execute("PRAGMA user_version=1")
for filename, table in TABLES.items():
    with (DATA/filename).open(encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        rows=list(reader); cols=reader.fieldnames
    db.execute(f"CREATE TABLE {table} ({', '.join(c+' TEXT' for c in cols)})")
    db.executemany(f"INSERT INTO {table} VALUES ({','.join('?' for _ in cols)})",
                   [[r[c] for c in cols] for r in rows])

with (ROOT/"SOURCE_AUTHORITY.csv").open(encoding="utf-8-sig") as f:
    reader=csv.DictReader(f); rows=list(reader); cols=reader.fieldnames
db.execute(f"CREATE TABLE authority ({', '.join(c+' TEXT' for c in cols)})")
db.executemany(f"INSERT INTO authority VALUES ({','.join('?' for _ in cols)})",
               [[r[c] for c in cols] for r in rows])

state=json.loads((ROOT/"WP_C_STATE.json").read_text(encoding="utf-8"))
db.execute("CREATE TABLE project_state (key TEXT PRIMARY KEY, value TEXT)")
for k,v in state.items():
    db.execute("INSERT INTO project_state VALUES (?,?)",
               (k, json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else str(v)))
db.commit()
assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
db.close()
print(OUT)
