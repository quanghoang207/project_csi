# XORT

Công cụ học tập mã hóa/giải mã file bằng XOR lặp khóa, có xác thực HMAC-SHA256, giao diện Tkinter và demo phân tích repeating-key XOR trên văn bản mẫu tự tạo.

> Đây là dự án minh họa thuật toán, không dùng để bảo vệ dữ liệu thật. XOR lặp khóa không phải mã hóa an toàn; HMAC chỉ phát hiện sửa đổi, không làm XOR mạnh hơn.

## Yêu cầu

- Python 3.11
- Tkinter đi kèm bản cài Python; trên Linux có thể cần cài gói Tk riêng

## Cài đặt và chạy

```powershell
py -3.11 -m venv .venv
\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Trên macOS/Linux, kích hoạt môi trường bằng `source .venv/bin/activate`.

Trong tab **File**, chọn nguồn/đích và đúng một phương thức xác thực: mật khẩu hoặc keyfile. Để giải mã, chọn file `.enc` và nhập cùng mật khẩu/keyfile đã dùng khi mã hóa. Keyfile là bí mật; giữ bản sao lưu an toàn.

Tab **Demo XOR lặp** tạo ciphertext từ `analysis/sample_text.txt` với khóa thử do người dùng nhập, rồi thử khôi phục khóa và plaintext. Chỉ dùng dữ liệu mẫu này.

## Kiểm thử

```powershell
python -m pytest -q
```

Tạo bộ dữ liệu thử cục bộ (không commit `tests/data/`):

```powershell
python -m tests.make_testdata
python -m tests.make_testdata --include-large
```

Đo độ chính xác của demo trên sample tự tạo:

```powershell
python -m analysis.benchmark
```

## Định dạng file

`XORT` dùng header 29 byte: magic 4 byte, version 1 byte, salt ngẫu nhiên 16 byte và kích thước plaintext 8 byte big-endian. Tiếp theo là ciphertext XOR cùng độ dài và HMAC-SHA256 32 byte trên header+ciphertext. Giải mã xác minh HMAC trước khi tạo plaintext; kết quả được ghi vào `.tmp` rồi thay thế đích khi thành công.

Với mật khẩu, `hashlib.scrypt` dẫn xuất 64 byte và tách thành khóa XOR/HMAC. Với keyfile, bytes của keyfile là khóa XOR và HMAC key lấy từ SHA-256 có salt. Cùng một file mã hóa nhiều lần sẽ có salt khác nhau.

## Đóng gói Windows

Sau khi cài dependencies:

```powershell
pyinstaller --onefile --windowed --name XorTool --add-data "analysis/sample_text.txt;analysis" main.py
```

Thử file build trên một máy sạch trước khi phân phối; checklist đó nằm trong [docs/NEEDS_VERIFICATION.md](docs/NEEDS_VERIFICATION.md).

## Tài liệu

- [Báo cáo kỹ thuật](docs/REPORT.md)
- [Tổng hợp đóng góp](docs/TEAM_CONTRIBUTIONS.md)
- [Nội dung slide](docs/SLIDES.md)
- [Kịch bản demo](docs/DEMO_SCRIPT.md)
- [Checklist việc cần kiểm chứng](docs/NEEDS_VERIFICATION.md)
- [Theo dõi lỗi](docs/BUG_TRACKER.csv)