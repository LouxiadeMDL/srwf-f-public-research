"""Read one local input; emit metadata only. No uploads or writes."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', args.label):
        parser.error('Use a short public label containing letters, numbers, _ or -.')
    digest = hashlib.sha256()
    size = 0
    try:
        with args.input.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(block)
                size += len(block)
    except OSError:
        parser.exit(1, 'Cannot read the selected input.\n')
    print(json.dumps({'label': args.label, 'size': size, 'sha256': digest.hexdigest()}))


if __name__ == '__main__':
    main()
