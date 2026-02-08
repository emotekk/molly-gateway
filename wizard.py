import os
import subprocess
from flask import Flask, request, render_template_string

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Molly-Pi Setup</title>
    <style>
        body { background: #121212; color: #e0e0e0; font-family: sans-serif; display: flex; justify-content: center; padding: 20px; }
        .card { background: #1e1e1e; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); width: 100%; max-width: 450px; }
        h2 { color: #bb86fc; margin-bottom: 10px; }
        p { font-size: 0.9em; color: #b0b0b0; line-height: 1.5; }
        
        .section-title { font-size: 0.8em; font-weight: bold; color: #888; text-transform: uppercase; margin-top: 20px; letter-spacing: 1px; }
        
        /* How it Works Styles */
        .flow-container { background: #181818; padding: 15px; border-radius: 8px; margin: 10px 0; font-size: 0.85em; border: 1px solid #333; }
        .flow-step { display: flex; align-items: flex-start; margin-bottom: 12px; }
        .flow-step:last-child { margin-bottom: 0; }
        .step-num { background: #bb86fc; color: #000; min-width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 12px; font-size: 0.75em; }
        
        .instruction-box { background: #252525; padding: 15px; border-radius: 8px; border-left: 4px solid #03dac6; margin: 15px 0; font-size: 0.85em; }
        .instruction-box a { color: #03dac6; text-decoration: none; font-weight: bold; }
        
        input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 6px; border: 1px solid #333; background: #2c2c2c; color: white; box-sizing: border-box; }
        button { width: 100%; padding: 14px; border-radius: 6px; border: none; background: #03dac6; color: #000; font-weight: bold; cursor: pointer; margin-top: 10px; }
        .footer { margin-top: 25px; font-size: 0.7em; color: #555; text-align: center; border-top: 1px solid #333; padding-top: 15px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Molly-Pi Gateway</h2>
        <p>Your private bridge for battery-efficient Signal notifications.</p>

        <div class="section-title">The Notification Path</div>
        
        <div class="flow-container">
            <div class="flow-step">
                <div class="step-num">1</div>
                <div><b>Signal Server:</b> Receives a message for you.</div>
            </div>
            <div class="flow-step">
                <div class="step-num">2</div>
                <div><b>Molly-Pi:</b> Acts as a linked device; stays "awake" to catch the ping.</div>
            </div>
            <div class="flow-step">
                <div class="step-num">3</div>
                <div><b>Tailscale:</b> Sends a secure signal through a private tunnel to your phone.</div>
            </div>
            <div class="flow-step">
                <div class="step-num">4</div>
                <div><b>Your Phone:</b> Molly wakes up and fetches the message. No Google needed!</div>
            </div>
        </div>

        <div class="section-title">Setup Configuration</div>
        <div class="instruction-box">
            <strong>Auth Key:</strong> Your "secure pass" to join your Tailscale network. 
            Get it at <a href="https://login.tailscale.com/admin/settings/keys" target="_blank">Tailscale Console</a>.
        </div>

        <form action="/setup" method="post">
            <input type="text" name="ts_key" placeholder="tskey-auth-..." required>
            <input type="text" name="device_name" placeholder="Gateway Name (e.g. molly-pi)" value="molly-pi" required>
            <button type="submit">ACTIVATE GATEWAY</button>
        </form>

        <div class="footer">
            Molly-Pi Project • Private & Open Source
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/setup', methods=['POST'])
def do_setup():
    ts_key = request.form.get('ts_key', '').strip()
    device_name = request.form.get('device_name', 'molly-pi').strip()
    
    try:
        with open(".env", "w") as f:
            f.write(f"TS_AUTHKEY={ts_key}\n")
            f.write(f"DEVICE_NAME={device_name}\n")
    except Exception as e:
        return f"Error saving config: {e}", 500

    cmd = f"sudo tailscale up --authkey={ts_key} --hostname={device_name} && sudo docker compose up -d"
    subprocess.Popen(cmd, shell=True)
    
    return """
    <body style="background:#121212; color:white; font-family:sans-serif; text-align:center; padding-top:100px;">
        <h1 style="color:#03dac6;">Activation Started!</h1>
        <p>Your Pi is joining your network. Please wait 1-2 minutes.</p>
        <p>In your Tailscale dashboard, find <b>""" + device_name + """</b> and set <b>Disable Key Expiry</b>.</p>
    </body>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)