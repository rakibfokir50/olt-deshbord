from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import random

app = Flask(__name__)
app.secret_key = 'robiul_olt_dashboard_secret_key_999'

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

# Dynamic OLT List
OLT_LIST = [
    {"id": 1, "name": "Robiul OLT 1", "ip": "103.154.49.229", "port": 7001, "pons": 4},
    {"id": 2, "name": "Robiul OLT 2", "ip": "103.154.49.229", "port": 7002, "pons": 8},
]

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    return render_template('index.html', olts=OLT_LIST)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if username == ADMIN_USER and password == ADMIN_PASS:
        session['logged_in'] = True
        return redirect(url_for('home'))
    return render_template('login.html', error="Invalid Username or Password!")

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

# ➕ New OLT Add API
@app.route('/api/add-olt', methods=['POST'])
def add_olt():
    data = request.json
    new_id = len(OLT_LIST) + 1
    new_olt = {
        "id": new_id,
        "name": data.get('name'),
        "ip": data.get('ip'),
        "port": int(data.get('port')),
        "pons": int(data.get('pons', 4))
    }
    OLT_LIST.append(new_olt)
    return jsonify({"status": "success", "message": f"{data.get('name')} successfully added!"})

# 📡 Fetch ONU Data (PON Serial Wise)
@app.route('/api/get-onu-data/<int:olt_id>')
def get_onu_data(olt_id):
    target_olt = next((o for o in OLT_LIST if o['id'] == olt_id), None)
    if not target_olt:
        return jsonify({"status": "error", "message": "OLT Not Found"}), 404

    onu_list = []
    total_pons = target_olt.get('pons', 4)
    
    # Generate ONUs sequentially PON 1 to PON N
    for pon_num in range(1, total_pons + 1):
        onu_count = 12 if olt_id == 2 else 6
        for idx in range(1, onu_count + 1):
            rx_power = round(random.uniform(-28.0, -16.0), 1)
            status = "Online" if rx_power > -27.0 else "Offline"
            onu_list.append({
                "id": f"{pon_num}_{idx}",
                "pon": f"PON {pon_num}",
                "username": f"User_P{pon_num}_{idx:02d}",
                "mac": f"E0:67:B3:{pon_num:02X}:{idx:02X}:{random.randint(10,99)}",
                "rx": f"{rx_power}",
                "tx": "+2.1",
                "temp": f"{random.randint(38, 50)}°C",
                "status": status,
                "vlan": "100" if pon_num % 2 != 0 else "200"
            })

    sorted_onus = sorted(onu_list, key=lambda x: int(x['pon'].replace('PON ', '')))
    return jsonify({"status": "success", "data": sorted_onus, "olt_name": target_olt['name']})

# ✏️ Edit VLAN API
@app.route('/api/update-vlan', methods=['POST'])
def update_vlan():
    data = request.json
    return jsonify({"status": "success", "message": f"VLAN for MAC ({data.get('mac')}) updated to {data.get('vlan')}!"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
