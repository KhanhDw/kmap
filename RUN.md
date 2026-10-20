# Hướng dẫn chạy dự án KMap

Tài liệu này hướng dẫn khởi động KMap trên Windows bằng PowerShell. Các lệnh được chạy tại thư mục gốc của dự án.

## 1. Yêu cầu

- Docker Desktop đang chạy, có hỗ trợ Docker Compose.
- Git để lấy mã nguồn dự án.
- (Tùy chọn, chỉ khi phát triển không dùng Docker) Python 3.12 và Node.js 20 trở lên.

Kiểm tra Docker:

```powershell
docker --version
docker compose version
```

## 2. Khởi động toàn bộ dự án bằng Docker (khuyến nghị)

### Bước 1: Tạo file cấu hình môi trường

Tại thư mục gốc dự án:

```powershell
Copy-Item .env.example .env
```

Mở file `.env`. Có thể dùng cấu hình mẫu cho môi trường phát triển trên máy cá nhân. Trước khi triển khai hoặc chia sẻ dịch vụ ra bên ngoài, hãy đổi các giá trị bí mật như `JWT_SECRET`, `POSTGRES_PASSWORD` và mật khẩu quản trị; không đưa file `.env` lên Git.

### Bước 2: Build và chạy các dịch vụ

```powershell
docker compose up -d --build
```

Lần đầu chạy, Docker cần tải các image và build API/web nên có thể mất vài phút. Hệ thống gồm:

- PostgreSQL + PostGIS: cơ sở dữ liệu.
- API: backend FastAPI.
- Web: frontend React/Vite được build và phục vụ qua Nginx.
- Caddy: cổng truy cập chung và proxy request đến web/API.

### Bước 3: Mở ứng dụng và kiểm tra API

- Web: http://localhost
- API health: http://localhost/api/v1/health
- API docs trong môi trường development: http://localhost/api/v1/docs

### Xem trạng thái và log

```powershell
docker compose ps
docker compose logs -f
```

Xem log một dịch vụ cụ thể:

```powershell
docker compose logs -f api
docker compose logs -f web
docker compose logs -f db
```

Nhấn `Ctrl+C` để ngừng theo dõi log; các container vẫn tiếp tục chạy.

### Dừng dự án

Dừng và xóa các container/network nhưng giữ lại dữ liệu database:

```powershell
docker compose down
```

Khởi động lại các container đã tạo:

```powershell
docker compose up -d
```

> Không thêm `-v` vào lệnh `docker compose down` nếu muốn giữ dữ liệu database và media.

## 3. Chạy backend/frontend riêng để phát triển

Chạy riêng từng phần cần một PostgreSQL có bật PostGIS và có thể truy cập từ máy phát triển. Có thể dùng database sẵn có hoặc tự cài đặt; Compose hiện tại không publish cổng database ra máy host.

### Bước 1: Chuẩn bị cấu hình

Tạo `.env` ở thư mục gốc nếu chưa có:

```powershell
Copy-Item .env.example .env
```

Trong `.env`, cấu hình `DATABASE_URL` để trỏ đến database có thể truy cập từ máy này (thường dùng `localhost` thay cho hostname nội bộ `db` của Docker Compose). Đảm bảo thông tin đăng nhập khớp với database. Để gọi API trực tiếp từ Vite, đặt:

```dotenv
FRONTEND_ORIGIN=http://localhost:5173
```

### Bước 2: Cài dependency và chạy backend

Tại thư mục gốc dự án, tạo virtual environment và cài backend:

```powershell
py -3.12 -m venv backend\.venv
.\backend\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .\backend
```

Nếu PowerShell không cho phép kích hoạt virtual environment, mở PowerShell với quyền phù hợp hoặc cho phép script cục bộ trong phiên hiện tại:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\backend\.venv\Scripts\Activate.ps1
```

Chạy API:

```powershell
Set-Location backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API chạy tại http://localhost:8000. Tài liệu API: http://localhost:8000/api/v1/docs. Giữ terminal này mở khi phát triển; nhấn `Ctrl+C` để dừng.

### Bước 3: Cài dependency và chạy frontend

Mở một terminal PowerShell khác tại thư mục gốc:

```powershell
Set-Location frontend
npm ci
$env:VITE_API_URL = "http://localhost:8000/api/v1"
npm run dev
```

Mở URL Vite hiển thị trong terminal, thường là http://localhost:5173. Biến `VITE_API_URL` được đặt trong terminal hiện tại; nếu mở terminal mới thì cần đặt lại trước khi chạy frontend.

## 4. Chạy kiểm thử

### Backend trong Docker

```powershell
docker compose exec api pytest -q
```

### Backend chạy local

Từ thư mục gốc dự án, kích hoạt virtual environment nếu chưa kích hoạt, sau đó:

```powershell
Set-Location backend
pytest -q
ruff check .
```

### Build frontend

```powershell
Set-Location frontend
npm run build
```

## 5. Xử lý lỗi thường gặp

- **Không truy cập được `http://localhost`:** kiểm tra Docker Desktop đã chạy và dùng `docker compose ps` để xác nhận các dịch vụ đã khởi động.
- **Cổng 80 hoặc 443 đang được sử dụng:** dừng ứng dụng khác đang chiếm cổng đó rồi chạy lại `docker compose up -d`.
- **API/database không sẵn sàng:** xem `docker compose logs -f db api`; kiểm tra các biến kết nối database trong `.env`.
- **Frontend local không gọi được API:** xác nhận backend đang chạy ở cổng 8000, `VITE_API_URL` trỏ đúng API và `FRONTEND_ORIGIN` trong `.env` là `http://localhost:5173`. Khởi động lại backend sau khi sửa `.env`.
- **Thay đổi cấu hình build của frontend khi chạy Docker không có hiệu lực:** build lại image web bằng `docker compose up -d --build web`.
