import httpx
try:
    res = httpx.get("http://localhost:8000/api/docs")
    print(res.status_code)
except Exception as e:
    print("Error:", e)
