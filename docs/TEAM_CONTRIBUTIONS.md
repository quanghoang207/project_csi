# Tổng hợp phần việc theo 5 vai trò

Đây là bản tổng hợp theo phân công trong đề. Nhóm cần thay tên Người 1-5 bằng tên thật và xác nhận ai đã làm/review từng phần trước khi nộp; không dùng nội dung này để khẳng định lịch sử Git hoặc quyền tác giả chưa được xác minh.

## Người 1: Core XOR

- Cài đặt `xor_bytes` với khóa lặp và offset toàn cục.
- Cài đặt `xor_stream` theo chunk 1 MiB, báo tiến trình, gọi callback HMAC và nhận hủy.
- Cài đặt `xor_file` ghi file tạm, chặn nguồn trùng đích và dọn tạm khi lỗi/hủy.
- Cài đặt `sha256_file` đọc theo khối.
- Kiểm tra biên chunk và khứ hồi file lớn bằng SHA-256.
- Đã đo khứ hồi file 200 MiB trên Python 3.14.7; kết quả 4.4 giây trên môi trường hiện tại.

## Người 2: Khóa và định dạng

- Cung cấp bốn lớp lỗi dùng chung.
- Dẫn xuất khóa mật khẩu bằng scrypt với UTF-8 và salt ngẫu nhiên.
- Hỗ trợ tạo, lưu và đọc keyfile nhị phân.
- Đóng gói header XORT, ciphertext XOR và HMAC-SHA256.
- Xác thực HMAC trước khi ghi plaintext, dùng so sánh constant-time.
- Kiểm thử sai khóa, sửa dữ liệu, file thường, cắt cụt và hủy.

## Người 3: GUI

- Xây ứng dụng Tkinter chọn file nguồn/đích và gợi ý tên `.enc`.
- Hỗ trợ mật khẩu hiện/ẩn, keyfile và sinh keyfile ngẫu nhiên.
- Chạy tác vụ nền, chuyển sự kiện qua queue và chỉ cập nhật widget ở main thread.
- Hiển thị tiến trình/trạng thái và hỗ trợ hủy.
- Ánh xạ lỗi lõi sang thông báo tiếng Việt.
- Thêm tab demo gọi breaker trên sample tự tạo; cần kiểm tra trực tiếp trên desktop.

## Người 4: Phân tích repeating-key XOR

- Tạo văn bản mẫu tiếng Anh công khai, không chứa dữ liệu cá nhân.
- Cài đặt Hamming distance và xếp hạng độ dài khóa.
- Phân tích từng cột bằng mô hình tần suất tiếng Anh để đoán khóa/plaintext.
- Cung cấp benchmark theo độ dài khóa và độ dài plaintext.
- Ghi rõ giới hạn: breaker không phù hợp mọi ngôn ngữ/dữ liệu và chỉ dùng cho demo tự tạo.
- Giải thích vì sao pad dùng một lần đáp ứng giả định khác; không khẳng định XOR lặp an toàn.

## Người 5: Test, tài liệu, tích hợp

- Tạo fixture cục bộ rỗng, một byte, tiếng Việt, PNG/JPG, PDF, ZIP và các biên chunk.
- Viết test pytest cho core, file format, breaker, hủy và các lỗi bảo mật.
- Viết hướng dẫn cài đặt/chạy, báo cáo lý thuyết/thiết kế và checklist cần xác minh.
- Tạo benchmark CSV, bảng lỗi và kịch bản demo.
- Chạy 37 test trên Python 3.14.7; kết quả trên Python 3.11 và máy thứ hai còn cần xác nhận.
- Việc tạo PR/review, ảnh thật, xuất slide và quay video cần được nhóm thực hiện.