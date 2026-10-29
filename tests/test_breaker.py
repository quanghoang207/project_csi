from pathlib import Path

import pytest

from analysis.breaker import break_repeating_xor, hamming, rank_keysizes
from core.xor_engine import xor_bytes

SAMPLE = Path(__file__).parents[1] / "analysis" / "sample_text.txt"


def test_hamming_reference_vector():
    assert hamming(b"this is a test", b"wokka wokka!!!") == 37


@pytest.mark.parametrize("key", [b"CODE", b"ORANGE", b"SECURITY", b"XORPROJECT", b"LONGKEY12345"])
def test_breaker_recovers_sample(key):
    plaintext = SAMPLE.read_bytes() * 5
    ciphertext = xor_bytes(plaintext, key)
    found_key, found_plaintext = break_repeating_xor(ciphertext)
    assert found_key == key
    assert found_plaintext == plaintext


def test_rank_keysizes_includes_repeating_key_length():
    plaintext = SAMPLE.read_bytes() * 3
    ranking = rank_keysizes(xor_bytes(plaintext, b"ORANGE"), max_keysize=20, top=20)
    assert 6 in {keysize for keysize, _ in ranking}


def test_breaker_rejects_insufficient_input():
    with pytest.raises(ValueError):
        break_repeating_xor(b"tiny")