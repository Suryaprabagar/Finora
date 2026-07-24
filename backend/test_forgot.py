import httpx
try:
    res = httpx.post("http://127.0.0.1:8000/api/v1/auth/forgot-password", json={"email": "test@test.com"})
    print(res.status_code, res.text)
except Exception as e:
    print("Error:", e)
