import asyncio
from httpx import AsyncClient
from app.main import app
import sys

async def main():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        try:
            response = await ac.post("/api/v1/auth/login", json={"email": "surya1332005@gmail.com", "password": "password"})
            print("Status:", response.status_code)
            print("Response:", response.text)
        except Exception as e:
            import traceback
            traceback.print_exc()

asyncio.run(main())
