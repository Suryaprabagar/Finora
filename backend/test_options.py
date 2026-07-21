import httpx
try:
    res = httpx.options("http://127.0.0.1:8000/api/v1/auth/login")
    print("OPTIONS:", res.status_code)
except Exception as e:
    print("Error:", e)
