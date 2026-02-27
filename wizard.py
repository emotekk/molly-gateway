import os
import subprocess
import secrets
import time
import sqlite3
import json
from flask import Flask, render_template, request, Response, send_file, jsonify

app = Flask(__name__)

def generate_vapid():
    return secrets.token_urlsafe(32)

def get_devices():
    """Query MollySocket database for registered devices"""
    db_path = './data/mollysocket.db'
    
    if not os.path.exists(db_path):
        return []
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Query the connections table (MollySocket stores devices here)
        cursor.execute("""
            SELECT 
                uuid,
                device_id,
                endpoint,
                created,
                last_ping
            FROM connections
            ORDER BY created DESC
        """)
        
        devices = []
        for row in cursor.fetchall():
            devices.append({
                'uuid': row['uuid'],
                'device_id': row['device_id'] if row['device_id'] else 'Unknown',
                'endpoint': row['endpoint'],
                'created': row['created'],
                'last_ping': row['last_ping'] if row['last_ping'] else 'Never'
            })
        
        conn.close()
        return devices
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    except Exception as e:
        print(f"Error reading devices: {e}")
        return []

@app.route('/')
def index():
    if os.path.exists('.env'):
        return render_template('dashboard.html')
    return render_template('index.html')

@app.route('/setup')
def setup():
    ts_key = request.args.get('key')
    name = request.args.get('name', 'molly-gateway')
    
    def generate():
        try:
            yield "Configuring firewall...\n"
            subprocess.run("sudo iptables -I INPUT -i tailscale0 -j ACCEPT", shell=True)
            subprocess.run("sudo iptables -I FORWARD -i tailscale0 -j ACCEPT", shell=True)
            
            yield "Connecting to Tailscale...\n"
            subprocess.run(f"sudo tailscale up --authkey={ts_key} --hostname={name} --netfilter-mode=off --reset", shell=True)

            # Get network info
            ts_ip = subprocess.check_output(["tailscale", "ip", "-4"]).decode("utf-8").strip()
            local_ip = subprocess.check_output(["hostname", "-I"]).decode("utf-8").split()[0]
            hostname = subprocess.check_output(["hostname"]).decode("utf-8").strip()
            
            yield "Generating keys and .env config...\n"
            vapid = generate_vapid()
            with open(".env", "w") as f:
                f.write(f"# MollySocket Configuration\n")
                f.write(f"MOLLY_VAPID_PRIVKEY={vapid}\n")
                f.write(f'MOLLY_ALLOWED_ENDPOINTS=["*"]\n')
                f.write(f"\n# Network Information\n")
                f.write(f"TAILSCALE_IP={ts_ip}\n")
                f.write(f"LOCAL_IP={local_ip}\n")
                f.write(f"HOSTNAME={hostname}\n")

            yield "Pulling and starting Molly Engine (this takes a moment)...\n"
            # We run this synchronously so the stream stays open until Docker is 'done'
            subprocess.run(["sudo", "docker-compose", "pull"], check=True)
            subprocess.run(["sudo", "docker-compose", "up", "-d", "--force-recreate"], check=True)
            
            # Wait up to 10 seconds for the container to actually appear in the system
            for i in range(10):
                check = subprocess.run(["sudo", "docker", "ps", "-a", "--filter", "name=molly-socket", "--format", "{{.Names}}"], capture_output=True, text=True)
                if "molly-socket" in check.stdout:
                    yield "SUCCESS: Container initialized. Redirecting...\n"
                    return
                time.sleep(1)
                yield "Waiting for container to spawn...\n"

            yield "WARNING: Container is taking a long time to start. Check dashboard in a moment.\n"

        except Exception as e:
            yield f"ERROR: {str(e)}\n"

    return Response(generate(), mimetype='text/plain')

@app.route('/health')
def health():
    result = subprocess.run(["sudo", "docker", "inspect", "-f", "{{.State.Status}}", "molly-socket"], capture_output=True, text=True)
    status = result.stdout.strip()
    
    # Get network info from .env
    env_data = {}
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_data[key.lower()] = value
    
    return {
        "status": status if status else "starting",
        "tailscale_ip": env_data.get('tailscale_ip', 'unknown'),
        "local_ip": env_data.get('local_ip', 'unknown'),
        "hostname": env_data.get('hostname', 'unknown')
    }

@app.route('/devices')
def list_devices():
    """List all registered devices"""
    devices = get_devices()
    return jsonify({
        'count': len(devices),
        'devices': devices
    })

@app.route('/devices/remove/<uuid>', methods=['POST'])
def remove_device(uuid):
    """Remove a device from the database"""
    db_path = './data/mollysocket.db'
    
    if not os.path.exists(db_path):
        return jsonify({'status': 'error', 'message': 'Database not found'}), 404
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Delete the device
        cursor.execute("DELETE FROM connections WHERE uuid = ?", (uuid,))
        conn.commit()
        
        if cursor.rowcount > 0:
            conn.close()
            return jsonify({'status': 'success', 'message': 'Device removed'})
        else:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Device not found'}), 404
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/logs')
def get_logs():
    result = subprocess.run(["sudo", "docker", "logs", "--tail", "100", "molly-socket"], capture_output=True, text=True)
    return Response(result.stdout + result.stderr, mimetype='text/plain')

@app.route('/download-config')
def download_config():
    return send_file('.env', as_attachment=True) if os.path.exists('.env') else ("Missing", 404)

@app.route('/reset-gateway', methods=['POST'])
def reset_gateway():
    subprocess.run(["sudo", "docker-compose", "down"], check=True)
    if os.path.exists('.env'): os.remove('.env')
    subprocess.run(["sudo", "rm", "-rf", "./data"], check=True)
    return {"status": "success"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)