# Quy tắc nghiệp vụ bắt buộc

## 1. Ảnh 360°

**Chấp nhận:** JPEG hoặc PNG (kiểm tra bằng nội dung, không tin đuôi file), tối đa 20 MB, chiều rộng tối thiểu 4096 px, tỷ lệ rộng:cao = 2:1 sai số ±2%, tối đa 120 triệu điểm ảnh.

**Thứ tự kiểm tra khi upload** (dừng ở lỗi đầu tiên):
1. Đăng nhập, không bị ban.
2. Rate limit và quota (mục 5).
3. Kích thước (413 nếu quá 20 MB; đọc theo luồng, không nạp cả file rồi mới kiểm).
4. Loại file thật bằng Pillow; kiểm tra số điểm ảnh.
5. Kích thước ảnh và tỷ lệ.
6. Tọa độ trong vùng phục vụ (D-08).
7. `terms_version` khớp phiên bản hiện hành của server.
8. Trùng SHA-256 (D-06).
9. Xử lý: bỏ toàn bộ EXIF, tạo `display`, `mobile`, `thumb` (D-04), lưu `exif_data`.

**Khác:**
- EXIF GPS chỉ dùng để gợi ý vị trí ở giao diện, không dùng làm điều kiện từ chối.
- Không lưu tên file do client gửi. Tên file lưu luôn là UUID.
- API công khai và API của chủ ảnh không bao giờ trả `exif_data`; chỉ endpoint admin trả.
- Ảnh công khai chỉ trả khi `status = 'approved' AND deleted_at IS NULL`.

## 2. Đường

- Chỉ nhận LineString, `ST_IsValid`, từ 2 đến 500 điểm, dài hơn 20 m (tính bằng `geography`).
- Toàn bộ đường nằm trong hợp các vùng phục vụ đã đệm 100 m (D-08).
- Đường cộng đồng không ghi đè hay sửa dữ liệu OSM.
- Không có chức năng sửa đường ở MVP: user xóa và vẽ lại.

## 3. Phân quyền

| Hành động | Ẩn danh | user | moderator | admin |
| :-- | :-- | :-- | :-- | :-- |
| Xem bản đồ, ảnh đã duyệt, đường đã duyệt | ✓ | ✓ | ✓ | ✓ |
| Đóng góp ảnh/đường, xem và xóa mềm của mình | | ✓ | ✓ | ✓ |
| Xem hàng chờ, duyệt/từ chối, sửa vị trí/hướng ảnh | | | ✓ | ✓ |
| Upload hàng loạt tự duyệt, xem thống kê | | | ✓ | ✓ |
| Xóa mềm ảnh/đường của người khác | | | ✓ | ✓ |
| Quản lý user (role, ban, đặt lại mật khẩu), purge ảnh | | | | ✓ |

Ràng buộc: không tự đổi role hoặc ban chính mình; luôn còn ít nhất 1 admin; user bị ban không đăng nhập được và token bị thu hồi.

## 4. Mã lỗi

Định dạng: `{"error": {"code": "...", "message": "<tiếng Việt>"}}`. Mã lỗi tiếng Anh.

| HTTP | code | Khi nào |
| :-- | :-- | :-- |
| 401 | `unauthorized` | Thiếu hoặc hết hạn token |
| 403 | `forbidden`, `banned` | Sai quyền; tài khoản bị khóa |
| 404 | `not_found` | Không có hoặc đã xóa |
| 409 | `duplicate_photo`, `email_taken` | Trùng ảnh; trùng email |
| 413 | `file_too_large` | Quá 20 MB |
| 422 | `validation_error`, `out_of_area`, `bad_image_ratio`, `image_too_small`, `unsupported_type`, `terms_required`, `invalid_geometry` | Dữ liệu không hợp lệ |
| 429 | `rate_limited`, `daily_quota_exceeded` | Vượt hạn mức |
| 500 | `internal_error` | Lỗi không lường trước (không kèm chi tiết) |

## 5. Hạn mức

- Đăng ký/đăng nhập: 10 lần/phút/IP.
- Endpoint ghi: 20 lần/phút/user (admin/moderator miễn khi upload hàng loạt).
- Tài khoản dưới 7 ngày tuổi: tối đa 10 ảnh mỗi ngày (đếm trong DB). Moderator/admin miễn.
- Request body: 25 MB cho endpoint upload ảnh; 1 MB cho các endpoint còn lại (đặt ở Caddy).

## 6. Lưu trữ và xóa

- Mọi xóa là xóa mềm (`deleted_at`) và chỉ người sở hữu hoặc moderator/admin được làm.
- Từ chối ảnh → xóa file (D-05). Purge ảnh → xóa file + `exif_data = NULL` + `purged_at` (chỉ admin).
- Backup giữ 14 ngày nên file đã purge còn tồn tại trong backup tối đa 14 ngày; phải nêu trong `/privacy`.

## 7. Bảo mật

- Không trả stack trace; bắt mọi exception ở handler chung, ghi log kèm request id.
- Không log mật khẩu, token, EXIF GPS.
- Truy cập file qua lớp `Storage` có chống path traversal.
- Header bảo mật cơ bản ở Caddy (HSTS, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, chặn nhúng khung).
- Mọi endpoint ghi yêu cầu đăng nhập và kiểm tra chủ sở hữu hoặc role.
