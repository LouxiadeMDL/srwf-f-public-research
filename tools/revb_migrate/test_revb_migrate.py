#!/usr/bin/env python3
"""No ROMs, fonts or dialogue: every sector in these tests is synthetic."""
from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import revb_migrate as m


def iso_both(value, width=4):
    return value.to_bytes(width, 'little') + value.to_bytes(width, 'big')


def record(identifier, lba, size, directory=False):
    identifier = identifier if isinstance(identifier, bytes) else identifier.encode('ascii')
    size_record = 33 + len(identifier) + (len(identifier) % 2 == 0)
    data = bytearray(size_record)
    data[0] = size_record
    data[2:10] = iso_both(lba)
    data[10:18] = iso_both(size)
    data[25] = 2 if directory else 0
    data[28:32] = iso_both(1, 2)
    data[32] = len(identifier)
    data[33:33 + len(identifier)] = identifier
    return bytes(data)


def fixture(folder):
    folder.mkdir()
    sectors = [bytes(m.USER) for _ in range(160)]
    pvd = bytearray(m.USER)
    pvd[:7] = b'\x01CD001\x01'
    pvd[80:88] = iso_both(640)
    pvd[128:132] = iso_both(m.USER, 2)
    pvd[132:140] = iso_both(10)
    pvd[140:144] = struct.pack('<I', 18)
    pvd[148:152] = struct.pack('>I', 19)
    pvd[156:190] = record(b'\x00', 20, m.USER, True)
    sectors[16] = bytes(pvd)
    sectors[17] = b'\xffCD001\x01' + bytes(m.USER - 7)
    sectors[18] = b'\x01\x00' + struct.pack('<IH', 20, 1) + bytes(2) + bytes(m.USER - 10)
    sectors[19] = b'\x01\x00' + struct.pack('>IH', 20, 1) + bytes(2) + bytes(m.USER - 10)
    entries = [('0', 21, 4 * m.USER), ('SCEDATA.BIN', 40, 2500),
               ('TSR.BIN', 48, 3200), ('BMESS.BIN', 56, 4500),
               ('FACE.BIN', 64, 1980), ('ADPCM.XA', 200, 2324), ('LEVELUP.XA', 500, 2324)]
    directory = record(b'\x00', 20, m.USER, True) + record(b'\x01', 20, m.USER, True)
    for index, (name, lba, size) in enumerate(entries):
        directory += record(name + ';1', lba, size)
        if lba < 160:
            count = (size + m.USER - 1) // m.USER
            # Nonzero last-sector padding is intentional and must be preserved.
            data = bytes(((i * 13 + index * 19) % 251 + 1) for i in range(count * m.USER))
            for i in range(count):
                sectors[lba + i] = data[i * m.USER:(i + 1) * m.USER]
    sectors[20] = directory.ljust(m.USER, b'\x00')
    sectors[30] = b'UNALLOCATED_BUT_NONZERO_DO_NOT_TOUCH'.ljust(m.USER, b'\x00')
    with (folder / 'source1.bin').open('wb') as f:
        for lba, data in enumerate(sectors):
            f.write(m.mode1(lba, data))
    # Opaque companions: transfer preservation only; no claim these encode XA/audio.
    (folder / 'source2.bin').write_bytes(bytes([0x52]) * (m.RAW * 300))
    (folder / 'source3.bin').write_bytes(bytes([0x73]) * (m.RAW * 180))
    cue = folder / 'source.cue'
    cue.write_bytes(b'CATALOG 0000000000000\r\nFILE "source1.bin" BINARY\r\n  TRACK 01 MODE1/2352\r\n    INDEX 01 00:00:00\r\nFILE "source2.bin" BINARY\r\n  TRACK 02 MODE2/2352\r\n    INDEX 00 00:00:00\r\n    INDEX 01 00:03:00\r\nFILE "source3.bin" BINARY\r\n  TRACK 03 AUDIO\r\n    INDEX 00 00:00:00\r\n    INDEX 01 00:02:00\r\n')
    profile = {'kind': 'SYNTHETIC', 'files': len(entries),
               'tracks': [(p.stat().st_size, m.hash_file(p)) for p in (folder / f'source{i}.bin' for i in (1, 2, 3))]}
    return cue, profile


def mutate_user(path, lba, transform):
    with path.open('r+b') as f:
        f.seek(lba * m.RAW)
        block = f.read(m.RAW)
        data = bytearray(block[16:2064])
        transform(data)
        f.seek(lba * m.RAW)
        f.write(m.mode1(lba, bytes(data)))


class MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shared = tempfile.TemporaryDirectory()
        cls.seed = Path(cls.shared.name) / 'seed'
        fixture(cls.seed)

    @classmethod
    def tearDownClass(cls):
        cls.shared.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'input'
        shutil.copytree(self.seed, self.source)
        self.cue = self.source / 'source.cue'
        self.profile = {'kind': 'SYNTHETIC', 'files': 7, 'tracks': [
            (p.stat().st_size, m.hash_file(p)) for p in (self.source / f'source{i}.bin' for i in (1, 2, 3))]}

    def tearDown(self):
        self.temp.cleanup()

    def plan(self, requests=None, relocate=False):
        return m.make_plan(self.cue, requests or {}, relocate, 1, self.profile)

    def candidate(self, requests=None, relocate=False, name='candidate'):
        plan = self.plan(requests, relocate)
        report = m.build(self.cue, plan, self.root / name, self.profile)
        return plan, report, self.root / name / 'candidate.cue'

    def test_01_inventory_and_external_scope(self):
        inv = m.inventory(self.source / 'source1.bin')
        self.assertEqual(len(inv['files']), 7)
        self.assertEqual(sum(x['inside_track1'] for x in inv['files']), 5)
        self.assertEqual([x['sha256'] for x in inv['files'] if not x['inside_track1']], [None, None])

    def test_02_noop_is_bit_exact(self):
        _, report, cue = self.candidate()
        self.assertEqual(report['changed_raw_sectors'], 0)
        self.assertEqual(m.hash_file(cue.parent / 'Track01.bin'), self.profile['tracks'][0][1])
        self.assertEqual(report['runtime'], 'NOT_RUN')
        self.assertEqual(report['test_kind'], 'SYNTHETIC')

    def test_03_move_three_resources_and_reserve(self):
        plan, report, _ = self.candidate({'SCEDATA.BIN': 4096, 'TSR.BIN': 2048, 'BMESS.BIN': 0}, True)
        self.assertEqual(report['static'], 'PASS')
        self.assertGreater(report['changed_raw_sectors'], 0)
        self.assertEqual(plan['capacity']['reserved_bytes'], 6144)
        self.assertTrue(all(x['new_lba'] != x['old_lba'] for x in plan['allocations']))

    def test_04_prefer_in_place(self):
        plan = self.plan({'SCEDATA.BIN': 4096})
        self.assertEqual(plan['allocations'][0]['new_lba'], 40)

    def test_05_build_deterministic(self):
        requests = {'SCEDATA.BIN': 2048, 'TSR.BIN': 0}
        _, first, _ = self.candidate(requests, True, 'a')
        _, second, _ = self.candidate(requests, True, 'b')
        self.assertEqual(first['candidate_track1_sha256'], second['candidate_track1_sha256'])

    def test_06_sources_unchanged(self):
        before = m.freeze(self.cue, self.profile)
        self.candidate({'SCEDATA.BIN': 0}, True)
        self.assertEqual(before, m.freeze(self.cue, self.profile))

    def test_07_guard_nonzero_unallocated_sector(self):
        plan, _, cue = self.candidate({'SCEDATA.BIN': 4 * m.USER}, True)
        with m.RawImage(self.source / 'source1.bin') as a, m.RawImage(cue.parent / 'Track01.bin') as b:
            self.assertEqual(a.raw(30), b.raw(30))
        for allocation in plan['allocations']:
            self.assertFalse(allocation['new_lba'] <= 30 < allocation['new_lba'] + allocation['allocated_sectors'])

    def test_08_root0_move_rejected(self):
        with self.assertRaises(m.MigrationError):
            self.plan({'0': 0}, True)

    def test_09_XA_move_rejected(self):
        with self.assertRaises(m.MigrationError):
            self.plan({'ADPCM.XA': 0}, True)

    def test_10_wrong_source_hash_rejected(self):
        bad = copy.deepcopy(self.profile)
        bad['tracks'][0] = (bad['tracks'][0][0], '0' * 64)
        with self.assertRaises(m.MigrationError):
            m.make_plan(self.cue, {}, profile=bad)

    def test_11_synthetic_rejected_by_production_profile(self):
        with self.assertRaises(m.MigrationError):
            m.make_plan(self.cue, {})

    def test_12_capacity_overflow_rejected(self):
        with self.assertRaisesRegex(m.MigrationError, 'NO_CAPACITY'):
            self.plan({'SCEDATA.BIN': 10 * 1024 * 1024})

    def test_13_negative_boolean_reserve_rejected(self):
        for value in (-1, True, 1.5):
            with self.subTest(value=value), self.assertRaises(m.MigrationError):
                self.plan({'SCEDATA.BIN': value})

    def test_14_tampered_plan_seal_rejected(self):
        plan = self.plan({'SCEDATA.BIN': 0}, True)
        plan['allocations'][0]['new_lba'] = 21
        with self.assertRaises(m.MigrationError):
            m.build(self.cue, plan, self.root / 'bad', self.profile)
        self.assertFalse((self.root / 'bad').exists())

    def test_15_resealed_wrong_allocation_rejected(self):
        plan = m.unseal(self.plan({'SCEDATA.BIN': 0}, True))
        plan['allocations'][0]['new_lba'] = 21
        with self.assertRaises(m.MigrationError):
            m.validate_plan(self.cue, m.sealed(plan), self.profile)

    def test_16_candidate_noninterference_violation_rejected(self):
        plan, _, cue = self.candidate({'SCEDATA.BIN': 0}, True)
        mutate_user(cue.parent / 'Track01.bin', 30, lambda d: d.__setitem__(0, d[0] ^ 1))
        with self.assertRaises(m.MigrationError):
            m.verify_candidate(self.cue, plan, cue, self.profile)

    def test_17_candidate_payload_corruption_rejected(self):
        plan, _, cue = self.candidate({'SCEDATA.BIN': 0}, True)
        mutate_user(cue.parent / 'Track01.bin', plan['allocations'][0]['new_lba'], lambda d: d.__setitem__(0, d[0] ^ 1))
        with self.assertRaises(m.MigrationError):
            m.verify_candidate(self.cue, plan, cue, self.profile)

    def test_18_candidate_ECC_corruption_rejected(self):
        plan, _, cue = self.candidate({'SCEDATA.BIN': 0}, True)
        with (cue.parent / 'Track01.bin').open('r+b') as f:
            position = plan['allocations'][0]['new_lba'] * m.RAW + 2248
            f.seek(position)
            value = f.read(1)[0]
            f.seek(position)
            f.write(bytes([value ^ 1]))
        with self.assertRaises(m.MigrationError):
            m.verify_candidate(self.cue, plan, cue, self.profile)

    def test_19_track2_change_rejected(self):
        plan, _, cue = self.candidate()
        with (cue.parent / 'Track02.bin').open('r+b') as f:
            f.write(b'!')
        with self.assertRaises(m.MigrationError):
            m.verify_candidate(self.cue, plan, cue, self.profile)

    def test_20_output_overwrite_rejected(self):
        target = self.root / 'exists'
        target.mkdir()
        (target / 'sentinel').write_text('KEEP')
        with self.assertRaises(m.MigrationError):
            m.build(self.cue, self.plan(), target, self.profile)
        self.assertEqual((target / 'sentinel').read_text(), 'KEEP')

    def test_21_output_under_input_rejected(self):
        with self.assertRaises(m.MigrationError):
            m.build(self.cue, self.plan(), self.source / 'bad', self.profile)

    def test_22_cue_mode_index_and_traversal_rejected(self):
        original = self.cue.read_bytes()
        for before, after in [(b'MODE2/2352', b'MODE1/2352'), (b'00:03:00', b'00:02:00'),
                              (b'"source1.bin"', b'"../source1.bin"')]:
            self.cue.write_bytes(original.replace(before, after))
            with self.subTest(after=after), self.assertRaises(m.MigrationError):
                m.read_cue(self.cue)
        self.cue.write_bytes(original)

    def test_23_ISO_endian_mismatch_rejected(self):
        mutate_user(self.source / 'source1.bin', 16, lambda d: d.__setitem__(84, 1))
        with self.assertRaises(m.MigrationError):
            m.inventory(self.source / 'source1.bin')

    def test_24_split_join_bit_exact(self):
        path = self.source / 'source1.bin'
        manifest = m.split_track(path, self.root / 'parts', 13 * m.RAW + 3)
        self.assertTrue(all(x['size'] % m.RAW == 0 for x in manifest['parts']))
        self.assertEqual(manifest['chunk_bytes'], 13 * m.RAW)
        result = m.join_track(self.root / 'parts' / 'TRANSFER.json', self.root / 'restored')
        self.assertEqual(result['sha256'], m.hash_file(path))
        self.assertEqual((self.root / 'restored' / path.name).read_bytes(), path.read_bytes())

    def test_25_transfer_tamper_rejected(self):
        m.split_track(self.source / 'source1.bin', self.root / 'parts', 13 * m.RAW)
        with (self.root / 'parts' / '00001.part').open('r+b') as f:
            f.write(b'!')
        with self.assertRaises(m.MigrationError):
            m.join_track(self.root / 'parts' / 'TRANSFER.json', self.root / 'bad')
        self.assertFalse((self.root / 'bad').exists())

    def test_26_transfer_reorder_rejected_even_resealed(self):
        manifest = m.unseal(m.split_track(self.source / 'source1.bin', self.root / 'parts', 13 * m.RAW))
        manifest['parts'][0], manifest['parts'][1] = manifest['parts'][1], manifest['parts'][0]
        path = self.root / 'parts' / 'REORDERED.json'
        m.write_json(path, m.sealed(manifest))
        with self.assertRaises(m.MigrationError):
            m.join_track(path, self.root / 'bad')

    def test_27_transfer_missing_part_rejected(self):
        m.split_track(self.source / 'source1.bin', self.root / 'parts', 13 * m.RAW)
        (self.root / 'parts' / '00001.part').unlink()
        with self.assertRaises(m.MigrationError):
            m.join_track(self.root / 'parts' / 'TRANSFER.json', self.root / 'bad')

    def test_28_duplicate_JSON_key_rejected(self):
        path = self.root / 'duplicate.json'
        path.write_text('{"x":1,"x":2}')
        with self.assertRaises(m.MigrationError):
            m.load_json(path)

    def test_29_original_invalid_ECC_rejected_not_normalized(self):
        with (self.source / 'source1.bin').open('r+b') as f:
            f.seek(40 * m.RAW + 2248)
            value = f.read(1)[0]
            f.seek(40 * m.RAW + 2248)
            f.write(bytes([value ^ 1]))
        self.profile['tracks'][0] = ((self.source / 'source1.bin').stat().st_size, m.hash_file(self.source / 'source1.bin'))
        with self.assertRaises(m.MigrationError):
            self.candidate({'SCEDATA.BIN': 0}, True)
        self.assertFalse((self.root / 'candidate').exists())

    def test_30_independent_bitwise_EDC(self):
        for data in (b'', b'123456789', bytes(range(256)), bytes([71]) * 2064):
            state = 0
            for value in data:
                state ^= value
                for _ in range(8):
                    state = (state >> 1) ^ (0xD8018001 if state & 1 else 0)
            self.assertEqual(m.edc(data), state)

    def test_31_header_boundary_and_parity_mutation(self):
        self.assertEqual(m.address(0), bytes.fromhex('00020001'))
        self.assertEqual(m.address(74), bytes.fromhex('00027401'))
        self.assertEqual(m.address(75), bytes.fromhex('00030001'))
        a, b = m.mode1(0, bytes(m.USER)), m.mode1(1, bytes(m.USER))
        self.assertNotEqual(a[2064:2068], b[2064:2068])
        self.assertNotEqual(a[2076:], b[2076:])

    def test_32_last_sector_padding_preserved(self):
        plan, _, cue = self.candidate({'SCEDATA.BIN': 0}, True)
        old_lba, new_lba = plan['allocations'][0]['old_lba'], plan['allocations'][0]['new_lba']
        with m.RawImage(self.source / 'source1.bin') as a, m.RawImage(cue.parent / 'Track01.bin') as b:
            self.assertEqual(a.user(old_lba + 1), b.user(new_lba + 1))
            self.assertNotEqual(a.user(old_lba + 1)[452:], bytes(m.USER - 452))

    def test_33_plan_roundtrip_serialization(self):
        plan = self.plan({'SCEDATA.BIN': 1, 'TSR.BIN': 0}, True)
        path = self.root / 'plan.json'
        m.write_json(path, plan)
        self.assertEqual(m.validate_plan(self.cue, m.load_json(path), self.profile), m.unseal(plan))

    def test_34_no_semantic_or_runtime_promotion(self):
        _, report, _ = self.candidate({'SCEDATA.BIN': 0}, True)
        self.assertEqual(report['semantic_payload_changes'], 'NONE')
        self.assertEqual(report['save_compatibility'], 'NOT_RUN')
        self.assertEqual(report['release'], 'BLOCKED_PENDING_RUNTIME')
        self.assertIn('enable_all_flags', m.POLICY['forbidden'])

    def test_35_CLI_help_and_policy(self):
        script = Path(m.__file__)
        for arg in ('--help', 'policy'):
            process = subprocess.run([sys.executable, str(script), arg], capture_output=True, text=True, timeout=20)
            self.assertEqual(process.returncode, 0, process.stderr)

    def test_36_CLI_wrong_version_returns_blocked(self):
        process = subprocess.run([sys.executable, str(Path(m.__file__)), 'scan', '--cue', str(self.cue),
                                  '--out', str(self.root / 'scan.json')], capture_output=True, text=True, timeout=20)
        self.assertEqual(process.returncode, 2)
        self.assertEqual(json.loads(process.stderr)['status'], 'BLOCKED')
        self.assertFalse((self.root / 'scan.json').exists())


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.passed_ids = []
    def addSuccess(self, test):
        super().addSuccess(test)
        self.passed_ids.append(test.id())


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MigrationTests)
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordingResult).run(suite)
    summary = {'schema': 'REVB_TOOL_SYNTHETIC_TEST_RUN_1', 'kind': 'SYNTHETIC_ONLY',
               'python': sys.version, 'platform': sys.platform,
               'tests_run': result.testsRun, 'passes': len(result.passed_ids),
               'failures': len(result.failures), 'errors': len(result.errors),
               'passed_tests': result.passed_ids,
               'failure_details': [(str(t), detail) for t, detail in result.failures + result.errors],
               'source_sha256': m.hash_file(Path(m.__file__)),
               'real_RevB_build': 'NOT_RUN', 'emulator': 'NOT_RUN', 'hardware': 'NOT_RUN'}
    Path('TEST_RESULTS.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() else 1)
