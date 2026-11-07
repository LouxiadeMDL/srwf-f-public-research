"""Recompute six source-bound root11 pairs from a user-held archive, without dumps."""
from pathlib import Path
from zipfile import ZipFile
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parent
SCENES = {
    'P12': '481c1eca6c675824bb8e9e985528d4199d3f51c1e5aaef12ccca84c452b8e148',
    'P30': 'cf6fbf72e8328c06ea9f93e554b231222307b0c40f52ce031a1366aea7d7abaf',
    'P47': 'a7cb85e1dfec73ce282b8082e6c0b3227599d3caa77a419b1c3b055f135f2f50',
}

def audit(archive):
    results = []
    with ZipFile(archive) as z:
        for scene, digest in SCENES.items():
            name = 'HVM04B_H02_Semantics_20261018/work/hvm04_input_recovery/inputs/scenes/' + scene + '.bin'
            if sum(i.filename == name for i in z.infolist()) != 1:
                raise ValueError('Missing or duplicate scene: ' + scene)
            if z.getinfo(name).file_size > 100000:
                raise ValueError('Oversized scene')
            data = z.read(name)
            if hashlib.sha256(data).hexdigest() != digest:
                raise ValueError('Unexpected scene identity: ' + scene)
            be16 = lambda at: int.from_bytes(data[at:at + 2], 'big')
            root = lambda i: 4 * i + int.from_bytes(data[4*i:4*i+4], 'big', signed=True)
            r11, r12 = root(11), root(12)
            pairs = []
            for at in (r11, r11 + 10):
                if data[at:at+2] != bytes([0xEB, 1]) or data[at+6:at+8] != bytes([0xF0, 0]):
                    raise ValueError('Unexpected pair/branch grammar')
                target = at + 8 + int.from_bytes(data[at+8:at+10], 'big', signed=True)
                if not 0 <= target <= len(data) - 4 or data[target:target+2] != bytes([0xD0, 2]):
                    raise ValueError('Expected following flag query')
                pairs.append({'offset': hex(at), 'first': f'{be16(at+2):04X}',
                              'second': f'{be16(at+4):04X}', 'F0_target': hex(target),
                              'target_flag': f'{be16(target+2):04X}'})
            results.append({'scene': scene, 'sha256': digest, 'root11': hex(r11),
                            'root12': hex(r12), 'ordered_pairs': pairs})
    return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists() or not args.out.resolve().is_relative_to((ROOT / '.local_results').resolve()):
        parser.error('Use a new file under this handoff .local_results directory')
    result = audit(args.archive)
    expected = json.loads((ROOT / 'ROOT11_PAIRS.json').read_text(encoding='utf-8'))
    if result != expected:
        raise ValueError('Result differs from the frozen structural summary')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print('PASS: three source-bound scenes, six pairs; no natural gameplay claimed')
