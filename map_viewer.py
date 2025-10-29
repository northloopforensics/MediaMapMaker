#!/usr/bin/env python3
"""
Standalone Map Viewer Server
Serves the pre-generated map HTML and media files
"""

import http.server
import socketserver
import os
import sys
import webbrowser
import time
from pathlib import Path

# Handle PyInstaller bundled resources
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

PORT = 8001

class MapServerHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve from current directory (where executable is run from)
        super().__init__(*args, directory=os.getcwd(), **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()
    
    def log_message(self, format, *args):
        # Suppress log messages for cleaner output
        pass

def main():
    print("="*70)
    print("MAP MEDIA VIEWER")
    print("="*70)
    
    # Check if Media folder exists
    media_path = Path("Media")
    if not media_path.exists():
        print("\n❌ ERROR: Media folder not found!")
        print("   Please make sure the 'Media' folder is in the same directory as this executable.")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    # Check if map HTML exists, if not extract from bundled resource
    map_file = "media_map.html"
    if not Path(map_file).exists():
        try:
            bundled_map = resource_path("media_map.html")
            if Path(bundled_map).exists():
                import shutil
                shutil.copy(bundled_map, map_file)
                print(f"✅ Extracted map file: {map_file}")
            else:
                print(f"\n❌ ERROR: Map file not found!")
                print(f"   Expected: {map_file}")
                input("\nPress Enter to exit...")
                sys.exit(1)
        except Exception as e:
            print(f"\n❌ ERROR: Could not extract map file: {e}")
            input("\nPress Enter to exit...")
            sys.exit(1)
    
    print(f"\n✅ Media folder found with files")
    print(f"✅ Map file found: {map_file}")
    
    # Start the server
    print(f"\n🌐 Starting server on port {PORT}...")
    
    try:
        with socketserver.TCPServer(("", PORT), MapServerHandler) as httpd:
            print(f"✅ Server running at http://localhost:{PORT}")
            print(f"\n🗺️  Opening map in browser...")
            
            # Give server a moment to start
            time.sleep(0.5)
            
            # Open browser
            webbrowser.open(f"http://localhost:{PORT}/{map_file}")
            
            print(f"\n{'='*70}")
            print("SERVER RUNNING - Keep this window open")
            print("="*70)
            print("\nThe map is now open in your browser.")
            print("You can interact with the map, view media, and use all filters.")
            print("\nPress Ctrl+C to stop the server and exit.")
            print("="*70)
            
            # Keep server running
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("Server stopped. Goodbye!")
        print("="*70)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\n❌ ERROR: Port {PORT} is already in use!")
            print("   Please close any other programs using this port and try again.")
        else:
            print(f"\n❌ ERROR: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
