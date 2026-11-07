"""Publication-tool regression tests; no ROM, executor, or emulator required."""
from pathlib import Path
from copy import deepcopy
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile
import prepare_input
from validate_probes import validate

class Tests(unittest.TestCase):
    def setUp(self):
        self.result = json.loads((Path(__file__).parent / 'PROBES_SUMMARY.json').read_text())
    def test_recorded_19_outcomes(self):
        self.assertEqual(validate(self.result)['passed'], 19)
    def test_missing_case_rejected(self):
        self.result['cases'].pop()
        with self.assertRaises(AssertionError): validate(self.result)
    def test_reversed_predicate_rejected(self):
        self.result['cases'][0]['predicate_bit7'] = True
        with self.assertRaises(AssertionError): validate(self.result)
    def test_item_cap_violation_rejected(self):
        row = next(c for c in self.result['cases'] if c['type'] == 'C2.0E' and c['initial'] == 9)
        row['after'] = 10
        with self.assertRaises(AssertionError): validate(self.result)
    def test_stale_value_not_silently_zeroed(self):
        row = next(c for c in self.result['cases'] if c['type'] == 'C1.0A' and c['selector'] == '0x1ee')
        row['numeric'] = 0
        with self.assertRaises(AssertionError): validate(self.result)
    def test_alignment_rejection_required(self):
        self.result['alignment'][-1]['outcome'] = 'RETURNED'
        with self.assertRaises(AssertionError): validate(self.result)
    def test_query_must_not_write_low_ram(self):
        self.result['cases'][0]['low_stores'] = [{'region': 'low'}]
        with self.assertRaises(AssertionError): validate(self.result)
    def test_prepare_checks_all_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); archive = root / 'synthetic.zip'; out = root / 'private'
            with ZipFile(archive, 'w') as z: z.writestr('first', b'A'); z.writestr('second', b'B')
            spec = {'one': ('first', hashlib.sha256(b'A').hexdigest()),
                    'two': ('second', hashlib.sha256(b'C').hexdigest())}
            with patch.object(prepare_input, 'MEMBERS', spec):
                with self.assertRaises(ValueError): prepare_input.prepare(archive, out)
            self.assertFalse(out.exists())
    def test_prepare_refuses_different_existing_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); archive = root / 'synthetic.zip'; out = root / 'private'; out.mkdir()
            (out / 'one').write_bytes(b'B')
            with ZipFile(archive, 'w') as z: z.writestr('first', b'A')
            spec = {'one': ('first', hashlib.sha256(b'A').hexdigest())}
            with patch.object(prepare_input, 'MEMBERS', spec):
                with self.assertRaises(ValueError): prepare_input.prepare(archive, out)
            self.assertEqual((out / 'one').read_bytes(), b'B')

if __name__ == '__main__': unittest.main(verbosity=2)
