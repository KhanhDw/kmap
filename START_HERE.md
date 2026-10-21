# Cách dùng bộ tài liệu này (dành cho chủ dự án)

## 1. Đặt vào repo
Tạo repo `kmap`, copy toàn bộ nội dung bộ này vào gốc repo (giữ nguyên `CLAUDE.md`, `BACKLOG.md`, `docs/`). Mở Claude Code (hoặc agent tương đương) trong thư mục repo. `CLAUDE.md` sẽ được agent đọc tự động; nếu agent của bạn không tự đọc, hãy bảo nó đọc file này đầu tiên.

## 2. Tin nhắn đầu tiên (phiên M0)
```
Đọc CLAUDE.md và docs/STATUS.md. Milestone hiện tại là M0_v1.
Đọc docs/milestones/M0_v1.md và docs/milestones/M0.md và đối chiếu logic và thực hiện đúng phạm vi. Khi xong, báo cáo theo mẫu trong CLAUDE.md.
```

## 3. Mỗi milestone về sau
Sau khi bạn tự kiểm tra các mục nghiệm thu (nên thử trên điện thoại thật), nói với agent:
```
M<x> đạt. Đổi trạng thái M<x> sang "Đã xác nhận" trong docs/STATUS.md,
đặt milestone hiện tại là M<y>, đọc docs/milestones/M<y>.md và làm đúng phạm vi.
```
Nên bắt đầu phiên mới (xóa ngữ cảnh) cho mỗi milestone; `STATUS.md` và `CLAUDE.md` đủ để agent tiếp tục.

## 4. Thứ tự và điểm chặn cần bạn có mặt
- **M1:** agent in báo cáo ranh giới và dừng chờ bạn xác nhận (việc #2 ở `docs/HUMAN_TASKS.md`).
- **M2:** cần bạn chọn nguồn vệ tinh và điền `.env` (việc #3) để nghiệm thu nền vệ tinh.
- **M4:** điền thông tin admin vào `.env` (việc #8); cuối M4 nên thử deploy lên VPS.
- **M7:** soát `/terms`, `/privacy`; thử khôi phục backup cùng agent.

## 5. Mẹo
- Giao **từng milestone**, đừng giao cả dự án một lần.
- Agent lệch phạm vi → nhắc: "Chỉ làm đúng mục Làm của milestone hiện tại. Ý tưởng thêm ghi vào BACKLOG.md."
- Khi có lỗi, đưa log nguyên văn và lệnh vừa chạy, không mô tả lại bằng lời.
- Kiểm tra `git log` sau mỗi milestone để dễ quay lại.
- Bắt đầu chụp ảnh 360° ngay tuần 1: đây là việc dài nhất và agent không làm thay được.

## 6. Thay đổi so với kế hoạch bản đầu

| Chủ đề | Bản đầu | Bản này |
| :-- | :-- | :-- |
| Thời gian | 3 tuần | 4–5 tuần, có dự phòng và bảng việc của con người theo tuần |
| M5 | Một khối 4 ngày | Tách M5a (backend), M5b (admin UI), M5c (client UI) |
| Compose | 3 service nhưng có Caddy ở ngoài | `web` = Caddy dựng nhiều giai đoạn (D-01) |
| Ảnh lân cận | Gần nhất theo khoảng cách | Có hướng: `forward`/`backward` theo bearing (D-07) |
| Ảnh trên điện thoại | Một bản 8192 px | Thêm bản 4096 và chọn theo giới hạn texture WebGL (D-04, M3) |
| Giấy phép | CC BY-SA 4.0 cho tất cả | Ảnh CC BY-SA 4.0, hình học đường CC0 (D-03) |
| Xóa | Chỉ xóa mềm | Thêm từ chối = xóa file, và purge cho yêu cầu gỡ ảnh (D-05) |
| Chống trùng | SHA-256 UNIQUE toàn bảng | Unique một phần + chặn file đã purge (D-06) |
| Khu vực | Kiểm tra bằng độ | Bảng `service_areas`, đệm 100 m trên `geography` (D-08) |
| OSM | Bảng mặc định, import một lần | Schema `osm`, script chạy lại được, backup loại trừ OSM (D-09) |
| Rate limit | Chưa nói cách làm | In-process, 1 worker, IP từ proxy, quota đếm trong DB (D-10) |
| Token | JWT, refresh 30 ngày | Refresh lưu băm, xoay, thu hồi khi ban/logout/reset; kiểm tra ban mỗi request (D-11) |
| Nền vệ tinh | Mặc định dùng nguồn công khai | Không mặc định; trống thì ẩn layer (D-12) |
| Marker ảnh | Không nói | Giới hạn 2.000 + gom cụm (D-14) |
| Backup | Có | Loại trừ OSM, snapshot 14 bản, bản sao ngoài VPS, cảnh báo ở dashboard |
| Quên mật khẩu | Không | Admin đặt lại mật khẩu (M6) |
| E2E | Chỉ ở M7 | Khung từ M4, đầy đủ từ M5c |
| Nghiệm thu | Nhiều mục cảm tính | Thêm lệnh, số đo và test cụ thể |
| Cách giao agent | Một tài liệu dài | `CLAUDE.md` + `STATUS.md` + một file cho mỗi milestone |
