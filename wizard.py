from flask import Flask, render_template_string, request, redirect
import os
import subprocess

app = Flask(__name__)

# Modern, Mobile-First CSS
CSS = """
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
       background-color: #121212; color: #e0e0e0; display: flex; justify-content: center; align-items: center; 
       height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }
.card { background: #1e1e1e; padding: 30px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); 
        max-width: 400px; width: 100%; border: 1px solid #333; }
h1 { font-size: 24px; margin-bottom: 8px; color: #fff; text-align: center; }
p { color: #aaa; font-size: 14px; text-align: center; margin-bottom: 24px; }
label { display: block; margin-bottom: 8px; font-weight: 600; font-size: 13px; color: #4dabf7; }
input { width: 100%; padding: 12px; margin-bottom: 20px; border: 1px solid #444; border-radius: 8px; 
        background: #252525; color: #fff; font-size: 16px; box-sizing: border-box; }
button { width: 100%; padding: 14px; border: none; border-radius: 8px; background: #228be6; color: white; 
         font-size: 16px; font-weight: 600; cursor: pointer; transition: background 0.2s; }
button:hover { background: #1c7ed6; }
.footer { margin-top: 20px; font-size: 11px; color: #666; text-align: center; }
"""

HTML_TEMPLATE = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Molly-Pi Setup</title>
    <style>{CSS}</style>
</head>
<body>
    <div class="card">
        <h1>🚀 Molly-Pi Setup</h1>
        <p>Complete the fields below to activate your secure notification gateway.</p>
        <form method="POST" action="/setup">
            <label for="ts_key">Tailscale Auth Key</label>
            <input type="text" name="ts_key" placeholder="tskey-auth-..." required>
            
            <label for="device_name">Gateway Name</label>
            <input type="text" name="device_name" value="molly-gateway" required>
            
            <button type="submit">Activate Gateway</button>
        </form>
        <div class="footer">Your keys are stored locally and never shared.</div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/setup', methods=['POST'])
def do_setup():
    ts_key = request.form['ts_key']
    device_name = request.form['device_name']
    
    # Save to .env for Docker
    with open(".env", "w") as f:
        f.write(f"TS_AUTHKEY={ts_key}\n")
        f.write(f"DEVICE_NAME={device_name}\n")
    
    # In a real environment, we'd trigger a script to 'docker-compose up -d'
    # For now, we show a success message.
    return "<h1>Config Saved!</h1><p>The gateway is restarting. You can close this tab.</p>"

if __name__ == '__main__':
    # Run on port 80 so user doesn't need to type ":5000"
    app.run(host='0.0.0.0', port=80)