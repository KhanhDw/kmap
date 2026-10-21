# BACKLOG

Ý tưởng ngoài phạm vi MVP. Agent chỉ **ghi thêm** vào đây, không code.

## Đã biết từ đầu (chưa làm ở MVP)

- Cập nhật dữ liệu OSM định kỳ: import vào schema tạm rồi hoán đổi (swap) trong một transaction. (M1 chỉ yêu cầu script chạy lại được.)
- GPX import, báo cáo vi phạm, reputation / auto-approve.
- Blur mặt và biển số tự động.
- pHash chống ảnh gần trùng; Hausdorff / snap đường vào OSM.
- Tile server riêng (TileServer-GL / TiTiler), cache tile vệ tinh hợp lệ.
- MinIO / presigned URL (lớp `Storage` đã chuẩn bị để đổi).
- PWA offline, routing, app native.
- Xác thực email, quên mật khẩu tự phục vụ, đăng nhập mạng xã hội.
- Đa ngôn ngữ.
- Xử lý ảnh nền (hàng đợi) nếu lượng upload tăng.
- Multi-resolution tiles cho Pannellum thay cho 2 bản 8192/4096.
- Giám sát (uptime, lỗi) và cảnh báo.

## Ý tưởng mới (agent ghi vào đây)

- Tự host nền phố OSM để bỏ phụ thuộc tile bên thứ ba lúc chạy: dùng PBF Việt Nam từ Geofabrik (đã có trong `fetch_osm.sh`) tạo vector tiles/PMTiles và phục vụ nội bộ. Cần chủ dự án duyệt cập nhật `PLAN.md`/stack trước khi làm; vẫn giữ ghi công OpenStreetMap.

## Từ M0_v1
- (trống)
