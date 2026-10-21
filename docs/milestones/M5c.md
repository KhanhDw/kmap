# M5c — Đóng góp ảnh của người dùng (tuần 3, ngày 14–15)

Đọc trước: `docs/RULES.md` mục 1 và 5, `docs/DECISIONS.md` (D-03, D-16).

## Làm
- `/contribute/photo` (yêu cầu đăng nhập, chưa đăng nhập thì chuyển tới `/login` rồi quay lại):
  - Chọn file (kiểm tra sơ bộ ở client: loại file, dung lượng, tỷ lệ 2:1 để báo lỗi sớm; server vẫn là nơi quyết định cuối cùng).
  - Bản đồ nhỏ chọn vị trí; nút "Dùng vị trí hiện tại của tôi"; gợi ý từ EXIF GPS nếu có. Nhập `heading` tùy chọn kèm hướng dẫn ngắn.
  - Hộp tick điều khoản: ghi rõ ảnh phát hành theo CC BY-SA 4.0 và tên hiển thị sẽ công khai; liên kết tới `/terms` (trang nội dung hoàn thiện ở M7; ở M5c dùng trang tạm). `terms_version` lấy từ `/config`.
  - Thanh tiến trình upload; hiển thị lỗi tiếng Việt theo mã lỗi (`docs/RULES.md` mục 4).
- `/me`: tab "Ảnh của tôi" với thumbnail (placeholder cho ảnh bị từ chối vì file đã xóa), badge trạng thái, lý do từ chối, nút xóa (xóa mềm, có xác nhận). (Tab "Đường" thêm ở M6.)
- Điều hướng: trên điện thoại dùng thanh dưới (Bản đồ, Đóng góp, Của tôi); touch target ≥ 44 px; kiểm tra ở 360 px.
- **E2E đầy đủ (Playwright):** đăng ký → upload ảnh giả → thấy `pending` ở `/me` → admin duyệt → ảnh hiện trên bản đồ công khai; một kịch bản khác: admin từ chối → user thấy lý do ở `/me`.

## Không làm
Đóng góp đường.

## Nghiệm thu
- [ ] E2E hai kịch bản trên xanh trong `make e2e`.
- [ ] Upload ảnh sai tỷ lệ, ngoài vùng, trùng đều hiện đúng thông báo tiếng Việt.
- [ ] Không thể gửi khi chưa tick điều khoản.
- [ ] Trên viewport 360 px không có cuộn ngang (`scrollWidth <= innerWidth`) ở `/`, `/contribute/photo`, `/me`.
- [ ] Chủ dự án thử upload ảnh 360° thật từ điện thoại và ghi lại kết quả.

## Báo cáo
Theo mẫu trong `CLAUDE.md`.
