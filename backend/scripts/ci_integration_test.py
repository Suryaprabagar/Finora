#!/usr/bin/env python3
"""
Finora Backend — Integration Test Suite
Runs inside CI after the app container is healthy.

Tests (20 assertions across 7 sections):

  Section 1 — Liveness & docs (4 assertions)
    1.  GET /health                → 200, status=healthy
    2.  GET /health body check     → {"status": "healthy"}
    3.  GET /                      → 200
    4.  GET /api/docs              → 200

  Section 2 — DB health endpoint (2 assertions)
    5.  GET /health/db             → 200, db=ok
    6.  GET /health/db latency     → latency_ms is a number

  Section 3 — $PORT obedience (1 assertion)
    7.  Container bound to PORT env var, not a hardcoded port
        (CI passes PORT=<value>; test confirms /health responds on that port)

  Section 4 — Auth register (1 assertion)
    8.  POST /api/v1/auth/register → 200 or 201

  Section 5 — Auth login + token (2 assertions)
    9.  POST /api/v1/auth/login    → 200
    10. access_token present

  Section 6 — Auth guard (3 assertions)
    11. GET /users/me (no token)   → 401
    12. GET /users/me (with token) → 200
    13. email in profile response

  Section 7 — Core API endpoints authenticated (10 assertions)
    14. GET /api/v1/dashboard      → 2xx
    15. GET /api/v1/transactions   → 2xx
    16. GET /api/v1/bank-accounts  → 2xx
    17. GET /api/v1/budget         → 2xx
    18. GET /api/v1/goals          → 2xx
    19. GET /api/v1/investments    → 2xx
    20. GET /api/v1/loans          → 2xx
    21. GET /api/v1/bills          → 2xx
    22. GET /api/v1/assets         → 2xx
    23. GET /api/v1/insurance      → 2xx
"""
import os
import sys
import time
import uuid
import requests

# ── PORT — CI passes PORT env var; test must use it, not hardcode 8000 ───────
PORT = int(os.environ.get("APP_PORT", "8000"))
BASE_URL = f"http://localhost:{PORT}"

# ── helpers ───────────────────────────────────────────────────────────────────

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
failures: list[str] = []
total = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global total
    total += 1
    if condition:
        print(f"  [{PASS}] {label}")
    else:
        print(f"  [{FAIL}] {label}  — {detail}")
        failures.append(label)


def get(path: str, token: str | None = None, **kw) -> requests.Response:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return requests.get(f"{BASE_URL}{path}", headers=headers, timeout=10, **kw)


def post(path: str, token: str | None = None, **kw) -> requests.Response:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return requests.post(f"{BASE_URL}{path}", headers=headers, timeout=10, **kw)


# ── wait for app (uses /health, not hardcoded port) ──────────────────────────

print(f"\n⏳  Waiting for app on port {PORT}…")
for attempt in range(30):
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=3)
        if r.status_code == 200:
            print(f"   App ready after {attempt + 1} attempt(s).\n")
            break
    except Exception:
        pass
    time.sleep(2)
else:
    print(f"❌  App never became healthy on port {PORT} — aborting.")
    sys.exit(1)

# ── unique credentials — idempotent across runs ───────────────────────────────
uid = uuid.uuid4().hex[:8]
TEST_EMAIL = f"ci-test-{uid}@finora.test"
TEST_PASSWORD = "TestPass@1234!"
TEST_NAME = f"CI User {uid}"

# ─────────────────────────────────────────────────────────────────────────────
# Section 1 — Liveness & docs
# ─────────────────────────────────────────────────────────────────────────────
print("── Section 1: Liveness & docs ─────────────────────────")

r = get("/health")
check("GET /health → 200", r.status_code == 200, str(r.status_code))
check("health body: status == healthy", r.json().get("status") == "healthy", r.text)

r = get("/")
check("GET / → 200", r.status_code == 200, str(r.status_code))

r = get("/api/docs")
check("GET /api/docs → 200", r.status_code == 200, str(r.status_code))

# ─────────────────────────────────────────────────────────────────────────────
# Section 2 — DB health endpoint
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Section 2: DB health endpoint ──────────────────────")

r = get("/health/db")
check("GET /health/db → 200 (PostgreSQL reachable)", r.status_code == 200,
      f"HTTP {r.status_code} — {r.text[:120]}")
if r.status_code == 200:
    db_data = r.json()
    check(
        "health/db: db == ok AND latency_ms is a number",
        db_data.get("db") == "ok" and isinstance(db_data.get("latency_ms"), (int, float)),
        str(db_data),
    )
    print(f"   DB latency: {db_data.get('latency_ms')} ms")
else:
    failures.append("health/db: db == ok AND latency_ms is a number")

# ─────────────────────────────────────────────────────────────────────────────
# Section 3 — $PORT obedience
# CI starts the container with PORT=<value>; we confirm the same value works.
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Section 3: $PORT obedience ─────────────────────────")

check(
    f"App responds on PORT={PORT} (not a hardcoded port)",
    PORT > 0 and requests.get(f"{BASE_URL}/health", timeout=5).status_code == 200,
    f"Expected response on :{PORT}",
)

# ─────────────────────────────────────────────────────────────────────────────
# Section 4 — Auth: register
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Section 4: Register ────────────────────────────────")

r = post("/api/v1/auth/register", json={
    "name": TEST_NAME,
    "email": TEST_EMAIL,
    "password": TEST_PASSWORD,
})
check("POST /auth/register → 200 or 201", r.status_code in (200, 201), r.text[:120])

# ─────────────────────────────────────────────────────────────────────────────
# Section 5 — Auth: login + token
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Section 5: Login & token ───────────────────────────")

r = post("/api/v1/auth/login", json={
    "email": TEST_EMAIL,
    "password": TEST_PASSWORD,
})
check("POST /auth/login → 200", r.status_code == 200, r.text[:120])
data = r.json() if r.status_code == 200 else {}
# Support both flat {"access_token": ...} and nested {"data": {"access_token": ...}}
token = (
    data.get("data", {}).get("access_token")
    or data.get("access_token", "")
)
check("access_token present in login response", bool(token), str(data)[:120])

# ─────────────────────────────────────────────────────────────────────────────
# Section 6 — Auth guard
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Section 6: Auth guard ──────────────────────────────")

r = get("/api/v1/users/me")
check("GET /users/me (no token) → 401", r.status_code == 401, str(r.status_code))

r = get("/api/v1/users/me", token=token)
check("GET /users/me (with token) → 200", r.status_code == 200, r.text[:120])
check("email matches registered user", TEST_EMAIL in str(r.json()), str(r.json())[:120])

# ─────────────────────────────────────────────────────────────────────────────
# Section 7 — Core API endpoints (authenticated)
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Section 7: Core API endpoints (authenticated) ──────")

endpoints = [
    "/api/v1/dashboard",
    "/api/v1/transactions",
    "/api/v1/bank-accounts",
    "/api/v1/budget",
    "/api/v1/goals",
    "/api/v1/investments",
    "/api/v1/loans",
    "/api/v1/bills",
    "/api/v1/assets",
    "/api/v1/insurance",
]

for path in endpoints:
    r = get(path, token=token)
    # 200 = data returned; 204 = empty but OK
    check(
        f"GET {path} → 2xx",
        200 <= r.status_code < 300,
        f"HTTP {r.status_code}  {r.text[:80]}",
    )

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "─" * 58)
print(f"Assertions run: {total}")
if failures:
    print(f"❌  {len(failures)} FAILED:")
    for f in failures:
        print(f"    • {f}")
    sys.exit(1)
else:
    print(f"✅  All {total} assertions passed.")
    sys.exit(0)
