#!/usr/bin/env python3
"""
Finora Backend - Startup script.
Runs database migrations and starts the FastAPI development server.
"""
import subprocess
import sys
import os

def main():
    # Ensure we're in the backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)

    print("=" * 60)
    print("  Finora Backend Startup")
    print("=" * 60)

    # Check for .env file
    if not os.path.exists(".env"):
        print("[WARNING] .env file not found. Copying from .env.example...")
        import shutil
        shutil.copy(".env.example", ".env")
        print("[OK] Created .env from .env.example. Please update DATABASE_URL.")

    # Run Alembic migrations
    print("\n[1/3] Running database migrations...")
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"[ERROR] Migration failed: {result.stderr}")
        print("Make sure PostgreSQL is running and DATABASE_URL in .env is correct.")
        sys.exit(1)
    print("[OK] Migrations applied successfully.")

    # Create generated_reports directory
    os.makedirs("generated_reports", exist_ok=True)
    print("[OK] Reports directory ready.")

    # Start the server
    print("\n[3/3] Starting FastAPI server on http://localhost:8000")
    print("API Docs: http://localhost:8000/api/docs")
    print("Press Ctrl+C to stop.\n")
    os.execvp("uvicorn", ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"])

if __name__ == "__main__":
    main()
