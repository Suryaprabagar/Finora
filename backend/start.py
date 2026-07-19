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

    # Determine alembic and uvicorn paths based on environment
    is_windows = os.name == 'nt'
    venv_bin = "Scripts" if is_windows else "bin"
    ext = ".exe" if is_windows else ""
    
    alembic_path = os.path.join("venv", venv_bin, "alembic" + ext)
    alembic_cmd = alembic_path if os.path.exists(alembic_path) else ("alembic" + ext)
        
    uvicorn_path = os.path.join("venv", venv_bin, "uvicorn" + ext)
    uvicorn_cmd = uvicorn_path if os.path.exists(uvicorn_path) else ("uvicorn" + ext)

    # Run Alembic migrations
    print("\n[1/3] Running database migrations...")
    result = subprocess.run(
        [alembic_cmd, "upgrade", "head"],
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
    if is_windows:
        # On Windows, execvp isn't fully supported, use subprocess
        try:
            subprocess.run([uvicorn_cmd, "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"])
        except KeyboardInterrupt:
            print("Stopping server...")
    else:
        os.execvp(uvicorn_cmd, [uvicorn_cmd, "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"])

if __name__ == "__main__":
    main()
