"""Additional synthetic tests, using no game bytes."""
import struct
import unittest
import revb_migrate as m
from test_revb_migrate import MigrationTests, mutate_user, iso_both


class ExtraTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        MigrationTests.setUpClass.__func__(cls)
    @classmethod
    def tearDownClass(cls):
        MigrationTests.tearDownClass.__func__(cls)
    setUp = MigrationTests.setUp
    tearDown = MigrationTests.tearDown
    plan = MigrationTests.plan
    candidate = MigrationTests.candidate

    def refresh(self):
        path = self.source / 'source1.bin'
        self.profile['tracks'][0] = (path.stat().st_size, m.hash_file(path))

    def test_37_cyclic_swap_reads_original_not_overwritten_output(self):
        path = self.source / 'source1.bin'
        with m.RawImage(path) as image:
            zeros = [lba for lba in range(25, image.count) if image.user(lba) == bytes(m.USER)]
        for lba in zeros:
            mutate_user(path, lba, lambda data: data.__setitem__(slice(None), bytes([0x55]) * m.USER))
        self.refresh()
        plan, result, cue = self.candidate({'SCEDATA.BIN': 0, 'TSR.BIN': 0}, True)
        locations = {x['name']: x['new_lba'] for x in plan['allocations']}
        self.assertEqual(locations, {'SCEDATA.BIN': 48, 'TSR.BIN': 40})
        self.assertEqual(result['static'], 'PASS')
        # Direct sector slices independently confirm the two-way swap.
        original = path.read_bytes()
        output = (cue.parent / 'Track01.bin').read_bytes()
        for old, new in ((40, 48), (48, 40)):
            for offset in (0, 1):
                self.assertEqual(original[(old + offset) * 2352 + 16:(old + offset) * 2352 + 2064],
                                 output[(new + offset) * 2352 + 16:(new + offset) * 2352 + 2064])

    def test_38_alias_split_rejected(self):
        path = self.source / 'source1.bin'
        face = next(x for x in m.inventory(path)['files'] if x['name'] == 'FACE.BIN')
        lba, offset = divmod(face['record_offset'], m.USER)
        def change(data):
            data[offset + 2:offset + 10] = iso_both(40)
            data[offset + 10:offset + 18] = iso_both(2500)
        mutate_user(path, lba, change)
        self.refresh()
        self.assertEqual(len(m.inventory(path)['files']), 7)
        with self.assertRaisesRegex(m.MigrationError, 'Shared top-level extent'):
            self.plan({'SCEDATA.BIN': 0}, True)

    def test_39_partial_extent_overlap_rejected(self):
        path = self.source / 'source1.bin'
        face = next(x for x in m.inventory(path)['files'] if x['name'] == 'FACE.BIN')
        lba, offset = divmod(face['record_offset'], m.USER)
        mutate_user(path, lba, lambda data: data.__setitem__(slice(offset + 2, offset + 10), iso_both(41)))
        with self.assertRaisesRegex(m.MigrationError, 'Partial file overlap'):
            m.inventory(path)

    def test_40_independent_directory_and_payload_reader(self):
        plan, _, cue = self.candidate({'SCEDATA.BIN': 2048, 'TSR.BIN': 0}, True)
        raw = (cue.parent / 'Track01.bin').read_bytes()
        original = (self.source / 'source1.bin').read_bytes()
        directory = raw[20 * 2352 + 16:20 * 2352 + 2064]
        pos, locations = 0, {}
        while directory[pos]:
            length = directory[pos]
            name_length = directory[pos + 32]
            name = directory[pos + 33:pos + 33 + name_length]
            extent = struct.unpack_from('<I', directory, pos + 2)[0]
            self.assertEqual(extent, struct.unpack_from('>I', directory, pos + 6)[0])
            size = struct.unpack_from('<I', directory, pos + 10)[0]
            locations[name] = (extent, size)
            pos += length
        for name, old, size in ((b'SCEDATA.BIN;1', 40, 2500), (b'TSR.BIN;1', 48, 3200)):
            new, actual_size = locations[name]
            self.assertEqual(actual_size, size)
            count = (size + 2047) // 2048
            actual = b''.join(raw[(new+i)*2352+16:(new+i)*2352+2064] for i in range(count))[:size]
            expected = b''.join(original[(old+i)*2352+16:(old+i)*2352+2064] for i in range(count))[:size]
            self.assertEqual(actual, expected)
        self.assertEqual(locations[b'0;1'][0], 21)
