@app.route('/setup', methods=['GET', 'POST']) # Added GET for the test link
def do_setup():
    is_test = request.args.get('test') == 'true'
    
    if is_test:
        ts_key = "test-key-123"
        device_name = "test-gateway"
    else:
        # Standard POST logic
        ts_key = request.form.get('ts_key', '').strip()
        device_name = request.form.get('device_name', 'molly-pi').strip()
        with open(".env", "w") as f:
            f.write(f"TS_AUTHKEY={ts_key}\nDEVICE_NAME={device_name}\n")

    return render_template('index.html', activating=True, key=ts_key, name=device_name, is_test=is_test)

@app.route('/stream_logs')
def stream_logs():
    ts_key = request.args.get('key')
    name = request.args.get('name')
    is_test = ts_key == "test-key-123" # Simple check for test mode
    
    def generate():
        if is_test:
            # Simulate a 5-second fake installation
            yield "data: [TEST] Initializing mock install...\\n\\n"
            time.sleep(1)
            yield "data: [TEST] Logging out of existing sessions...\\n\\n"
            time.sleep(1)
            yield f"data: [TEST] Success! Authenticated as {name}\\n\\n"
            time.sleep(1)
            yield "data: [TEST] Pulling Docker images...\\n\\n"
            time.sleep(2)
            yield "data: [TEST] Containers started successfully.\\n\\n"
        else:
            # Real logic
            subprocess.run(["sudo", "tailscale", "logout"])
            cmd = f"sudo tailscale up --authkey={ts_key} --hostname={name} && sudo docker compose up -d"
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in iter(process.stdout.readline, ""):
                if line.strip(): yield f"data: {line.strip()}\\n\\n"
            process.stdout.close()

        yield "data: [DONE]\\n\\n"

    return Response(generate(), mimetype='text/event-stream')

@app.route('/system/<action>', methods=['POST'])
def system_action(action):
    if action == 'reboot':
        subprocess.Popen(["sudo", "reboot"])
    elif action == 'shutdown':
        subprocess.Popen(["sudo", "poweroff"])
    return jsonify({"status": "command_sent"})