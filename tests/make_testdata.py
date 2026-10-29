"""Tạo fixture file cục bộ; không đưa dữ liệu sinh vào Git."""

import argparse
import io
import struct
import zlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from PIL import Image

from core.xor_engine import CHUNK_SIZE


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    body = kind + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def _make_png() -> bytes:
    header = struct.pack(">2I5B", 1, 1, 8, 2, 0, 0, 0)
    pixels = zlib.compress(b"\x00\x23\x78\x9a")
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", header)
        + _png_chunk(b"IDAT", pixels)
        + _png_chunk(b"IEND", b"")
    )


def _make_jpeg() -> bytes:
    image = Image.new("RGB", (2, 2), (36, 120, 154))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def _make_pdf() -> bytes:
    objects = (
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 1 1] /Resources << >> >>",
    )
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(body + b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(b"xref\n0 4\n0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(pdf)


def generate_testdata(output_dir, include_large: bool = False) -> list[Path]:
    """Sinh file nhị phân/văn bản chuẩn và các kích thước biên của chunk."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    fixtures = {
        "empty.bin": b"",
        "one_byte.bin": b"\x00",
        "vietnamese.txt": "Xin chào, đây là dữ liệu kiểm thử tiếng Việt có dấu.\n".encode("utf-8"),
        "tiny.png": _make_png(),
        "tiny.jpg": _make_jpeg(),
        "sample.pdf": _make_pdf(),
    }
    zip_buffer = io.BytesIO()
    with ZipFile(zip_buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("sample.txt", "Nội dung ZIP kiểm thử.\n")
    fixtures["sample.zip"] = zip_buffer.getvalue()

    paths = []
    for name, content in fixtures.items():
        path = output_dir / name
        path.write_bytes(content)
        paths.append(path)

    boundary_data = bytes(range(256)) * (2 * CHUNK_SIZE // 256 + 1)
    for size in (CHUNK_SIZE - 1, CHUNK_SIZE, CHUNK_SIZE + 1, 2 * CHUNK_SIZE):
        path = output_dir / f"boundary_{size}.bin"
        path.write_bytes(boundary_data[:size])
        paths.append(path)

    if include_large:
        large_path = output_dir / "large_200mb.bin"
        block = bytes(range(256)) * (CHUNK_SIZE // 256)
        with large_path.open("wb") as stream:
            for _ in range(200):
                stream.write(block)
        paths.append(large_path)
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "data")
    parser.add_argument("--include-large", action="store_true", help="Tạo thêm file 200 MiB.")
    args = parser.parse_args()
    paths = generate_testdata(args.output_dir, include_large=args.include_large)
    print(f"Đã tạo {len(paths)} file trong {args.output_dir}")


if __name__ == "__main__":
    main()