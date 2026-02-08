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
        .card { background: #1e1e1e; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); width: 100%; max-width: 420px; }
        h2 { color: #bb86fc; margin-top: 0; margin-bottom: 5px; }
        .subtitle { color: #888; font-size: 0.9em; margin-bottom: 25px; }
        
        /* Input Styles */
        label { display: block; font-size: 0.8em; color: #bb86fc; margin-bottom: 5px; font-weight: bold; }
        input { width: 100%; padding: 12px; margin-bottom: 20px; border-radius: 6px; border: 1px solid #333; background: #2c2c2c; color: white; box-sizing: border-box; }
        button { width: 100%; padding: 14px; border-radius: 6px; border: none; background: #03dac6; color: #000; font-weight: bold; cursor: pointer; font-size: 1em; }
        
        hr { border: 0; border-top: 1px solid #333; margin: 30px 0; }
        
        /* Details Section (Below the Fold) */
        .details-title { font-size: 0.75em; font-weight: bold; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px; }
        .info-section { font-size: 0.85em; color: #b0b0b0; line-height: 1.5; margin-bottom: 20px; }
        .info-section b { color: #e0e0e0; }
        
        .flow-step { margin-bottom: 10px; padding-left: 15px; border-left: 2px solid #333; }
        .instruction-link { color: #03dac6; text-decoration: none; font-weight: bold; }
        
        .footer { margin-top: 25px; font-size: 0.7em; color: #444; text-align: center; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Molly-Pi Setup</h2>
        <div class="subtitle">Activate your private notification gateway.</div>


        <form action="/setup" method="post">
            <label>Tailscale Auth Key</label>
            <input type="text" name="ts_key" placeholder="tskey-auth-..." required>
            
            <label>Gateway Name</label>
            <input type="text" name="device_name" placeholder="e.g. molly-pi" value="molly-pi" required>
            <div style="font-size: 0.75em; color: #666; margin-top: -15px; margin-bottom: 20px;">
                This is how the device will appear in your Tailscale dashboard.
            </div>
            
            <button type="submit">ACTIVATE GATEWAY</button>
        </form>


        <hr>

        <div class="details-title">Help & Documentation</div>
        
        <div class="info-section">
            <b>Where do I get a key?</b><br>
            Generate a key in your <a href="https://login.tailscale.com/admin/settings/keys" class="instruction-link" target="_blank">Tailscale Console</a>. 
            Ensure "Ephemeral" is off so the gateway stays linked.
        </div>

        <div class="info-section">
            <b>What is an Auth Key?</b><br>
            It is a secure "invite code" that lets this Pi join your private network without you having to manually log in on the device.
        </div>

        <div class="info-section">
            <b>How it works:</b>
            <div class="flow-step">1. This Pi joins your private Tailscale network.</div>
            <div class="flow-step">2. It acts as a "stand-in" device for Signal.</div>
            <div class="flow-step">3. Notifications are tunneled securely to your phone.</div>
        </div>

        <div class="footer">
            Molly-Pi Gateway v1.0.0 • Open Source
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
        <p>The Pi is joining your network.</p>
        <p>Once it appears in Tailscale, remember to <b>Disable Key Expiry</b>.</p>
    </body>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)