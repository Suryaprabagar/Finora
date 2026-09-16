#!/usr/bin/env python3
"""
Finora Backend - Startup script.
Runs database migrations and starts the FastAPI development server.

Google Drive persistence is opt-in. Set GOOGLE_DRIVE_ENABLED=true in .env
after completing the Google Drive setup described in README.md.
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
        print("[OK] Created .env from .env.example.")
        print("     Please review .env and set GOOGLE_DRIVE_ENABLED=true if desired.")

    # Ensure .finora working directory exists
    finora_dir = ".finora"
    for subdir in ("cache", "state", "temp", "locks", "logs"):
        os.makedirs(os.path.join(finora_dir, subdir), exist_ok=True)

    # Determine alembic and uvicorn paths based on environment
    is_windows = os.name == 'nt'
    venv_bin = "Scripts" if is_windows else "bin"
    ext = ".exe" if is_windows else ""

    alembic_path = os.path.join("venv", venv_bin, "alembic" + ext)
    alembic_cmd = alembic_path if os.path.exists(alembic_path) else ("alembic" + ext)

    uvicorn_path = os.path.join("venv", venv_bin, "uvicorn" + ext)
    uvicorn_cmd = uvicorn_path if os.path.exists(uvicorn_path) else ("uvicorn" + ext)

    # Run Alembic migrations
    print("\n[1/4] Running database migrations...")
    result = subprocess.run(
        [alembic_cmd, "upgrade", "head"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"[ERROR] Migration failed:\n{result.stderr}")
        print("Ensure the database is accessible and DATABASE_URL in .env is correct.")
        sys.exit(1)
    print("[OK] Migrations applied successfully.")

    # Create generated_reports directory
    os.makedirs("generated_reports", exist_ok=True)

    # Show Drive status
    drive_enabled = os.environ.get("GOOGLE_DRIVE_ENABLED", "").lower() in ("true", "1", "yes")
    if not drive_enabled:
        # Also check .env file directly
        try:
            with open(".env") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GOOGLE_DRIVE_ENABLED") and "true" in line.lower():
                        drive_enabled = True
                        break
        except OSError:
            pass

    if drive_enabled:
        print("\n[2/4] Google Drive sync: ENABLED")
        print("      Drive authentication will run on first startup.")
        print("      Ensure credentials.json is present in the backend directory.")
    else:
        print("\n[2/4] Google Drive sync: DISABLED (local-only mode)")
        print("      To enable: set GOOGLE_DRIVE_ENABLED=true in .env")

    # Start the server
    print("\n[3/4] Reports directory ready.")
    print("\n[4/4] Starting FastAPI server on http://localhost:8000")
    print("API Docs: http://localhost:8000/api/docs")
    print("Press Ctrl+C to stop.\n")

    if is_windows:
        try:
            subprocess.run([
                uvicorn_cmd, "app.main:app",
                "--reload", "--host", "0.0.0.0", "--port", "8000"
            ])
        except KeyboardInterrupt:
            print("\nStopping server...")
    else:
        os.execvp(uvicorn_cmd, [
            uvicorn_cmd, "app.main:app",
            "--reload", "--host", "0.0.0.0", "--port", "8000"
        ])


if __name__ == "__main__":
    main()
