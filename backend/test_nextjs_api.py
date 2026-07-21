import httpx
try:
    res = httpx.get("http://127.0.0.1:3000/api/analytics/dashboard")
    print("Nextjs API route:", res.status_code)
except Exception as e:
    print("Error:", e)
