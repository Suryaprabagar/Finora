import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
import sys

async def main():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        try:
            response = await ac.post("/api/v1/auth/login", json={"email": "surya1332005@gmail.com", "password": "password"})
            print("Status:", response.status_code)
            print("Response:", response.text)
        except Exception as e:
            import traceback
            traceback.print_exc()

asyncio.run(main())
