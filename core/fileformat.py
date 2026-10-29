# core/fileformat.py

import hmac
import os
import threading
from collections.abc import Callable
from pathlib import Path

from core.errors import (
    InvalidFileFormatError,
    WrongKeyOrCorruptedError,
    OperationCancelled,
)
from core.keygen import (
    generate_salt,
    derive_keys,
    keys_from_keyfile,
    load_keyfile,
)
from core.xor_engine import xor_stream

MAGIC = b"XORT"
VERSION = 1
HEADER_SIZE = 29  # 4 (MAGIC) + 1 (VERSION) + 16 (SALT) + 8 (ORIGINAL_SIZE)
MAC_SIZE = 32     # HMAC-SHA256


def _validate_auth_inputs(password: str | None, keyfile: str | os.PathLike[str] | None) -> None:
    """Kiểm tra logic đầu vào: chỉ nhận đúng một trong hai (password hoặc keyfile)."""
    if (password is not None) and (keyfile is not None):
        raise ValueError("Chỉ được cung cấp mật khẩu hoặc keyfile, không được dùng cả hai.")
    if (password is None) and (keyfile is None):
        raise ValueError("Phải cung cấp mật khẩu hoặc keyfile để mã hoá/giải mã.")


def encrypt_file(
    in_path: str | os.PathLike[str],
    out_path: str | os.PathLike[str],
    password: str | None = None,
    keyfile: str | os.PathLike[str] | None = None,
    progress_cb: Callable[[int, int], None] | None = None,
    cancel_event: threading.Event | None = None,
) -> None:
    """
    Mã hoá file theo định dạng chuẩn:
    [MAGIC:4][VERSION:1][SALT:16][ORIGINAL_SIZE:8][DỮ LIỆU ĐÃ XOR][HMAC:32]
    """
    _validate_auth_inputs(password, keyfile)
    in_path, out_path = Path(in_path), Path(out_path)

    if not in_path.is_file():
        raise FileNotFoundError(f"Không tìm thấy file nguồn: {in_path}")

    if in_path.resolve() == out_path.resolve():
        raise ValueError("File nguồn và file đích không được trùng nhau.")

    # 1. Chuẩn bị khóa và salt
    salt = generate_salt()
    if password is not None:
        enc_key, mac_key = derive_keys(password, salt)
    else:
        key_bytes = load_keyfile(keyfile)
        enc_key, mac_key = keys_from_keyfile(key_bytes, salt)

    original_size = in_path.stat().st_size
    
    # Tạo header
    header = MAGIC + bytes([VERSION]) + salt + original_size.to_bytes(8, "big")

    # 2. Tạo file tạm để ghi an toàn
    tmp_path = out_path.with_name(out_path.name + ".tmp")

    try:
        # Khởi tạo HMAC gắn trên header trước
        h = hmac.new(mac_key, header, "sha256")

        with open(in_path, "rb") as fin, open(tmp_path, "wb") as fout:
            # Ghi header trước tiên
            fout.write(header)
            
            # [CẦN NGƯỜI 1] Gọi xor_stream, truyền on_output để cập nhật HMAC từng khối ciphertext đầu ra
            xor_stream(
                fin,
                fout,
                enc_key,
                size=original_size,
                progress_cb=progress_cb,
                cancel_event=cancel_event,
                on_output=h.update
            )
            
            # Ghi 32 byte HMAC vào cuối file
            fout.write(h.digest())

        # Thay thế file tạm thành file đích chính thức khi hoàn tất
        os.replace(tmp_path, out_path)

    except BaseException:
        # Dọn dẹp file rác nếu xảy ra lỗi hoặc bị huỷ
        tmp_path.unlink(missing_ok=True)
        raise


def decrypt_file(
    in_path: str | os.PathLike[str],
    out_path: str | os.PathLike[str],
    password: str | None = None,
    keyfile: str | os.PathLike[str] | None = None,
    progress_cb: Callable[[int, int], None] | None = None,
    cancel_event: threading.Event | None = None,
) -> None:
    """
    Giải mã file với quy trình bắt buộc 2 lượt:
    1. Kiểm tra cấu trúc file và xác thực toàn vẹn bằng HMAC (Lượt 1).
    2. Tiến hành giải mã XOR và ghi ra file đích (Lượt 2).
    """
    _validate_auth_inputs(password, keyfile)
    in_path, out_path = Path(in_path), Path(out_path)

    if not in_path.is_file():
        raise FileNotFoundError(f"Không tìm thấy file nguồn: {in_path}")

    if in_path.resolve() == out_path.resolve():
        raise ValueError("File nguồn và file đích không được trùng nhau.")

    file_size = in_path.stat().st_size
    if file_size < HEADER_SIZE + MAC_SIZE:
        raise InvalidFileFormatError("Kích thước file quá nhỏ hoặc không đúng định dạng mã hoá.")

    with open(in_path, "rb") as fin:
        # Đọc và kiểm tra header
        header = fin.read(HEADER_SIZE)
        if not header.startswith(MAGIC) or header[4] != VERSION:
            raise InvalidFileFormatError("Magic bytes hoặc phiên bản không hợp lệ (không phải file của công cụ).")

        salt = header[5:21]
        original_size = int.from_bytes(header[21:29], "big")

        cipher_len = file_size - HEADER_SIZE - MAC_SIZE
        if cipher_len != original_size:
            raise WrongKeyOrCorruptedError("Kích thước dữ liệu mã hoá bên trong không khớp (file bị cắt bớt hoặc hỏng).")

        # Đọc 32 byte MAC ở cuối file
        fin.seek(file_size - MAC_SIZE)
        stored_mac = fin.read(MAC_SIZE)

        # Dẫn xuất khóa
        if password is not None:
            enc_key, mac_key = derive_keys(password, salt)
        else:
            key_bytes = load_keyfile(keyfile)
            enc_key, mac_key = keys_from_keyfile(key_bytes, salt)

        # LƯỢT 1: Tính và kiểm tra HMAC trên toàn bộ (header + ciphertext)
        # Quay về vị trí bắt đầu phần ciphertext (sau header) để quét HMAC
        fin.seek(HEADER_SIZE)
        h = hmac.new(mac_key, header, "sha256")
        
        bytes_checked = 0
        chunk_size = 1024 * 1024
        
        while bytes_checked < cipher_len:
            if cancel_event is not None and cancel_event.is_set():
                raise OperationCancelled()
            
            to_read = min(chunk_size, cipher_len - bytes_checked)
            chunk = fin.read(to_read)
            if not chunk:
                break
            
            h.update(chunk)
            bytes_checked += len(chunk)
            
            # Gợi ý tiến trình: Lượt kiểm tra HMAC chiếm 0% -> 50% thanh tiến trình
            if progress_cb:
                progress_cb(bytes_checked, cipher_len * 2)

        # So sánh bảo mật chống timing attack
        if not hmac.compare_digest(h.digest(), stored_mac):
            raise WrongKeyOrCorruptedError("Sai mật khẩu/keyfile hoặc file đã bị chỉnh sửa/toàn vẹn bị phá vỡ.")

        # LƯỢT 2: Giải mã thực sự và ghi ra file tạm
        tmp_path = out_path.with_name(out_path.name + ".tmp")
        try:
            fin.seek(HEADER_SIZE)  # Quay lại đầu phần ciphertext
            with open(tmp_path, "wb") as fout:
                # Bọc lại progress_cb để tiếp tục từ 50% đến 100%
                def decrypt_progress_wrapper(done, total):
                    if progress_cb:
                        progress_cb(cipher_len + done, cipher_len * 2)

                # [CẦN NGƯỜI 1] Gọi xor_stream để thực hiện giải mã (XOR 2 lần trả về plaintext gốc)
                xor_stream(
                    fin,
                    fout,
                    enc_key,
                    size=cipher_len,
                    progress_cb=decrypt_progress_wrapper,
                    cancel_event=cancel_event
                )

            os.replace(tmp_path, out_path)

        except BaseException:
            tmp_path.unlink(missing_ok=True)
            raise
