"""Create the application schema."""

from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def _execute_script(script: str) -> None:
    for statement in script.split(";"):
        if statement.strip():
            op.execute(statement)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE TYPE user_role AS ENUM ('user', 'moderator', 'admin')")
    op.execute("CREATE TYPE item_status AS ENUM ('pending', 'approved', 'rejected')")
    op.execute("CREATE TYPE road_type AS ENUM ('primary', 'secondary', 'residential', 'path')")

    _execute_script(
        """
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

        CREATE TABLE service_areas (
            slug text PRIMARY KEY,
            name text NOT NULL,
            geom geometry(MultiPolygon, 4326) NOT NULL
        );
        CREATE INDEX service_areas_geom_idx ON service_areas USING GIST (geom);

        CREATE TABLE photos (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            contributor_id uuid NOT NULL REFERENCES users(id),
            location geometry(Point, 4326) NOT NULL,
            heading real CHECK (heading IS NULL OR (heading >= 0 AND heading < 360)),
            captured_at timestamptz,
            display_key text,
            mobile_key text,
            thumbnail_key text,
            sha256 text NOT NULL,
            orig_width int NOT NULL,
            orig_height int NOT NULL,
            width int,
            height int,
            file_size bigint NOT NULL,
            exif_data jsonb,
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
            geometry geometry(LineString, 4326) NOT NULL,
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
        """
    )


def downgrade() -> None:
    _execute_script(
        """
        DROP TABLE contributor_terms;
        DROP TABLE user_roads;
        DROP TABLE photos;
        DROP TABLE service_areas;
        DROP TABLE refresh_tokens;
        DROP TABLE users;
        DROP TYPE road_type;
        DROP TYPE item_status;
        DROP TYPE user_role;
        """
    )
