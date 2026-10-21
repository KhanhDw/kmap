#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
START_SECONDS=$SECONDS

if [[ ! -f .env ]]; then
    echo "Missing .env. Copy .env.example to .env and configure the database first." >&2
    exit 1
fi

while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    case "$line" in
        POSTGRES_USER=*) POSTGRES_USER="${line#*=}" ;;
        POSTGRES_PASSWORD=*) POSTGRES_PASSWORD="${line#*=}" ;;
        POSTGRES_DB=*) POSTGRES_DB="${line#*=}" ;;
        OSM_DB_HOST=*) OSM_DB_HOST="${line#*=}" ;;
        OSM_DB_PORT=*) OSM_DB_PORT="${line#*=}" ;;
        OSM_DATA_DIR=*) OSM_DATA_DIR="${line#*=}" ;;
        OSM_CACHE_MB=*) OSM_CACHE_MB="${line#*=}" ;;
        OVERPASS_URL=*) OVERPASS_URL="${line#*=}" ;;
    esac
done < .env

: "${POSTGRES_USER:?POSTGRES_USER must be set in .env}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set in .env}"
: "${POSTGRES_DB:?POSTGRES_DB must be set in .env}"
OSM_DB_HOST="${OSM_DB_HOST:-127.0.0.1}"
OSM_DB_PORT="${OSM_DB_PORT:-5432}"
OSM_DATA_DIR="${OSM_DATA_DIR:-./data/osm}"
OSM_CACHE_MB="${OSM_CACHE_MB:-1200}"
OVERPASS_URL="${OVERPASS_URL:-https://overpass-api.de/api/interpreter}"
if [[ "$OSM_DATA_DIR" != /* ]]; then
    OSM_DATA_DIR="$ROOT_DIR/$OSM_DATA_DIR"
fi

for command in curl md5sum osmium osm2pgsql psql; do
    if ! command -v "$command" >/dev/null 2>&1; then
        echo "Required command not found: $command" >&2
        exit 1
    fi
done
if command -v docker.exe >/dev/null 2>&1; then
    DOCKER_CLI=docker.exe
elif command -v docker >/dev/null 2>&1; then
    DOCKER_CLI=docker
else
    echo "Docker CLI is required to generate the report inside the API container." >&2
    exit 1
fi

OSM2PGSQL_HELP="$(osm2pgsql --help 2>&1 || true)"
if [[ "$OSM2PGSQL_HELP" != *"--output-pgsql-schema"* ]]; then
    echo "osm2pgsql must support --output-pgsql-schema (use a current 1.x/2.x release)." >&2
    exit 1
fi

export PGPASSWORD="$POSTGRES_PASSWORD"
export PGHOST="$OSM_DB_HOST"
export PGPORT="$OSM_DB_PORT"
export PGUSER="$POSTGRES_USER"
export PGDATABASE="$POSTGRES_DB"

if ! psql -v ON_ERROR_STOP=1 -Atc 'SELECT 1' >/dev/null; then
    echo "Cannot connect to PostgreSQL at $OSM_DB_HOST:$OSM_DB_PORT/$POSTGRES_DB." >&2
    echo "Start the development DB port with: docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db" >&2
    exit 1
fi

mkdir -p "$OSM_DATA_DIR"
PBF_PATH="$OSM_DATA_DIR/vietnam-latest.osm.pbf"
PBF_TEMP="$PBF_PATH.partial"
EXTRACT_PATH="$OSM_DATA_DIR/an-giang.osm.pbf"
EXTRACT_TEMP="$OSM_DATA_DIR/an-giang.partial.osm.pbf"
OVERPASS_PATH="$OSM_DATA_DIR/an-giang-overpass.osm"
SOURCE_REASON="Geofabrik vietnam-latest.osm.pbf"
OVERPASS_QUERY='[out:xml][timeout:240];(way["highway"](area:3614672096);way["highway"](area:3614676456););(._;>;);out body;'
STAGING_STARTED=false
cleanup() {
    rm -f "$PBF_TEMP" "$EXTRACT_TEMP" "$OSM_DATA_DIR/an-giang-overpass.osm.partial"
    if [[ "$STAGING_STARTED" == true ]]; then
        psql -v ON_ERROR_STOP=1 -c 'DROP SCHEMA IF EXISTS osm_stage CASCADE' >/dev/null \
            || echo "Warning: unable to remove incomplete osm_stage schema." >&2
    fi
}
trap cleanup EXIT

PBF_VALID=false
if [[ -f "$PBF_PATH" ]]; then
    CHECKSUM="$(curl -fsSL https://download.geofabrik.de/asia/vietnam-latest.osm.pbf.md5 | awk '{print $1}')"
    if [[ -n "$CHECKSUM" ]] && printf '%s  %s\n' "$CHECKSUM" "$PBF_PATH" | md5sum -c - >/dev/null; then
        PBF_VALID=true
    fi
fi

if [[ "$PBF_VALID" != true ]]; then
    if curl -fL --retry 2 --retry-delay 2 \
        https://download.geofabrik.de/asia/vietnam-latest.osm.pbf \
        -o "$PBF_TEMP" \
        && CHECKSUM="$(curl -fsSL https://download.geofabrik.de/asia/vietnam-latest.osm.pbf.md5 | awk '{print $1}')" \
        && [[ -n "$CHECKSUM" ]] \
        && printf '%s  %s\n' "$CHECKSUM" "$PBF_TEMP" | md5sum -c - >/dev/null; then
        mv "$PBF_TEMP" "$PBF_PATH"
        PBF_VALID=true
    else
        DOWNLOAD_REASON="Geofabrik download or MD5 verification failed at $(date -u +%FT%TZ); using the bounded Overpass road query."
        echo "$DOWNLOAD_REASON" >&2
        curl -fL --retry 1 --max-time 300 \
            --data-urlencode "data=$OVERPASS_QUERY" \
            "$OVERPASS_URL" \
            -o "$OVERPASS_PATH.partial"
        mv "$OVERPASS_PATH.partial" "$OVERPASS_PATH"
        SOURCE_REASON="$DOWNLOAD_REASON"
    fi
fi

if [[ "$PBF_VALID" == true ]]; then
    python3 scripts/make_extract_polygon.py \
        config/areas.geojson \
        "$OSM_DATA_DIR/service-areas.geojson"
    osmium extract --overwrite --strategy=complete_ways \
        -p "$OSM_DATA_DIR/service-areas.geojson" \
        -o "$EXTRACT_TEMP" \
        "$PBF_PATH"
    mv "$EXTRACT_TEMP" "$EXTRACT_PATH"
    INPUT_PATH="$EXTRACT_PATH"
else
    INPUT_PATH="$OVERPASS_PATH"
fi

STAGING_STARTED=true
psql -v ON_ERROR_STOP=1 -c 'DROP SCHEMA IF EXISTS osm_stage CASCADE; CREATE SCHEMA osm_stage;'
osm2pgsql \
    --create \
    --slim \
    --output=pgsql \
    --output-pgsql-schema=osm_stage \
    --database="$PGDATABASE" \
    --username="$PGUSER" \
    --host="$PGHOST" \
    --port="$PGPORT" \
    --cache="$OSM_CACHE_MB" \
    --prefix=planet_osm \
    "$INPUT_PATH"

psql -v ON_ERROR_STOP=1 <<'SQL'
CREATE MATERIALIZED VIEW osm_stage.roads AS
SELECT
    osm_id::bigint AS id,
    name,
    highway,
    ST_Transform(way, 4326)::geometry(Geometry, 4326) AS geometry
FROM osm_stage.planet_osm_line
WHERE highway IS NOT NULL;

CREATE UNIQUE INDEX roads_id_idx ON osm_stage.roads (id);
CREATE INDEX roads_geometry_idx ON osm_stage.roads USING GIST (geometry);
ANALYZE osm_stage.roads;
SQL

ROAD_COUNTS="$(psql -v ON_ERROR_STOP=1 -AtF '|' -c \
    "SELECT a.slug, count(r.id) FROM service_areas AS a LEFT JOIN osm_stage.roads AS r ON ST_Intersects(r.geometry, a.geom) GROUP BY a.slug ORDER BY a.slug")"
if [[ "$(printf '%s\n' "$ROAD_COUNTS" | wc -l | tr -d ' ')" -ne 2 ]]; then
    echo "Expected exactly two synchronized service areas before importing OSM." >&2
    exit 1
fi
while IFS='|' read -r slug count; do
    echo "OSM road count for $slug: $count"
    if (( count < 50 )); then
        echo "Fewer than 50 roads found for $slug; leaving the active osm schema unchanged." >&2
        exit 3
    fi
done <<< "$ROAD_COUNTS"

psql -v ON_ERROR_STOP=1 <<'SQL'
BEGIN;
DROP SCHEMA IF EXISTS osm_old CASCADE;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'osm') THEN
        ALTER SCHEMA osm RENAME TO osm_old;
    END IF;
END
$$;
ALTER SCHEMA osm_stage RENAME TO osm;
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'kmap_osm_reader') THEN
        CREATE ROLE kmap_osm_reader NOLOGIN;
    END IF;
END
$$;
GRANT USAGE ON SCHEMA osm TO kmap_osm_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA osm TO kmap_osm_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA osm GRANT SELECT ON TABLES TO kmap_osm_reader;
COMMIT;

DROP SCHEMA IF EXISTS osm_old CASCADE;
SQL
STAGING_STARTED=false

export OSM_SOURCE_REASON="$SOURCE_REASON"
mkdir -p docs/reports
"$DOCKER_CLI" compose exec -T -e OSM_SOURCE_REASON="$SOURCE_REASON" api \
    python /scripts/report_osm.py > docs/reports/m1-osm-report.md
printf -- '- Thời gian chạy `fetch_osm.sh`: %s giây\n' \
    "$((SECONDS - START_SECONDS))" >> docs/reports/m1-osm-report.md
echo "Wrote docs/reports/m1-osm-report.md"
