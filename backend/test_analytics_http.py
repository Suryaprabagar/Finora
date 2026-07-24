import httpx
try:
    res = httpx.get("http://127.0.0.1:8000/api/v1/analytics/dashboard")
    print(res.status_code)
    print(res.text[:100])
except Exception as e:
    print("Error:", e)
