"""Tiện ích dùng chung cho kiểm tra file."""

import hashlib
from pathlib import Path

from core.xor_engine import CHUNK_SIZE


def sha256_file(path) -> str:
    """Trả về SHA-256 dạng hex của file, đọc theo khối 1 MiB."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()