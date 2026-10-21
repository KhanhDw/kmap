# M5a — Upload ảnh và API duyệt ảnh (tuần 2, ngày 9–10)

Đọc trước: `docs/RULES.md` mục 1, 5, 6; `docs/DECISIONS.md` (D-04, D-05, D-06, D-13, D-15, D-16); `docs/DATA_MODEL.md`.

## Làm

**Lớp xử lý**
- `services/storage.py`: interface `Storage` (`save`, `read`, `delete`, `delete_prefix`, `url`, `exists`) + bản local theo volume `/data/media`, chống path traversal.
- `services/exif.py`: đọc EXIF (GPS, thời gian chụp, thiết bị) thành JSON an toàn cho `exif_data`.
- `services/images.py`: kiểm tra và xử lý ảnh đúng thứ tự trong `docs/RULES.md` mục 1; tạo `display` (không phóng to), `mobile`, `thumb` (D-04); bản công khai không có EXIF; `MAX_IMAGE_PIXELS` theo D-13; xử lý trong threadpool với semaphore 2.

**API người dùng**
- `POST /api/v1/photos` (multipart: `file`, `lat`, `lon`, `heading?`, `captured_at?`, `terms_version`). Lưu `contributor_terms` khi nhận. Trạng thái `pending`.
- `GET /api/v1/me/photos` (kèm status, lý do từ chối), `DELETE /api/v1/photos/{id}` (xóa mềm; chủ sở hữu hoặc moderator/admin).
- Rate limit 20 lần/phút/user cho endpoint ghi; quota 10 ảnh/ngày cho tài khoản dưới 7 ngày tuổi (`docs/RULES.md` mục 5).

**API admin**
- `GET /admin/stats` (số ảnh chờ duyệt, đã duyệt, số đường chờ duyệt = 0 cho tới M6, tổng user).
- `GET /admin/queue/photos?status=&cursor=` (phân trang, cũ nhất trước; kèm contributor, `exif_data`).
- `GET /admin/photos/{id}` (đầy đủ, có `exif_data`).
- `POST /admin/photos/{id}/approve`; `POST /admin/photos/{id}/reject` (bắt buộc `reason`; **xóa file** theo D-05).
- `PATCH /admin/photos/{id}` (sửa vị trí và hướng; vị trí vẫn phải trong vùng).
- `POST /admin/photos` (upload + tự duyệt, không bị quota, ghi `moderator_id`).
- `POST /admin/photos/{id}/purge` (chỉ admin; D-05).
- Thay bản xử lý tạm của `seed_demo.py` (M3) bằng pipeline thật.

## Không làm
Giao diện (M5b, M5c).

## Nghiệm thu
Test pytest dùng PostGIS thật và ảnh sinh từ `make_test_panorama.py`:
- [ ] Hợp lệ: 8192×4096 → có `display` rộng 8192, `mobile` 4096, `thumb` 400; ảnh 6000×3000 → `display` rộng 6000 (không phóng to).
- [ ] Từ chối đúng mã lỗi: sai tỷ lệ, quá hẹp (< 4096), quá 20 MB (413), file `.txt` đổi đuôi `.jpg`, PNG hợp lệ nhận được, ảnh vượt giới hạn điểm ảnh (decompression bomb).
- [ ] Ngoài vùng → 422 `out_of_area` với thông báo tiếng Việt; trong khoảng đệm 100 m thì nhận.
- [ ] Trùng SHA-256 → 409; upload lại sau khi bị từ chối → nhận; upload lại sau khi bị purge → từ chối.
- [ ] Bản `display/mobile/thumb` **không chứa EXIF** (kiểm tra bằng đọc lại file); `exif_data` có dữ liệu cho admin; API công khai và `/me/photos` không bao giờ trả `exif_data`.
- [ ] `terms_version` sai → 422 `terms_required`.
- [ ] Quota: tài khoản mới ảnh thứ 11 trong ngày → 429 `daily_quota_exceeded`; admin không bị.
- [ ] Duyệt → ảnh xuất hiện ở `GET /photos`; từ chối → file bị xóa, `/me/photos` trả lý do; xóa mềm → biến mất khỏi công khai.
- [ ] User thường gọi endpoint admin → 403; moderator gọi purge → 403.
- [ ] Hai upload đồng thời không vượt semaphore (kiểm bằng test hoặc log).
- [ ] Đo thời gian xử lý 1 ảnh 8192×4096 và ghi vào báo cáo.

## Báo cáo
Theo mẫu trong `CLAUDE.md`, kèm thời gian xử lý ảnh và mức RAM đỉnh ước lượng.
