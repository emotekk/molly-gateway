import os
import subprocess
import secrets
import time
import sqlite3
from flask import Flask, render_template, request, Response, send_file, jsonify

app = Flask(__name__)

def generate_vapid():
    """Generate VAPID key - returns base64url encoded string"""
    return secrets.token_urlsafe(32)

def get_devices():
    """Query MollySocket database for registered devices"""
    db_path = './data/mollysocket.db'
    
    if not os.path.exists(db_path):
        return []
    
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Query the connections table
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
                'device_id': row['device_id'] if row['device_id'] else 'Unknown Device',
                'endpoint': row['endpoint'],
                'created': row['created'],
                'last_ping': row['last_ping'] if row['last_ping'] else 0
            })
        
        conn.close()
        return devices
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
    
    if not ts_key:
        return Response("Error: No Tailscale key provided\n", mimetype='text/plain')
    
    def generate():
        try:
            yield "🔧 Configuring firewall...\n"
            subprocess.run("sudo iptables -I INPUT -i tailscale0 -j ACCEPT 2>/dev/null", shell=True, timeout=10)
            subprocess.run("sudo iptables -I FORWARD -i tailscale0 -j ACCEPT 2>/dev/null", shell=True, timeout=10)
            subprocess.run("sudo iptables -I INPUT -p tcp --dport 8080 -j ACCEPT 2>/dev/null", shell=True, timeout=10)
            subprocess.run("sudo iptables -I INPUT -i tailscale0 -p tcp --dport 8080 -j ACCEPT 2>/dev/null", shell=True, timeout=10)
            
            yield "🔗 Disconnecting any previous Tailscale connection...\n"
            subprocess.run("sudo tailscale logout 2>/dev/null", shell=True, timeout=10)
            subprocess.run("sudo tailscale down 2>/dev/null", shell=True, timeout=10)
            
            yield "🔗 Connecting to Tailscale (this may take 30 seconds)...\n"
            result = subprocess.run(
                f"sudo tailscale up --authkey={ts_key} --hostname={name} --netfilter-mode=off --reset",
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                yield f"❌ Tailscale connection failed!\n"
                yield f"   Error: {result.stderr}\n"
                yield f"   Return code: {result.returncode}\n"
                yield "\n💡 Common fixes:\n"
                yield "   - Check your auth key is valid\n"
                yield "   - Try generating a new key at https://login.tailscale.com/admin/settings/keys\n"
                yield "   - Make sure the key is marked as 'Reusable'\n"
                return

            # Get network info
            yield "📡 Getting network information...\n"
            
            try:
                ts_ip = subprocess.check_output(["tailscale", "ip", "-4"], timeout=10).decode("utf-8").strip()
            except:
                yield "⚠️  Warning: Could not get Tailscale IP\n"
                ts_ip = "unknown"
            
            try:
                local_ip = subprocess.check_output(["hostname", "-I"], timeout=5).decode("utf-8").split()[0]
            except:
                local_ip = "unknown"
            
            try:
                hostname = subprocess.check_output(["hostname"], timeout=5).decode("utf-8").strip()
            except:
                hostname = "unknown"
            
            yield f"   Tailscale IP: {ts_ip}\n"
            yield f"   Local IP: {local_ip}\n"
            yield f"   Hostname: {hostname}\n"
            
            if ts_ip == "unknown":
                yield "\n❌ Failed to get Tailscale IP address!\n"
                yield "   Please check Tailscale connection: sudo tailscale status\n"
                return
            
            yield "🔑 Generating VAPID keys...\n"
            vapid = generate_vapid()
            
            yield "📝 Writing configuration file...\n"
            with open(".env", "w") as f:
                f.write("# MollySocket Configuration\n")
                f.write(f"MOLLY_VAPID_PRIVKEY={vapid}\n")
                f.write('MOLLY_ALLOWED_ENDPOINTS=["*"]\n')
                f.write("\n# Network Information\n")
                f.write(f"TAILSCALE_IP={ts_ip}\n")
                f.write(f"LOCAL_IP={local_ip}\n")
                f.write(f"HOSTNAME={hostname}\n")
            
            yield "   ✓ Configuration saved\n"

            yield "🐳 Pulling Docker image (this may take 2-3 minutes)...\n"
            subprocess.run(["sudo", "docker-compose", "pull"], check=True, timeout=180)
            
            yield "🚀 Starting MollySocket container...\n"
            subprocess.run(["sudo", "docker-compose", "up", "-d", "--force-recreate"], check=True, timeout=60)
            
            # Wait for container to start
            yield "⏳ Waiting for container to initialize...\n"
            for i in range(20):
                result = subprocess.run(
                    ["sudo", "docker", "ps", "--filter", "name=molly-socket", "--format", "{{.Status}}"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if "Up" in result.stdout:
                    yield "   ✓ Container is running!\n"
                    break
                    
                time.sleep(1)
                yield f"   Waiting... ({i+1}/20)\n"
            else:
                yield "⚠️  Container took longer than expected to start\n"
                yield "   Checking logs...\n"
                logs = subprocess.run(
                    ["sudo", "docker", "logs", "--tail", "10", "molly-socket"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                yield f"\n   Last 10 log lines:\n{logs.stdout}\n"
                return

            # Verify MollySocket is responding
            yield "🔍 Verifying MollySocket is responding...\n"
            time.sleep(2)
            try:
                import urllib.request
                response = urllib.request.urlopen(f"http://localhost:8080", timeout=5)
                yield "   ✓ MollySocket is responding!\n"
            except:
                yield "   ⚠️  MollySocket may not be responding yet\n"
                yield "   This is sometimes normal - check dashboard\n"

            yield "\n✅ SUCCESS! Setup complete.\n"
            yield "🎉 Redirecting to dashboard...\n"

        except subprocess.TimeoutExpired:
            yield f"\n❌ ERROR: Command timed out\n"
            yield "   This usually means:\n"
            yield "   - Tailscale connection is taking too long\n"
            yield "   - Network connectivity issues\n"
            yield "   - Docker download is very slow\n"
            yield "\n💡 Try:\n"
            yield "   - Check internet connection\n"
            yield "   - Try again with a new auth key\n"
            yield "   - Check: sudo tailscale status\n"
        except subprocess.CalledProcessError as e:
            yield f"\n❌ ERROR: Command failed: {str(e)}\n"
            if e.stderr:
                yield f"   Details: {e.stderr}\n"
        except Exception as e:
            yield f"\n❌ ERROR: {str(e)}\n"

    return Response(generate(), mimetype='text/plain')

@app.route('/health')
def health():
    result = subprocess.run(
        ["sudo", "docker", "inspect", "-f", "{{.State.Status}}", "molly-socket"],
        capture_output=True,
        text=True
    )
    status = result.stdout.strip()
    
    # Get network info from .env
    env_data = {}
    if os.path.exists('.env'):
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        env_data[key.lower()] = value
        except:
            pass
    
    return jsonify({
        "status": status if status else "unknown",
        "tailscale_ip": env_data.get('tailscale_ip', 'unknown'),
        "local_ip": env_data.get('local_ip', 'unknown'),
        "hostname": env_data.get('hostname', 'unknown')
    })

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
        conn = sqlite3.connect(db_path, timeout=5.0)
        cursor = conn.cursor()
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
    result = subprocess.run(
        ["sudo", "docker", "logs", "--tail", "100", "molly-socket"],
        capture_output=True,
        text=True
    )
    return Response(result.stdout + result.stderr, mimetype='text/plain')

@app.route('/download-config')
def download_config():
    if os.path.exists('.env'):
        return send_file('.env', as_attachment=True, download_name='mollysocket.env')
    return ("Configuration file not found", 404)

@app.route('/reset-gateway', methods=['POST'])
def reset_gateway():
    try:
        # Stop container
        subprocess.run(["sudo", "docker-compose", "down"], check=True, timeout=30)
        
        # Disconnect and logout from Tailscale
        subprocess.run(["sudo", "tailscale", "logout"], check=False, timeout=10)
        subprocess.run(["sudo", "tailscale", "down"], check=False, timeout=10)
        
        # Remove config and data
        if os.path.exists('.env'):
            os.remove('.env')
        subprocess.run(["sudo", "rm", "-rf", "./data"], check=True, timeout=10)
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)