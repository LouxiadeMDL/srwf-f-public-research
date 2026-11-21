#!/usr/bin/env python3
"""Recover exactly one pinned N03 parent SQLite from its private delivery ZIP.

No source files are changed. Extracts one member by streaming, then validates
the actual uncompressed byte size and SHA-256 before publishing to a new path.
Does not publish private content or claim N02-U1 production acceptance.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import zipfile

PARENT_NAME = "SSF_SSFF_N03_relations_20261119.sqlite"
PARENT_SIZE = 1690554368
PARENT_SHA256 = "f00e3109d9099647f85f7fd73506ab5b1ae00714ba99b9aa65892ce5d136d350"


def extract_verified(archive, target, *, expected_name, expected_size, expected_sha):
    archive, target = Path(archive), Path(target)
    if not archive.is_file():
        raise FileNotFoundError(archive)
    if target.exists():
        raise FileExistsError("Refuse to overwrite original or checkpoint: " + str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        matches = [item for item in z.infolist()
                   if not item.is_dir()
                   and item.filename.rsplit("/", 1)[-1] == expected_name]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one {expected_name}; found {len(matches)}")
        info = matches[0]
        if info.file_size != expected_size:
            raise ValueError(f"Unexpected uncompressed size: {info.file_size}")
        # Temporary file lives alongside target so final os.replace is atomic.
        fd, temp_name = tempfile.mkstemp(prefix=".n02_u1_parent_", dir=target.parent)
        os.close(fd)
        temp = Path(temp_name)
        try:
            h = hashlib.sha256()
            count = 0
            with z.open(info, "r") as source, temp.open("wb") as dest:
                while True:
                    block = source.read(8 * 1024 * 1024)
                    if not block:
                        break
                    count += len(block)
                    h.update(block)
                    dest.write(block)
                dest.flush()
                os.fsync(dest.fileno())
            if count != expected_size or h.hexdigest() != expected_sha:
                raise ValueError("N03 source size/SHA-256 mismatch: output NOT published")
            os.replace(temp, target)
        finally:
            temp.unlink(missing_ok=True)
    return {"state": "VERIFIED_PARENT_ONLY_NOT_N02_U1_PASS",
            "archive": archive.name, "member": info.filename,
            "parent": target.name, "bytes": count, "sha256": h.hexdigest()}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--archive", required=True, help="Original private N03/N04 ZIP")
    p.add_argument("--out", required=True, help="New local SQLite path")
    p.add_argument("--receipt", required=True, help="New private JSON receipt path")
    args = p.parse_args()
    report = Path(args.receipt)
    if report.exists():
        raise FileExistsError("Receipt already exists: " + str(report))
    if Path(args.out).resolve() == report.resolve():
        raise ValueError("The database and receipt must not share a path")
    info = extract_verified(args.archive, args.out,
                            expected_name=PARENT_NAME,
                            expected_size=PARENT_SIZE,
                            expected_sha=PARENT_SHA256)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(info, indent=2), encoding="utf-8")
    print(json.dumps(info))


if __name__ == "__main__":
    main()
