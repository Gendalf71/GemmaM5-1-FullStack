#!/usr/bin/env python3
"""Validate engineering PNG dimensions and an empty outer safety margin."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import sys
import zlib

PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'


def fail(message: str) -> None:
    print(f'ERROR: {message}', file=sys.stderr)
    raise SystemExit(1)


def paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else b if pb <= pc else c


def decode_rgb(path: Path) -> tuple[int, int, list[bytes]]:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        fail(f'not a PNG: {path}')
    pos = len(PNG_SIGNATURE)
    width = height = bit_depth = color_type = None
    compressed = bytearray()
    while pos < len(data):
        length = struct.unpack('>I', data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if kind == b'IHDR':
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack('>IIBBBBB', payload)
            if compression != 0 or filtering != 0 or interlace != 0:
                fail(f'unsupported PNG encoding: {path}')
        elif kind == b'IDAT':
            compressed.extend(payload)
        elif kind == b'IEND':
            break
    if None in (width, height, bit_depth, color_type):
        fail(f'missing IHDR: {path}')
    if bit_depth != 8 or color_type not in (2, 6):
        fail(f'asset must be 8-bit RGB/RGBA: {path}')
    channels = 3 if color_type == 2 else 4
    raw = zlib.decompress(bytes(compressed))
    stride = width * channels
    expected = height * (stride + 1)
    if len(raw) != expected:
        fail(f'unexpected decoded PNG size: {path}')
    rows: list[bytes] = []
    previous = bytearray(stride)
    offset = 0
    for _ in range(height):
        filter_type = raw[offset]
        scan = bytearray(raw[offset + 1:offset + 1 + stride])
        offset += stride + 1
        reconstructed = bytearray(stride)
        for i, value in enumerate(scan):
            left = reconstructed[i - channels] if i >= channels else 0
            up = previous[i]
            up_left = previous[i - channels] if i >= channels else 0
            if filter_type == 0:
                result = value
            elif filter_type == 1:
                result = (value + left) & 255
            elif filter_type == 2:
                result = (value + up) & 255
            elif filter_type == 3:
                result = (value + ((left + up) // 2)) & 255
            elif filter_type == 4:
                result = (value + paeth(left, up, up_left)) & 255
            else:
                fail(f'unsupported PNG filter {filter_type}: {path}')
            reconstructed[i] = result
        rows.append(bytes(reconstructed))
        previous = reconstructed
    return width, height, rows


def pixel(row: bytes, x: int, channels: int) -> tuple[int, ...]:
    start = x * channels
    return tuple(row[start:start + channels])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    args = parser.parse_args()
    root = args.manifest.resolve().parents[2]
    try:
        manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f'cannot read asset manifest: {exc}')
    if manifest.get('schema_version') != 1:
        fail('asset manifest schema_version must be 1')
    for entry in manifest.get('assets', []):
        relative = entry.get('path')
        if not isinstance(relative, str):
            fail('asset path must be a string')
        path = root / relative
        width, height, rows = decode_rgb(path)
        if [width, height] != entry.get('dimensions'):
            fail(f'dimension drift for {relative}: {width}x{height}')
        margin = entry.get('minimum_blank_margin_px')
        if not isinstance(margin, int) or margin < 1:
            fail(f'invalid margin for {relative}')
        channels = len(rows[0]) // width
        background = pixel(rows[0], 0, channels)
        for y, row in enumerate(rows):
            for x in range(width):
                if x >= margin and x < width - margin and y >= margin and y < height - margin:
                    continue
                current = pixel(row, x, channels)
                if current != background:
                    fail(f'non-background pixel enters {margin}px safety margin: {relative} at {x},{y}')
    print(f"Visual assets verified: {len(manifest.get('assets', []))}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
