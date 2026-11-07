"""Prepare hash-bound local inputs from a user-held archive; do not distribute them."""
from pathlib import Path
from zipfile import ZipFile
import argparse
import hashlib

ROOT = Path(__file__).resolve().parent
MEMBERS = {
    'EXEC0.bin': (
        'HVM04B_H02_Semantics_20261018/work/hvm04_input_recovery/inputs/0',
        'a7e9a648641d728dcf6f60a778d6a1e5ccfebc77c92a0d3fd64cbcd5f19db409'),
    'vendor/sh2_subset.py': (
        'HVM04B_H02_Semantics_20261018/work/h02_local_semantics/sh2_subset.py',
        '588686ebb6a16c7a9f5bc2d0b893d492c79ea3334c02e5a001a7921add3edf30'),
}

def prepare(archive: Path, destination: Path) -> None:
    """Read two exact members; reject mismatches before any output is written."""
    original = hashlib.sha256(archive.read_bytes()).hexdigest()
    pending = []
    with ZipFile(archive) as z:
        for name, (member, expected) in MEMBERS.items():
            if sum(i.filename == member for i in z.infolist()) != 1:
                raise ValueError('Missing or duplicate required member: ' + member)
            if z.getinfo(member).file_size > 2 * 1024 * 1024:
                raise ValueError('Oversized required member')
            data = z.read(member)
            if hashlib.sha256(data).hexdigest() != expected:
                raise ValueError('Input identity mismatch: ' + name)
            target = destination / name
            if target.is_symlink():
                raise ValueError('Refusing a symbolic-link destination')
            if target.exists() and target.read_bytes() != data:
                raise ValueError('Refusing to replace different local input')
            pending.append((target, data))
    for target, data in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            with target.open('xb') as f:
                f.write(data)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != original:
        raise RuntimeError('Source archive changed during preparation')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True, type=Path)
    args = parser.parse_args()
    prepare(args.archive, ROOT / '.local_inputs')
    print('Verified EXEC0 and executor in ignored local inputs; source unchanged')
