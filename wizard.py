import os
import subprocess
import time
from flask import Flask, request, render_template_string, Response, jsonify

app = Flask(__name__)

# Keep your existing HTML_TEMPLATE here...
HTML_TEMPLATE = """
# ... (Use the UI code from our previous step) ...
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/setup', methods=['POST'])
def do_setup():
    # Safely get form data
    ts_key = request.form.get('ts_key', '').strip()
    device_name = request.form.get('device_name', 'molly-pi').strip()
    
    if not ts_key:
        return "Error: Tailscale Auth Key is required", 400

    # Save to .env immediately
    try:
        with open(".env", "w") as f:
            f.write(f"TS_AUTHKEY={ts_key}\n")
            f.write(f"DEVICE_NAME={device_name}\n")
    except Exception as e:
        return f"File Error: {e}", 500

    # Pass the variables to the results page via query strings for the EventSource
    return render_template_string("""
    <body style="background:#121212; color:white; font-family:monospace; padding: 20px; line-height:1.4;">
        <h2 style="color:#03dac6;">System Activation</h2>
        <div id="console" style="background:#000; padding:15px; border-radius:8px; height:350px; overflow-y:auto; border:1px solid #333; font-size:0.85em; color:#00ff00; white-space: pre-wrap;">
            [SYSTEM] Starting install stream...<br>
        </div>
        
        <div id="final-steps" style="display:none; margin-top:20px; padding:15px; background:#1e1e1e; border-radius:8px; border:1px solid #03dac6;">
            <h3 style="margin-top:0; color:#03dac6;">Success! Gateway is Online</h3>
            <p>Tailscale IP: <b id="ip-addr" style="font-size:1.2em;"></b></p>
            <p style="font-size:0.85em; color:#888;"><b>Next Step:</b> Open your Tailscale Admin Console and <b>Disable Key Expiry</b> for this device.</p>
            <a href="https://login.tailscale.com/admin/machines" target="_blank" style="display:inline-block; padding:10px 20px; background:#03dac6; color:black; text-decoration:none; border-radius:5px; font-weight:bold; font-family:sans-serif;">Open Tailscale Admin</a>
        </div>

        <script>
            const consoleBox = document.getElementById('console');
            // We pass the key and name to the stream via URL params
            const eventSource = new EventSource("/stream_logs?key={{key}}&name={{name}}");
            
            eventSource.onmessage = function(e) {
                if (e.data === "[DONE]") {
                    eventSource.close();
                    consoleBox.innerHTML += "<br>[SYSTEM] Process finished.";
                    checkFinalStatus();
                } else if (e.data.startsWith("[ERROR]")) {
                    eventSource.close();
                    consoleBox.innerHTML += "<br><span style='color:red;'>" + e.data + "</span>";
                } else {
                    consoleBox.innerHTML += e.data + "<br>";
                    consoleBox.scrollTop = consoleBox.scrollHeight;
                }
            };

            async function checkFinalStatus() {
                try {
                    const res = await fetch('/status');
                    const data = await res.json();
                    if (data.online) {
                        document.getElementById('ip-addr').innerText = data.ip;
                        document.getElementById('final-steps').style.display = "block";
                        consoleBox.style.height = "150px"; // Shrink console to show success
                    }
                } catch (err) { console.log("Status check failed", err); }
            }
        </script>
    </body>
    """, key=ts_key, name=device_name)

@app.route('/stream_logs')
def stream_logs():
    ts_key = request.args.get('key')
    name = request.args.get('name')
    
    def generate():
        # Step 1: Force logout any old Tailscale session to avoid conflicts
        yield "data: [SYSTEM] Cleaning up old Tailscale sessions...\\n\\n"
        subprocess.run(["sudo", "tailscale", "logout"])
        
        # Step 2: Run the command
        cmd = f"sudo tailscale up --authkey={ts_key} --hostname={name} --accept-routes && sudo docker compose up -d"
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        for line in iter(process.stdout.readline, ""):
            clean_line = line.strip().replace('"', "'") # Prevent JS breakages
            if clean_line:
                yield f"data: {clean_line}\\n\\n"
        
        process.stdout.close()
        yield "data: [DONE]\\n\\n"

    return Response(generate(), mimetype='text/event-stream')

@app.route('/status')
def get_status():
    # Use -4 to get the Tailscale IPv4 address
    ip = subprocess.getoutput("tailscale ip -4").strip()
    # Check if we have a valid Tailscale IP (starts with 100.)
    is_online = bool(ip and ip.startswith("100."))
    return jsonify({"online": is_online, "ip": ip})

if __name__ == '__main__':
    # Running on port 80 requires sudo
    app.run(host='0.0.0.0', port=80, debug=False)