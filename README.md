# KMap — Bản đồ 360° Tân Châu · Phú Tân · An Giang

Khung MVP: web, API và hạ tầng chạy bằng Docker Compose.

## Yêu cầu
- Docker + Docker Compose
- (Tuỳ chọn) Python 3.12 và Node 20 để phát triển ngoài container

## Chạy lần đầu

`ash
cp .env.example .env
# Đổi JWT_SECRET và POSTGRES_PASSWORD trước khi triển khai công khai.
docker compose up -d --build
`

Mở:
- Web: http://localhost
- API health: http://localhost/api/v1/health
- API docs (development): http://localhost/api/v1/docs

## Lệnh nhanh

`ash
make up
make down
make logs
make test
make lint
make e2e
make migrate
`

## Kiểm thử backend

`ash
cd backend
python -m pytest -q
python -m ruff check app tests
`

## Kiểm thử frontend

`ash
cd frontend
npm install
npm run build
`

## Stack đã chọn
- Python 3.12
- FastAPI
- PostgreSQL 16 + PostGIS 3.4
- Node 20 + Vite + React 18 + TypeScript
- Caddy 2

## Trạng thái
- M0: khung dự án
- M1–M7: xem docs/milestones/
