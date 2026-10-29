
class XorToolError(Exception):
    """Lớp cơ sở cho mọi lỗi của công cụ XOR."""
    pass


class InvalidFileFormatError(XorToolError):
    """Lỗi xuất hiện khi file đầu vào không phải là định dạng do công cụ mã hoá."""
    pass


class WrongKeyOrCorruptedError(XorToolError):
    """Lỗi xuất hiện khi sai mật khẩu/keyfile hoặc file bị chỉnh sửa/hỏng."""
    pass


class OperationCancelled(XorToolError):
    """Lỗi xuất hiện khi người dùng bấm nút Huỷ trong quá trình xử lý."""
    pass
