import httpx
try:
    res = httpx.get("http://127.0.0.1:8000/api/v1/categories")
    print(res.status_code, res.text)
except Exception as e:
    print("Error:", e)
