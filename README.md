# KMap — Bản đồ 360° Tân Châu · Phú Tân · An Giang

Khung MVP: web, API và hạ tầng chạy bằng Docker Compose.

## Yêu cầu
- Docker + Docker Compose
- (Tuỳ chọn) Python 3.12 và Node 20 để phát triển ngoài container

## Chạy lần đầu

```bash
cp .env.example .env
# Đổi JWT_SECRET và POSTGRES_PASSWORD trước khi triển khai công khai.
docker compose up -d --build
```

Mở:
- Web: http://localhost
- API health: http://localhost/api/v1/health
- API docs (development): http://localhost/api/v1/docs

## Kiểm thử backend

```bash
docker compose exec api pytest -q
# Hoặc chạy local từ thư mục backend sau khi cài dependencies:
cd backend
pip install -e .
pytest -q
ruff check .
```

## Trạng thái
- M0: khung dự án
- M1–M7: xem `milestones/`
