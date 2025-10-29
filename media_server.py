"""
Simple HTTP Server for Media Files
Run this alongside your Streamlit app to serve media files
"""

import http.server
import socketserver
import os
from pathlib import Path

# Configuration
WORKSPACE_FOLDER = r"C:\Users\mactwo\Desktop\MapMediaWork"
PORT = 8001

class MediaHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WORKSPACE_FOLDER, **kwargs)
    
    def end_headers(self):
        # Add CORS headers to allow Streamlit to access the media
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

if __name__ == "__main__":
    print(f"Starting Media Server...")
    print(f"Serving files from: {WORKSPACE_FOLDER}")
    print(f"Server running at: http://localhost:{PORT}")
    print(f"\n📍 IMPORTANT:")
    print(f"   Open your map at: http://localhost:{PORT}/media_map_new.html")
    print(f"   (NOT as a file:// URL)")
    print(f"\nPress Ctrl+C to stop the server\n")
    
    with socketserver.TCPServer(("", PORT), MediaHTTPRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()
