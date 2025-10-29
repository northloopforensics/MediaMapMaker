#!/usr/bin/env python3
"""Quick build - uses existing media_map.html"""

import subprocess
import sys
from pathlib import Path

print("="*70)
print("BUILDING EXECUTABLE (Using existing map)")
print("="*70)

# Check if map exists
if not Path('media_map.html').exists():
    print("❌ media_map.html not found!")
    print("   Run: python csv_to_map.py first")
    sys.exit(1)

print("✅ Found media_map.html")

# Check PyInstaller
try:
    import PyInstaller
    print("✅ PyInstaller is installed")
except ImportError:
    print("Installing PyInstaller...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])

# Build
print("\n🔨 Building executable...")
try:
    result = subprocess.run([
        sys.executable, 
        '-m', 
        'PyInstaller',
        '--clean',
        '--noconfirm',
        '--onefile',
        '--console',
        '--name=MapMediaViewer',
        '--add-data=media_map.html;.',
        '--icon=map_icon.ico' if Path('map_icon.ico').exists() else '',
        'map_viewer.py'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("\n" + "="*70)
        print("✅ BUILD COMPLETE!")
        print("="*70)
        exe_path = Path('dist/MapMediaViewer.exe')
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\n📂 Executable: {exe_path.absolute()}")
            print(f"📏 Size: {size_mb:.1f} MB")
            print("\n📋 TO DISTRIBUTE:")
            print("   1. Copy dist/MapMediaViewer.exe")
            print("   2. Copy your entire Media folder")
            print("   3. User puts them together and runs MapMediaViewer.exe")
            print("\n" + "="*70)
        else:
            print("❌ Executable not found in dist folder")
    else:
        print("❌ Build failed!")
        print(result.stderr)
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
