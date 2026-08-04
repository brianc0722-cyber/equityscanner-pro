"""
Convenience launcher for the EquityScanner Pro Streamlit dashboard.
Run from project root:
    python run_dashboard.py
"""
import subprocess
import sys
from pathlib import Path

def main():
    dashboard_path = Path(__file__).parent / "dashboard" / "app.py"
    if not dashboard_path.exists():
        print("Dashboard not found. Make sure you are in the stock_scanner directory.")
        sys.exit(1)
    
    print("🚀 Launching EquityScanner Pro Dashboard...")
    print(f"   File: {dashboard_path}")
    print("   Press Ctrl+C to stop.\n")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(dashboard_path),
            "--server.port", "8501",
            "--server.headless", "true"
        ], check=True)
    except KeyboardInterrupt:
        print("\nDashboard stopped.")

if __name__ == "__main__":
    main()
