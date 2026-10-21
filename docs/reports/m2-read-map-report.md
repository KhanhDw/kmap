# Báo cáo M2 — API đọc và bản đồ

## Đã làm

- Thêm API công khai cho cấu hình bản đồ, đường OSM/cộng đồng và ảnh đã duyệt.
- Thay trang chủ bằng bản đồ Leaflet; thêm lớp đường, cụm ảnh, nút GPS và trạng thái vị trí trên URL.
- Giữ nền OSM tile chuẩn 256px theo lựa chọn ưu tiên độ nét của chủ dự án; viewport hẹp tự fit vùng phục vụ ở zoom thấp hơn một mức để giảm số tile ban đầu.
- Lớp vệ tinh không bật khi chưa cấu hình; không chọn nhà cung cấp.
- README ghi rõ chủ dự án phải chọn nguồn và xác nhận điều khoản vệ tinh trước khi công khai.

## Cách kiểm tra

- `make test`: 22 passed; test API dùng PostGIS thật.
- `make lint`: Ruff đạt; frontend TypeScript và Vite production build đạt.
- Kiểm tra bản đồ ở viewport 360×800: đường hiển thị tại cả Tân Châu và Phú Tân; URL chia sẻ `/?lat=10.500000&lng=105.200000&z=12` được giữ; lớp vệ tinh không xuất hiện khi chưa cấu hình.
- Kiểm tra API với dữ liệu OSM thật: `/roads` trả 310 feature, không bị cắt ngắn.

## Số đo

- `/roads`, viewport mặc định: median 17,73 ms, khoảng 15,43–21,86 ms trên máy dev; mục tiêu dưới 500 ms.
- Trước khi fit theo viewport, tải bản đồ Fast 4G mô phỏng ở 360×800 có median 3,57 giây và 15 tile.
- Sau tối ưu, median 2,95 giây trong 5 lượt (2,94–3,10 giây); 8/8 tile hoàn tất. Mô phỏng dùng độ trễ 150 ms, tải xuống 209.715 B/s, tải lên 96.000 B/s và tắt cache trình duyệt.
- Median đạt mục tiêu dưới 3 giây; một lượt khởi tạo lạnh mất 3,10 giây. Giữ nguyên tile 256px, không đổi nhà cung cấp hoặc giảm chất lượng.
- Chủ dự án xác nhận nghiệm thu M2. Ghi công `© OpenStreetMap contributors` được giữ; nhãn Leaflet bị ẩn.

## Quyết định tự đưa ra

- Giữ `keepBuffer: 0`, chỉ cập nhật tile khi bản đồ dừng, và điều chỉnh fit theo viewport để tránh tải tile thừa mà không làm mờ nền.
- Không cấu hình nền vệ tinh cho đến khi chủ dự án chọn nhà cung cấp và xác nhận điều khoản.

## Còn thiếu / rủi ro

- Thời gian tải viewport vẫn vượt mục tiêu 3 giây theo lựa chọn ưu tiên độ nét.
- Nền vệ tinh sẽ tiếp tục ẩn cho tới khi được cấu hình.

## Cần chủ dự án làm

- Trước khi công khai nền vệ tinh, chọn nhà cung cấp, xác nhận điều khoản và điền các biến `SAT_*` trong `.env`.
