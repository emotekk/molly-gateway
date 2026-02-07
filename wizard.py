import os
import subprocess
from flask import Flask, request, render_template_string

app = Flask(__name__)

# The Mobile-Friendly UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Molly-Pi Setup</title>
    <style>
        body { background: #121212; color: #e0e0e0; font-family: sans-serif; display: flex; justify-content: center; padding: 20px; }
        .card { background: #1e1e1e; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); width: 100%; max-width: 400px; }
        h2 { color: #bb86fc; margin-bottom: 10px; }
        p { font-size: 0.9em; color: #b0b0b0; line-height: 1.4; }
        input { width: 100%; padding: 12px; margin: 15px 0; border-radius: 6px; border: 1px solid #333; background: #2c2c2c; color: white; box-sizing: border-box; }
        button { width: 100%; padding: 14px; border-radius: 6px; border: none; background: #03dac6; color: #000; font-weight: bold; cursor: pointer; }
        .footer { margin-top: 20px; font-size: 0.7em; color: #666; text-align: center; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Molly-Pi Setup</h2>
        <p>Enter your Tailscale Auth Key to link this device to your private network.</p>
        
        <form action="/setup" method="post">
            <input type="text" name="ts_key" placeholder="tskey-auth-..." required>
            <input type="text" name="device_name" placeholder="Device Name (e.g. molly-pi)" required>
            <button type="submit">ACTIVATE GATEWAY</button>
        </form>

        <div class="footer">
            Note: Use a "One-Time" or "Reusable" key from your Tailscale console.
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
    
    # 1. Save configuration to .env file
    try:
        with open(".env", "w") as f:
            f.write(f"TS_AUTHKEY={ts_key}\n")
            f.write(f"DEVICE_NAME={device_name}\n")
    except Exception as e:
        return f"Error saving config: {e}", 500

    # 2. Run Tailscale and Docker in the background
    # We use Popen so the web response is sent immediately before the long tasks start
    cmd = f"sudo tailscale up --authkey={ts_key} --hostname={device_name} && sudo docker compose up -d"
    subprocess.Popen(cmd, shell=True)
    
    return """
    <body style="background:#121212; color:white; font-family:sans-serif; text-align:center; padding-top:100px;">
        <h1 style="color:#03dac6;">Activation Started!</h1>
        <p>Your Pi is now joining Tailscale and downloading the Molly containers.</p>
        <p>This page will now close. Check your Tailscale Dashboard in a few minutes.</p>
    </body>
    """

if __name__ == '__main__':
    # Listen on all interfaces (0.0.0.0) so your phone can see it
    app.run(host='0.0.0.0', port=80)