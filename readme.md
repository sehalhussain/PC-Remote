# PC Remote

A web-based remote control application that allows you to control your PC using a mobile device or any web browser. Control mouse movement, clicks, keyboard input, media playback, and volume - all from your phone's browser.

## Features

### 🖱️ Mouse Control
- **Mouse Movement**: Drag on the virtual trackpad to move the cursor on your PC
- **Left Click**: Single tap on the trackpad or click the "Left Click" button
- **Right Click**: Long press (500ms) on the trackpad or click the "Right Click" button
- **Double Click**: Click the "Double Click" button
- **Scroll**: Two-finger swipe on the trackpad or use mouse wheel

### ⌨️ Keyboard Control
- **Single Key Press**: Send individual keyboard keys to your PC
- **Text Input**: Type text on your mobile device and send it to your PC
- **Keyboard Shortcuts**: Send complex hotkey combinations
- **Special Keys**: Support for Enter, Backspace, Space, Escape, Tab, Delete, Home, End, and function keys (F5, F11)
- **Common Shortcuts**: Ctrl+C, Ctrl+V, Ctrl+Z, Ctrl+A, Alt+F4, Win+D

### 🎵 Media Controls
- Previous Track
- Stop
- Play/Pause
- Next Track

### 🔊 Volume Controls
- Visual volume slider with real-time feedback
- Mute toggle button
- Volume up/down controls

### 🚀 Quick Actions
- **Back**: Alt+Left (browser back)
- **Fullscreen**: F11
- **Alt+Tab**: Switch between open applications
- **Desktop**: Win+D (show desktop)

### 🔧 Server Management
- Shutdown server remotely from the web interface
- Tray icon with quick access to features
- QR code for easy mobile connection

## Installation

### Prerequisites
- Python 3.x
- pip (Python package manager)

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install flask pyautogui qrcode pillow pystray
```

### Required Packages
- **Flask**: Web framework for running the server
- **pyautogui**: Cross-platform GUI automation library for mouse and keyboard control
- **qrcode**: Generate QR codes for easy mobile connection
- **Pillow**: Image processing library for QR code and tray icon
- **pystray**: System tray icon integration

## Usage

### Option 1: GUI Mode (Recommended)

Run the GUI version for a full desktop experience with QR code and system tray:

```bash
python server_gui.py
```

This will:
1. Save a QR code image (`connection_qr.png`) with your connection URL
2. Show a Windows notification with the server URL
3. Start the server in the background
4. Minimize to system tray for easy access
5. Right-click tray icon to show QR code again or copy URL

### Option 2: Simple Mode

For a minimal console-only experience:

```bash
python server.py
```

The server will start on `http://0.0.0.0:49200`

### Connecting from Mobile Device

1. Make sure your mobile device and PC are on the same network
2. On GUI mode, scan the QR code that appears when starting
3. Or open a web browser on your mobile device and go to the displayed URL
4. Navigate to `http://<YOUR-PC-IP>:49200`

### Connecting from Another Computer

Open a web browser and navigate to `http://<TARGET-PC-IP>:49200`

## Building Standalone Executable

### What Gets Bundled
When built, PyInstaller includes ALL Python dependencies into the single executable:
- Flask server
- pyautogui for mouse/keyboard control
- qrcode, Pillow, pystray for GUI features
- All templates and assets

**Users don't need to install anything - just run the .exe!**

### Adding Custom Icon

To use a custom icon for the executable:

1. Save your 512x512 PNG image as `icon.png` in the project folder
2. Run the build script - it will automatically convert PNG to ICO format
3. Or manually create `icon.ico` and place it in the project folder

### Build Instructions

To create a standalone `.exe` file:

```bash
python build_exe.py
```

Or using PyInstaller directly:

```bash
pyinstaller --onefile --windowed --add-data "templates;templates" --name "PC_Remote" server_gui.py
```

The executable will be created in the `dist/` folder.

### Running the Executable

1. Double-click `PC_Remote.exe` to run (no installation needed!)
2. Scan the QR code with your mobile device or enter the URL manually
3. Control your PC from anywhere on your network
4. Right-click the tray icon to show QR code again or quit

## API Endpoints

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/move` | POST | Move mouse cursor relatively | `{x: number, y: number}` |
| `/click` | POST | Perform mouse click | `{button: 'left'\|'right'\|'double'}` |
| `/scroll` | POST | Scroll the mouse wheel | `{y: number}` (negative = scroll down, positive = scroll up) |
| `/key` | POST | Press a single key | `{key: string}` |
| `/key_repeat` | POST | Press a key multiple times | `{key: string, count: number}` |
| `/type` | POST | Type text on PC | `{text: string}` |
| `/hotkey` | POST | Execute hotkey combination | `{keys: [string, ...]}` |
| `/shutdown` | POST | Stop the server | None |

## Project Structure

```
PC Remote/
├── server.py              # Simple Flask backend server
├── server_gui.py          # GUI version with QR code and tray icon
├── build_exe.py           # Build script for creating .exe
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html         # Web interface frontend
├── Lib/                   # Python libraries
└── Scripts/               # Python scripts
```

## Configuration

The server runs on port **49200** by default. You can modify this in the server files:

```python
app.run(host='0.0.0.0', port=49200, threaded=True)
```

## Security Note

This server runs on your local network without authentication. Be cautious when using it in public networks as it allows full control over your PC.

## Tested On

- Windows 11
- Python 3.x

## Developer

**Sehal Hussain**

---

⭐ If you find this project useful, consider giving it a star!