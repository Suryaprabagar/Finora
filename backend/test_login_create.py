import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        try:
            # register
            res1 = await client.post("http://127.0.0.1:8000/api/v1/auth/register", json={
                "full_name": "Test User",
                "email": "test1234@test.com",
                "password": "password123"
            })
            print("Register:", res1.status_code, res1.text)

            # login
            res2 = await client.post("http://127.0.0.1:8000/api/v1/auth/login", json={
                "email": "test1234@test.com",
                "password": "password123"
            })
            print("Login:", res2.status_code, res2.text)
        except Exception as e:
            print("Error:", e)

asyncio.run(main())
