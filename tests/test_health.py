import os
import pytest
from httpx import AsyncClient, ASGITransport

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/test.db"
os.environ["ADMIN_TOKEN"] = "test-token"
os.environ["CRON_SECRET"] = "test-cron"
os.environ["LLM_PROVIDER"] = "mock"

from backend.app.main import app


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
