import os
import subprocess
import time
from flask import Flask, request, render_template_string, Response

app = Flask(__name__)

# ... (keep the HTML_TEMPLATE from before for the index route) ...

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/setup', methods=['POST'])
def do_setup():
    ts_key = request.form.get('ts_key', '').strip()
    device_name = request.form.get('device_name', 'molly-pi').strip()
    
    with open(".env", "w") as f:
        f.write(f"TS_AUTHKEY={ts_key}\n")
        f.write(f"DEVICE_NAME={device_name}\n")

    return render_template_string("""
    <body style="background:#121212; color:white; font-family:monospace; padding: 20px;">
        <h2 style="color:#03dac6;">System Activation</h2>
        <div id="console" style="background:#000; padding:15px; border-radius:8px; height:300px; overflow-y:auto; border:1px solid #333; font-size:0.85em; color:#00ff00;">
            [SYSTEM] Initializing installation...<br>
        </div>
        
        <div id="final-steps" style="display:none; margin-top:20px; padding:15px; background:#1e1e1e; border-radius:8px; border:1px solid #03dac6;">
            <h3 style="margin-top:0; color:#03dac6;">Done!</h3>
            <p>IP Address: <b id="ip-addr"></b></p>
            <p style="font-size:0.8em; color:#888;">Note: Go to Tailscale Admin > Machines and <b>Disable Key Expiry</b> for this device.</p>
        </div>

        <script>
            const consoleBox = document.getElementById('console');
            
            // Connect to the log stream
            const eventSource = new EventSource("/stream_logs?key={{key}}&name={{name}}");
            
            eventSource.onmessage = function(e) {
                if (e.data === "[DONE]") {
                    eventSource.close();
                    checkFinalStatus();
                } else {
                    consoleBox.innerHTML += e.data + "<br>";
                    consoleBox.scrollTop = consoleBox.scrollHeight;
                }
            };

            async function checkFinalStatus() {
                const res = await fetch('/status');
                const data = await res.json();
                if (data.online) {
                    document.getElementById('ip-addr').innerText = data.ip;
                    document.getElementById('final-steps').style.display = "block";
                }
            }
        </script>
    </body>
    """, key=ts_key, name=device_name)

@app.route('/stream_logs')
def stream_logs():
    ts_key = request.args.get('key')
    name = request.args.get('name')
    
    def generate():
        # Command to run
        cmd = f"sudo tailscale up --authkey={ts_key} --hostname={name} && sudo docker compose up -d"
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        for line in iter(process.stdout.readline, ""):
            yield f"data: {line.strip()}\\n\\n"
        
        process.stdout.close()
        yield "data: [DONE]\\n\\n"

    return Response(generate(), mimetype='text/event-stream')

@app.route('/status')
def get_status():
    ip = subprocess.getoutput("tailscale ip -4").strip()
    # Check if we have a valid Tailscale IP
    is_online = bool(ip and "100." in ip)
    return {"online": is_online, "ip": ip}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)