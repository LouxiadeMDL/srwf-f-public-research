#!/usr/bin/env python3
"""Run the complete synthetic suite and write honest acceptance receipts."""
import json
import os
from pathlib import Path
import sys
import unittest
import revb_migrate as m
from test_revb_migrate import MigrationTests, RecordingResult
from test_extra import ExtraTests

suite = unittest.TestSuite([
    unittest.defaultTestLoader.loadTestsFromTestCase(MigrationTests),
    unittest.defaultTestLoader.loadTestsFromTestCase(ExtraTests),
])
result = unittest.TextTestRunner(verbosity=2, resultclass=RecordingResult).run(suite)
status = 'PASS' if result.wasSuccessful() else 'FAIL'
summary = {
    'schema': 'REVB_TOOL_SYNTHETIC_TEST_RUN_1', 'kind': 'SYNTHETIC_ONLY',
    'python': sys.version, 'platform': sys.platform,
    'commit': os.environ.get('GITHUB_SHA'), 'run_id': os.environ.get('GITHUB_RUN_ID'),
    'tests_run': result.testsRun, 'passes': len(result.passed_ids),
    'failures': len(result.failures), 'errors': len(result.errors),
    'passed_tests': result.passed_ids,
    'failure_details': [(str(t), detail) for t, detail in result.failures + result.errors],
    'source_sha256': m.hash_file(Path(m.__file__)),
    'test_sources': {name: m.hash_file(Path(name)) for name in ('test_revb_migrate.py', 'test_extra.py', 'ci_test.py')},
    'real_RevB_build': 'NOT_RUN', 'emulator': 'NOT_RUN', 'hardware': 'NOT_RUN',
}
matrix = {
    'schema': 'REVB_MIGRATION_ACCEPTANCE_MATRIX_1',
    'source_sha256': summary['source_sha256'],
    'commit': summary['commit'], 'run_id': summary['run_id'],
    'synthetic_tests': {'status': status, 'executed': result.testsRun,
                        'passed': len(result.passed_ids), 'failures': len(result.failures), 'errors': len(result.errors)},
    'real_RevB_native_input_byte_verification': 'NOT_RUN_IN_THIS_DELIVERY',
    'real_RevB_noop_build': 'NOT_RUN',
    'real_RevB_relocation_build_and_readback': 'NOT_RUN',
    'second_ECC_implementation_or_external_vector_check': 'NOT_RUN',
    'emulator_cold_boot': 'NOT_RUN',
    'native_save_and_cold_reload': 'NOT_RUN',
    'menu_text_picture_hidden_event_changes': 'NOT_IMPLEMENTED_IN_PHYSICAL_LAYER',
    'multi_track_expansion': 'BLOCKED_NOT_IMPLEMENTED',
    'hardware': 'NOT_RUN',
    'release': 'BLOCKED_PENDING_REAL_IMAGE_AND_RUNTIME_ACCEPTANCE',
}
for name, obj in [('TEST_RESULTS.json', summary), ('ACCEPTANCE_MATRIX.json', matrix)]:
    Path(name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(matrix, ensure_ascii=False, sort_keys=True))
raise SystemExit(0 if result.wasSuccessful() else 1)
