# Finora — Where your financial future begins.

A comprehensive Personal Financial Management platform built with **Next.js 15 + FastAPI + SQLite**.

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 15, React 19, TypeScript, Tailwind CSS |
| **UI Components** | shadcn/ui (Radix), Recharts, TanStack Table |
| **State** | Zustand, TanStack Query |
| **Backend** | FastAPI (Python 3.11+), SQLAlchemy 2.0 (async) |
| **Database** | SQLite (local, via aiosqlite) |
| **Auth** | JWT (python-jose), bcrypt |
| **Reports** | WeasyPrint (PDF), openpyxl (Excel), csv |
| **Cloud Backup** | Google Drive (opt-in) |

## Project Structure

```
finora/
├── frontend/          # Next.js 15 App Router
│   └── src/
│       ├── app/       # Pages (dashboard, auth)
│       ├── components/# Layout, shared, charts
│       ├── lib/api/   # Axios API client
│       ├── store/     # Zustand stores
│       └── types/     # TypeScript types
└── backend/           # FastAPI
    ├── app/
    │   ├── api/v1/    # Route handlers
    │   ├── core/      # Config, DB, security
    │   ├── models/    # SQLAlchemy models
    │   ├── schemas/   # Pydantic schemas
    │   ├── services/  # backup_service, market_service
    │   └── storage/   # Google Drive persistence layer
    ├── alembic/       # Database migrations
    ├── scripts/       # Seed data, CI tests
    ├── templates/     # PDF report templates
    └── tests/         # Test suite
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- No external database required — SQLite is built in.

### 1. Backend Setup

```powershell
cd backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Review .env — defaults work for local use

# Run migrations (creates finora.db automatically)
alembic upgrade head

# Seed demo data (optional)
python scripts/seed_data.py

# Start server
python start.py
```

Backend API: **http://localhost:8000**  
API Docs: **http://localhost:8000/api/docs**

### 2. Frontend Setup

```powershell
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend: **http://localhost:3000**

---

## Google Drive Setup (Optional)

Google Drive provides persistent cloud backup and recovery. It is **disabled by default**.

### Step 1 — Create a Google Cloud project

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g. `finora-backup`).
3. Enable the **Google Drive API** for your project.
4. Go to **APIs & Services → Credentials**.
5. Create an **OAuth 2.0 Client ID** (Application type: **Desktop app**).
6. Download the credentials and save as `backend/credentials.json`.

> **IMPORTANT**: Never commit `credentials.json` or `.finora/token.json` to Git.
> Both are already listed in `.gitignore`.

### Step 2 — Enable Drive in `.env`

```env
GOOGLE_DRIVE_ENABLED=true
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_TOKEN_FILE=.finora/token.json
MAX_VERSIONS=5
AUTOSAVE_INTERVAL=300
```

### Step 3 — First run

Start Finora normally. On the first run it will open a browser window asking you to
grant permission to access Google Drive. After you approve, the token is saved to
`.finora/token.json` and reused automatically.

```
Connecting to Google Drive...
Finding latest state...
No previous Drive state found — starting fresh.
Autosave enabled (every 300s).
Finora ready.
```

### Step 4 — Verify Drive structure

After running, you should see this folder structure in your Google Drive:

```
Finora/
├── current/
│   ├── state.json
│   └── manifest.json
├── versions/
│   ├── v001/
│   ├── v002/
│   └── ...
└── logs/
```

---

## Google Drive Persistence Behaviour

| Event | Action |
|-------|--------|
| **Backend start** | Downloads latest valid state → restores into SQLite |
| **Every 5 minutes** | Exports SQLite → uploads to `current/` (no new version) |
| **Backend shutdown** | Exports → creates new numbered version → uploads → verifies → cleans old |
| **Manual sync** | `POST /api/v1/sync/trigger` |

### Version retention

Up to **5 permanent versions** are kept (configurable via `MAX_VERSIONS`).

```
versions/
    v101/  ← deleted when v106 confirmed
    v102/
    v103/
    v104/
    v105/
```

After v106 is uploaded and verified:

```
versions/
    v102/
    v103/
    v104/
    v105/
    v106/
```

Old versions are **only deleted after** the new version is confirmed valid.

### Recovery from corruption

If the latest Drive state is corrupt, Finora automatically falls back to the
newest valid previous version:

```
current/ = corrupt  → try v005
v005     = corrupt  → try v004
v004     = valid    → restored ✓
```

If Google Drive is unavailable:
- **Local SQLite exists** → continue in offline mode (data is intact)
- **No local SQLite** → startup fails with a clear error

---

## Sync Status API

```
GET  /api/v1/sync/status   # Current sync state
POST /api/v1/sync/trigger  # Manual save to Drive
GET  /api/v1/sync/versions # List stored versions
```

Example status response:

```json
{
  "google_drive": "connected",
  "last_sync": "2026-09-04T10:32:00Z",
  "local_state": "current",
  "cloud_state": "current",
  "versions": 5,
  "max_versions": 5,
  "drive_enabled": true
}
```

---

## Demo Account

After running the seed script:

| Field | Value |
|-------|-------|
| **Email** | demo@finora.app |
| **Password** | demo1234 |

The demo account comes pre-loaded with 6 months of realistic Indian financial data.

---

## Features

| Feature | Description |
|---------|-------------|
| **Dashboard** | Net worth, cash flow charts, KPIs |
| **Transactions** | Full CRUD, CSV import/export, bulk operations |
| **Income** | Tracking with category breakdown |
| **Expenses** | Category analysis, trend charts |
| **Budget** | Monthly budgets with progress tracking |
| **Bank Accounts** | Multi-account management, transfers |
| **Credit Cards** | Utilization tracking, payment recording |
| **Investments** | Portfolio tracker (stocks, MF, gold, FD, PPF, NPS) |
| **Loans** | EMI tracking, amortization schedules |
| **Assets** | Property, vehicle, jewellery tracking |
| **Insurance** | Policy management, claims tracking |
| **Bills** | Recurring bill reminders |
| **Goals** | Financial goal tracking with contributions |
| **Reports** | PDF/CSV/Excel export for all modules |
| **Settings** | Profile, currency, categories, data backup/restore |
| **Sync** | Google Drive backup (opt-in) |

## Default Currency

Indian Rupee (₹ / INR). Configurable per user in Settings → Currency.

## Running Tests

```powershell
cd backend
.\venv\Scripts\activate

# Storage persistence tests only
python -m pytest tests/test_storage/ -v

# Full test suite
python -m pytest tests/ -v
```

## Reset Demo Data

In the app: **Settings → Data → Reset Demo Data**

Or via API:
```bash
POST /api/v1/settings/reset-demo
Authorization: Bearer <demo_user_token>
```
