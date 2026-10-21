# KMap — Bản đồ 360° Tân Châu · Phú Tân · An Giang

Khung MVP: web, API và hạ tầng chạy bằng Docker Compose.

## Yêu cầu

- Docker + Docker Compose
- (Tuỳ chọn) Python 3.12 và Node 20 để phát triển ngoài container

## Chạy lần đầu

```bash
cp .env.example .env
# Đổi JWT_SECRET và POSTGRES_PASSWORD trước khi triển khai công khai.
docker compose up -d db
docker compose build api
docker compose run --rm api alembic upgrade head
docker compose up -d --build
```

Mở:

- Web: http://localhost
- API health: http://localhost/api/v1/health
- API docs (development): http://localhost/api/v1/docs

## Lệnh nhanh

```bash
make up
make down
make logs
make test
make lint
make e2e
make migrate
```

## Kiểm thử backend

Chạy từ thư mục gốc khi stack đã khởi động:

```bash
make test
make lint
```

## Kiểm thử frontend

```bash
cd frontend
npm install
npm run build
```

## Import dữ liệu OSM

Cài `osmium-tool`, `osm2pgsql` và `psql` trong WSL. Sau `make up`, mở cổng DB cho
môi trường phát triển rồi nhập dữ liệu:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db
bash scripts/fetch_osm.sh
```

Script cắt dữ liệu theo `config/areas.geojson`, thay schema `osm` nguyên tử và ghi
báo cáo vào `docs/reports/m1-osm-report.md`.

## Cấu hình nền bản đồ

Nền phố dùng tile URL và ghi công OSM từ `.env`. Nền vệ tinh mặc định bị ẩn;
không có nhà cung cấp mặc định. Trước khi bật hoặc công khai nền vệ tinh, chủ dự
án phải tự chọn nguồn và xác nhận điều khoản sử dụng, rồi cấu hình
`SAT_TILE_URL`, `SAT_ATTRIBUTION` và `SAT_MAX_ZOOM` trong `.env`. Ứng dụng không
proxy hoặc cache tile của bên thứ ba. Bản đồ vẫn hiển thị ghi công
`© OpenStreetMap contributors`; nhãn thương hiệu Leaflet được ẩn.

## Stack đã chọn

- Python 3.12
- FastAPI
- PostgreSQL 16 + PostGIS 3.4
- Node 20 + Vite + React 18 + TypeScript
- Caddy 2

## Trạng thái

- M0 và M0_v1: đã xác nhận
- M1: đã xác nhận; đã nhập OSM cho hai vùng Tân Châu và Phú Tân thuộc An Giang
- M2: đã xác nhận; tile OSM 256px rõ nét, map tự fit vùng phục vụ theo viewport hẹp (trung vị 2,95 giây trên Fast 4G mô phỏng); nền vệ tinh chưa cấu hình và bị ẩn
- M3: đang làm; xem `docs/milestones/M3.md`
- M4–M7: chưa bắt đầu; xem `docs/milestones/`
