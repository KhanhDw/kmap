# Việc của chủ dự án (agent không làm được)

Làm song song để không chặn agent. Cột "Hạn" là mốc muộn nhất để không làm trễ lịch.

| # | Việc | Hạn | Chặn milestone | Ghi chú |
| :-- | :-- | :-- | :-- | :-- |
| 1 | **Chụp thử 5 ảnh 360°** bằng thiết bị định dùng. Kiểm tra tỷ lệ 2:1, chiều rộng ≥ 4096 px, dung lượng ≤ 20 MB, có/không có EXIF GPS | Tuần 1 | M3 (kiểm chứng), M5a | Nếu camera xuất ảnh > 20 MB hoặc tỷ lệ khác 2:1, báo ngay để chỉnh quy tắc |
| 2 | **Xác nhận ranh giới** hai vùng theo báo cáo của agent. Nếu OSM thiếu/sai, đưa KML hoặc GeoJSON | Cuối M1 | M1 → M2 | Nên đối chiếu với đơn vị hành chính hiện hành |
| 3 | **Chọn nguồn vệ tinh**, đọc điều khoản (được phép hiển thị trực tiếp trên web công khai không? có cần khóa API không? giới hạn lượt?), rồi điền `SAT_TILE_URL`, `SAT_ATTRIBUTION`, `SAT_MAX_ZOOM` vào `.env` | Cuối tuần 1 | Nghiệm thu M2, ra mắt | Để trống = không có nền vệ tinh. Cũng cân nhắc độ phân giải có đủ hữu ích ở cấp đường làng không |
| 4 | **Chốt giấy phép** (mặc định: ảnh CC BY-SA 4.0, hình học đường CC0 1.0 — D-03) | Trước M5c | M5c, M6, M7 | Sau ra mắt không nên đổi |
| 5 | **VPS và tên miền**: tối thiểu 2 vCPU / 4 GB / 80 GB SSD, Ubuntu LTS, Docker; ưu tiên Việt Nam hoặc Singapore. Trỏ DNS | Tuần 2 | M7 | |
| 6 | **Deploy thử (staging)** theo README sau M4–M5 để phát hiện sớm lỗi HTTPS, DNS, quyền thư mục | Cuối tuần 3 | M7 | |
| 7 | **Chụp 20–50 ảnh 360° thật** dọc các trục đường chính của hai vùng, cách nhau 15–30 m, kèm ghi vị trí; ghi hướng nếu có | Cuối tuần 3 (bắt đầu từ tuần 2) | Nghiệm thu cuối | Không cần chờ agent |
| 8 | **Tài khoản admin đầu tiên**: chọn email và mật khẩu mạnh, điền vào `.env` | Trước M4 deploy | M4, M7 | Không gửi mật khẩu cho agent; tự đặt trong `.env` |
| 9 | **Chốt nơi backup ngoài VPS** (ổ khác, dịch vụ lưu trữ, máy khác) và điền `.env` | Tuần 4 | M7 | Backup chỉ nằm trên cùng VPS thì không đủ |
| 10 | **Email nhận yêu cầu gỡ ảnh** và thông tin đơn vị vận hành để điền vào `/terms`, `/privacy` | Tuần 4 | M7 | |
| 11 | **Soát `/terms` và `/privacy`**; nếu có thể, nhờ người am hiểu pháp lý (bao gồm quy định bảo vệ dữ liệu cá nhân hiện hành) xem lại rồi gỡ dòng "BẢN NHÁP" | Trước ra mắt | Ra mắt | Agent không được bịa viện dẫn pháp luật |
| 12 | **Quy trình duyệt ảnh**: dùng `docs/MODERATION_CHECKLIST.md`, quyết định ai duyệt và thời gian xử lý mục tiêu | Tuần 4 | Ra mắt | MVP chưa có blur tự động |
| 13 | **Thử khôi phục từ backup** cùng agent (kiểm tra bằng mắt kết quả ở `docs/RESTORE_TEST.md`) | Tuần 4 | Ra mắt | |
| 14 | **Kiểm tra bên ngoài** sau deploy: chỉ cổng 80/443 mở, http chuyển https, thử từ mạng di động | Tuần 5 | Ra mắt | |
| 15 | **Duyệt 20+ ảnh thật** và nạp vào hệ thống | Tuần 5 | Ra mắt | |
