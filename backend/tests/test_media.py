from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


def test_media_files_are_served_with_immutable_cache_headers() -> None:
    path = Path(settings.MEDIA_DIR) / f"test-{uuid4()}.jpg"
    contents = b"synthetic media response"
    path.write_bytes(contents)
    client = TestClient(app)
    try:
        response = client.get(f"{settings.MEDIA_URL_PREFIX}/{path.name}")
        assert response.status_code == 200
        assert response.content == contents
        assert (
            response.headers["cache-control"]
            == "public, max-age=31536000, immutable"
        )
    finally:
        client.close()
        path.unlink(missing_ok=True)
