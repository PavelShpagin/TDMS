#!/usr/bin/env python3
"""
TDMS Standalone Server
A standalone FastAPI server for the Table Database Management System.
Runs on port 8000 by default for web-based access.
"""

import uvicorn
from src.web.main import app

def main():
    """
    Start the TDMS FastAPI server on port 8000.
    
    This provides web-based access to the Table Database Management System
    without the desktop PyWebView wrapper. Suitable for:
    - Web deployment
    - Development and testing
    - Multi-user access
    - Integration with other web services
    """
    print("Starting TDMS Web Server...")
    print("Access the application at: http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        app,
        host="0.0.0.0",  # Allow external connections
        port=8000,
        log_level="info",
        reload=False  # Set to True for development
    )

if __name__ == "__main__":
    main()
