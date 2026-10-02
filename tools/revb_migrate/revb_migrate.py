#!/usr/bin/env python3
"""RevB migration v0.1: physical relocation only; Python 3.10+; no game assets.

Original inputs are read-only. Production entrypoints pin all three native tracks.
No semantic patching, codec execution, track growth or runtime-PASS promotion.
See README_CN.md for scope, rules, sequence and acceptance boundaries.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import mmap
import os
from pathlib import Path
import re
import shutil
import struct
import sys
import tempfile
from contextlib import contextmanager
from typing import Any

VERSION = '0.1.0'
RAW, USER = 2352, 2048
SYNC = b'\x00' + b'\xff' * 10 + b'\x00'
NATIVE = {
    'kind': 'REVB_21M', 'files': 34,
    'tracks': [
        (238711536, '66fe113b6c0d99dc74c9f32e587466877719ecd67a59a7c1adea1b71f5e5707a'),
        (335919696, 'e7b397d1711dcae23eed94889947d72cf712f7342d3403ab52990fabbc8a4281'),
        (3880800, '66f03f518c58106976cab1f83c19190103f10f66ccc40ce049c7e08cce58691b'),
    ],
}
ORDER = ['SCEDATA.BIN', 'TSR.BIN', 'BMESS.BIN', 'DIC.BIN',
         'FACE.BIN', 'EFFECT.BIN', 'C_ROBOT.BIN', 'KOM.PAC']
POLICY = {
    'version': VERSION, 'scope': 'Saturn F RevB 21M; physical Track1 relocation only',
    'workflow': ['pin_inputs', 'parse_native_directory', 'audit_zero_gaps',
                 'allocate_prefer_in_place', 'seal_plan', 'build_new_copy',
                 'full_raw_readback', 'all_file_readback', 'rehash_inputs',
                 'external_runtime_and_save_acceptance'],
    'allocation_order': ORDER,
    'forbidden': ['overwrite_inputs_or_outputs', 'run_unknown_executable',
                  'write_WP_RevA_PS_FF_bytes', 'move_root0_or_metadata',
                  'change_track_lengths_modes_or_indexes', 'rewrite_XA_or_audio',
                  'split_alias_groups', 'guess_free_space_from_directory_absence',
                  'change_payload_or_internal_pointers', 'enable_all_flags',
                  'promote_synthetic_T0_to_native_DLC', 'claim_runtime_from_static_pass'],
    'not_implemented': ['semantic_payload_import', 'text_encoding_or_compression',
                        'hidden_event_patching', 'multi_track_expansion', 'emulator_runner'],
    'zero_gap_warning': 'Zero user data is an allocation candidate, not proof of no hidden runtime consumer.',
    'runtime': 'NOT_RUN', 'save_compatibility': 'NOT_RUN',
}

class MigrationError(Exception):
    pass


def require(ok: bool, message: str) -> None:
    if not ok:
        raise MigrationError(message)


def integer(x: Any, minimum: int = 0, maximum: int = 0xFFFFFFFF) -> int:
    require(type(x) is int and minimum <= x <= maximum, 'Invalid integer/range')
    return x


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def sealed(body: dict) -> dict:
    require('seal_sha256' not in body, 'Already sealed')
    return dict(body, seal_sha256=sha(canonical(body)))


def unseal(obj: dict) -> dict:
    body = dict(obj)
    digest = body.pop('seal_sha256', None)
    require(digest == sha(canonical(body)), 'Manifest/plan seal mismatch')
    return body


def load_json(path: Path) -> dict:
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, 'Duplicate JSON key: ' + key)
            out[key] = value
        return out
    obj = json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=pairs)
    require(isinstance(obj, dict), 'JSON root must be an object')
    return obj


def write_json(path: Path, obj: Any) -> None:
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write('\n')


def base_name(name: str) -> str:
    require(isinstance(name, str) and bool(name) and name not in ('.', '..'), 'Invalid name')
    require(not any(c in name for c in '/\\:\x00\r\n'), 'Only local basenames are supported')
    require(name == name.strip() and not name.endswith('.'), 'Ambiguous Windows basename')
    return name


@contextmanager
def new_directory(destination: Path, sources: list[Path]):
    destination = destination.absolute()
    require(not destination.exists() and not destination.is_symlink(), 'Output already exists')
    require(destination.parent.is_dir(), 'Output parent must exist')
    resolved = destination.resolve()
    for src in sources:
        parent = src.resolve().parent
        require(resolved != parent and parent not in resolved.parents,
                'Output must be outside every input directory')
    with tempfile.TemporaryDirectory(prefix='.revb-staging-', dir=destination.parent) as tmp:
        staging = Path(tmp) / 'result'
        staging.mkdir()
        yield staging
        require(not destination.exists(), 'Output appeared during build')
        os.rename(staging, destination)


def bcd(n: int) -> int:
    require(0 <= n <= 99, 'CD address out of range')
    return (n // 10) * 16 + n % 10


def address(lba: int) -> bytes:
    frames = integer(lba) + 150
    minutes, rest = divmod(frames, 4500)
    seconds, frame = divmod(rest, 75)
    return bytes((bcd(minutes), bcd(seconds), bcd(frame), 1))


# Original Python implementation of the CD-ROM EDC and Reed-Solomon parity
# arithmetic. Format reference: ECMA-130; terminology cross-check: ECM/edccchk.
GF = [((x << 1) ^ (0x11D if x & 128 else 0)) for x in range(256)]
INV = [0] * 256
for _x in range(256):
    INV[_x ^ GF[_x]] = _x
CRC = []
for _x in range(256):
    _r = _x
    for _ in range(8):
        _r = (_r >> 1) ^ (0xD8018001 if _r & 1 else 0)
    CRC.append(_r)


def edc(data: bytes | bytearray) -> int:
    state = 0
    for value in data:
        state = (state >> 8) ^ CRC[(state ^ value) & 255]
    return state


def parity(data: bytes | bytearray, rows: int, columns: int, step: int, increment: int) -> bytes:
    require(len(data) == rows * columns, 'Parity input length')
    result = bytearray(2 * rows)
    for row in range(rows):
        pos = (row // 2) * step + row % 2
        a = b = 0
        for _ in range(columns):
            value = data[pos]
            b ^= value
            a = GF[a ^ value]
            pos = (pos + increment) % len(data)
        left = INV[GF[a] ^ b]
        result[row] = left
        result[row + rows] = left ^ b
    return bytes(result)


def mode1(lba: int, payload: bytes) -> bytes:
    require(len(payload) == USER, 'Mode1 needs exactly 2048 user bytes')
    out = bytearray(RAW)
    out[:12], out[12:16], out[16:2064] = SYNC, address(lba), payload
    struct.pack_into('<I', out, 2064, edc(out[:2064]))
    out[2076:2248] = parity(out[12:2076], 86, 24, 2, 86)
    out[2248:2352] = parity(out[12:2248], 52, 43, 86, 88)
    return bytes(out)


class RawImage:
    def __init__(self, path: Path):
        self.path = path
        size = path.stat().st_size
        require(size > 0 and size % RAW == 0, 'Not a complete 2352-byte-sector image')
        self.count = size // RAW
        self.file = path.open('rb')
        self.mapping = mmap.mmap(self.file.fileno(), 0, access=mmap.ACCESS_READ)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.mapping.close()
        self.file.close()

    def raw(self, lba: int) -> bytes:
        require(0 <= lba < self.count, 'LBA outside Track1')
        return self.mapping[lba * RAW:(lba + 1) * RAW]

    def user(self, lba: int) -> bytes:
        data = self.raw(lba)
        require(data[:12] == SYNC and data[12:16] == address(lba), 'Unexpected Mode1 header/MSF')
        return data[16:2064]

    def logical(self, lba: int, size: int) -> bytes:
        require(size >= 0 and lba + (size + USER - 1) // USER <= self.count, 'Extent beyond Mode1')
        return b''.join(self.user(i) for i in range(lba, lba + (size + USER - 1) // USER))[:size]


def both(data: bytes, offset: int, width: int = 4) -> int:
    a = int.from_bytes(data[offset:offset + width], 'little')
    b = int.from_bytes(data[offset + width:offset + 2 * width], 'big')
    require(a == b, 'ISO little/big-endian copies differ')
    return a


def read_cue(path: Path) -> dict:
    text = path.read_bytes().decode('utf-8-sig')
    tracks, current = [], None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(('REM ', 'CATALOG ')):
            continue
        match = re.fullmatch(r'FILE "([^"\r\n]+)" BINARY', line)
        if match:
            name = base_name(match.group(1))
            current = {'name': name, 'indexes': {}}
            tracks.append(current)
            continue
        match = re.fullmatch(r'TRACK (\d{2}) (MODE1/2352|MODE2/2352|AUDIO)', line)
        if match:
            require(current is not None and 'number' not in current, 'One track per FILE required')
            current.update(number=int(match.group(1)), mode=match.group(2))
            continue
        match = re.fullmatch(r'INDEX (\d{2}) (\d{2}):(\d{2}):(\d{2})', line)
        if match:
            require(current is not None and 'number' in current, 'INDEX without TRACK')
            index, minute, second, frame = map(int, match.groups())
            require(index not in current['indexes'] and second < 60 and frame < 75, 'Invalid INDEX')
            current['indexes'][index] = (minute * 60 + second) * 75 + frame
            continue
        raise MigrationError('Unsupported CUE statement: ' + line)
    require(len(tracks) == 3, 'Exactly three distinct track files required')
    expected = [('MODE1/2352', {1: 0}), ('MODE2/2352', {0: 0, 1: 225}), ('AUDIO', {0: 0, 1: 150})]
    paths = []
    for number, (track, (mode, indexes)) in enumerate(zip(tracks, expected), 1):
        require(track.get('number') == number and track.get('mode') == mode and track['indexes'] == indexes,
                'Track mode, number or pregap/index differs from supported RevB topology')
        file = path.parent / track['name']
        require(file.is_file() and not file.is_symlink(), 'Missing track or symbolic link')
        require(all(not os.path.samefile(file, other) for other in paths), 'Track files alias each other')
        require(file.stat().st_size % RAW == 0 and file.stat().st_size // RAW > max(indexes.values()), 'Incomplete track')
        paths.append(file)
    return {'text': text, 'tracks': tracks, 'paths': paths, 'cue_sha256': hash_file(path)}


def freeze(cue: Path, profile: dict = NATIVE) -> dict:
    parsed = read_cue(cue)
    rows = []
    require(profile['kind'] in ('REVB_21M', 'SYNTHETIC'), 'Unknown profile kind')
    for path, (size, digest) in zip(parsed['paths'], profile['tracks']):
        actual = (path.stat().st_size, hash_file(path))
        require(actual == (size, digest), 'Wrong source version/hash: ' + path.name)
        rows.append({'size': actual[0], 'sha256': actual[1]})
    return {'kind': profile['kind'], 'cue_sha256': parsed['cue_sha256'], 'tracks': rows}


def inventory(track1: Path) -> dict:
    with RawImage(track1) as image:
        pvd = image.user(16)
        require(pvd[:7] == b'\x01CD001\x01', 'Primary descriptor must be at LBA16')
        require(both(pvd, 128, 2) == USER, 'Unsupported ISO logical block size')
        volume = both(pvd, 80)
        path_size = both(pvd, 132)
        protected = [(0, 16)]
        terminated = False
        for lba in range(16, min(image.count, 256)):
            descriptor = image.user(lba)
            require(descriptor[1:7] == b'CD001\x01', 'Bad descriptor')
            require(descriptor[0] in (1, 255) and (lba == 16 or descriptor[0] == 255),
                    'Supplementary/boot descriptors need a separate contract')
            if descriptor[0] == 255:
                protected.append((16, lba + 1))
                terminated = True
                break
        require(terminated, 'Missing volume descriptor terminator')
        require(path_size > 0, 'Empty path table')
        for offset, endian in ((140, 'little'), (144, 'little'), (148, 'big'), (152, 'big')):
            location = int.from_bytes(pvd[offset:offset + 4], endian)
            if location:
                end = location + (path_size + USER - 1) // USER
                require(end <= image.count, 'Path table beyond Track1')
                protected.append((location, end))
        root = pvd[156:190]
        require(root[0] == 34 and root[1] == 0 and root[25] & 2, 'Unsupported root record')
        root_lba, root_size = both(root, 2), both(root, 10)
        require(root_size > 0, 'Empty root directory')
        root_end = root_lba + (root_size + USER - 1) // USER
        protected.append((root_lba, root_end))
        directory = image.logical(root_lba, root_size)
        entries, pos = [], 0
        while pos < len(directory):
            length = directory[pos]
            if not length:
                boundary = min(((pos // USER) + 1) * USER, len(directory))
                require(not any(directory[pos:boundary]), 'Nonzero directory padding')
                pos = boundary
                continue
            require(length >= 34 and pos % USER + length <= USER and pos + length <= len(directory), 'Invalid directory record length')
            record = directory[pos:pos + length]
            name_length = record[32]
            require(33 + name_length <= length, 'Invalid ISO identifier length')
            identity = record[33:33 + name_length]
            location, size = both(record, 2), both(record, 10)
            require(both(record, 28, 2) == 1, 'Unsupported volume sequence')
            if identity in (b'\x00', b'\x01'):
                require(location == root_lba and size == root_size and record[25] & 2, 'Root self/parent mismatch')
            else:
                require(not (record[25] & (2 | 128)), 'Subdirectories/multi-extent files not supported')
                require(record[1] == 0, 'Extended attributes not supported')
                name = identity.decode('ascii').split(';')[0]
                base_name(name)
                require(location < volume and size > 0, 'Invalid extent')
                sectors = (size + USER - 1) // USER
                inside = location + sectors <= image.count
                if inside:
                    require(record[26] == 0 and record[27] == 0, 'Interleaved Mode1 resource')
                    payload = image.logical(location, sectors * USER)
                    digest, padded = sha(payload[:size]), sha(payload)
                else:
                    require(name in ('ADPCM.XA', 'LEVELUP.XA') and location >= image.count,
                            'Unknown cross-track or boundary-straddling resource')
                    digest = padded = None
                entries.append({'name': name, 'identifier': identity.decode('ascii'), 'lba': location,
                                'size': size, 'sectors': sectors, 'inside_track1': inside,
                                'sha256': digest, 'padded_sha256': padded,
                                'record_offset': root_lba * USER + pos,
                                'record_other_sha256': sha(record[:2] + record[10:])})
            pos += length
        require(len({row['name'] for row in entries}) == len(entries), 'Ambiguous duplicate filename')
        for row in entries:
            if not row['inside_track1']:
                continue
            a, b = row['lba'], row['lba'] + row['sectors']
            require(all(b <= x or a >= y for x, y in protected), 'File overlaps protected metadata')
        local = [row for row in entries if row['inside_track1']]
        for i, left in enumerate(local):
            for right in local[i + 1:]:
                overlap = max(left['lba'], right['lba']) < min(left['lba'] + left['sectors'], right['lba'] + right['sectors'])
                require(not overlap or (left['lba'], left['size']) == (right['lba'], right['size']), 'Partial file overlap')
        return {'track1_sectors': image.count, 'volume_sectors': volume,
                'root_lba': root_lba, 'root_size': root_size,
                'protected': protected, 'files': entries}


def make_plan(cue: Path, requests: dict[str, int], relocate: bool = False,
              alignment: int = 16, profile: dict = NATIVE) -> dict:
    frozen = freeze(cue, profile)
    parsed = read_cue(cue)
    inv = inventory(parsed['paths'][0])
    require(len(inv['files']) == profile['files'], 'Unexpected native directory file count')
    integer(alignment, 1, 4096)
    require(type(relocate) is bool and isinstance(requests, dict), 'Invalid planning options')
    resources = {row['name']: row for row in inv['files']}
    for name, reserve in requests.items():
        require(name in ORDER and name in resources, 'Resource is pinned or not whitelisted: ' + name)
        integer(reserve, 0, 64 * 1024 * 1024)
        item = resources[name]
        require(item['inside_track1'], 'Cannot move external resource')
        require(sum((r['lba'], r['size']) == (item['lba'], item['size']) for r in inv['files']) == 1,
                'Shared top-level extent: moving/splitting aliases is prohibited')
    available = bytearray(inv['track1_sectors'])
    occupied = bytearray(len(available))
    for start, end in inv['protected']:
        occupied[start:end] = b'\x01' * (end - start)
    for item in inv['files']:
        if item['inside_track1']:
            start, end = item['lba'], item['lba'] + item['sectors']
            occupied[start:end] = b'\x01' * (end - start)
    with RawImage(parsed['paths'][0]) as image:
        for lba, used in enumerate(occupied):
            if not used:
                available[lba] = int(image.user(lba) == bytes(USER))
    zero_sectors = sum(available)
    for name in requests:
        item = resources[name]
        available[item['lba']:item['lba'] + item['sectors']] = b'\x01' * item['sectors']
    candidates = sum(available)
    allocations = []
    def fits(start, count):
        return 0 <= start and start + count <= len(available) and all(available[start:start + count])
    for name in ORDER:
        if name not in requests:
            continue
        item = resources[name]
        count = item['sectors'] + (requests[name] + USER - 1) // USER
        target = None
        if not relocate and fits(item['lba'], count):
            target = item['lba']
        else:
            for candidate in range(0, len(available) - count + 1, alignment):
                if (not relocate or candidate != item['lba']) and fits(candidate, count):
                    target = candidate
                    break
        require(target is not None, 'NO_CAPACITY_WITHIN_TRACK1: ' + name + '; no cross-track expansion attempted')
        available[target:target + count] = bytes(count)
        allocations.append({'name': name, 'old_lba': item['lba'], 'new_lba': target,
                            'file_sectors': item['sectors'], 'allocated_sectors': count,
                            'logical_size': item['size'], 'payload_sha256': item['sha256'],
                            'record_offset': item['record_offset']})
    # Convert tuples to JSON-compatible lists before sealing/comparison.
    inv = json.loads(canonical(inv))
    return sealed({'schema': 'REVB_MIGRATION_PLAN_1', 'version': VERSION,
                   'input': frozen, 'requests': requests, 'relocate': relocate,
                   'alignment': alignment, 'inventory': inv, 'allocations': allocations,
                   'capacity': {'zero_candidate_sectors': zero_sectors,
                                'selected_source_plus_zero_sectors': candidates,
                                'unallocated_candidate_sectors': sum(available),
                                'reserved_bytes': sum((a['allocated_sectors'] - a['file_sectors']) * USER for a in allocations)},
                   'runtime': 'NOT_RUN', 'release': 'BLOCKED_PENDING_RUNTIME',
                   'warnings': [POLICY['zero_gap_warning'], 'Disk reserve does not prove RAM/decompression capacity.']})


def validate_plan(cue: Path, plan: dict, profile: dict = NATIVE) -> dict:
    body = unseal(plan)
    require(body.get('schema') == 'REVB_MIGRATION_PLAN_1', 'Unknown plan schema')
    current = make_plan(cue, body['requests'], body['relocate'], body['alignment'], profile)
    require(canonical(plan) == canonical(current), 'Plan differs from independently recalculated allocation')
    return body


def recipe(source: RawImage, plan: dict) -> tuple[set[int], dict[int, bytes]]:
    touched, directory = set(), {}
    for item in plan['allocations']:
        old, new = item['old_lba'], item['new_lba']
        touched.update(range(old, old + item['file_sectors']))
        touched.update(range(new, new + item['allocated_sectors']))
        if old != new:
            sector, offset = divmod(item['record_offset'], USER)
            if sector not in directory:
                directory[sector] = bytearray(source.user(sector))
            directory[sector][offset + 2:offset + 10] = struct.pack('<I', new) + struct.pack('>I', new)
            touched.add(sector)
    return touched, {key: bytes(value) for key, value in directory.items()}


def expected_sector(source: RawImage, lba: int, plan: dict, directory: dict[int, bytes]) -> bytes:
    if lba in directory:
        return mode1(lba, directory[lba])
    for item in plan['allocations']:
        rel = lba - item['new_lba']
        if 0 <= rel < item['allocated_sectors']:
            payload = source.user(item['old_lba'] + rel) if rel < item['file_sectors'] else bytes(USER)
            return mode1(lba, payload)
    for item in plan['allocations']:
        if item['old_lba'] <= lba < item['old_lba'] + item['file_sectors']:
            return mode1(lba, bytes(USER))
    return source.raw(lba)


def render_cue(parsed: dict) -> str:
    index = 0
    def replace(match):
        nonlocal index
        index += 1
        return match.group(1) + f'Track{index:02d}.bin' + match.group(3)
    return re.sub(r'(?m)^(\s*FILE ")([^"\r\n]+)(" BINARY[^\r\n]*)', replace, parsed['text'])


def verify_candidate(cue: Path, plan: dict, candidate_cue: Path, profile: dict = NATIVE) -> dict:
    body = validate_plan(cue, plan, profile)
    source, target = read_cue(cue), read_cue(candidate_cue)
    for i in (1, 2):
        require(hash_file(target['paths'][i]) == body['input']['tracks'][i]['sha256'], 'XA/audio track changed')
    require(target['text'] == render_cue(source), 'Output CUE changed beyond filenames')
    observed = inventory(target['paths'][0])
    original = body['inventory']
    require(observed['track1_sectors'] == original['track1_sectors'], 'Track1 length changed')
    require(len(observed['files']) == len(original['files']), 'File removed/added')
    allocations = {a['name']: a for a in body['allocations']}
    for before, after in zip(original['files'], observed['files']):
        expected = dict(before)
        if before['name'] in allocations:
            expected['lba'] = allocations[before['name']]['new_lba']
        require(expected == after, 'Resource/metadata readback mismatch: ' + before['name'])
    changed = 0
    with RawImage(source['paths'][0]) as src, RawImage(target['paths'][0]) as dst:
        touched, directory = recipe(src, body)
        require(src.count == dst.count, 'Raw image length changed')
        for lba in range(src.count):
            wanted = expected_sector(src, lba, body, directory) if lba in touched else src.raw(lba)
            actual = dst.raw(lba)
            require(actual == wanted, f'Raw-sector readback mismatch at LBA {lba}')
            if actual != src.raw(lba):
                changed += 1
                require(mode1(lba, actual[16:2064]) == actual, 'EDC/ECC/MSF mismatch')
    require(freeze(cue, profile) == body['input'], 'Source changed during verification')
    return {'schema': 'REVB_MIGRATION_ACCEPTANCE_1', 'version': VERSION,
            'test_kind': profile['kind'], 'static': 'PASS',
            'directory_records': len(observed['files']),
            'mode1_payload_hashes_verified': sum(x['inside_track1'] for x in observed['files']),
            'external_XA': 'DESCRIPTORS_AND_ENTIRE_TRACK_PRESERVED_NOT_MODE1_DECODED',
            'changed_raw_sectors': changed, 'source_unchanged': True,
            'candidate_track1_sha256': hash_file(target['paths'][0]),
            'plan_sha256': plan['seal_sha256'], 'tool_sha256': hash_file(Path(__file__)),
            'runtime': 'NOT_RUN', 'save_compatibility': 'NOT_RUN',
            'semantic_payload_changes': 'NONE', 'release': 'BLOCKED_PENDING_RUNTIME'}


def build(cue: Path, plan: dict, destination: Path, profile: dict = NATIVE) -> dict:
    body = validate_plan(cue, plan, profile)
    parsed = read_cue(cue)
    with new_directory(destination, [cue] + parsed['paths']) as staging:
        for number, source in enumerate(parsed['paths'], 1):
            target = staging / f'Track{number:02d}.bin'
            shutil.copyfile(source, target)
            require(hash_file(target) == body['input']['tracks'][number - 1]['sha256'], 'Input changed during copy')
        with RawImage(parsed['paths'][0]) as source:
            touched, directory = recipe(source, body)
            # A malformed original sector must not be silently normalized.
            for lba in sorted(touched):
                require(mode1(lba, source.user(lba)) == source.raw(lba), f'Original EDC/ECC invalid at {lba}')
            with (staging / 'Track01.bin').open('r+b') as target:
                for lba in sorted(touched):
                    target.seek(lba * RAW)
                    target.write(expected_sector(source, lba, body, directory))
                target.flush()
                os.fsync(target.fileno())
        (staging / 'candidate.cue').write_bytes(render_cue(parsed).encode('utf-8'))
        report = verify_candidate(cue, plan, staging / 'candidate.cue', profile)
        write_json(staging / 'PLAN.json', plan)
        write_json(staging / 'ACCEPTANCE.json', report)
        (staging / 'NOT_RUNTIME_ACCEPTED.txt').write_text(
            'Static physical relocation only. Runtime, saves, new content and hardware are NOT accepted.\n', encoding='utf-8')
    return report


def split_track(source: Path, destination: Path, max_bytes: int = 16 * 1024 * 1024) -> dict:
    integer(max_bytes, RAW, 1024 * 1024 * 1024)
    size = source.stat().st_size
    require(size > 0 and size % RAW == 0, 'Transfer input must contain complete raw sectors')
    chunk = max_bytes // RAW * RAW
    original = hash_file(source)
    with new_directory(destination, [source]) as staging:
        parts, offset = [], 0
        overall = hashlib.sha256()
        with source.open('rb') as f:
            while True:
                data = f.read(chunk)
                if not data:
                    break
                name = f'{len(parts):05d}.part'
                (staging / name).write_bytes(data)
                overall.update(data)
                parts.append({'name': name, 'offset': offset, 'size': len(data), 'sha256': sha(data)})
                offset += len(data)
        require(offset == size and overall.hexdigest() == original and hash_file(source) == original, 'Source changed while splitting')
        manifest = sealed({'schema': 'REVB_RAW_TRANSFER_1', 'sector_bytes': RAW,
                           'filename': base_name(source.name), 'size': size,
                           'sha256': original, 'chunk_bytes': chunk, 'parts': parts,
                           'purpose': 'TRANSFER_ONLY_NOT_A_CUE_TRACK_LAYOUT'})
        write_json(staging / 'TRANSFER.json', manifest)
    return manifest


def join_track(manifest_path: Path, destination: Path) -> dict:
    manifest = load_json(manifest_path)
    body = unseal(manifest)
    require(body['schema'] == 'REVB_RAW_TRANSFER_1' and body['sector_bytes'] == RAW, 'Unknown transfer format')
    name = base_name(body['filename'])
    total = integer(body['size'], RAW, 1024 * 1024 * 1024 * 16)
    chunk = integer(body['chunk_bytes'], RAW, 1024 * 1024 * 1024)
    require(total % RAW == 0 and chunk % RAW == 0 and isinstance(body['parts'], list) and body['parts'], 'Invalid transfer geometry')
    offset, inputs = 0, [manifest_path]
    for index, part in enumerate(body['parts']):
        require(part['name'] == f'{index:05d}.part' and part['offset'] == offset, 'Missing/reordered/duplicate transfer part')
        expected_size = min(chunk, total - offset)
        require(expected_size > 0 and part['size'] == expected_size, 'Invalid part length')
        path = manifest_path.parent / base_name(part['name'])
        require(path.is_file() and not path.is_symlink() and path.stat().st_size == expected_size, 'Missing/truncated/linked part')
        inputs.append(path)
        offset += expected_size
    require(offset == total, 'Incomplete transfer sequence')
    with new_directory(destination, inputs) as staging:
        h = hashlib.sha256()
        with (staging / name).open('xb') as out:
            for path, part in zip(inputs[1:], body['parts']):
                piece = hashlib.sha256()
                with path.open('rb') as f:
                    for data in iter(lambda: f.read(4 * 1024 * 1024), b''):
                        piece.update(data)
                        h.update(data)
                        out.write(data)
                require(piece.hexdigest() == part['sha256'], 'Transfer part hash mismatch')
            out.flush()
            os.fsync(out.fileno())
        require((staging / name).stat().st_size == total and h.hexdigest() == body['sha256'], 'Reassembled track mismatch')
        require(hash_file(staging / name) == body['sha256'], 'Final reassembly readback mismatch')
        report = {'transfer': 'PASS', 'size': total, 'sha256': h.hexdigest(), 'runtime': 'NOT_RUN'}
        write_json(staging / 'TRANSFER_ACCEPTANCE.json', report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('policy')
    for command in ('scan', 'plan', 'build', 'verify'):
        p = sub.add_parser(command)
        p.add_argument('--cue', type=Path, required=True)
        if command in ('scan', 'plan'):
            p.add_argument('--out', type=Path, required=True)
        if command == 'plan':
            p.add_argument('--reserve', action='append', default=[], metavar='FILE=BYTES')
            p.add_argument('--relocate', action='store_true')
            p.add_argument('--alignment', type=int, default=16)
        if command in ('build', 'verify'):
            p.add_argument('--plan', type=Path, required=True)
        if command == 'build':
            p.add_argument('--outdir', type=Path, required=True)
        if command == 'verify':
            p.add_argument('--candidate-cue', type=Path, required=True)
    p = sub.add_parser('split')
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--outdir', type=Path, required=True)
    p.add_argument('--mib', type=int, default=16)
    p = sub.add_parser('join')
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--outdir', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'policy':
            result = POLICY
        elif args.command == 'scan':
            result = {'input': freeze(args.cue), 'inventory': inventory(read_cue(args.cue)['paths'][0]), 'runtime': 'NOT_RUN'}
            require(len(result['inventory']['files']) == NATIVE['files'], 'Native directory count differs')
            write_json(args.out, result)
        elif args.command == 'plan':
            requests = {}
            for request in args.reserve:
                name, value = request.split('=', 1)
                require(name not in requests, 'Duplicate reservation')
                requests[name] = int(value, 0)
            result = make_plan(args.cue, requests, args.relocate, args.alignment)
            write_json(args.out, result)
        elif args.command == 'build':
            result = build(args.cue, load_json(args.plan), args.outdir)
        elif args.command == 'verify':
            result = verify_candidate(args.cue, load_json(args.plan), args.candidate_cue)
        elif args.command == 'split':
            result = split_track(args.input, args.outdir, args.mib * 1024 * 1024)
        else:
            result = join_track(args.manifest, args.outdir)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except (MigrationError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'BLOCKED', 'reason': str(exc), 'runtime': 'NOT_RUN'}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
