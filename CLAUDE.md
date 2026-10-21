# KMap — hướng dẫn cho agent

KMap là web bản đồ + ảnh 360° (kiểu Street View) + cổng đóng góp + trang admin duyệt, phủ **phường Tân Châu** và **xã Phú Tân** (An Giang). Đây là MVP: ưu tiên đơn giản, chạy được, kiểm chứng được.

## Bắt đầu mỗi phiên làm việc

1. Đọc `docs/STATUS.md` để biết milestone hiện tại và trạng thái.
2. Đọc `docs/milestones/<milestone hiện tại>.md`. Chỉ đọc thêm `docs/DECISIONS.md`, `docs/RULES.md`, `docs/DATA_MODEL.md` khi milestone trỏ tới hoặc khi cần tra cứu.
3. Chỉ làm milestone hiện tại. Không làm trước, không làm lại milestone khác trừ khi sửa lỗi hồi quy.

## Quy tắc cứng

1. Thứ tự: M0 → M1 → M2 → M3 → M4 → M5a → M5b → M5c → M6 → M7. Chỉ sang milestone kế khi mọi tiêu chí nghiệm thu đạt (có lệnh hoặc test chứng minh) **và chủ dự án xác nhận**.
2. Không thêm tính năng ngoài mục "Làm" của milestone hiện tại. Ý tưởng mới → ghi vào `BACKLOG.md`, không code.
3. Giữ nguyên stack ở `docs/PLAN.md` mục 3. Chỉ đổi công nghệ khi bị chặn thực sự, và phải hỏi trước.
4. Các quyết định trong `docs/DECISIONS.md` là cố định. Muốn đổi → dừng và hỏi.
5. Không hardcode cấu hình hay bí mật; mọi thứ qua `.env`. Giữ `.env.example` đầy đủ và luôn cập nhật. Không commit `.env`.
6. Không bịa dữ liệu thật: tọa độ, ranh giới, số liệu, nguồn dữ liệu, nội dung pháp lý. Thiếu thì dừng và hỏi.
7. Không tự chọn nhà cung cấp tile vệ tinh; không cache hàng loạt tile của bên thứ ba.
8. Không sửa hay xóa dữ liệu OSM. Đường cộng đồng không bao giờ ghi đè OSM.
9. Test dùng PostGIS thật (database `kmap_test` trong service `db`), không mock PostGIS.
10. Xong milestone: `make test` và `make lint` xanh, commit rõ ràng, cập nhật README và `docs/STATUS.md`, rồi báo cáo theo mẫu bên dưới.

## Khi nào dừng và hỏi chủ dự án

Chỉ hỏi khi: thiếu dữ liệu hoặc quyền truy cập; yêu cầu mâu thuẫn; số đo vượt ngưỡng cảnh báo ghi trong milestone; cần đổi stack hoặc một quyết định cố định.
Cách hỏi: nêu vấn đề, đã thử gì, 2–3 phương án kèm đề xuất của bạn.
Mọi việc còn lại tự quyết theo hướng đơn giản nhất và ghi một dòng vào báo cáo cuối milestone.

## Lệnh chuẩn (tạo ở M0, giữ tên ổn định)

| Lệnh | Việc |
| :-- | :-- |
| `make up` / `make down` / `make logs` | Dựng, tắt, xem log toàn hệ thống |
| `make migrate` | Chạy Alembic lên bản mới nhất |
| `make test` | pytest (backend) + Vitest (frontend) |
| `make lint` | ruff + mypy-lite/pyright (nếu có) + eslint + tsc |
| `make e2e` | Playwright smoke test |
| `make seed-admin` | Tạo admin đầu tiên từ biến môi trường |

## Quy ước code

- Backend: Python 3.12, type hint đầy đủ, Pydantic v2, SQLAlchemy 2 (style mới), router mỏng, logic ở `services/`.
- Frontend: TypeScript strict, gọi API qua `src/api/`, dữ liệu server qua TanStack Query, không dùng `any` nếu tránh được.
- Tên mã, biến, endpoint, mã lỗi: tiếng Anh. Thông báo cho người dùng và nội dung giao diện: **tiếng Việt**.
- Lỗi API luôn có dạng `{"error": {"code": "...", "message": "..."}}` (xem `docs/RULES.md`). Không bao giờ trả stack trace.
- Mọi xóa là xóa mềm (`deleted_at`), trừ thao tác `purge` được mô tả trong `docs/RULES.md`.
- Commit: `type(mX): mô tả ngắn` (ví dụ `feat(m5a): photo upload pipeline`). Một milestone có thể nhiều commit.
- Mỗi tính năng có test đi kèm; test cho quy tắc nghiệp vụ nằm trong `backend/tests/`.

## Báo cáo cuối milestone (mẫu)

```
## Báo cáo <Mx>
**Đã làm:** (gạch đầu dòng ngắn)
**Cách kiểm tra:** (lệnh chạy được + kết quả mong đợi)
**Số đo:** (số liệu milestone yêu cầu, ví dụ thời gian, số lượng)
**Quyết định tự đưa ra:** (mỗi việc 1 dòng)
**Còn thiếu / rủi ro:** (nếu có)
**Cần chủ dự án làm:** (nếu có, liên kết tới docs/HUMAN_TASKS.md)
```
