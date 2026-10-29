# Việc cần kiểm chứng hoặc hoàn tất ngoài repo

Tệp này gom các hạng mục không thể xác nhận chỉ bằng mã nguồn hiện tại hoặc cần quyền/người/thiết bị bên ngoài. Đánh dấu trạng thái và ghi người phụ trách/ngày trước khi nộp.

| Hạng mục | Trạng thái | Cách kiểm tra / người cần tham gia |
|---|---|---|
| Chạy toàn bộ pytest trên Python 3.11 | Chưa xác nhận | Môi trường khả dụng trong phiên là Python 3.14.7; 37 test đã pass tại đây. Tạo venv 3.11 rồi `python -m pytest -q`. |
| Chạy test trên ít nhất hai máy | Cần nhóm xác nhận | Mỗi máy chạy cùng commit; đính kèm log và phiên bản Python/OS. |
| Kiểm tra core với file 200 MiB | Đã kiểm tra | XOR khứ hồi + SHA-256 pass trong 4.4 giây trên Python 3.14.7; thời gian tùy phần cứng. |
| GUI kéo/thu nhỏ trong lúc mã hóa file 500 MiB | Cần kiểm tra thủ công | Chạy trên Windows có Tkinter; xác nhận UI phản hồi và progress tăng. |
| Hủy khi đang xử lý file lớn | Cần kiểm tra thủ công | Hủy giữa chừng; xác nhận file nguồn nguyên vẹn, không còn `.tmp`. Test tự động hiện có kiểm tra hủy trước khi bắt đầu. |
| Tkinter hiển thị tiếng Việt trên máy đích | Cần kiểm tra | Thử đường dẫn có dấu/khoảng trắng và font trên Windows/macOS/Linux mục tiêu. |
| Build PyInstaller trên Windows | Build thành công, chưa chạy ứng dụng | `dist/XorTool.exe` đã được tạo bằng Python 3.14.7 với `analysis/sample_text.txt` kèm theo. Cần mở app, kiểm tra tab demo và build lại bằng Python 3.11 cho môi trường nộp. |
| Chạy `.exe` trên máy không cài Python | Cần máy sạch | Thử khứ hồi, keyfile, hủy và demo trên máy đích; ghi lỗi thiếu DLL/Tk nếu có. |
| Độ chính xác benchmark chính thức | Chưa đo trong báo cáo cuối | Chạy `python -m analysis.benchmark`, lưu CSV/stdout, ghi commit và môi trường. Thử thêm tiếng Việt để ghi nhận giới hạn, không kỳ vọng cùng độ chính xác. |
| PNG/JPG/PDF/ZIP fixture hợp lệ | Cần xác minh công cụ định dạng | Mở từng fixture bằng viewer/validator tương ứng; hiện test fileformat kiểm tra byte round-trip, không kiểm tra parser ảnh/PDF. |
| Ảnh chụp giao diện, xuất slide và video | Nhóm cần hoàn tất | Báo cáo và nội dung slide đã có; chụp GUI thật, xuất slide từ `docs/SLIDES.md`, quay theo `docs/DEMO_SCRIPT.md`; không dùng hình/clip giả lập. |
| Pull request, review chéo, bảng lỗi và đóng góp từng người | Nhóm cần thực hiện | Tạo branch/PR, ít nhất một reviewer, điền bug tracker và xác nhận vai trò/danh tính theo thực tế. |
| Xác nhận yêu cầu giảng viên | Cần hỏi trực tiếp | Xác nhận Python/UI, phạm vi XOR/HMAC và yêu cầu phần breaker theo đề bài chính thức. |

## Giới hạn kiểm chứng hiện tại

- Bộ kiểm thử chạy thành công: 37 passed trên interpreter VS Code Python 3.14.7; chưa chạy trên Python 3.11 hoặc máy thứ hai.
- Không thể xác nhận độ phản hồi GUI, đóng gói chạy máy sạch, hình/video, review GitHub, hoặc việc nhóm đã chạy trên máy thứ hai từ repo cục bộ.
- XORT là bài tập học thuật. Không dùng để bảo vệ dữ liệu thực hoặc áp dụng breaker lên file của người khác.