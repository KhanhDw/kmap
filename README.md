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

## Stack đã chọn

- Python 3.12
- FastAPI
- PostgreSQL 16 + PostGIS 3.4
- Node 20 + Vite + React 18 + TypeScript
- Caddy 2

## Trạng thái

- M0 và M0_v1: đã xác nhận
- M1: đã xác nhận; đã nhập OSM cho hai vùng Tân Châu và Phú Tân thuộc An Giang
- M2: đang làm; nguồn vệ tinh chưa cấu hình, layer sẽ ẩn khi thiếu cấu hình
- M2–M7: chưa bắt đầu; xem `docs/milestones/`
