"""
Desktop TDMS application that uses the exact same web interface as the web version.
This ensures 100% consistency between web and desktop versions.
"""

import threading
import time
import atexit
from pathlib import Path

import webview
import webbrowser
import uvicorn

# Load environment variables before importing the web app
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path.cwd() / ".env", override=False)
    print("Loaded .env file for desktop app")
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")

# Import the web application
from src.web.main import app

# Start OAuth callback server
try:
    from src.desktop.oauth_server import get_oauth_server
    oauth_server = get_oauth_server()
    print("OAuth callback server started on http://localhost:8080")
except Exception as e:
    print(f"Warning: Could not start OAuth callback server: {e}")
    oauth_server = None


class DesktopServer:
    def __init__(self):
        self.server = None
        self.server_thread = None
        self.port = self._find_free_port()  # Find available port automatically
        
        # Ensure desktop databases directory exists
        self.storage_dir = Path("desktop_databases")
        self.storage_dir.mkdir(exist_ok=True)
        
        # Auto-save on exit
        atexit.register(self._cleanup)

    def _find_free_port(self):
        """Find a free port for desktop app, avoid 8000 (reserved for web)"""
        import socket
        # Start from 8001 to avoid conflict with web app on 8000
        for port in range(8001, 8100):  # Try ports 8001-8099
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    return port
            except OSError:
                continue
        return 8001  # Fallback

    def _cleanup(self):
        """Cleanup on exit"""
        if self.server:
            print("Shutting down desktop server...")

    def start_server(self):
        """Start the FastAPI server in a separate thread"""
        try:
            uvicorn.run(app, host="127.0.0.1", port=self.port, log_level="warning")
        except Exception as e:
            print(f"Server error: {e}")

    def run(self):
        """Run the desktop application"""
        print(f"Starting TDMS Desktop on port {self.port}")
        
        # Start the FastAPI server in a background thread
        self.server_thread = threading.Thread(target=self.start_server, daemon=True)
        self.server_thread.start()
        
        # Wait a moment for the server to start
        time.sleep(3)
        
        # Expose minimal JS bridge to open URLs in system browser
        class JsApi:
            def open_url(self, url: str) -> None:  # pywebview exposes methods to JS
                try:
                    webbrowser.open(url)
                except Exception:
                    pass

        # Create the webview window pointing to the local server
        window = webview.create_window(
            "TDMS Desktop Application",
            f"http://127.0.0.1:{self.port}?desktop=true",
            width=1400,
            height=900,
            min_size=(1000, 700),
            resizable=True,
            js_api=JsApi(),
        )
        
        # Start the webview
        webview.start(debug=False, gui='edgechromium')


def main() -> None:
    """Main function to start the desktop application"""
    desktop_app = DesktopServer()
    desktop_app.run()


if __name__ == "__main__":
    main()
