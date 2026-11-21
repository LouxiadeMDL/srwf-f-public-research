#!/usr/bin/env python3
"""Synthetic-only streaming ZIP restore tests; no private N03 bytes."""
import hashlib
from pathlib import Path
import sys
import tempfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from n02_u1_restore_parent import extract_verified


def main():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        name = "sample_parent.sqlite"
        payload = b"SQLite format 3\x00" + b"fake row byte\xff" * 8192
        digest = hashlib.sha256(payload).hexdigest()
        archive = root / "parent.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("project/output/" + name, payload)
        target = root / "new" / name
        receipt = extract_verified(
            archive, target, expected_name=name,
            expected_size=len(payload), expected_sha=digest)
        assert target.read_bytes() == payload
        assert receipt["state"] == "VERIFIED_PARENT_ONLY_NOT_N02_U1_PASS"
        try:
            extract_verified(archive, target, expected_name=name,
                             expected_size=len(payload), expected_sha=digest)
            raise AssertionError("Overwrite unexpectedly accepted")
        except FileExistsError:
            pass
        for label, kwargs in [
            ("hash", {"expected_name": name, "expected_size": len(payload),
                      "expected_sha": "0" * 64}),
            ("size", {"expected_name": name, "expected_size": len(payload) + 1,
                      "expected_sha": digest}),
            ("missing", {"expected_name": "not-present.sqlite",
                         "expected_size": len(payload), "expected_sha": digest}),
        ]:
            output = root / ("fail_" + label + ".sqlite")
            try:
                extract_verified(archive, output, **kwargs)
                raise AssertionError(label + " tamper unexpectedly accepted")
            except ValueError:
                pass
            assert not output.exists(), label
        print("N02-U1 synthetic restore tests PASS (hash/size/name/overwrite refusal)")
        print("NOTE: production N03 archive was NOT tested in CI.")


if __name__ == "__main__":
    main()
