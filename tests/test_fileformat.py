import hashlib
import threading

import pytest

from core.errors import InvalidFileFormatError, OperationCancelled, WrongKeyOrCorruptedError
from core.fileformat import decrypt_file, encrypt_file
from core.keygen import generate_random_key, save_keyfile
from tests.make_testdata import generate_testdata


@pytest.mark.parametrize("content", [b"", b"x", "nội dung tiếng Việt có dấu".encode(), bytes(range(256))])
def test_password_round_trip(tmp_path, content):
    source, encrypted, restored = (tmp_path / name for name in ("input.bin", "input.enc", "restored.bin"))
    source.write_bytes(content)
    encrypt_file(source, encrypted, password="mật khẩu an toàn")
    decrypt_file(encrypted, restored, password="mật khẩu an toàn")
    assert hashlib.sha256(source.read_bytes()).digest() == hashlib.sha256(restored.read_bytes()).digest()


def test_keyfile_round_trip(tmp_path):
    source, key_path = tmp_path / "input.bin", tmp_path / "secret.key"
    source.write_bytes(b"keyfile works")
    save_keyfile(key_path, generate_random_key())
    encrypt_file(source, tmp_path / "data.enc", keyfile=key_path)
    decrypt_file(tmp_path / "data.enc", tmp_path / "restored.bin", keyfile=key_path)
    assert source.read_bytes() == (tmp_path / "restored.bin").read_bytes()


def test_generated_media_and_document_round_trips(tmp_path):
    data_dir = tmp_path / "fixtures"
    paths = generate_testdata(data_dir)
    fixture_names = {"empty.bin", "one_byte.bin", "vietnamese.txt", "tiny.png", "tiny.jpg", "sample.pdf", "sample.zip"}
    for source in (path for path in paths if path.name in fixture_names):
        encrypted = tmp_path / f"{source.name}.enc"
        restored = tmp_path / f"restored_{source.name}"
        encrypt_file(source, encrypted, password="mật khẩu fixture")
        decrypt_file(encrypted, restored, password="mật khẩu fixture")
        assert hashlib.sha256(source.read_bytes()).digest() == hashlib.sha256(restored.read_bytes()).digest()


def test_wrong_password_does_not_create_output(tmp_path):
    source, encrypted, restored = tmp_path / "source.bin", tmp_path / "source.enc", tmp_path / "restored.bin"
    source.write_bytes(b"authenticated contents")
    encrypt_file(source, encrypted, password="correct")
    with pytest.raises(WrongKeyOrCorruptedError):
        decrypt_file(encrypted, restored, password="incorrect")
    assert not restored.exists()
    assert not restored.with_name(restored.name + ".tmp").exists()


@pytest.mark.parametrize("offset", [0, 5, 29, -1])
def test_tampering_is_rejected_without_output(tmp_path, offset):
    source, encrypted, restored = tmp_path / "source.bin", tmp_path / "source.enc", tmp_path / "restored.bin"
    source.write_bytes(b"some authenticated content")
    encrypt_file(source, encrypted, password="passphrase")
    damaged = bytearray(encrypted.read_bytes())
    index = len(damaged) - 1 if offset == -1 else offset
    damaged[index] ^= 1
    encrypted.write_bytes(damaged)
    error = InvalidFileFormatError if offset == 0 else WrongKeyOrCorruptedError
    with pytest.raises(error):
        decrypt_file(encrypted, restored, password="passphrase")
    assert not restored.exists()


def test_plain_file_is_rejected(tmp_path):
    plain, output = tmp_path / "plain.txt", tmp_path / "out.bin"
    plain.write_text("not an encrypted file", encoding="utf-8")
    with pytest.raises(InvalidFileFormatError):
        decrypt_file(plain, output, password="passphrase")
    assert not output.exists()


def test_truncated_file_is_rejected(tmp_path):
    source, encrypted, output = tmp_path / "source", tmp_path / "source.enc", tmp_path / "output"
    source.write_bytes(b"data")
    encrypt_file(source, encrypted, password="passphrase")
    encrypted.write_bytes(encrypted.read_bytes()[:-1])
    with pytest.raises(WrongKeyOrCorruptedError):
        decrypt_file(encrypted, output, password="passphrase")
    assert not output.exists()


def test_encryptions_use_different_salts(tmp_path):
    source = tmp_path / "same.bin"
    source.write_bytes(b"same input")
    encrypt_file(source, tmp_path / "first.enc", password="passphrase")
    encrypt_file(source, tmp_path / "second.enc", password="passphrase")
    assert (tmp_path / "first.enc").read_bytes() != (tmp_path / "second.enc").read_bytes()


@pytest.mark.parametrize("auth", [{}, {"password": "pass", "keyfile": "key"}])
def test_exactly_one_auth_method_is_required(tmp_path, auth):
    with pytest.raises(ValueError):
        encrypt_file(tmp_path / "missing", tmp_path / "out", **auth)


def test_cancelled_encrypt_cleans_temporary_output(tmp_path):
    source, output = tmp_path / "source", tmp_path / "output.enc"
    source.write_bytes(b"contents")
    cancelled = threading.Event()
    cancelled.set()
    with pytest.raises(OperationCancelled):
        encrypt_file(source, output, password="passphrase", cancel_event=cancelled)
    assert not output.exists()
    assert not output.with_name(output.name + ".tmp").exists()