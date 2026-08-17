# =============================================================================
# Build Script — Create standalone .exe using PyInstaller
# =============================================================================
"""
Run this script to build the application into a standalone .exe file.

Usage:
    python scripts/build_exe.py

Output:
    dist/StockScreener/StockScreener.exe
"""
import os
import sys
import subprocess
import shutil


def find_streamlit_path():
    """Find the Streamlit installation directory for bundling static assets."""
    import streamlit
    return os.path.dirname(streamlit.__file__)


def build():
    """Build the PyInstaller executable."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    streamlit_path = find_streamlit_path()
    streamlit_static = os.path.join(streamlit_path, "static")

    # Data files to include
    datas = [
        (streamlit_static, os.path.join("streamlit", "static")),
        ("config.py", "."),
        ("app.py", "."),
    ]

    # Include data directory if it exists
    if os.path.exists("data"):
        datas.append(("data", "data"))

    # Include ML model if it exists
    if os.path.exists("ml_model/model.pkl"):
        datas.append(("ml_model/model.pkl", "ml_model"))
        datas.append(("ml_model/scaler.pkl", "ml_model"))
        datas.append(("ml_model/features.pkl", "ml_model"))

    # Build the --add-data arguments
    separator = ";" if sys.platform == "win32" else ":"
    data_args = []
    for src, dst in datas:
        data_args.extend(["--add-data", f"{src}{separator}{dst}"])

    # Hidden imports that PyInstaller misses
    hidden_imports = [
        "streamlit",
        "streamlit.web.bootstrap",
        "streamlit.runtime.scriptrunner",
        "streamlit_autorefresh",
        "yfinance",
        "pandas",
        "numpy",
        "sklearn",
        "xgboost",
        "plotly",
        "requests",
        "PIL",
    ]

    hidden_args = []
    for h in hidden_imports:
        hidden_args.extend(["--hidden-import", h])

    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "StockScreener",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--windowed",
        "--icon", "NONE",
        *data_args,
        *hidden_args,
        "--collect-all", "streamlit",
        "--collect-all", "streamlit_autorefresh",
        "--collect-all", "plotly",
        "run_app.py",
    ]

    print("=" * 60)
    print("Building StockScreener.exe")
    print("=" * 60)
    print(f"Command: {' '.join(cmd[:10])}...")
    print()

    result = subprocess.run(cmd, capture_output=False)

    if result.returncode == 0:
        print()
        print("=" * 60)
        print("✅ Build successful!")
        print(f"Executable: dist/StockScreener/StockScreener.exe")
        print("=" * 60)
    else:
        print()
        print("❌ Build failed. Check the output above for errors.")
        sys.exit(1)


if __name__ == "__main__":
    build()
