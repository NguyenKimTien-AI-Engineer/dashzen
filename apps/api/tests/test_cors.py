import pytest
from api.main import create_app
from core.config import get_settings
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def cors_client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("API_CORS_ORIGINS", "http://localhost:3000")
    get_settings.cache_clear()
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_preflight_allows_vercel_studio_origin(cors_client: AsyncClient) -> None:
    origin = "https://dashzen-mu.vercel.app"
    response = await cors_client.options(
        "/v1/auth/register",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert response.headers.get("access-control-allow-credentials") == "true"
