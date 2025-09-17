from __future__ import annotations

import threading
import time
import webbrowser
from pathlib import Path

import webview
import uvicorn

from src.web.main import app


def start_server():
    """Start the FastAPI server in a separate thread"""
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")


def main() -> None:
    """Main function to start the desktop application"""
    # Start the FastAPI server in a background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Wait a moment for the server to start
    time.sleep(2)
    
    # Create the webview window pointing to the local server
    window = webview.create_window(
        "TDMS Desktop Application",
        "http://127.0.0.1:8000",
        width=1200,
        height=800,
        min_size=(800, 600),
        resizable=True
    )
    
    # Start the webview
    webview.start(debug=False)


def build_desktop() -> None:
    """Build the desktop application (for future packaging)"""
    print("Building desktop application...")
    print("Desktop app is ready to run with: python -m src.desktop.app")
    print("For creating an executable, you can use PyInstaller:")
    print("pip install pyinstaller")
    print("pyinstaller --onefile --windowed --name TDMS-Desktop src/desktop/app.py")


if __name__ == "__main__":
    main()


