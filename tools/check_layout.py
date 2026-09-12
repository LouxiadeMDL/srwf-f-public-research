"""Check interval arithmetic only; no game data or decoding is involved."""
import argparse
import json


def check(start, end, count, stride):
    if start < 0 or end < start or count < 0 or stride <= 0:
        raise ValueError('Invalid interval, count or stride')
    return end - start == count * stride


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    for name in ('start', 'end', 'count', 'stride'):
        parser.add_argument('--' + name, type=lambda value: int(value, 0))
    args = parser.parse_args()
    if args.self_test:
        cases = [(10, 22, 3, 4, True), (10, 23, 3, 4, False), (0, 0, 0, 1, True)]
        for *values, expected in cases:
            if check(*values) != expected:
                raise RuntimeError('Synthetic check failed')
        for values in [(-1, 0, 1, 1), (3, 2, 1, 1), (0, 1, -1, 1), (0, 1, 1, 0)]:
            try:
                check(*values)
            except ValueError:
                continue
            raise RuntimeError('Invalid-input rejection failed')
        print('PASS: 7 synthetic checks; no game claim')
        return
    values = [args.start, args.end, args.count, args.stride]
    if None in values:
        parser.error('Provide --start, --end, --count and --stride')
    try:
        matches = check(*values)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps({'arithmetic_matches': matches, 'runtime_verified': False}))
    if not matches:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
