import subprocess
import time
import httpx

print('Starting uvicorn...')
proc = subprocess.Popen(
    ['python', '-m', 'uvicorn', 'app.main:app', '--port', '8001'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

time.sleep(3) # Wait for it to start

print('Sending request...')
try:
    res = httpx.post("http://127.0.0.1:8001/api/v1/auth/login", json={"email": "test@test.com", "password": "password"})
    print("Response:", res.status_code)
except Exception as e:
    print("Request failed:", e)

print('Killing uvicorn...')
proc.terminate()
stdout, stderr = proc.communicate()

print('--- STDOUT ---')
print(stdout)
print('--- STDERR ---')
print(stderr)
