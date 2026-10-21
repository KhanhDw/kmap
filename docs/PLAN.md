# KMap — Kế hoạch tổng thể

**Khu vực:** phường Tân Châu và xã Phú Tân, tỉnh An Giang.
**Mục tiêu:** MVP web (client + admin) chạy trên VPS, ra mắt sau 4–5 tuần (3 tuần code + dư địa cho việc của con người: chụp ảnh, duyệt, pháp lý, deploy).

## 1. Lịch

| Tuần | Milestone | Việc song song của chủ dự án |
| :-- | :-- | :-- |
| 1 | M0, M1, M2 | Chụp thử 5 ảnh 360°; xác nhận ranh giới; chọn nguồn vệ tinh |
| 2 | M3, M4, M5a | Chuẩn bị VPS + DNS; bắt đầu chụp ảnh dọc trục đường chính |
| 3 | M5b, M5c | Deploy thử lên VPS theo README (staging) |
| 4 | M6, M7 | Soát `/terms`, `/privacy`; chốt nơi backup ngoài VPS |
| 5 | Dự phòng | Duyệt ảnh thật, nạp ≥ 20 ảnh, kiểm tra cuối, ra mắt |

Chi tiết việc của con người: `docs/HUMAN_TASKS.md`.

## 2. Phạm vi

### 2.1 Trong phạm vi

- Bản đồ nền đường phố (OSM) và nền vệ tinh (nguồn cấu hình qua `.env`), chuyển layer, nút GPS.
- Hiển thị đường OSM (chỉ đọc) và đường cộng đồng đã duyệt (màu khác).
- Ảnh 360°: marker (có gom cụm), viewer Pannellum, nút ảnh lân cận theo hướng.
- Tài khoản: đăng ký, đăng nhập, đăng xuất (email + mật khẩu).
- Đóng góp ảnh 360° (có điều khoản), đóng góp đường (vẽ tay polyline).
- Trang "Của tôi": danh sách đóng góp, trạng thái, lý do từ chối, xóa mềm.
- Admin: dashboard, hàng chờ ảnh và đường (duyệt/từ chối kèm lý do), upload hàng loạt (tự duyệt), quản lý user (đổi role, ban, đặt lại mật khẩu), gỡ hẳn ảnh (purge).
- Giới hạn địa lý: mọi đóng góp phải nằm trong vùng phục vụ (đệm 100 m).
- Triển khai Docker Compose, HTTPS, backup hằng ngày có thử khôi phục.

### 2.2 Ngoài phạm vi

GPX, báo cáo vi phạm, reputation/auto-approve, blur tự động, pHash, Hausdorff, tile server, Sentinel, MinIO/presigned URL, PWA offline, routing, app native, xác thực email, quên mật khẩu tự phục vụ, đăng nhập mạng xã hội, đa ngôn ngữ (chỉ tiếng Việt), xử lý ảnh nền (hàng đợi).

## 3. Stack cố định

| Lớp | Công nghệ |
| :-- | :-- |
| Frontend | React 18 + TypeScript + Vite, Tailwind CSS, shadcn/ui, TanStack Query, React Router |
| Bản đồ | Leaflet + react-leaflet + leaflet-draw + leaflet.markercluster |
| Viewer 360° | Pannellum, đóng gói cục bộ (không dùng CDN), bọc bằng wrapper component |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, GeoAlchemy2, Alembic, Pydantic v2 |
| Ảnh | Pillow, piexif hoặc exifread |
| Auth | JWT (PyJWT hoặc python-jose), argon2 |
| Rate limit | In-process (ví dụ slowapi), xem D-10 |
| DB | PostgreSQL 16 + PostGIS 3.4 |
| Lưu file | Volume `/data/media`, qua lớp `Storage` (interface) để sau đổi S3/MinIO |
| Proxy/HTTPS | Caddy, chạy trong service `web` |
| Test | pytest + httpx, Vitest (logic chính), Playwright (smoke E2E) |
| Đóng gói | Docker Compose, 3 service: `db`, `api`, `web` (D-01) |

Trình quản lý gói Python (uv hoặc pip) do agent chọn, ghi trong README.

## 4. Vùng phục vụ

Dự án phủ **hai vùng riêng biệt**: phường Tân Châu và xã Phú Tân. Không dùng một bbox chung vì sẽ gồm cả khu vực ngoài phạm vi.

1. `config/areas.geojson` (FeatureCollection, 2 polygon, thuộc tính `name`, `slug`) là nguồn sự thật. Lấy từ quan hệ ranh giới hành chính của OSM (Overpass hoặc Nominatim). Chi tiết ở `docs/milestones/M1.md`.
2. Nếu OSM thiếu hoặc sai ranh giới (kể cả còn theo đơn vị hành chính cũ), **dừng và hỏi chủ dự án**; chủ dự án cung cấp KML/GeoJSON. Không tự bịa tọa độ.
3. Khi khởi động, API đồng bộ file này vào bảng `service_areas` (D-08). Mọi kiểm tra "trong vùng" dùng bảng này với đệm 100 m tính trên `geography`.
4. Thêm vùng mới = thêm feature vào file và khởi động lại, không sửa code.

## 5. Cấu trúc repo

```
kmap/
├── CLAUDE.md  BACKLOG.md  README.md  Makefile
├── docker-compose.yml  docker-compose.dev.yml  .env.example
├── Caddyfile
├── config/areas.geojson
├── docs/                     (STATUS, PLAN, DECISIONS, DATA_MODEL, RULES,
│   └── milestones/            HUMAN_TASKS, MODERATION_CHECKLIST, RUNBOOK, ...)
├── backend/
│   ├── Dockerfile  pyproject.toml  alembic/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/       (config, security, deps, ratelimit, errors)
│   │   ├── models/     (user, refresh_token, photo, road, terms, area)
│   │   ├── schemas/
│   │   ├── routers/    (auth, config, roads, photos, me, admin)
│   │   └── services/   (storage, images, exif, areas, neighbors, moderation)
│   └── tests/
├── frontend/
│   ├── Dockerfile  vite.config.ts
│   └── src/ (api/  components/  lib/  pages/client/  pages/admin/  routes.tsx)
├── e2e/                      (Playwright)
└── scripts/
    ├── fetch_osm.sh  seed_admin.py  seed_demo.py
    ├── backup.sh  restore.sh
    └── make_test_panorama.py  (sinh ảnh equirectangular giả để test)
```

## 6. Yêu cầu chất lượng

- **Hiệu năng:** viewport mặc định tải dưới 3 giây trên Fast 4G mô phỏng (đo bằng Playwright/Chrome DevTools, ghi số vào báo cáo). Thumbnail cho marker/lưới; ảnh đầy đủ chỉ tải khi mở viewer.
- **Bảo mật:** không lộ stack trace; kiểm tra kiểu file bằng nội dung; tên file lưu bằng UUID; giới hạn kích thước request ở proxy; secret chỉ trong `.env`; Postgres và API không mở cổng ra ngoài.
- **Test tối thiểu:** auth, phân quyền, kiểm tra ảnh (tỷ lệ, trùng, ngoài vùng, loại file, EXIF), kiểm tra đường, luồng duyệt, quota. `make test` chạy được trong một lệnh.
- **Khả dụng:** client ưu tiên điện thoại (touch target ≥ 44 px, chạy tốt ở 360 px); admin ưu tiên máy tính nhưng không vỡ trên tablet.
- **Code:** type hint đầy đủ ở backend; `ruff` + `eslint` + `tsc` không lỗi.

## 7. Định nghĩa hoàn thành (toàn dự án)

- [ ] `docker compose up -d --build` dựng toàn hệ thống trên VPS sạch, có HTTPS; chỉ cổng 80/443 mở ra ngoài.
- [ ] Bản đồ hiển thị đường OSM của cả hai vùng; chuyển được nền đường/vệ tinh (khi nguồn vệ tinh đã được chủ dự án cấu hình).
- [ ] Có ít nhất 20 ảnh 360° thật đã duyệt, đúng vị trí; xem, xoay, chuyển ảnh lân cận hoạt động trên điện thoại.
- [ ] User đăng ký, đăng nhập, upload ảnh, vẽ đường, xem trạng thái ở `/me`.
- [ ] Admin: dashboard, upload hàng loạt, duyệt/từ chối ảnh và đường kèm lý do, quản lý user, purge ảnh.
- [ ] Đóng góp ngoài vùng phục vụ bị từ chối với thông báo rõ ràng.
- [ ] Backup hằng ngày chạy, có bản sao ngoài VPS, đã khôi phục thử thành công (`docs/RESTORE_TEST.md`).
- [ ] Ghi công OpenStreetMap, nguồn vệ tinh, điều khoản CC BY-SA 4.0 (ảnh) và CC0 (hình học đường) hiển thị đúng.
- [ ] `/terms` và `/privacy` đã được chủ dự án (và người am hiểu pháp lý nếu có) soát.
- [ ] Test backend, frontend và E2E đều qua.
- [ ] README đủ để người khác deploy và vận hành; `docs/RUNBOOK.md` có quy trình gỡ ảnh theo yêu cầu.
