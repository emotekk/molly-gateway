import os
import subprocess
import secrets
import time
from flask import Flask, render_template, request, Response, send_file

app = Flask(__name__)

def generate_vapid():
    return secrets.token_urlsafe(32)

def get_local_ip():
    """Get the local network IP address"""
    try:
        result = subprocess.check_output(["hostname", "-I"]).decode("utf-8").strip()
        return result.split()[0] if result else None
    except:
        return None

def get_tailscale_ip():
    """Get the Tailscale IP address"""
    try:
        return subprocess.check_output(["tailscale", "ip", "-4"]).decode("utf-8").strip()
    except:
        return None

def get_hostname():
    """Get the local hostname"""
    try:
        return subprocess.check_output(["hostname"]).decode("utf-8").strip()
    except:
        return None

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

            # Get all network addresses
            ts_ip = get_tailscale_ip()
            local_ip = get_local_ip()
            hostname = get_hostname()
            
            yield f"Tailscale IP: {ts_ip}\n"
            yield f"Local IP: {local_ip}\n"
            yield f"Hostname: {hostname}\n"
            
            yield "Generating keys and .env config...\n"
            vapid = generate_vapid()
            
            # Write .env with correct variable names for MollySocket
            # IMPORTANT: MOLLY_ALLOWED_ENDPOINTS must be JSON array format ["*"]
            with open(".env", "w") as f:
                f.write(f"# MollySocket Configuration\n")
                f.write(f"# CRITICAL: Use MOLLY_VAPID_PRIVKEY (not MOLLY_VAPID_KEY)\n")
                f.write(f"MOLLY_VAPID_PRIVKEY={vapid}\n")
                f.write(f'# CRITICAL: MOLLY_ALLOWED_ENDPOINTS must be JSON array format\n')
                f.write(f'MOLLY_ALLOWED_ENDPOINTS=["*"]\n')
                f.write(f"# Network Information\n")
                f.write(f"TAILSCALE_IP={ts_ip}\n")
                f.write(f"LOCAL_IP={local_ip}\n")
                f.write(f"HOSTNAME={hostname}\n")

            yield "Pulling and starting Molly Engine (this takes a moment)...\n"
            subprocess.run(["sudo", "docker-compose", "pull"], check=True)
            subprocess.run(["sudo", "docker-compose", "up", "-d", "--force-recreate"], check=True)
            
            # Wait up to 20 seconds for the container to start properly
            yield "Waiting for container to start...\n"
            for i in range(20):
                check = subprocess.run(["sudo", "docker", "ps", "--filter", "name=molly-socket", "--filter", "status=running", "--format", "{{.Names}}"], capture_output=True, text=True)
                if "molly-socket" in check.stdout:
                    # Container is running, now check logs for errors
                    time.sleep(2)  # Give it a moment to start up
                    logs = subprocess.run(["sudo", "docker", "logs", "--tail", "5", "molly-socket"], capture_output=True, text=True)
                    if "ERROR" not in logs.stderr and "ERROR" not in logs.stdout:
                        yield f"SUCCESS: Gateway ready!\n"
                        yield f"Tailscale URL: http://{ts_ip}:8080\n"
                        yield f"Local test URL: http://{local_ip}:8080\n"
                        yield "REDIRECT_NOW\n"
                        return
                    else:
                        yield f"WARNING: Container started but showing errors. Check logs.\n"
                        return
                time.sleep(1)
                if i % 3 == 0:
                    yield "."

            yield "WARNING: Container is taking a long time to start. Check dashboard logs.\n"

        except Exception as e:
            yield f"ERROR: {str(e)}\n"

    return Response(generate(), mimetype='text/plain')

@app.route('/health')
def health():
    result = subprocess.run(["sudo", "docker", "inspect", "-f", "{{.State.Status}}", "molly-socket"], capture_output=True, text=True)
    status = result.stdout.strip()
    
    # Get all network information
    ts_ip = get_tailscale_ip()
    local_ip = get_local_ip()
    hostname = get_hostname()
    
    return {
        "status": status if status else "starting",
        "tailscale_ip": ts_ip or "unknown",
        "local_ip": local_ip or "unknown",
        "hostname": hostname or "unknown"
    }

@app.route('/logs')
def get_logs():
    result = subprocess.run(["sudo", "docker", "logs", "--tail", "100", "molly-socket"], capture_output=True, text=True)
    return Response(result.stdout + result.stderr, mimetype='text/plain')

@app.route('/download-config')
def download_config():
    return send_file('.env', as_attachment=True) if os.path.exists('.env') else ("Missing", 404)

@app.route('/reset-gateway', methods=['POST'])
def reset_gateway():
    try:
        subprocess.run(["sudo", "docker-compose", "down"], check=True, timeout=30)
        if os.path.exists('.env'): 
            os.remove('.env')
        if os.path.exists('data'): 
            subprocess.run(["sudo", "rm", "-rf", "data"], check=True, timeout=10)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)