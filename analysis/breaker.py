"""Phân tích repeating-key XOR trên dữ liệu thử do người dùng cung cấp."""

import math
from collections import Counter

from core.xor_engine import xor_bytes

_ENGLISH_FREQUENCIES = {
    " ": 0.182, "e": 0.102, "t": 0.075, "a": 0.065, "o": 0.061,
    "n": 0.057, "i": 0.056, "s": 0.053, "r": 0.049, "h": 0.049,
    "d": 0.034, "l": 0.033, "u": 0.022, "c": 0.022, "m": 0.020,
    "f": 0.018, "w": 0.017, "g": 0.016, "p": 0.015, "y": 0.015,
    "b": 0.012, "v": 0.008, "k": 0.006, "x": 0.002, "j": 0.002,
    "q": 0.001, "z": 0.001,
}
_BYTE_SCORES = [math.log(0.00015)] * 256
for _character, _frequency in _ENGLISH_FREQUENCIES.items():
    _BYTE_SCORES[ord(_character)] = math.log(_frequency)
    if _character.isalpha():
        _BYTE_SCORES[ord(_character.upper())] = math.log(_frequency * 0.7)
for _character in "'.,!?;:-()\"\n\r":
    _BYTE_SCORES[ord(_character)] = math.log(0.004)
for _value in range(32, 127):
    if _BYTE_SCORES[_value] == math.log(0.00015):
        _BYTE_SCORES[_value] = math.log(0.001)


def hamming(a: bytes, b: bytes) -> int:
    """Đếm số bit khác nhau ở các vị trí tương ứng trong hai byte strings."""
    return sum((left ^ right).bit_count() for left, right in zip(a, b))


def rank_keysizes(
    ct: bytes,
    max_keysize: int = 40,
    top: int = 5,
) -> list[tuple[int, float]]:
    """Xếp hạng độ dài khóa theo khoảng cách Hamming chuẩn hóa trung bình."""
    if max_keysize < 2:
        raise ValueError("max_keysize phải lớn hơn hoặc bằng 2.")
    if top < 1:
        raise ValueError("top phải lớn hơn hoặc bằng 1.")

    rankings = []
    for keysize in range(2, min(max_keysize, len(ct) // 4) + 1):
        blocks = [ct[index:index + keysize] for index in range(0, keysize * 8, keysize)]
        if len(blocks) < 4 or any(len(block) != keysize for block in blocks):
            continue
        distances = [
            hamming(blocks[index], blocks[index + 1]) / keysize
            for index in range(len(blocks) - 1)
        ]
        rankings.append((keysize, sum(distances) / len(distances)))
    return sorted(rankings, key=lambda item: item[1])[:top]


def _score_english(data: bytes) -> float:
    if not data:
        return float("-inf")
    score = sum(_BYTE_SCORES[value] for value in data) / len(data)
    text = data.decode("latin-1").lower()
    score += 0.025 * sum(text.count(word) for word in (" the ", " and ", " of ", " to ", " is "))
    score -= 2.0 * sum(value < 32 and value not in (9, 10, 13) for value in data) / len(data)
    score -= 1.0 * sum(value > 126 for value in data) / len(data)
    return score


def _best_single_byte_key(column: bytes) -> int:
    frequencies = Counter(column)
    return max(
        range(256),
        key=lambda candidate: sum(
            count * _BYTE_SCORES[value ^ candidate]
            for value, count in frequencies.items()
        ),
    )


def _normalized_key(key: bytes) -> bytes:
    for length in range(1, len(key) + 1):
        if len(key) % length == 0 and key == key[:length] * (len(key) // length):
            return key[:length]
    return key


def break_repeating_xor(ct: bytes, max_keysize: int = 40) -> tuple[bytes, bytes]:
    """Ước lượng khóa và plaintext tiếng Anh của repeating-key XOR."""
    if not ct:
        raise ValueError("Ciphertext quá ngắn để phân tích.")
    candidates = rank_keysizes(ct, max_keysize=max_keysize, top=5)
    if not candidates:
        raise ValueError("Ciphertext cần tối thiểu 8 byte để phân tích.")

    best_key, best_plaintext, best_score = b"", b"", float("-inf")
    candidate_sizes = {size for size, _ in candidates}
    candidate_sizes.update(size * 2 for size, _ in candidates if size * 2 <= max_keysize)
    for keysize in candidate_sizes:
        if keysize > len(ct) // 4:
            continue
        columns = [ct[index::keysize] for index in range(keysize)]
        key = bytes(_best_single_byte_key(column) for column in columns)
        key = _normalized_key(key)
        plaintext = xor_bytes(ct, key)
        score = _score_english(plaintext)
        if score > best_score:
            best_key, best_plaintext, best_score = key, plaintext, score
    return best_key, best_plaintext