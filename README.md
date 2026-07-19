# Finora — Where your financial future begins.

A comprehensive Personal Financial Management platform built with **Next.js 15 + FastAPI**.

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 15, React 19, TypeScript, Tailwind CSS |
| **UI Components** | shadcn/ui (Radix), Recharts, TanStack Table |
| **State** | Zustand, TanStack Query |
| **Backend** | FastAPI (Python 3.11), SQLAlchemy 2.0 (async) |
| **Database** | PostgreSQL 15+ |
| **Auth** | JWT (python-jose), bcrypt |
| **Reports** | WeasyPrint (PDF), openpyxl (Excel), csv |

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
    │   └── schemas/   # Pydantic schemas
    ├── alembic/       # Database migrations
    ├── scripts/       # Seed data
    └── templates/     # PDF report templates
```

## Quick Start

### Prerequisites
- PostgreSQL 15+ running locally
- Python 3.11+
- Node.js 20+

### 1. Database Setup

```sql
-- Run in psql
CREATE DATABASE finora;
CREATE USER finora_user WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE finora TO finora_user;
```

### 2. Backend Setup

```powershell
cd backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env and set DATABASE_URL to your PostgreSQL connection string

# Run migrations
alembic upgrade head

# Seed demo data
python scripts/seed_data.py

# Start server
uvicorn app.main:app --reload --port 8000
```

Backend API will be available at: **http://localhost:8000**
API Docs: **http://localhost:8000/api/docs**

### 3. Frontend Setup

```powershell
cd frontend

# Install dependencies (already done)
npm install

# Start development server
npm run dev
```

Frontend will be available at: **http://localhost:3000**

## Demo Account

After running the seed script:

| Field | Value |
|-------|-------|
| **Email** | demo@finora.app |
| **Password** | demo1234 |

The demo account comes pre-loaded with 6 months of realistic Indian financial data including transactions, investments, loans, goals, and bills.

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
| **Settings** | Profile, currency, categories, data reset |

## Default Currency

Indian Rupee (₹ / INR). Configurable per user in Settings → Currency.

## Reset Demo Data

In the app: **Settings → Data → Reset Demo Data**

Or via API:
```bash
POST /api/v1/settings/reset-demo
Authorization: Bearer <demo_user_token>
```
