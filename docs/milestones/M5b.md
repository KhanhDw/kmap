# M5b — Giao diện admin duyệt ảnh (tuần 3, ngày 11–13)

Đọc trước: `docs/MODERATION_CHECKLIST.md` (mẫu lý do từ chối), `docs/RULES.md` mục 3.

## Làm
- Layout admin (thanh bên, tối ưu máy tính, không vỡ trên tablet), dashboard 4 thẻ số từ `/admin/stats` (chờ duyệt ảnh, đã duyệt, chờ duyệt đường, user).
- `/admin/upload` — upload hàng loạt:
  - Kéo thả nhiều ảnh; mỗi dòng có thumbnail xem trước, trạng thái, nút thử lại.
  - Đặt vị trí từng ảnh trên bản đồ nhỏ; gợi ý từ EXIF GPS nếu có (đọc ở client); sau khi chọn vị trí tự chuyển sang ảnh kế tiếp để thao tác nhanh. Nhập `heading` tùy chọn.
  - Gửi **từng ảnh một request**, song song tối đa 2 (D-13). Hiển thị lỗi từng ảnh bằng thông báo tiếng Việt (trùng, ngoài vùng, sai tỷ lệ...) mà không dừng cả lô.
- `/admin/photos`:
  - Lưới thumbnail có lọc theo trạng thái (mặc định "chờ duyệt"), phân trang.
  - Panel bên phải: viewer 360° (bản `display`), bản đồ nhỏ, metadata (người đóng góp, ngày chụp, kích thước, EXIF tóm tắt).
  - Sửa vị trí (kéo marker trên bản đồ nhỏ) và hướng, rồi lưu.
  - Phím tắt: **A** duyệt, **R** từ chối, **→** ảnh kế, **←** ảnh trước. **R** mở hộp thoại có các lý do mẫu (từ `docs/MODERATION_CHECKLIST.md`) và ô nhập tự do; phím tắt bị vô hiệu khi đang gõ trong ô nhập; `Ctrl+Enter` xác nhận.
  - Nút "Gỡ hẳn (purge)" chỉ hiện với admin, phải gõ "XOA" để xác nhận.
- Logic phím tắt tách thành hàm/hook có test Vitest.

## Không làm
Trang đóng góp của người dùng, quản lý đường và user.

## Nghiệm thu
- [ ] Vitest cho xử lý phím tắt (không kích hoạt khi đang gõ; R mở hộp thoại; không duyệt khi chưa chọn ảnh).
- [ ] E2E: admin upload 5 ảnh giả (mỗi ảnh một vị trí) → tự duyệt → `GET /photos` trả đủ 5; một ảnh trùng và một ảnh ngoài vùng hiện lỗi riêng, không làm hỏng các ảnh còn lại.
- [ ] E2E: ảnh `pending` → bấm A → hiện ở bản đồ công khai; bấm R + lý do → ảnh biến mất khỏi hàng chờ và file bị xóa.
- [ ] Chủ dự án thử nạp 20 ảnh giả bằng tay và ghi lại thời gian thao tác (mục tiêu: vài phút).
- [ ] Moderator không thấy nút purge; admin thấy.

## Báo cáo
Theo mẫu trong `CLAUDE.md`, kèm ảnh chụp màn hình các trang admin.
