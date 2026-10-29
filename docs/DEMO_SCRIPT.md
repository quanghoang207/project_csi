# Kịch bản demo

Thời lượng gợi ý: 4-6 phút.

1. Mở XORT, chỉ ra hai phương thức xác thực. Nhắc người xem không dùng XOR demo để bảo vệ dữ liệu thật.
2. Tạo một file văn bản nhỏ có dấu tiếng Việt, mã hóa bằng mật khẩu, rồi giải mã. So sánh nội dung đầu/cuối.
3. Mã hóa lại cùng file và chỉ ra hai file `.enc` khác nhau do salt ngẫu nhiên.
4. Thử sai mật khẩu và sửa một byte ciphertext; xác nhận ứng dụng báo lỗi, không tạo plaintext đầu ra.
5. Tạo keyfile ngẫu nhiên, mã hóa/giải mã một file nhị phân nhỏ và lưu keyfile an toàn.
6. Mở tab demo repeating-key XOR, dùng sample có sẵn và khóa `ORANGE`; chỉ ra khóa/plaintext tìm được.
7. Kết thúc bằng giới hạn: repeating-key XOR bị phân tích; HMAC không làm thuật toán XOR mạnh hơn; ứng dụng thật cần authenticated encryption chuẩn.

Trước khi quay, chạy test, thử demo trên máy trình bày, đóng cửa sổ thông báo nhạy cảm và không để lộ keyfile thật.