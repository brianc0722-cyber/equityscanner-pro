#!/usr/bin/env python3
"""
EquityScanner Pro — Unified Launcher
Starts both the FastAPI backend and Streamlit dashboard together.

This solves the "fully running backend + dashboard" gap.

Usage:
    python run_all.py
    python run_all.py --api-only
    python run_all.py --dashboard-only
"""
import subprocess
import sys
import time
import argparse
import os
from pathlib import Path

import requests  # used for health check wait

ROOT = Path(__file__).parent.resolve()

def run_api():
    """Start FastAPI with correct environment."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    
    cmd = [
        sys.executable, "-m", "uvicorn",
        "api.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ]
    print("🚀 Starting FastAPI backend → http://localhost:8000")
    return subprocess.Popen(cmd, cwd=ROOT, env=env)

def run_dashboard():
    """Start Streamlit dashboard."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        "dashboard/app.py",
        "--server.port", "8501",
        "--server.headless", "true",
        "--server.address", "0.0.0.0",
        "--browser.gatherUsageStats", "false"
    ]
    print("📊 Starting Streamlit dashboard → http://localhost:8501")
    return subprocess.Popen(cmd, cwd=ROOT, env=env)

import requests

def wait_for_api(timeout: int = 25):
    """Wait until FastAPI /health is responsive."""
    print("⏳ Waiting for FastAPI to become ready...", end=" ", flush=True)
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get("http://localhost:8000/health", timeout=1.5)
            if r.status_code == 200:
                print("✅ Ready!")
                return True
        except Exception:
            pass
        time.sleep(0.8)
        print(".", end="", flush=True)
    print("\n⚠️  API did not become ready in time (will continue in demo mode).")
    return False

def main():
    parser = argparse.ArgumentParser(description="Launch EquityScanner Pro")
    parser.add_argument("--api-only", action="store_true", help="Only start FastAPI")
    parser.add_argument("--dashboard-only", action="store_true", help="Only start Streamlit")
    args = parser.parse_args()

    processes = []

    try:
        if not args.dashboard_only:
            processes.append(run_api())
            wait_for_api(timeout=30)

        if not args.api_only:
            processes.append(run_dashboard())

        print("\n" + "="*65)
        print("✅ EquityScanner Pro is fully running!")
        print("="*65)
        print("   • FastAPI Backend:  http://localhost:8000")
        print("   • API Docs:         http://localhost:8000/docs")
        print("   • Dashboard:        http://localhost:8501")
        print("\n   → Click the big 🚀 RUN QUICK START button in the sidebar")
        print("   → Live API status indicator now shows in the dashboard")
        print("   → Pre-market direction strongly drives recommendations")
        print("\nPress Ctrl+C to stop everything.\n")

        # Keep the script alive
        while True:
            time.sleep(2)

    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        for p in reversed(processes):
            try:
                p.terminate()
                p.wait(timeout=6)
            except Exception:
                pass
        print("All services stopped cleanly.")

if __name__ == "__main__":
    main()
