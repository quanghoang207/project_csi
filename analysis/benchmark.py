"""Đo độ chính xác của breaker trên sample tự tạo, không dùng dữ liệu bên ngoài."""

import argparse
from pathlib import Path

from analysis.breaker import break_repeating_xor
from core.xor_engine import xor_bytes


def run_benchmark(sample_path: Path) -> list[tuple[int, int, float]]:
    """Trả bảng (độ dài khóa, byte plaintext, tỷ lệ byte khôi phục đúng)."""
    sample = sample_path.read_bytes()
    keys = (b"CODE", b"ORANGE", b"SECURITY", b"XORPROJECT", b"LONGKEY12345")
    lengths = (512, 2048, 4096, 8192)
    results = []
    for key in keys:
        for length in lengths:
            plaintext = (sample * (length // len(sample) + 1))[:length]
            _, recovered = break_repeating_xor(xor_bytes(plaintext, key))
            accuracy = sum(left == right for left, right in zip(plaintext, recovered)) / length
            results.append((len(key), length, accuracy))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=Path, default=Path(__file__).with_name("sample_text.txt"))
    args = parser.parse_args()
    print("key_length,text_bytes,success_rate")
    for key_length, text_bytes, rate in run_benchmark(args.sample):
        print(f"{key_length},{text_bytes},{rate:.3f}")


if __name__ == "__main__":
    main()