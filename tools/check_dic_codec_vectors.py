"""Strict, synthetic checker for the documented SRW F DIC-style codec grammar.

This is an original clean-room utility derived from the public structural description.
It contains no game bytes and does not copy the third-party C implementation.

Run:
    python tools/check_dic_codec_vectors.py --self-test
    python tools/check_dic_codec_vectors.py --decode-hex "..."
"""
from __future__ import annotations

import argparse


class CodecError(ValueError):
    pass


class StrictDecoder:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0
        self.control = 0
        self.bits_left = 0
        self.out = bytearray()

    def byte(self) -> int:
        if self.pos >= len(self.data):
            raise CodecError("unexpected end of input")
        value = self.data[self.pos]
        self.pos += 1
        return value

    def bit(self) -> int:
        if self.bits_left == 0:
            self.control = self.byte()
            self.bits_left = 8
        self.bits_left -= 1
        return (self.control >> self.bits_left) & 1

    def bits(self, count: int) -> int:
        value = 0
        for _ in range(count):
            value = (value << 1) | self.bit()
        return value

    def copy_backref(self, distance: int, length: int) -> None:
        if not 1 <= distance <= 0x2000:
            raise CodecError(f"invalid distance {distance}")
        if distance > len(self.out):
            raise CodecError("back-reference before start of output")
        for _ in range(length):
            self.out.append(self.out[-distance])

    def decode(self) -> bytes:
        while True:
            if self.bit():
                self.out.append(self.byte())
                continue

            if self.bit() == 0:
                length = self.bits(2) + 2
                raw = self.byte()
                distance = 0x100 - raw
                self.copy_backref(distance, length)
                continue

            high = self.byte()
            low = self.byte()
            packed = (high << 8) | low
            ref13 = packed >> 3
            distance = 0x2000 - ref13
            low3 = packed & 7
            if low3:
                length = low3 + 2
            else:
                ext = self.byte()
                if ext == 0:
                    return bytes(self.out)
                length = ext + 1
            self.copy_backref(distance, length)


class SyntheticBuilder:
    """Emit synthetic commands using the documented bit/data interleaving."""

    def __init__(self):
        self.buf = bytearray([0])
        self.control_offset = 0
        self.current_bit = 8
        self.control = 0

    def data(self, value: int) -> None:
        self.buf.append(value & 0xFF)

    def bit(self, value: int) -> None:
        if self.current_bit == 0:
            self.buf[self.control_offset] = self.control
            self.control_offset = len(self.buf)
            self.buf.append(0)
            self.current_bit = 8
            self.control = 0
        self.current_bit -= 1
        self.control |= (value & 1) << self.current_bit

    def bits(self, count: int, value: int) -> None:
        for shift in range(count - 1, -1, -1):
            self.bit((value >> shift) & 1)

    def literal(self, value: int) -> None:
        self.bit(1)
        self.data(value)

    def short(self, distance: int, length: int) -> None:
        if not (1 <= distance <= 0x100 and 2 <= length <= 5):
            raise ValueError("bad short back-reference")
        self.bits(4, length - 2)
        self.data((-distance) & 0xFF)

    def long(self, distance: int, length: int) -> None:
        if not (1 <= distance <= 0x2000 and 2 <= length <= 0x100):
            raise ValueError("bad long back-reference")
        self.bits(2, 1)
        neg = (-distance) & 0x1FFF
        if 3 <= length <= 9:
            packed = (neg << 3) | (length - 2)
            self.data(packed >> 8)
            self.data(packed)
        else:
            packed = neg << 3
            self.data(packed >> 8)
            self.data(packed)
            self.data(length - 1)

    def finish(self) -> bytes:
        self.bits(2, 1)
        self.data(0)
        self.data(0)
        self.data(0)
        self.buf[self.control_offset] = self.control
        return bytes(self.buf)


def decode(data: bytes) -> bytes:
    return StrictDecoder(data).decode()


def self_test() -> None:
    tests = []

    b = SyntheticBuilder()
    for ch in b"ABC":
        b.literal(ch)
    tests.append(("literal", b.finish(), b"ABC"))

    b = SyntheticBuilder()
    for ch in b"ABC":
        b.literal(ch)
    b.short(3, 3)
    tests.append(("short-backref", b.finish(), b"ABCABC"))

    b = SyntheticBuilder()
    b.literal(ord("A"))
    b.long(1, 256)
    tests.append(("extended-256", b.finish(), b"A" * 257))

    for name, packed, expected in tests:
        actual = decode(packed)
        if actual != expected:
            raise SystemExit(f"FAIL {name}: {len(actual)} != {len(expected)}")
        print(f"PASS {name}: compressed={len(packed)} decoded={len(actual)}")

    for name, packed in [
        ("truncated-literal", bytes.fromhex("80")),
        ("truncated-long", bytes.fromhex("40 00")),
        ("backref-before-output", bytes.fromhex("00 ff")),
    ]:
        try:
            decode(packed)
        except CodecError:
            print(f"PASS {name}: rejected")
        else:
            raise SystemExit(f"FAIL {name}: malformed input accepted")

    print("PASS: all synthetic DIC codec checks")


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--decode-hex")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    packed = bytes.fromhex(args.decode_hex)
    out = decode(packed)
    print(out.hex(" "))


if __name__ == "__main__":
    main()
