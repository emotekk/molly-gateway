import os
import subprocess
import time
import datetime
from flask import Flask, request, render_template, Response, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    if os.path.exists(".env"):
        ip = subprocess.getoutput("tailscale ip -4").strip()
        is_online = bool(ip and ip.startswith("100."))
        docker_status = subprocess.getoutput("sudo docker ps --filter 'name=molly-socket' --format '{{.Status}}'").strip()
        is_active = "Up" in docker_status
        return render_template('index.html', dashboard=True, online=is_online, ip=ip, service_active=is_active)
    
    return render_template('index.html', activating=False, dashboard=False)

@app.route('/setup', methods=['GET', 'POST'])
def do_setup():
    is_test = request.args.get('test') == 'true'
    if is_test:
        ts_key, device_name = "test-key-123", "test-gateway"
    else:
        ts_key = request.form.get('ts_key', '').strip()
        device_name = request.form.get('device_name', 'molly-pi').strip()
        if not ts_key: return "Missing Auth Key", 400
        with open(".env", "w") as f:
            f.write(f"TS_AUTHKEY={ts_key}\nDEVICE_NAME={device_name}\n")

    return render_template('index.html', activating=True, key=ts_key, name=device_name, is_test=is_test)

@app.route('/stream_logs')
def stream_logs():
    ts_key = request.args.get('key')
    name = request.args.get('name')
    is_test = (ts_key == "test-key-123")
    
    def generate():
        if is_test:
            yield "data: [TEST] Initializing mock installation...\n\n"
            time.sleep(1); yield "data: [TEST] Cleaning up old network sessions...\n\n"
            time.sleep(1); yield f"data: [TEST] Successfully authenticated as {name}\n\n"
            time.sleep(1); yield "data: [TEST] Molly-Pi services are UP and RUNNING.\n\n"
        else:
            yield "data: [SYSTEM] Disconnecting old Tailscale session...\n\n"
            subprocess.run(["sudo", "tailscale", "logout"])
            cmd = f"sudo tailscale up --authkey={ts_key} --hostname={name} && sudo docker compose up -d"
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in iter(process.stdout.readline, ""):
                clean_line = line.strip().replace('"', "'")
                if clean_line: yield f"data: {clean_line}\n\n"
            process.stdout.close()
        yield "data: [DONE]\n\n"

    return Response(generate(), mimetype='text/event-stream', headers={'Cache-Control': 'no-cache','Transfer-Encoding': 'chunked','Connection': 'keep-alive'})

@app.route('/status')
def get_status():
    ip = subprocess.getoutput("tailscale ip -4").strip()
    return jsonify({"online": bool(ip and ip.startswith("100.")), "ip": ip})

@app.route('/download_config')
def download_config():
    ip = subprocess.getoutput("tailscale ip -4").strip()
    config_text = f"MOLLY-PI CONFIG\nIP: {ip}\nDATE: {datetime.datetime.now()}"
    return Response(config_text, mimetype="text/plain", headers={"Content-disposition": "attachment; filename=molly_config.txt"})

@app.route('/system/<action>', methods=['POST'])
def system_action(action):
    if action == 'reboot': subprocess.Popen(["sudo", "reboot"])
    elif action == 'shutdown': subprocess.Popen(["sudo", "poweroff"])
    elif action == 'reset':
        if os.path.exists(".env"): os.remove(".env")
        subprocess.run(["sudo", "tailscale", "logout"])
        return jsonify({"status": "reset_complete"})
    return jsonify({"status": "command_sent"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)