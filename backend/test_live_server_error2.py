import subprocess
import time
import httpx
import sys

print('Starting uvicorn...')
proc = subprocess.Popen(
    [r'venv\Scripts\python.exe', '-m', 'uvicorn', 'app.main:app', '--port', '8005'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

time.sleep(4) # Wait for it to start

print('Sending request...')
try:
    res = httpx.post("http://127.0.0.1:8005/api/v1/auth/login", json={"email": "surya1332005@gmail.com", "password": "password"})
    print("Response:", res.status_code)
except Exception as e:
    print("Request failed:", e)

print('Killing uvicorn...')
proc.terminate()
stdout, stderr = proc.communicate(timeout=5)

print('--- STDOUT ---')
print(stdout)
print('--- STDERR ---')
print(stderr)
