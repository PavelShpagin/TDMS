"""Simple OAuth callback server for desktop app."""

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback redirects."""
    
    # Class variable to store received codes
    received_codes = {}
    
    def do_GET(self):
        """Handle GET requests to /oauth/callback."""
        parsed = urlparse(self.path)
        
        if parsed.path == '/oauth/callback':
            # Parse query parameters
            params = parse_qs(parsed.query)
            state = params.get('state', [None])[0]
            code = params.get('code', [None])[0]
            error = params.get('error', [None])[0]
            
            if state:
                # Store the code/error by state
                OAuthCallbackHandler.received_codes[state] = {
                    'code': code,
                    'error': error
                }
            
            # Send response to browser
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Authorization Complete</title>
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }
                    .container {
                        background: white;
                        padding: 3rem;
                        border-radius: 10px;
                        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                        text-align: center;
                        max-width: 400px;
                    }
                    h1 {
                        color: #2d3748;
                        margin-bottom: 1rem;
                    }
                    p {
                        color: #718096;
                        line-height: 1.6;
                    }
                    .success {
                        color: #48bb78;
                        font-size: 3rem;
                        margin-bottom: 1rem;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="success">✓</div>
                    <h1>Authorization Complete!</h1>
                    <p>You can close this window and return to the application.</p>
                </div>
                <script>
                    // Auto-close after 3 seconds
                    setTimeout(() => window.close(), 3000);
                </script>
            </body>
            </html>
            '''
            
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress HTTP request logging."""
        pass


class OAuthCallbackServer:
    """OAuth callback server that runs on port 8080."""
    
    def __init__(self, port=8080):
        self.port = port
        self.server = None
        self.thread = None
    
    def start(self):
        """Start the OAuth callback server in a background thread."""
        if self.thread and self.thread.is_alive():
            return  # Already running
        
        self.server = HTTPServer(('localhost', self.port), OAuthCallbackHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        print(f"OAuth callback server started on http://localhost:{self.port}")
    
    def stop(self):
        """Stop the OAuth callback server."""
        if self.server:
            self.server.shutdown()
            self.server = None
    
    def get_code(self, state, timeout=60):
        """
        Wait for and retrieve an OAuth code for the given state.
        
        Args:
            state: The OAuth state parameter
            timeout: Maximum seconds to wait
            
        Returns:
            dict with 'code' and 'error' keys, or None if timeout
        """
        import time
        start = time.time()
        
        while time.time() - start < timeout:
            if state in OAuthCallbackHandler.received_codes:
                result = OAuthCallbackHandler.received_codes.pop(state)
                return result
            time.sleep(0.1)
        
        return None


# Global instance
_oauth_server = None

def get_oauth_server():
    """Get or create the global OAuth callback server."""
    global _oauth_server
    if _oauth_server is None:
        _oauth_server = OAuthCallbackServer()
        _oauth_server.start()
    return _oauth_server


