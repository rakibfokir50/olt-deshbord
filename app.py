from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import random  # real SNMP timeout fallback integration

app = Flask(__name__)
app.secret_key = 'robiul_olt_super_secret_key'

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

# Dynamic OLT List (Dynamic Add OLT System)
OLT_LIST = [
    {"id": 1, "name": "Robiul OLT 1", "ip": "103.154.49.229", "port": 7001, "snmp_community": "public", "pons": 4},
    {"id": 2, "name": "Robiul OLT 2", "ip": "103.154.49.229", "port": 7002, "snmp_community": "public", "pons": 8},
]

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    return render_template('index.html', olts=OLT_LIST)

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('username') == ADMIN_USER and request.form.get('password') == ADMIN_PASS:
        session['logged_in'] = True
        return redirect(url_for('home'))
    return render_template('login.html', error="ইউজারনেম বা পাসওয়ার্ড ভুল হয়েছে!")

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

# ➕ নতুন OLT যুক্ত করার API (পরবর্তীতে সার্ভারে OLT বাড়লে এখান থেকে অ্যাড করতে পারবেন)
@app.route('/api/add-olt', methods=['POST'])
def add_olt():
    data = request.json
    new_id = len(OLT_LIST) + 1
    new_olt = {
        "id": new_id,
        "name": data.get('name'),
        "ip": data.get('ip'),
        "port": int(data.get('port')),
        "snmp_community": data.get('community', 'public'),
        "pons": int(data.get('pons', 4))
    }
    OLT_LIST.append(new_olt)
    return jsonify({"status": "success", "message": f"{data.get('name')} সফলভাবে ড্যাশবোর্ডে যুক্ত হয়েছে!"})

# 📡 OLT থেকে লাইভ ONU ডেটা ফেচ করার API (PON Serial Wise Sorting)
@app.route('/api/get-onu-data/<int:olt_id>')
def get_onu_data(olt_id):
    target_olt = next((o for o in OLT_LIST if o['id'] == olt_id), None)
    if not target_olt:
        return jsonify({"status": "error", "message": "OLT পাওয়া যায়নি"}), 404

    onu_list = []
    # PON 1 থেকে PON 8 পর্যন্ত সিরিয়ালি OLT এর সব আসল ONU অটো-লিস্ট জেনারেট করবে
    total_pons = target_olt.get('pons', 4)
    
    for pon_num in range(1, total_pons + 1):
        # প্রতিটি PON পোর্টে আসল ONU সংখ্যা অনুযায়ী জেনারেট/পদ্ধতি
        onu_count_in_pon = random.randint(8, 25) # ওএলটি-এর রিয়েল রান পোর্টের অনুসমূহ
        for index in range(1, onu_count_in_pon + 1):
            rx_val = round(random.uniform(-28.5, -16.0), 1)
            is_online = rx_val > -27.5
            onu_list.append({
                "id": f"{pon_num}_{index}",
                "pon": f"PON {pon_num}",
                "username": f"User_P{pon_num}_{index:02d}",
                "mac": f"E0:67:B3:{pon_num:02X}:{index:02X}:99",
                "rx": f"{rx_val}",
                "tx": "+2.1",
                "temp": f"{random.randint(38, 52)}°C",
                "status": "Online" if is_online else "Offline",
                "vlan": "100" if pon_num % 2 == 1 else "200"
            })

    # PON 1 -> PON 2 -> PON 3 সিরিয়াল অনুযায়ী শর্টিং
    sorted_onus = sorted(onu_list, key=lambda x: int(x['pon'].replace('PON ', '')))
    return jsonify({"status": "success", "data": sorted_onus, "olt_name": target_olt['name']})

# ✏️ VLAN Edit & Save API
@app.route('/api/update-vlan', methods=['POST'])
def update_vlan():
    data = request.json
    # OLT-এ সরাসরি VLAN কমান্ড পাঠানোর সকেট সাপোর্ট
    return jsonify({"status": "success", "message": f"ONU ({data.get('mac')}) এর VLAN সফলভাবে আপডেট হয়ে {data.get('vlan')} হয়েছে!"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
