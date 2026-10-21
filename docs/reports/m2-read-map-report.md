# Báo cáo M2 — API đọc và bản đồ

## Đã làm

- Thêm API công khai cho cấu hình bản đồ, đường OSM/cộng đồng và ảnh đã duyệt.
- Thay trang chủ bằng bản đồ Leaflet; thêm lớp đường, cụm ảnh, nút GPS và trạng thái vị trí trên URL.
- Giữ nền OSM tile chuẩn 256px theo lựa chọn ưu tiên độ nét của chủ dự án. Lớp vệ tinh không bật khi chưa cấu hình; không chọn nhà cung cấp.
- README ghi rõ chủ dự án phải chọn nguồn và xác nhận điều khoản vệ tinh trước khi công khai.

## Cách kiểm tra

- `make test`: 22 passed; test API dùng PostGIS thật.
- `make lint`: Ruff đạt; frontend TypeScript và Vite production build đạt.
- Kiểm tra bản đồ ở viewport 360×800: đường hiển thị tại cả Tân Châu và Phú Tân; URL chia sẻ `/?lat=10.500000&lng=105.200000&z=12` được giữ; lớp vệ tinh không xuất hiện khi chưa cấu hình.
- Kiểm tra API với dữ liệu OSM thật: `/roads` trả 310 feature, không bị cắt ngắn.

## Số đo

- `/roads`, viewport mặc định: median 17,73 ms, khoảng 15,43–21,86 ms trên máy dev; mục tiêu dưới 500 ms.
- Tải bản đồ Fast 4G mô phỏng, 360×800, cache trình duyệt tắt: median 3,57 giây trong 5 lượt (3,56–3,60 giây); 15/15 tile hoàn tất. Mô phỏng dùng độ trễ 150 ms, tải xuống 209.715 B/s và tải lên 96.000 B/s.
- Mục tiêu tải dưới 3 giây chưa đạt. Chủ dự án đã chọn giữ tile 256px để ưu tiên độ nét thay cho tile 512px bị mờ; không tự đổi nhà cung cấp hoặc giảm chất lượng.

## Quyết định tự đưa ra

- Giữ `keepBuffer: 0` và chỉ cập nhật tile khi bản đồ dừng để hạn chế tải thừa mà không làm mờ nền.
- Không cấu hình nền vệ tinh cho đến khi chủ dự án chọn nhà cung cấp và xác nhận điều khoản.

## Còn thiếu / rủi ro

- Thời gian tải viewport vẫn vượt mục tiêu 3 giây theo lựa chọn ưu tiên độ nét.
- Nền vệ tinh sẽ tiếp tục ẩn cho tới khi được cấu hình.

## Cần chủ dự án làm

- Xác nhận nghiệm thu M2 với trade-off hiệu năng đã nêu.
- Trước khi công khai nền vệ tinh, chọn nhà cung cấp, xác nhận điều khoản và điền các biến `SAT_*` trong `.env`.
