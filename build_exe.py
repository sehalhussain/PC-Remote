"""
Build script for creating PC Remote standalone executable
"""
import subprocess
import sys
import os
import shutil
from PIL import Image

base_dir = os.path.dirname(os.path.abspath(__file__))

def get_icon_path():
    """Find or create icon.ico from icon.png if available"""
    # Check for existing icon.ico
    icon_ico = os.path.join(base_dir, "icon.ico")
    if os.path.exists(icon_ico):
        return icon_ico
    
    # Check for icon.png and convert
    icon_png = os.path.join(base_dir, "icon.png")
    if os.path.exists(icon_png):
        img = Image.open(icon_png)
        # Convert to ICO
        icon_ico = os.path.join(base_dir, "icon.ico")
        img.save(icon_ico, format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256), (512,512)])
        return icon_ico
    
    return None

def build_executable():
    """Build the standalone executable using PyInstaller"""
    
    # Find/create icon
    icon_path = get_icon_path()
    
    # Also get icon.ico path for including in bundle
    icon_ico = os.path.join(base_dir, "icon.ico")
    
    # Use local pyinstaller if available
    pyinstaller_path = os.path.join(base_dir, "Scripts", "pyinstaller.exe")
    
    # Base command
    cmd = [
        pyinstaller_path,
        "--onefile",                    # Single executable
        "--windowed",                   # No console window
        "--add-data", "templates;templates",  # Include templates folder
        "--name", "PC_Remote",          # Output executable name
        "server_gui.py"
    ]
    
    # Add icon to EXE if available
    if icon_path:
        cmd.extend(["--icon", icon_path])
        print(f"Using icon for EXE: {icon_path}")
    
    # Also include icon.ico for tray icon access in bundled app
    if os.path.exists(icon_ico):
        # Add as data file so it can be loaded at runtime
        cmd.extend(["--add-data", f"icon.ico;."])
        print(f"Including icon.ico in bundle for tray icon")
    
    print("Building executable...")
    print(f"Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, check=True)
    
    if result.returncode == 0:
        print("\n" + "=" * 50)
        print("Build successful!")
        print("Executable created at: dist/PC_Remote.exe")
        print("=" * 50)
    else:
        print("Build failed!")
        sys.exit(1)


if __name__ == "__main__":
    build_executable()