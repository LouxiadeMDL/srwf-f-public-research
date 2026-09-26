#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WP/YZZL Super Robot Wars F - SCEDATA[71] read-only extractor
2026-09-26 v1.0

Input:
  - WP/YZZL F full Saturn BIN/CUE, or
  - an already extracted SCEDATA.BIN

Output:
  - full SCEDATA.BIN
  - SCEDATA_071_COMPRESSED.bin
  - SCEDATA_071_DECOMP.bin / YZZL_71.bin
  - parsed 112-byte header pointers
  - SHA-256 / extraction report
  - one ZIP ready to upload back to ChatGPT

No ROM/BIN is modified. Standard-library Python only.
"""

from __future__ import annotations
import argparse, hashlib, json, os, time, zipfile
from pathlib import Path

VERSION = "WP_SCEDATA71_EXTRACTOR_20260926_v1.0"
INDEX = 71

EXPECTED = {
    "scedata_size": 579071,
    "entry_count": 80,
    "entry_start": 524800,
    "entry_end": 532910,
    "decoded_size": 13236,
    "decoded_sha256":
        "bf35b4e83f5608993e4b8ad8c46792c6dfc12dbb82ee186b308134537bb602ec",
    "known_target_lba": 103742,
}

FORMATS = [
    (2352, 16, 2048, "MODE1/2352"),
    (2352, 24, 2048, "MODE2_FORM1/2352"),
    (2048, 0, 2048, "ISO/2048"),
]


class ExtractError(RuntimeError):
    pass


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        while True:
            b = f.read(8 * 1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def be32s(b: bytes, o: int) -> int:
    return int.from_bytes(b[o:o+4], "big", signed=True)


def le32(b: bytes, o: int) -> int:
    return int.from_bytes(b[o:o+4], "little")


def parse_directory(data: bytes):
    if len(data) < 16:
        raise ExtractError("SCEDATA too small")
    first = be32s(data, 0)
    if first <= 0 or first % 8:
        raise ExtractError(f"invalid SCEDATA directory: first={first}")
    count = first // 8
    if not (1 <= count <= 1024) or first > len(data):
        raise ExtractError(f"invalid SCEDATA entry count: {count}")

    out = []
    for i in range(count):
        f0, f1 = i * 8, i * 8 + 4
        start = f0 + be32s(data, f0)
        end = f1 + be32s(data, f1)
        if not (0 <= start <= end <= len(data)):
            raise ExtractError(
                f"entry {i} out of range: {start}..{end} / {len(data)}"
            )
        out.append({
            "index": i,
            "table_offset": f0,
            "start": start,
            "end": end,
            "compressed_size": end - start,
        })
    return out


class DIC:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0
        self.ctrl = 0
        self.left = 0

    def byte(self):
        if self.pos >= len(self.data):
            raise ExtractError(f"unexpected EOI at compressed +0x{self.pos:X}")
        v = self.data[self.pos]
        self.pos += 1
        return v

    def bit(self):
        if not self.left:
            self.ctrl = self.byte()
            self.left = 8
        self.left -= 1
        return (self.ctrl >> self.left) & 1

    def bits(self, n):
        v = 0
        for _ in range(n):
            v = (v << 1) | self.bit()
        return v


def decode_dic(data: bytes):
    """
    Strict SRW F DIC decoder.

    Historical dic-dec.c stored extended length in uint8_t; 0xFF + 1
    wrapped 256 -> 0. Here length is a Python int, so length 256 is valid.
    """
    r = DIC(data)
    out = bytearray()

    while True:
        if r.bit():
            out.append(r.byte())
            continue

        if r.bit():
            a, b = r.byte(), r.byte()
            ref = (a << 5) | (b >> 3)
            ln = (b & 7) + 2
            if ln == 2:
                ext = r.byte()
                if ext == 0:
                    return bytes(out), r.pos
                ln = ext + 1

            for _ in range(ln):
                src = len(out) + ref - 8192
                if not (0 <= src < len(out)):
                    raise ExtractError(
                        f"bad long backref: out={len(out)} ref={ref} src={src}"
                    )
                out.append(out[src])
        else:
            ln = r.bits(2) + 2
            off = r.byte()
            for _ in range(ln):
                src = len(out) + off - 256
                if not (0 <= src < len(out)):
                    raise ExtractError(
                        f"bad short backref: out={len(out)} off={off} src={src}"
                    )
                out.append(out[src])


def self_test():
    # literals ABC + EOD
    x = bytes([0xE8, 0x41, 0x42, 0x43, 0, 0, 0])
    d, used = decode_dic(x)
    assert d == b"ABC" and used == len(x)

    # AB + short backref(-2,len4) + EOD => ABABAB
    x = bytes([0xC9, 0x41, 0x42, 0xFE, 0, 0, 0])
    d, used = decode_dic(x)
    assert d == b"ABABAB" and used == len(x)

    # extended long backref length 256 (legacy decoder bug case)
    x = bytes([0xA8, 0x41, 0xFF, 0xF8, 0xFF, 0, 0, 0])
    d, used = decode_dic(x)
    assert d == b"A" * 257 and used == len(x)

    # one-entry SCEDATA directory fixture
    fake = (
        (8).to_bytes(4, "big", signed=True) +
        (11).to_bytes(4, "big", signed=True) +
        bytes([0xE8, 0x41, 0x42, 0x43, 0, 0, 0])
    )
    e = parse_directory(fake)
    assert len(e) == 1 and e[0]["start"] == 8 and e[0]["end"] == 15


def choose_file():
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        p = filedialog.askopenfilename(
            title="选择 WP/YZZL F 的 SRWF.BIN / CUE 或 SCEDATA.BIN",
            filetypes=[
                ("Supported", "*.bin *.cue"),
                ("BIN", "*.bin"),
                ("CUE", "*.cue"),
                ("All", "*.*"),
            ],
        )
        root.destroy()
        if p:
            return Path(p)
    except Exception:
        pass
    s = input("输入 SRWF.BIN / CUE / SCEDATA.BIN 完整路径: ").strip().strip('"')
    return Path(s) if s else None


def resolve_cue(p: Path) -> Path:
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s.upper().startswith("FILE "):
            continue
        x = s[5:].strip()
        if x.startswith('"'):
            j = x.find('"', 1)
            if j < 0:
                continue
            name = x[1:j]
        else:
            name = x.split()[0]
        q = (p.parent / name).resolve()
        if q.exists():
            return q
    raise ExtractError("CUE referenced BIN was not found")


def user_sector(f, phys, sector_size, user_off, user_size):
    if phys < 0:
        raise ExtractError("negative physical sector")
    f.seek(phys * sector_size + user_off)
    b = f.read(user_size)
    if len(b) != user_size:
        raise ExtractError(f"short sector read at {phys}")
    return b


def detect_iso(p: Path):
    size = p.stat().st_size
    with p.open("rb") as f:
        for secsz, off, usersz, desc in FORMATS:
            lim = min(400, size // secsz)
            for phys in range(lim):
                f.seek(phys * secsz + off)
                h = f.read(7)
                if len(h) == 7 and h[0] == 1 and h[1:6] == b"CD001" and h[6] == 1:
                    return {
                        "sector_size": secsz,
                        "user_offset": off,
                        "user_size": usersz,
                        "format": desc,
                        "pvd_physical_sector": phys,
                        "bias": phys - 16,
                    }
    return None


def read_extent(p: Path, lba: int, size: int, fmt: dict):
    out = bytearray()
    n = 0
    with p.open("rb") as f:
        while len(out) < size:
            phys = lba + n + fmt["bias"]
            out += user_sector(
                f, phys, fmt["sector_size"], fmt["user_offset"], fmt["user_size"]
            )
            n += 1
    return bytes(out[:size])


def dir_records(buf: bytes):
    pos = 0
    while pos < len(buf):
        ln = buf[pos]
        if not ln:
            pos = ((pos // 2048) + 1) * 2048
            continue
        if ln < 34 or pos + ln > len(buf):
            break
        r = buf[pos:pos+ln]
        lba, size, flags, nl = le32(r, 2), le32(r, 10), r[25], r[32]
        raw = r[33:33+nl]
        if raw == b"\x00":
            name = "."
        elif raw == b"\x01":
            name = ".."
        else:
            name = raw.decode("ascii", "replace").split(";", 1)[0]
        yield {"name": name, "lba": lba, "size": size, "flags": flags}
        pos += ln


def extract_iso_scedata(p: Path):
    fmt = detect_iso(p)
    if not fmt:
        return None, None

    pvd = read_extent(p, 16, 2048, fmt)
    root = pvd[156:190]
    if len(root) < 34 or root[0] < 34:
        raise ExtractError("bad ISO root record")

    root_lba, root_size = le32(root, 2), le32(root, 10)
    rd = read_extent(p, root_lba, root_size, fmt)

    for rec in dir_records(rd):
        if rec["name"].upper() == "SCEDATA.BIN":
            data = read_extent(p, rec["lba"], rec["size"], fmt)
            info = dict(fmt)
            info.update({
                "root_lba": root_lba,
                "root_size": root_size,
                "scedata_lba": rec["lba"],
                "scedata_size": rec["size"],
            })
            return data, info
    return None, fmt


def fallback_target(p: Path):
    for secsz, off, usersz, desc in FORMATS:
        for bias in (0, 150):
            fmt = {
                "sector_size": secsz,
                "user_offset": off,
                "user_size": usersz,
                "format": desc + "_FALLBACK",
                "pvd_physical_sector": None,
                "bias": bias,
            }
            try:
                d = read_extent(
                    p, EXPECTED["known_target_lba"], EXPECTED["scedata_size"], fmt
                )
                e = parse_directory(d)
                if (
                    len(e) == 80 and
                    e[71]["start"] == EXPECTED["entry_start"] and
                    e[71]["end"] == EXPECTED["entry_end"]
                ):
                    fmt.update({
                        "scedata_lba": EXPECTED["known_target_lba"],
                        "scedata_size": EXPECTED["scedata_size"],
                        "fallback": True,
                    })
                    return d, fmt
            except Exception:
                pass
    return None, None


def header_pointers(decoded: bytes):
    ans = []
    if len(decoded) < 112:
        return ans
    for i in range(28):
        o = i * 4
        rel = be32s(decoded, o)
        target = o + rel
        ans.append({
            "slot": i,
            "field_offset": o,
            "relative_be32_signed": rel,
            "target_offset": target,
            "target_in_block": 0 <= target < len(decoded),
        })
    return ans


def run(source: Path, out_root: Path):
    selected = source.resolve()
    if not selected.exists():
        raise ExtractError(f"not found: {selected}")

    actual = resolve_cue(selected) if selected.suffix.lower() == ".cue" else selected
    src_size = actual.stat().st_size
    src_sha = sha_file(actual)

    scedata = None
    iso = None
    kind = None

    # Small input: first try treating it as direct SCEDATA.
    if src_size < 16 * 1024 * 1024:
        raw = actual.read_bytes()
        try:
            parse_directory(raw)
            scedata, kind = raw, "SCEDATA_BIN_DIRECT"
        except Exception:
            pass

    if scedata is None:
        kind = "DISC_IMAGE"
        scedata, iso = extract_iso_scedata(actual)
        if scedata is None:
            scedata, iso = fallback_target(actual)
        if scedata is None:
            raise ExtractError(
                "SCEDATA.BIN not found. Select the WP/YZZL F data BIN/CUE "
                "or an extracted SCEDATA.BIN."
            )

    entries = parse_directory(scedata)
    if INDEX >= len(entries):
        raise ExtractError(f"SCEDATA has only {len(entries)} entries")

    ent = entries[INDEX]
    comp = scedata[ent["start"]:ent["end"]]
    dec, consumed = decode_dic(comp)

    checks = {
        "scedata_size_match": len(scedata) == EXPECTED["scedata_size"],
        "entry_count_match": len(entries) == EXPECTED["entry_count"],
        "entry_start_match": ent["start"] == EXPECTED["entry_start"],
        "entry_end_match": ent["end"] == EXPECTED["entry_end"],
        "decoded_size_match": len(dec) == EXPECTED["decoded_size"],
        "decoded_sha256_match": sha_bytes(dec) == EXPECTED["decoded_sha256"],
        "compressed_fully_consumed": consumed == len(comp),
    }
    passed = all(checks.values())

    stamp = time.strftime("%Y%m%d_%H%M%S")
    folder = out_root / f"WP_SCEDATA71_OUTPUT_{stamp}"
    folder.mkdir(parents=True)

    files = {
        "SCEDATA.BIN": scedata,
        "SCEDATA_071_COMPRESSED.bin": comp,
        "SCEDATA_071_DECOMP.bin": dec,
        "YZZL_71.bin": dec,
        "SCEDATA_071_HEADER112.bin": dec[:112],
    }
    for name, data in files.items():
        (folder / name).write_bytes(data)

    (folder / "SCEDATA_071_HEADER_POINTERS.json").write_text(
        json.dumps(header_pointers(dec), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report = {
        "schema": "WP_SCEDATA71_EXTRACTION_REPORT_v1",
        "tool": VERSION,
        "read_only": True,
        "selected_source_name": selected.name,
        "actual_binary_source_name": actual.name,
        "source_size": src_size,
        "source_sha256": src_sha,
        "input_kind": kind,
        "iso": iso,
        "scedata": {
            "size": len(scedata),
            "sha256": sha_bytes(scedata),
            "entry_count": len(entries),
        },
        "entry71": {
            **ent,
            "compressed_sha256": sha_bytes(comp),
            "decoder_consumed": consumed,
            "decoded_size": len(dec),
            "decoded_sha256": sha_bytes(dec),
        },
        "expected": EXPECTED,
        "checks": checks,
        "status":
            "PASS_WP_TARGET_SCEDATA71"
            if passed else
            "CHECK_REQUIRED_NOT_EXACT_WP_TARGET",
    }
    (folder / "EXTRACTION_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    hashes = []
    for p in sorted(folder.iterdir()):
        hashes.append(f"{sha_file(p)}  {p.name}")
    (folder / "SHA256SUMS.txt").write_text("\n".join(hashes) + "\n", encoding="utf-8")

    zip_name = (
        f"WP_F_SCEDATA71_EXTRACTION_PASS_{stamp}.zip"
        if passed else
        f"WP_F_SCEDATA71_EXTRACTION_CHECK_REQUIRED_{stamp}.zip"
    )
    zp = out_root / zip_name
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(folder.iterdir()):
            z.write(p, p.name)
    return report, zp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    self_test()
    if a.self_test and not a.source:
        print("[PASS] internal DIC/directory self-test")
        return 0

    src = Path(a.source) if a.source else choose_file()
    if not src:
        print("No input selected")
        return 2

    out = Path(a.out).resolve() if a.out else Path(__file__).resolve().parent / "OUTPUT"
    out.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(VERSION)
    print("READ ONLY - source will not be modified")
    print("Input:", src)
    print("Internal self-test: PASS")
    print("=" * 70)

    try:
        r, zp = run(src, out)
    except Exception as e:
        print("[FAILED]", e)
        return 1

    e = r["entry71"]
    print("STATUS:", r["status"])
    print("SCEDATA:", r["scedata"]["size"], "bytes,", r["scedata"]["entry_count"], "entries")
    print("SCEDATA[71] compressed:", e["start"], "..", e["end"])
    print("SCEDATA[71] decoded:", e["decoded_size"], "bytes")
    print("SHA256:", e["decoded_sha256"])
    print("ZIP:", zp)

    if r["status"] == "PASS_WP_TARGET_SCEDATA71":
        print("\n[PASS] Upload the generated ZIP back to ChatGPT.")
        return 0

    print("\n[WARNING] Not an exact match to the locked WP target.")
    print("Upload the CHECK_REQUIRED ZIP plus a screenshot of this window.")
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
