import os
import sys
import socket
import threading
import ctypes
from ctypes import wintypes
from flask import Flask, render_template, request, jsonify
import pyautogui
import signal
import qrcode
from PIL import Image
import pystray
from pystray import MenuItem as item

# Determine base directory for bundled app or source
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)  # For PyInstaller, use exe directory
    bundled_dir = sys._MEIPASS  # Temp directory where PyInstaller extracts files
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    bundled_dir = base_dir

template_dir = os.path.join(base_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

# Global variables
server_running = False
current_url = ""

# ==================== FLASK ROUTES ====================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/move', methods=['POST'])
def move():
    data = request.json
    pyautogui.moveRel(data.get('x', 0), data.get('y', 0))
    return jsonify({"status": "moved"}), 200

@app.route('/click', methods=['POST'])
def click():
    data = request.json
    button = data.get('button', 'left')
    if button == 'left':
        pyautogui.click()
    elif button == 'right':
        pyautogui.rightClick()
    elif button == 'double':
        pyautogui.doubleClick()
    return jsonify({"status": "clicked"}), 200

@app.route('/scroll', methods=['POST'])
def scroll():
    data = request.json
    pyautogui.scroll(data.get('y', 0))
    return jsonify({"status": "scrolled"}), 200

@app.route('/key', methods=['POST'])
def key():
    data = request.json
    key_name = data.get('key', '')
    if key_name:
        pyautogui.press(key_name)
    return jsonify({"status": "key_pressed"}), 200

@app.route('/key_repeat', methods=['POST'])
def key_repeat():
    data = request.json
    key_name = data.get('key', '')
    count = data.get('count', 1)
    if key_name:
        for _ in range(abs(count)):
            pyautogui.press(key_name)
    return jsonify({"status": "key_repeated"}), 200

@app.route('/type', methods=['POST'])
def type_text():
    data = request.json
    text = data.get('text', '')
    if text:
        pyautogui.write(text, interval=0.02)
    return jsonify({"status": "typed"}), 200

@app.route('/hotkey', methods=['POST'])
def hotkey():
    data = request.json
    keys = data.get('keys', [])
    if keys:
        pyautogui.hotkey(*keys)
    return jsonify({"status": "hotkey_pressed"}), 200

@app.route('/shutdown', methods=['POST'])
def shutdown():
    os.kill(os.getpid(), signal.SIGINT)
    return jsonify({"message": "Server shutting down..."})


# ==================== WINDOWS NATIVE NOTIFICATION ====================
def show_notification_async(title, message):
    """Show Windows notification in a separate thread to avoid blocking"""
    def notify():
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x0)  # MB_OK = 0
    threading.Thread(target=notify, daemon=True).start()

def show_notification(title, message):
    """Show Windows notification using ctypes - non-blocking"""
    # Use MB_OK (0) instead of 0x40000 which might be MB_ICONWARNING
    ctypes.windll.user32.MessageBoxW(0, message, title, 0x0)

def copy_to_clipboard(text):
    """Copy text to clipboard using ctypes"""
    if ctypes.windll.kernel32.OpenClipboard(0):
        ctypes.windll.kernel32.EmptyClipboard()
        # GlobalAlloc
        GMEM_MOVEABLE = 0x0002
        length = (len(text) + 1) * 2  # UTF-16
        h_global = ctypes.windll.kernel32.GlobalAlloc(GMEM_MOVEABLE, length)
        if h_global:
            # GlobalLock
            p_global = ctypes.windll.kernel32.GlobalLock(h_global)
            if p_global:
                ctypes.memmove(p_global, text.encode('utf-16le'), length)
                ctypes.windll.kernel32.GlobalUnlock(h_global)
                ctypes.windll.user32.SetClipboardData(1, h_global)  # CF_UNICODETEXT
        ctypes.windll.kernel32.CloseClipboard()


# ==================== NETWORK UTILITIES ====================
def get_local_ip():
    """Get the local IP address of the machine"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_connection_url():
    """Get the full connection URL"""
    return f"http://{get_local_ip()}:49200"


def save_qr_code(url):
    """Save QR code to a file and open it"""
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    qr_path = os.path.join(base_dir, "connection_qr.png")
    img.save(qr_path)
    # Open the image file
    os.startfile(qr_path)
    return qr_path


# ==================== TRAY ICON ====================
class TrayIcon:
    def __init__(self):
        self.icon = None
        self.running = True
        
    def create_image(self):
        """Create a tray icon image"""
        # Try to load icon.ico first (check both bundled and base directories)
        for check_dir in [bundled_dir, base_dir]:
            icon_path = os.path.join(check_dir, "icon.ico")
            if os.path.exists(icon_path):
                try:
                    img = Image.open(icon_path)
                    img = img.resize((64, 64), Image.LANCZOS)
                    print(f"Loaded tray icon from: {icon_path}")
                    return img
                except Exception as e:
                    print(f"Could not load icon.ico: {e}")
        
        # Fallback to icon.png
        for check_dir in [bundled_dir, base_dir]:
            icon_path = os.path.join(check_dir, "icon.png")
            if os.path.exists(icon_path):
                try:
                    img = Image.open(icon_path)
                    img = img.resize((64, 64), Image.LANCZOS)
                    print(f"Loaded tray icon from: {icon_path}")
                    return img
                except Exception as e:
                    print(f"Could not load icon.png: {e}")
        
        # Default: simple mouse/cursor icon - blue background
        img = Image.new('RGB', (64, 64), color=(37, 99, 235))
        
        # Draw a simple mouse shape in white
        for y in range(20, 44):
            width_at_y = min(20 + (y - 20) + 4, 50)
            for x in range(20, width_at_y):
                img.putpixel((x, y), (255, 255, 255))
        
        # Draw scroll wheel (two vertical lines)
        for y in range(22, 38):
            img.putpixel((44, y), (255, 255, 255))
            img.putpixel((48, y), (255, 255, 255))
        
        # Draw left button area
        for y in range(22, 30):
            for x in range(44, 47):
                img.putpixel((x, y), (255, 255, 255))
        # Draw right button area  
        for y in range(30, 38):
            for x in range(48, 51):
                img.putpixel((x, y), (255, 255, 255))
        
        return img
    
    def on_show_qr(self, icon, item):
        """Show QR code image"""
        global current_url
        save_qr_code(current_url)
        # Use async notification to avoid blocking
        threading.Thread(target=lambda: ctypes.windll.user32.MessageBoxW(0, f"QR Code saved!\nURL: {current_url}", "PC Remote", 0), daemon=True).start()
    
    def on_copy_url(self, icon, item):
        """Copy URL to clipboard"""
        global current_url
        copy_to_clipboard(current_url)
        threading.Thread(target=lambda: ctypes.windll.user32.MessageBoxW(0, "URL copied to clipboard!", "PC Remote", 0), daemon=True).start()
    
    def on_quit(self, icon, item):
        """Quit the application"""
        self.running = False
        icon.stop()
        # Schedule exit on main thread to avoid issues
        threading.Thread(target=lambda: os.kill(os.getpid(), signal.SIGINT), daemon=True).start()
    
    def run(self):
        global current_url
        menu = pystray.Menu(
            item('Show QR Code', self.on_show_qr),
            item('Copy URL', self.on_copy_url),
            item('---', None),
            item('Quit', self.on_quit)
        )
        
        self.icon = pystray.Icon(
            "PC Remote",
            self.create_image(),
            f"PC Remote - {current_url}",
            menu
        )
        self.icon.run()


# ==================== SERVER THREAD ====================
def run_server():
    """Run Flask server in a thread"""
    global server_running
    server_running = True
    print("=" * 50)
    print("  PC Remote Server Running")
    print(f"  Access at: {get_connection_url()}")
    print("  Press Ctrl+C to stop")
    print("=" * 50)
    app.run(host='0.0.0.0', port=49200, threaded=True, use_reloader=False)
    server_running = False


# ==================== MAIN ====================
if __name__ == '__main__':
    # Get connection URL
    current_url = get_connection_url()
    
    # Save and show QR code on startup
    qr_path = save_qr_code(current_url)
    
    # Show notification
    show_notification("PC Remote by Sehal Hussain", f"Server starting...\n{current_url}\nQR code saved to:\n{qr_path}")
    
    # Start server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Start tray icon
    tray = TrayIcon()
    tray.run()