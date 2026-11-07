"""Check bounded result summaries. This does not independently emulate a game."""
from pathlib import Path
from collections import Counter
import argparse
import json

ROOT = Path(__file__).resolve().parent

def validate(result):
    cases = result['cases']
    assert Counter(c['type'] for c in cases) == {'EB.01': 6, 'C2.0E': 6, 'C1.0A': 3}
    assert len(result['alignment']) == 4
    checks = []
    for c in cases:
        ok = not c['hooks']
        if c['type'] == 'EB.01':
            slots = {'0x7e': 3, '0x84': 5}
            expected = tuple(c['pair']) == tuple(slots[x] for x in c['selectors'])
            ok = ok and c['predicate_bit7'] == (not expected)
            ok = ok and c['R0'] == '0x6005' and c['numeric'] == 0x77777777
            ok = ok and not c['low_stores']
        elif c['type'] == 'C2.0E':
            allowed = c['item'] < 30 and c['initial'] <= 8
            ok = ok and c['after'] == c['initial'] + int(allowed)
            ok = ok and c['predicate_bit7'] == (not allowed) and c['R0'] == '0x6002'
            low = c['low_stores']
            ok = ok and len(low) == int(allowed)
            if low:
                ok = ok and int(low[0]['address'], 0) == 0x20200574 + c['item']
                ok = ok and low[0]['pc'] == '0x0602BBB2'
        else:
            found = c['selector'] in ('0x7e', '0x84')
            ok = ok and c['predicate_bit7'] == (not found)
            ok = ok and c['numeric'] == (100 if found else 0x77777777)
            ok = ok and c['R0'] == '0x6003' and not c['low_stores']
        assert ok, c
        checks.append({'case': c['type'], 'pass': True})
    expected_pairs = {(m, a) for m in ('Memory', 'StrictMemory')
                      for a in ('0x20000000', '0x20000002')}
    assert {(c['memory'], c['address']) for c in result['alignment']} == expected_pairs
    for c in result['alignment']:
        reject = c['memory'] == 'StrictMemory' and int(c['address'], 0) % 4 != 0
        assert c['outcome'] == ('REJECTED' if reject else 'RETURNED'), c
        checks.append({'case': 'alignment ' + c['memory'] + ' ' + c['address'], 'pass': True})
    return {'passed': len(checks), 'failed': 0, 'checks': checks}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('result', type=Path)
    parser.add_argument('--reference', type=Path, default=ROOT / 'PROBES_SUMMARY.json')
    args = parser.parse_args()
    result = json.loads(args.result.read_text(encoding='utf-8'))
    answer = validate(result)
    reference = json.loads(args.reference.read_text(encoding='utf-8'))
    assert result == reference, 'Result differs from the frozen summary'
    answer['matches_frozen_summary'] = True
    print(json.dumps(answer, ensure_ascii=False, indent=2))
