import os
from flask import Flask, render_template, request, jsonify
import pyautogui
import signal

base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

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

if __name__ == '__main__':
    print("=" * 50)
    print("  PC Remote Server Running")
    print("  Access at: http://<YOUR-PC-IP>:49200")
    print("  Press Ctrl+C to stop")
    print("=" * 50)
    app.run(host='0.0.0.0', port=49200, threaded=True)