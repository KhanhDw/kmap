# Mô hình dữ liệu

Triển khai bằng Alembic. Dữ liệu OSM nằm trong schema `osm` (D-09), chỉ truy cập qua view `osm.roads` (chỉ đọc).

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE user_role   AS ENUM ('user','moderator','admin');
CREATE TYPE item_status AS ENUM ('pending','approved','rejected');
CREATE TYPE road_type   AS ENUM ('primary','secondary','residential','path');

CREATE TABLE users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email text NOT NULL,
  password_hash text NOT NULL,
  display_name text NOT NULL,
  role user_role NOT NULL DEFAULT 'user',
  is_banned boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz
);
-- email lưu dạng chữ thường
CREATE UNIQUE INDEX users_email_uq ON users (lower(email));

CREATE TABLE refresh_tokens (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id),
  token_hash text NOT NULL UNIQUE,
  expires_at timestamptz NOT NULL,
  revoked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX refresh_tokens_user_idx ON refresh_tokens (user_id);

CREATE TABLE service_areas (          -- đồng bộ từ config/areas.geojson
  slug text PRIMARY KEY,
  name text NOT NULL,
  geom geometry(MultiPolygon,4326) NOT NULL
);
CREATE INDEX service_areas_geom_idx ON service_areas USING GIST (geom);

CREATE TABLE photos (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  contributor_id uuid NOT NULL REFERENCES users(id),
  location geometry(Point,4326) NOT NULL,
  heading real CHECK (heading IS NULL OR (heading >= 0 AND heading < 360)),
  captured_at timestamptz,
  -- các key là NULL sau khi bị từ chối (D-05) hoặc purge
  display_key text,
  mobile_key text,
  thumbnail_key text,
  sha256 text NOT NULL,              -- băm của file người dùng tải lên
  orig_width int NOT NULL, orig_height int NOT NULL,
  width int,  height int,            -- kích thước bản display
  file_size bigint NOT NULL,         -- dung lượng file tải lên
  exif_data jsonb,                   -- chỉ admin được đọc
  status item_status NOT NULL DEFAULT 'pending',
  moderator_id uuid REFERENCES users(id),
  moderated_at timestamptz,
  rejection_reason text,
  created_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz,
  purged_at timestamptz
);
CREATE INDEX photos_geom_idx ON photos USING GIST (location);
CREATE INDEX photos_geog_idx ON photos USING GIST ((location::geography));
CREATE INDEX photos_status_idx ON photos (status) WHERE deleted_at IS NULL;
CREATE INDEX photos_contributor_idx ON photos (contributor_id, created_at DESC);
CREATE UNIQUE INDEX photos_sha256_active_uq ON photos (sha256)
  WHERE deleted_at IS NULL AND status <> 'rejected';

CREATE TABLE user_roads (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  contributor_id uuid NOT NULL REFERENCES users(id),
  geometry geometry(LineString,4326) NOT NULL,
  name text,
  road_type road_type NOT NULL DEFAULT 'path',
  status item_status NOT NULL DEFAULT 'pending',
  moderator_id uuid REFERENCES users(id),
  moderated_at timestamptz,
  rejection_reason text,
  created_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz
);
CREATE INDEX user_roads_geom_idx ON user_roads USING GIST (geometry);
CREATE INDEX user_roads_status_idx ON user_roads (status) WHERE deleted_at IS NULL;
CREATE INDEX user_roads_contributor_idx ON user_roads (contributor_id, created_at DESC);

CREATE TABLE contributor_terms (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id),
  terms_version text NOT NULL,
  accepted_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX contributor_terms_user_idx ON contributor_terms (user_id);
```

Ghi chú cho agent:

- Truy vấn bán kính tính bằng mét dùng `location::geography` (có index ở trên) hoặc lọc bbox trên `location` trước rồi mới tính khoảng cách.
- View `osm.roads` có thể cần alias cột hình học (`way AS geometry`) tùy output của osm2pgsql.
- Bảng `service_areas` được ghi lại từ file GeoJSON khi khởi động; không sửa tay.
