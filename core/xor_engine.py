"""XOR lặp khóa theo khối, hỗ trợ tiến trình và hủy thao tác."""

import os
import threading
from collections.abc import Callable
from pathlib import Path
from typing import BinaryIO

from core.errors import OperationCancelled

CHUNK_SIZE = 1024 * 1024


def xor_bytes(data: bytes, key: bytes, offset: int = 0) -> bytes:
	"""XOR một khối dữ liệu với khóa lặp, bắt đầu tại offset toàn cục."""
	if not key:
		raise ValueError("Key rỗng.")
	if offset < 0:
		raise ValueError("Offset không được âm.")
	start = offset % len(key)
	stream = key[start:] + key[:start]
	repeats = (len(data) + len(key) - 1) // len(key)
	stream = (stream * repeats)[:len(data)]
	value = int.from_bytes(data, "big") ^ int.from_bytes(stream, "big")
	return value.to_bytes(len(data), "big")


def xor_stream(
	fin: BinaryIO,
	fout: BinaryIO,
	key: bytes,
	size: int | None = None,
	progress_cb: Callable[[int, int], None] | None = None,
	cancel_event: threading.Event | None = None,
	on_output: Callable[[bytes], None] | None = None,
) -> int:
	"""XOR luồng file; callback nhận chunk đầu ra và tiến trình theo byte."""
	if not key:
		raise ValueError("Key rỗng.")
	if size is not None and size < 0:
		raise ValueError("Kích thước không được âm.")

	done = 0
	while size is None or done < size:
		if cancel_event is not None and cancel_event.is_set():
			raise OperationCancelled("Thao tác đã bị huỷ.")
		amount = CHUNK_SIZE if size is None else min(CHUNK_SIZE, size - done)
		chunk = fin.read(amount)
		if not chunk:
			break
		output = xor_bytes(chunk, key, done)
		fout.write(output)
		if on_output is not None:
			on_output(output)
		done += len(chunk)
		if progress_cb is not None:
			progress_cb(done, size if size is not None else done)

	if cancel_event is not None and cancel_event.is_set():
		raise OperationCancelled("Thao tác đã bị huỷ.")
	return done


def xor_file(
	in_path: str | os.PathLike[str],
	out_path: str | os.PathLike[str],
	key: bytes,
	progress_cb: Callable[[int, int], None] | None = None,
	cancel_event: threading.Event | None = None,
) -> None:
	"""XOR file ra file tạm rồi thay thế đích khi hoàn tất."""
	in_path, out_path = Path(in_path), Path(out_path)
	if not in_path.is_file():
		raise FileNotFoundError(f"Không tìm thấy file nguồn: {in_path}")
	if in_path.resolve() == out_path.resolve():
		raise ValueError("File nguồn và file đích không được trùng nhau.")

	tmp_path = out_path.with_name(out_path.name + ".tmp")
	try:
		total = in_path.stat().st_size
		with in_path.open("rb") as fin, tmp_path.open("wb") as fout:
			xor_stream(
				fin,
				fout,
				key,
				size=total,
				progress_cb=progress_cb,
				cancel_event=cancel_event,
			)
		os.replace(tmp_path, out_path)
	except BaseException:
		tmp_path.unlink(missing_ok=True)
		raise
