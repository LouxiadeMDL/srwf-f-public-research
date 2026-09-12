"""Check an explicit reviewed allowlist, digests and suspicious text patterns.

This is a guard against accidental changes, not a rights or secret-free proof.
The manifest must be maintained manually after content review.
"""
import hashlib
import json
import re
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent.parent
    manifest_name = 'PUBLICATION_MANIFEST.json'
    manifest = json.loads((root / manifest_name).read_text(encoding='utf-8'))
    expected = manifest['files']
    actual = {}
    errors = []
    patterns = [r'(?i)[a-z]:[\\/]', r'gh[pousr]_[A-Za-z0-9]{20,}',
                r'github_pat_[A-Za-z0-9_]{20,}', '-----BEGIN ' + r'.*PRIVATE KEY' + '-----',
                r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
                r'(?i)drive\.google\.com', r'(?i)chatgpt\.com/c/']
    for path in root.rglob('*'):
        relative = path.relative_to(root)
        if '.git' in relative.parts:
            continue
        if path.is_symlink():
            errors.append(f'Symlink rejected: {relative}')
            continue
        if not path.is_file():
            continue
        name = relative.as_posix()
        data = path.read_bytes()
        if name != manifest_name:
            actual[name] = hashlib.sha256(data).hexdigest()
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            errors.append(f'Non-UTF-8 file: {name}')
            continue
        if b'\0' in data or len(data) > 100_000:
            errors.append(f'Binary marker or excessive size: {name}')
        for pattern in patterns:
            if re.search(pattern, text):
                errors.append(f'Suspicious text pattern: {name}')
    for name in sorted(actual.keys() | expected.keys()):
        if actual.get(name) != expected.get(name):
            errors.append(f'Unreviewed, missing or changed: {name}')
    if errors:
        print('\n'.join(errors))
        raise SystemExit(1)
    print(f'PASS: {len(actual)} payload files match reviewed allowlist; manual review still required')


if __name__ == '__main__':
    main()
