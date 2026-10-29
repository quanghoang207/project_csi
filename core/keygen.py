
import hashlib
import secrets
from os import PathLike
from pathlib import Path


def generate_salt() -> bytes:
    """Sinh 16 byte salt ngẫu nhiên dùng cho scrypt."""
    return secrets.token_bytes(16)


def derive_keys(password: str, salt: bytes) -> tuple[bytes, bytes]:
    """
    Dẫn xuất khóa từ mật khẩu văn bản và salt sử dụng hashlib.scrypt.
    Trả về tuple gồm (enc_key, mac_key), mỗi khóa dài 32 byte.
    """
    if not password:
        raise ValueError("Mật khẩu không được để trống.")
    
    # scrypt lấy 64 byte, sau đó chia đôi cho mã hoá (32 byte) và HMAC (32 byte)
    raw = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=64
    )
    return raw[:32], raw[32:]


def keys_from_keyfile(key: bytes, salt: bytes) -> tuple[bytes, bytes]:
    """
    Tạo cặp khóa từ keyfile nhị phân.
    enc_key chính là nội dung keyfile; mac_key được tính bằng SHA-256 có salt bảo vệ.
    """
    if not key:
        raise ValueError("Keyfile rỗng.")
    
    enc_key = key
    mac_key = hashlib.sha256(b"xortool-mac" + salt + key).digest()
    return enc_key, mac_key


def generate_random_key(length: int = 32) -> bytes:
    """Sinh khóa ngẫu nhiên (dùng cho tính năng tạo keyfile)."""
    return secrets.token_bytes(length)


def save_keyfile(path: str | PathLike[str], key: bytes) -> None:
    """Lưu key xuống file nhị phân."""
    path = Path(path)
    path.write_bytes(key)


def load_keyfile(path: str | PathLike[str]) -> bytes:
    """Đọc key từ file nhị phân."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Không tìm thấy file key: {path}")
    return path.read_bytes()
