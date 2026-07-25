#!/usr/bin/env python3
"""Shared bounded image validation for local multimodal requests."""
from __future__ import annotations

import base64
from pathlib import Path

MAX_IMAGE_BYTES = 12 * 1024 * 1024
SIGNATURES = (
    (b'\x89PNG\r\n\x1a\n', 'image/png'),
    (b'\xff\xd8\xff', 'image/jpeg'),
    (b'RIFF', 'image/webp'),
)


def read_validated_image(path: Path, *, max_bytes: int = MAX_IMAGE_BYTES) -> tuple[bytes, str]:
    if not path.is_file():
        raise ValueError(f'Image not found: {path}')
    size = path.stat().st_size
    if size <= 0:
        raise ValueError(f'Image is empty: {path}')
    if size > max_bytes:
        raise ValueError(f'Image exceeds {max_bytes} bytes: {path}')
    data = path.read_bytes()
    for signature, mime in SIGNATURES:
        if data.startswith(signature):
            if mime == 'image/webp' and (len(data) < 12 or data[8:12] != b'WEBP'):
                break
            return data, mime
    raise ValueError('Image must have a valid PNG, JPEG or WebP signature.')


def image_data_url(path: Path, *, max_bytes: int = MAX_IMAGE_BYTES) -> str:
    data, mime = read_validated_image(path, max_bytes=max_bytes)
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
