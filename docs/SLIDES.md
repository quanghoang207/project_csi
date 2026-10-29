# Bản nháp nội dung slide

## Slide 1: XORT, công cụ học XOR

- Mục tiêu: quan sát mã hóa XOR, tính toàn vẹn và phân tích khóa lặp.
- Giới hạn: demo học tập, không bảo vệ dữ liệu thật.
- Nhóm 5 người; thêm tên thật và lớp trước khi trình bày.

## Slide 2: Phép toán XOR

- $C_i = P_i \oplus K_{i \bmod L}$.
- $P_i = C_i \oplus K_{i \bmod L}$.
- Cùng XOR hai lần với cùng byte sẽ khôi phục byte gốc.

## Slide 3: Vì sao khóa lặp yếu

- Vị trí cách nhau bội số chiều dài khóa chia sẻ cùng byte khóa.
- Hamming normalized distance ước lượng chu kỳ.
- Phân tích tần suất từng cột có thể khôi phục plaintext tiếng Anh.
- Chụp màn hình tab demo với sample tự tạo sau khi chạy app thật.

## Slide 4: Định dạng file XORT

- Header: `XORT`, version, salt 16 byte, kích thước plaintext.
- Payload: ciphertext XOR cùng độ dài dữ liệu gốc.
- Footer: HMAC-SHA256 trên header + ciphertext.
- Chèn sơ đồ luồng trong `docs/REPORT.md`.

## Slide 5: Luồng mã hóa/giải mã

- Mã hóa: KDF/đọc keyfile, ghi header, XOR theo chunk, HMAC, atomic replace.
- Giải mã: xác minh HMAC trước, rồi mới XOR ra file tạm.
- Worker thread + queue giúp UI còn phản hồi; hủy dọn file `.tmp`.

## Slide 6: Kiểm thử và kết quả

- 37 pytest pass trên Python 3.14.7.
- Khứ hồi 200 MiB + SHA-256 pass trong 4.4 giây trên máy đo.
- Benchmark breaker: CSV tại `docs/BREAKER_RESULTS.csv`.
- Thay bằng ảnh, phiên bản Python và kết quả từ môi trường nhóm trước buổi bảo vệ.

## Slide 7: Giới hạn và hướng phát triển

- Repeating-key XOR không an toàn; HMAC không tăng tính bí mật.
- OTP chỉ lý tưởng khi pad ngẫu nhiên, dài bằng message, giữ bí mật, dùng đúng một lần.
- Ứng dụng thật: dùng thư viện đã kiểm chứng với AES-GCM/ChaCha20-Poly1305.
- Cần test Python 3.11, máy sạch, GUI 500 MiB, hủy giữa chừng.

## Slide 8: Kết luận và phân công

- Nêu phần việc từng thành viên theo `docs/TEAM_CONTRIBUTIONS.md`.
- Demo mã hóa, giải mã, phát hiện sửa đổi và breaker.
- Nêu rõ kết quả đo, hạn chế và việc nhóm còn cần xác minh.