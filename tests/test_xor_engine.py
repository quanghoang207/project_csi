import io
import threading

import pytest

from core.errors import OperationCancelled
from core.utils import sha256_file
from core.xor_engine import CHUNK_SIZE, xor_bytes, xor_file, xor_stream


@pytest.mark.parametrize("size", [0, 1, 9, CHUNK_SIZE - 1, CHUNK_SIZE, CHUNK_SIZE + 1])
def test_xor_bytes_is_its_own_inverse(size):
    data = bytes((index * 29) % 256 for index in range(size))
    key = b"key with odd length"
    assert xor_bytes(xor_bytes(data, key), key) == data


def test_xor_bytes_respects_global_offset():
    data, key = b"offset regression across chunks", b"abcde"
    assert xor_bytes(data, key) == xor_bytes(data[:11], key) + xor_bytes(data[11:], key, 11)


def test_xor_stream_reports_progress_and_output_callback():
    data, key = b"z" * (CHUNK_SIZE + 3), b"stream-key"
    output, reported, observed = io.BytesIO(), [], bytearray()
    count = xor_stream(
        io.BytesIO(data),
        output,
        key,
        size=len(data),
        progress_cb=lambda done, total: reported.append((done, total)),
        on_output=observed.extend,
    )
    assert count == len(data)
    assert reported[-1] == (len(data), len(data))
    assert observed == output.getvalue()
    assert xor_bytes(output.getvalue(), key) == data


def test_xor_file_round_trip_and_hash(tmp_path):
    source, encrypted, restored = (tmp_path / name for name in ("source.bin", "xored.bin", "restored.bin"))
    source.write_bytes(bytes(range(256)) * 5000)
    xor_file(source, encrypted, b"binary-key")
    xor_file(encrypted, restored, b"binary-key")
    assert sha256_file(source) == sha256_file(restored)
    assert not encrypted.with_name(encrypted.name + ".tmp").exists()


def test_cancelled_xor_file_removes_temporary_output(tmp_path):
    source, output = tmp_path / "source.bin", tmp_path / "output.bin"
    source.write_bytes(b"data")
    cancelled = threading.Event()
    cancelled.set()
    with pytest.raises(OperationCancelled):
        xor_file(source, output, b"key", cancel_event=cancelled)
    assert not output.exists()
    assert not output.with_name(output.name + ".tmp").exists()


def test_cancel_during_stream_cleans_temporary_output(tmp_path):
    source, output = tmp_path / "source.bin", tmp_path / "output.bin"
    source.write_bytes(b"x" * (CHUNK_SIZE * 2))
    cancelled = threading.Event()
    with pytest.raises(OperationCancelled):
        xor_file(
            source,
            output,
            b"key",
            progress_cb=lambda done, total: cancelled.set(),
            cancel_event=cancelled,
        )
    assert not output.exists()
    assert not output.with_name(output.name + ".tmp").exists()


def test_empty_key_is_rejected():
    with pytest.raises(ValueError, match="Key rỗng"):
        xor_bytes(b"data", b"")