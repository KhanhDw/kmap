# Quyết định cố định

Agent không tự đổi các mục này. Muốn đổi → dừng và hỏi chủ dự án.

**D-01 Compose có 3 service: `db`, `api`, `web`.**
`web` là image Caddy được dựng nhiều giai đoạn: build frontend (Node) rồi copy `dist` vào Caddy. Caddy phục vụ static, proxy `/api` sang `api`, phục vụ `/media` từ volume (mount read-only), tự cấp HTTPS. Chỉ `web` publish cổng 80/443. `db` và `api` chỉ nằm trong mạng nội bộ Docker. `docker-compose.dev.yml` được phép mở thêm cổng cho phát triển.

**D-02 Cùng origin, không CORS ở production.**
Frontend và API cùng domain qua Caddy. CORS chỉ bật cho môi trường dev, theo danh sách trong `.env`.

**D-03 Giấy phép đóng góp.**
Ảnh 360°: CC BY-SA 4.0. Hình học đường: CC0 1.0 (để có thể đóng góp ngược vào OSM, vì CC BY-SA không tương thích ODbL). Điều khoản `/terms` nêu rõ cả hai. Chủ dự án có thể đổi trước khi ra mắt; sau ra mắt thì không.

**D-04 Không lưu file ảnh gốc.**
Lưu 3 bản: `display.jpg` (rộng tối đa 8192, không phóng to, JPEG ~85), `mobile.jpg` (rộng 4096, nếu ảnh gốc hẹp hơn thì giữ nguyên), `thumb.jpg` (rộng 400). Metadata EXIF gốc lưu vào `exif_data` (chỉ admin thấy). Bản công khai không có EXIF. Lý do: tiết kiệm đĩa, giảm rủi ro quyền riêng tư, đơn giản.

**D-05 Từ chối = xóa file; gỡ hẳn = purge.**
Khi admin từ chối ảnh: xóa cả 3 file ngay, giữ dòng metadata và lý do. Khi xóa mềm ảnh đã duyệt: ảnh ngừng hiển thị công khai, file vẫn còn. `purge` (chỉ admin, theo yêu cầu gỡ ảnh): xóa file, đặt `exif_data = NULL`, ghi `purged_at`, giữ `sha256` trong dòng để chặn upload lại đúng file đó.

**D-06 Chống trùng.**
Unique partial index trên `sha256` chỉ cho ảnh chưa xóa mềm và chưa bị từ chối. Ngoài ra upload bị từ chối nếu `sha256` trùng với ảnh đã `purged_at`.

**D-07 Hướng ảnh và ảnh lân cận.**
`heading` = góc la bàn (0–360°, 0 = bắc) của điểm giữa ảnh equirectangular. Có `heading` thì viewer bật la bàn và truyền vào `northOffset` của Pannellum; agent phải kiểm chứng bằng ảnh test có dấu các hướng (`make_test_panorama.py`) rồi ghi quy ước đã xác nhận vào README. Không có `heading` thì viewer mở ở yaw 0, không la bàn, và `neighbors` chỉ sắp theo khoảng cách. `neighbors` nhận `bearing` tùy chọn (hướng đang nhìn); trả `forward` (gần nhất trong ±60° quanh bearing), `backward` (gần nhất trong ±60° quanh bearing + 180°), và `nearby` (còn lại trong 60 m, sắp theo khoảng cách).

**D-08 Vùng phục vụ.**
`config/areas.geojson` là nguồn sự thật, đồng bộ vào bảng `service_areas` (MultiPolygon, GiST) khi API khởi động (idempotent). "Trong vùng" = nằm trong hợp các vùng, đệm 100 m, tính bằng `ST_DWithin` trên `geography`. Đường: toàn bộ LineString phải nằm trong hợp đã đệm.

**D-09 Dữ liệu OSM nằm trong schema `osm`.**
Gồm bảng osm2pgsql và view `osm.roads` (cột `id`, `name`, `highway`, `geometry` SRID 4326). Dùng flex output, hoặc `--output-pgsql-schema` nếu phiên bản osm2pgsql hỗ trợ. `fetch_osm.sh` chạy lại được nhiều lần. Backup loại trừ schema `osm`; khôi phục thì chạy lại `fetch_osm.sh`.

**D-10 Rate limit.**
In-process, API chạy **1 worker** uvicorn (ghi trong README). Lấy IP thật từ `X-Forwarded-For` do Caddy đặt (uvicorn `--proxy-headers` + `--forwarded-allow-ips` giới hạn theo mạng Docker). Hạn mức: đăng ký/đăng nhập 10 lần/phút/IP; endpoint ghi 20 lần/phút/user. Quota ngày của user mới (10 ảnh/ngày) đếm trong DB, không dùng bộ nhớ.

**D-11 Xác thực.**
Access token JWT 60 phút, giữ trong bộ nhớ trình duyệt. Refresh token 30 ngày: chuỗi ngẫu nhiên, lưu **băm** trong bảng `refresh_tokens`, gửi bằng cookie `HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth` (đặt `Secure=false` khi dev qua http). Mỗi lần refresh xoay token (thu hồi cái cũ). Đăng xuất, ban, hoặc admin đặt lại mật khẩu → thu hồi toàn bộ refresh token của user. Dependency `get_current_user` luôn đọc user từ DB nên ban và đổi role có hiệu lực ngay. Mật khẩu tối thiểu 10 ký tự, argon2.

**D-12 Nền vệ tinh chỉ qua `.env`.**
`SAT_TILE_URL`, `SAT_ATTRIBUTION`, `SAT_MAX_ZOOM`. Nếu `SAT_TILE_URL` trống thì **ẩn** layer vệ tinh (không có mặc định). Agent không chọn nhà cung cấp; chủ dự án đọc điều khoản và điền vào `.env`. Không proxy hay cache tile.

**D-13 Xử lý ảnh đồng bộ.**
Xử lý trong threadpool, giới hạn đồng thời 2 ảnh (semaphore). Giới hạn `PIL.Image.MAX_IMAGE_PIXELS` ở 120 triệu điểm ảnh. Admin upload hàng loạt = client gửi từng ảnh một request (song song tối đa 2), mỗi ảnh có trạng thái và nút thử lại riêng.

**D-14 Marker ảnh.**
`GET /photos?bbox=` trả tối đa 2.000 điểm kèm cờ `truncated`. Client gom cụm bằng leaflet.markercluster; ở zoom thấp hơn 14 chỉ hiển thị gợi ý "phóng to để xem ảnh" nếu `truncated`.

**D-15 Phục vụ file ảnh.**
File ở `/data/media/photos/<uuid>/{display,mobile,thumb}.jpg`, URL `/media/photos/<uuid>/...`, header `Cache-Control: public, max-age=31536000, immutable`. Ảnh chờ duyệt cũng nằm ở đường dẫn này (UUID khó đoán); chấp nhận rủi ro này ở MVP. Ảnh bị từ chối đã bị xóa file (D-05).

**D-16 Tên hiển thị công khai.**
`display_name` của người đóng góp hiển thị công khai trong viewer. Điều khoản và form đăng ký nói rõ điều này.

**D-17 Thông số VPS.**
Tối thiểu 2 vCPU, 4 GB RAM, 80 GB SSD, Ubuntu LTS, Docker. Ưu tiên máy chủ ở Việt Nam hoặc Singapore để giảm độ trễ. Chủ dự án có thể chọn cấu hình lớn hơn.

**D-18 Log và health.**
Log JSON ra stdout, có request id; Docker log rotation (`max-size` 10m, `max-file` 3). `/api/v1/health` kiểm tra cả kết nối DB.
