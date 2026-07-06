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
import webbrowser
import tempfile
import base64
import io

# Determine base directory for bundled app or source
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)  # For PyInstaller, use exe directory
    bundled_dir = sys._MEIPASS  # Temp directory where PyInstaller extracts files
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    bundled_dir = base_dir

template_dir = os.path.join(bundled_dir, 'templates')
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


# ==================== WINDOWS CLIPBOARD ====================
def copy_to_clipboard(text):
    """Copy text to clipboard using ctypes"""
    if ctypes.windll.kernel32.OpenClipboard(0):
        ctypes.windll.kernel32.EmptyClipboard()
        GMEM_MOVEABLE = 0x0002
        length = (len(text) + 1) * 2  # UTF-16
        h_global = ctypes.windll.kernel32.GlobalAlloc(GMEM_MOVEABLE, length)
        if h_global:
            p_global = ctypes.windll.kernel32.GlobalLock(h_global)
            if p_global:
                ctypes.memmove(p_global, text.encode('utf-16le'), length)
                ctypes.windll.kernel32.GlobalUnlock(h_global)
                ctypes.windll.user32.SetClipboardData(1, h_global)  # CF_UNICODETEXT
        ctypes.windll.kernel32.CloseClipboard()


# ==================== QR CODE DIALOG (BROWSER) ====================
def show_qr_dialog(url):
    """Show QR code in an HTML page matching the remote's dark theme"""
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    # Escape URL for JavaScript
    url_escaped = url.replace("'", "\\'")
    
    # Create HTML matching index.html aesthetic
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PC Remote - Connect</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-font-smoothing: antialiased;
        }}
        body {{
            background: #09090b;
            color: #fafafa;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}
        .card {{
            background: #18181b;
            border: 1.5px solid #27272a;
            border-radius: 18px;
            padding: 32px;
            text-align: center;
            width: 340px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }}
        .header {{
            margin-bottom: 24px;
        }}
        .title {{
            font-size: 18px;
            font-weight: 600;
            letter-spacing: -0.3px;
            margin-bottom: 4px;
        }}
        .subtitle {{
            font-size: 12px;
            color: #52525b;
            margin-bottom: 16px;
        }}
        .status-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #09090b;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 500;
            color: #a1a1aa;
        }}
        .status-dot {{
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #22c55e;
            box-shadow: 0 0 8px #22c55e80;
        }}
        .qr-container {{
            background: #fafafa;
            padding: 16px;
            border-radius: 14px;
            display: inline-block;
            margin-bottom: 20px;
        }}
        .qr-container img {{
            display: block;
            width: 180px;
            height: 180px;
        }}
        .instruction {{
            font-size: 14px;
            color: #a1a1aa;
            margin-bottom: 12px;
            font-weight: 500;
        }}
        .url-box {{
            background: #09090b;
            border: 1.5px solid #27272a;
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 20px;
            font-family: 'Cascadia Code', 'Fira Code', monospace;
            color: #a1a1aa;
            font-size: 12px;
            word-break: break-all;
            user-select: all;
        }}
        .btn-row {{
            display: flex;
            gap: 10px;
        }}
        .btn {{
            flex: 1;
            padding: 12px;
            border: none;
            border-radius: 12px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            font-family: inherit;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: all 0.15s;
        }}
        .btn i {{
            width: 16px;
            height: 16px;
        }}
        .btn-primary {{
            background: #2563eb;
            color: #fff;
        }}
        .btn-primary:active {{
            background: #1d4ed8;
            transform: scale(0.96);
        }}
        .btn-primary.copied {{
            background: #22c55e;
        }}
        .btn-secondary {{
            background: #27272a;
            color: #a1a1aa;
            border: 1.5px solid #27272a;
        }}
        .btn-secondary:active {{
            background: #3f3f46;
            color: #fafafa;
            transform: scale(0.96);
        }}
        .footer {{
            margin-top: 20px;
            font-size: 11px;
            color: #3f3f46;
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <div class="title">PC Remote</div>
            <div class="subtitle">by Sehal Hussain</div>
            <div class="status-pill">
                <div class="status-dot"></div>
                Server Running
            </div>
        </div>
        
        <div class="qr-container">
            <img src="data:image/png;base64,{img_base64}" alt="QR Code">
        </div>
        
        <div class="instruction">Scan to open on your phone</div>
        
        <div class="url-box">{url}</div>
        
        <div class="btn-row">
            <button class="btn btn-primary" id="copyBtn" onclick="copyUrl(this)">
                <i data-lucide="clipboard-copy"></i>
                Copy URL
            </button>
            <button class="btn btn-secondary" onclick="openUrl()">
                <i data-lucide="external-link"></i>
                Open
            </button>
        </div>
        
        <div class="footer">Close this tab. Server is in the system tray.</div>
    </div>
    
    <script>
        lucide.createIcons();

        function copyUrl(btn) {{
            navigator.clipboard.writeText('{url_escaped}').then(function() {{
                btn.innerHTML = '<i data-lucide="check" style="width:16px;height:16px"></i> Copied';
                btn.classList.add('copied');
                lucide.createIcons({{ nodes: [btn] }});
                setTimeout(function() {{
                    btn.innerHTML = '<i data-lucide="clipboard-copy" style="width:16px;height:16px"></i> Copy URL';
                    btn.classList.remove('copied');
                    lucide.createIcons({{ nodes: [btn] }});
                }}, 2000);
            }}).catch(function() {{
                // Fallback for older browsers
                var textArea = document.createElement('textarea');
                textArea.value = '{url_escaped}';
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                btn.innerHTML = '<i data-lucide="check" style="width:16px;height:16px"></i> Copied';
                btn.classList.add('copied');
                lucide.createIcons({{ nodes: [btn] }});
            }});
        }}
        
        function openUrl() {{
            window.open('{url_escaped}', '_blank');
        }}
    </script>
</body>
</html>'''
    
    # Save to temp file and open in browser
    html_path = os.path.join(tempfile.gettempdir(), "pc_remote_qr.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    webbrowser.open('file://' + html_path)


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
        """Show QR code dialog"""
        global current_url
        show_qr_dialog(current_url)
    
    def on_copy_url(self, icon, item):
        """Copy URL to clipboard"""
        global current_url
        copy_to_clipboard(current_url)
        threading.Thread(
            target=lambda: ctypes.windll.user32.MessageBoxW(0, "URL copied to clipboard!", "PC Remote", 0), 
            daemon=True
        ).start()
    
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
    
    # Start server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Show QR code in browser
    show_qr_dialog(current_url)
    
    # Start tray icon
    tray = TrayIcon()
    tray.run()