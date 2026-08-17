# =============================================================================
# PyInstaller Entry Point — Launches Streamlit programmatically
# =============================================================================
"""
This script is the entry point for the PyInstaller .exe build.
It starts the Streamlit server and opens the browser automatically.

Usage:
    python run_app.py          → Starts the Streamlit app
    StockScreener.exe          → Same (after PyInstaller build)
"""
import sys
import os

# Ensure the bundled app can find its modules
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    app_dir = sys._MEIPASS
    os.chdir(os.path.dirname(sys.executable))
else:
    app_dir = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, app_dir)

from streamlit.web import bootstrap

if __name__ == "__main__":
    flag_options = {
        "server.headless": True,
        "server.port": 8501,
        "browser.gatherUsageStats": False,
        "theme.base": "dark",
        "theme.primaryColor": "#3b82f6",
        "theme.backgroundColor": "#0a0e1a",
        "theme.secondaryBackgroundColor": "#1e293b",
        "theme.textColor": "#e2e8f0",
    }

    app_path = os.path.join(app_dir, "app.py")
    bootstrap.run(app_path, False, [], flag_options)
