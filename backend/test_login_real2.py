import asyncio
import httpx
import time

async def main():
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post("http://localhost:8000/api/v1/auth/login", json={"email": "surya1332005@gmail.com", "password": "password"})
            print(res.status_code)
            print(res.text)
        except Exception as e:
            print("Error:", e)

asyncio.run(main())
