import os
import subprocess
import time
from flask import Flask, request, render_template, Response, jsonify

# Initialize the Flask application
app = Flask(__name__)

@app.route('/')
def index():
    """Renders the initial setup form."""
    return render_template('index.html', activating=False)

@app.route('/setup', methods=['GET', 'POST'])
def do_setup():
    """Handles both real setup (POST) and Test Mode (GET)."""
    is_test = request.args.get('test') == 'true'
    
    if is_test:
        ts_key = "test-key-123"
        device_name = "test-gateway"
    else:
        # Standard POST logic from the form
        ts_key = request.form.get('ts_key', '').strip()
        device_name = request.form.get('device_name', 'molly-pi').strip()
        
        # Guard against empty submissions
        if not ts_key:
            return "Missing Auth Key", 400

        # Save configuration for Docker to use
        try:
            with open(".env", "w") as f:
                f.write(f"TS_AUTHKEY={ts_key}\nDEVICE_NAME={device_name}\n")
        except Exception as e:
            return f"Failed to save .env file: {e}", 500

    # 'activating=True' switches index.html to the console view
    return render_template('index.html', activating=True, key=ts_key, name=device_name, is_test=is_test)

@app.route('/stream_logs')
def stream_logs():
    """Streams terminal output or mock logs to the browser console."""
    ts_key = request.args.get('key')
    name = request.args.get('name')
    is_test = (ts_key == "test-key-123")
    
    def generate():
        if is_test:
            # Simulate a fake installation for UI testing
            yield "data: [TEST] Initializing mock installation...\\n\\n"
            time.sleep(1)
            yield "data: [TEST] Cleaning up old network sessions...\\n\\n"
            time.sleep(1)
            yield f"data: [TEST] Successfully authenticated as {name}\\n\\n"
            time.sleep(1)
            yield "data: [TEST] Pulling container images...\\n\\n"
            time.sleep(2)
            yield "data: [TEST] Molly-Pi services are UP and RUNNING.\\n\\n"
        else:
            # REAL LOGIC: Reset Tailscale and run the setup commands
            yield "data: [SYSTEM] Disconnecting old Tailscale session...\\n\\n"
            subprocess.run(["sudo", "tailscale", "logout"])
            
            # Use 'sudo -n' to run non-interactively
            cmd = f"sudo tailscale up --authkey={ts_key} --hostname={name} && sudo docker compose up -d"
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            
            for line in iter(process.stdout.readline, ""):
                clean_line = line.strip().replace('"', "'")
                if clean_line:
                    yield f"data: {clean_line}\\n\\n"
            
            process.stdout.close()

        yield "data: [DONE]\\n\\n"

    return Response(generate(), mimetype='text/event-stream')

@app.route('/status')
def get_status():
    """Checks if the device is successfully on the Tailscale network."""
    # -4 ensures we get the IPv4 Tailscale address (100.x.x.x)
    ip = subprocess.getoutput("tailscale ip -4").strip()
    is_online = bool(ip and ip.startswith("100."))
    return jsonify({"online": is_online, "ip": ip})

@app.route('/system/<action>', methods=['POST'])
def system_action(action):
    """Handles hardware commands from the UI."""
    if action == 'reboot':
        subprocess.Popen(["sudo", "reboot"])
    elif action == 'shutdown':
        subprocess.Popen(["sudo", "poweroff"])
    return jsonify({"status": "command_sent"})

if __name__ == '__main__':
    # Run on port 80 for easy access (requires sudo)
    app.run(host='0.0.0.0', port=80, debug=False)