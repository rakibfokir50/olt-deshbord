from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import os
import random

app = Flask(__name__)
app.secret_key = 'robiul_olt_super_secret_key_123'

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

# Dynamic OLT Server Database
OLT_LIST = [
    {"id": 1, "name": "Robiul OLT 1", "ip": "103.154.49.229", "port": 7001, "pons": 4},
    {"id": 2, "name": "Robiul OLT 2", "ip": "103.154.49.229", "port": 7002, "pons": 8},
]

# --- HTML TEMPLATES (Inline to eliminate TemplateNotFound error) ---

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>OLT Dashboard Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #080c14; color: #fff; display: flex; align-items: center; justify-content: center; height: 100vh; font-family: 'Segoe UI', sans-serif; }
        .login-card { background: #0f172a; border: 1px solid #1e293b; border-radius: 12px; padding: 35px; width: 100%; max-width: 400px; box-shadow: 0 10px 30px rgba(0,0,0,0.6); }
    </style>
</head>
<body>
    <div class="login-card">
        <h3 class="text-center text-info mb-4 fw-bold">🌐 OLT Core Login</h3>
        {% if error %}
            <div class="alert alert-danger p-2 fs-6 text-center">{{ error }}</div>
        {% endif %}
        <form action="/login" method="POST">
            <div class="mb-3">
                <label class="form-label text-muted">Username</label>
                <input type="text" name="username" class="form-control bg-dark text-white border-secondary" required placeholder="admin">
            </div>
            <div class="mb-3">
                <label class="form-label text-muted">Password</label>
                <input type="password" name="password" class="form-control bg-dark text-white border-secondary" required placeholder="••••••••">
            </div>
            <button type="submit" class="btn btn-info w-100 fw-bold text-white mt-2">Login to Dashboard</button>
        </form>
    </div>
</body>
</html>
"""

INDEX_HTML = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pro OLT Fiber Monitoring Center</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
    <style>
        body { background: #080c14; color: #cbd5e1; font-family: 'Segoe UI', sans-serif; }
        .sidebar { background: #0f172a; min-height: 100vh; border-right: 1px solid #1e293b; padding: 20px; }
        .card-custom { background: #0f172a; border: 1px solid #1e293b; border-radius: 10px; }
        .olt-btn { background: #1e293b; border: 1px solid #334155; color: #fff; text-align: left; transition: 0.2s; }
        .olt-btn:hover, .olt-btn.active { background: #0284c7; border-color: #38bdf8; box-shadow: 0 0 10px rgba(2, 132, 199, 0.4); }
        .table-cyber { background: #0f172a; border-radius: 10px; overflow: hidden; }
        .table-cyber th { background: #1e293b; color: #38bdf8; font-weight: 700; border-bottom: 2px solid #334155; }
        .table-cyber td { border-color: #1e293b; vertical-align: middle; }
        .vlan-input { width: 75px; background: #080c14; border: 1px solid #38bdf8; color: #38bdf8; font-weight: bold; text-align: center; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <!-- Sidebar -->
            <div class="col-md-3 col-lg-2 sidebar">
                <h4 class="text-info fw-bold mb-4 text-center"><i class="bi bi-cpu-fill"></i> OLT CORE</h4>
                
                <div class="d-grid mb-4">
                    <button class="btn btn-primary fw-bold text-uppercase shadow" data-bs-toggle="modal" data-bs-target="#addOltModal">
                        <i class="bi bi-plus-square-fill me-1"></i> Add New OLT
                    </button>
                </div>

                <div class="text-uppercase text-muted fw-bold mb-2 fs-7">Connected OLTs</div>
                <div class="list-group list-group-flush" id="olt-list-group">
                    {% for olt in olts %}
                    <button class="btn olt-btn mb-2 p-3 rounded-3 w-100" onclick="loadOnuData('{{ olt.id }}', '{{ olt.name }}', this)">
                        <div class="fw-bold fs-5"><i class="bi bi-hdd-network-fill me-2"></i>{{ olt.name }}</div>
                        <small class="text-muted d-block mt-1">{{ olt.ip }}:{{ olt.port }} | {{ olt.pons }} PON</small>
                    </button>
                    {% endfor %}
                </div>

                <div class="mt-5 text-center">
                    <a href="/logout" class="btn btn-outline-danger btn-sm w-100 fw-bold"><i class="bi bi-power"></i> Logout Admin</a>
                </div>
            </div>

            <!-- Main Content -->
            <div class="col-md-9 col-lg-10 p-4">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <div>
                        <h2 id="olt-title" class="fw-bold text-white m-0">Select an OLT to Start Monitoring</h2>
                    </div>
                    <span class="badge bg-success fs-6 px-3 py-2"><i class="bi bi-check-circle-fill me-1"></i> SYSTEM ACTIVE</span>
                </div>

                <!-- Stats Summary -->
                <div class="row mb-4">
                    <div class="col-md-4">
                        <div class="card card-custom p-3 border-start border-info border-4">
                            <span class="text-muted text-uppercase fw-bold">Total Connected ONUs</span>
                            <h2 id="total-onu" class="fw-bold text-info m-0 fs-1">0</h2>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card card-custom p-3 border-start border-success border-4">
                            <span class="text-muted text-uppercase fw-bold">Online ONUs</span>
                            <h2 id="online-onu" class="fw-bold text-success m-0 fs-1">0</h2>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card card-custom p-3 border-start border-danger border-4">
                            <span class="text-muted text-uppercase fw-bold">Offline ONUs</span>
                            <h2 id="offline-onu" class="fw-bold text-danger m-0 fs-1">0</h2>
                        </div>
                    </div>
                </div>

                <!-- ONU Table -->
                <div class="card card-custom shadow-lg">
                    <div class="card-header bg-dark border-bottom border-secondary p-3">
                        <h5 class="m-0 text-info fw-bold"><i class="bi bi-list-nested me-2"></i> ONU Status List (PON 1 ➔ PON N Serial Wise)</h5>
                    </div>
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-cyber align-middle m-0">
                                <thead>
                                    <tr>
                                        <th>PON Port</th>
                                        <th>User / ONU Name</th>
                                        <th>MAC Address</th>
                                        <th>Rx Power</th>
                                        <th>Tx Power</th>
                                        <th>Temp</th>
                                        <th>Status</th>
                                        <th>VLAN (Edit)</th>
                                        <th>Action</th>
                                    </tr>
                                </thead>
                                <tbody id="onu-table-body">
                                    <tr>
                                        <td colspan="9" class="text-center text-muted p-5 fs-5">বামপাশের তালিকা থেকে যেকোনো OLT সিলেক্ট করুন। সব PON-এর অনু অটো চলে আসবে।</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal: Add OLT -->
    <div class="modal fade" id="addOltModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content bg-dark text-white border-secondary">
                <div class="modal-header border-secondary">
                    <h5 class="modal-title text-info fw-bold">Add New OLT Server</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <input type="text" id="olt-name" class="form-control mb-3 bg-secondary text-white border-0" placeholder="OLT Name (e.g. Robiul OLT 3)">
                    <input type="text" id="olt-ip" class="form-control mb-3 bg-secondary text-white border-0" placeholder="IP Address (e.g. 103.154.49.229)">
                    <input type="number" id="olt-port" class="form-control mb-3 bg-secondary text-white border-0" placeholder="Port (e.g. 7003)">
                    <input type="number" id="olt-pons" class="form-control mb-3 bg-secondary text-white border-0" placeholder="Total PON Ports (e.g. 4 or 8)">
                </div>
                <div class="modal-footer border-secondary">
                    <button type="button" class="btn btn-primary fw-bold w-100" onclick="saveOlt()">Save & Add OLT</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function loadOnuData(oltId, oltName, btnElement) {
            document.querySelectorAll('.olt-btn').forEach(b => b.classList.remove('active'));
            if(btnElement) btnElement.classList.add('active');

            document.getElementById('olt-title').innerText = oltName + " - Live Status";
            document.getElementById('onu-table-body').innerHTML = '<tr><td colspan="9" class="text-center text-info p-5"><div class="spinner-border me-2"></div> লোড হচ্ছে...</td></tr>';

            fetch('/api/get-onu-data/' + oltId)
                .then(res => res.json())
                .then(res => {
                    let rows = '';
                    let online = 0, offline = 0;
                    
                    res.data.forEach(item => {
                        if (item.status === 'Online') online++; else offline++;
                        let statusBadge = item.status === 'Online' 
                            ? '<span class="badge bg-success">Online</span>' 
                            : '<span class="badge bg-danger">Offline</span>';

                        rows += `<tr>
                            <td><span class="badge bg-primary">${item.pon}</span></td>
                            <td class="fw-bold text-white">${item.username}</td>
                            <td><code class="text-warning fs-6">${item.mac}</code></td>
                            <td class="fw-bold ${parseFloat(item.rx) < -26 ? 'text-danger' : 'text-info'}">${item.rx} dBm</td>
                            <td class="text-muted">${item.tx} dBm</td>
                            <td>${item.temp}</td>
                            <td>${statusBadge}</td>
                            <td>
                                <input type="text" class="vlan-input" id="vlan-${item.id}" value="${item.vlan}">
                            </td>
                            <td>
                                <button class="btn btn-sm btn-outline-info" onclick="updateVlan('${item.mac}', '${item.id}')"><i class="bi bi-save me-1"></i>Save</button>
                            </td>
                        </tr>`;
                    });

                    document.getElementById('onu-table-body').innerHTML = rows;
                    document.getElementById('total-onu').innerText = res.data.length;
                    document.getElementById('online-onu').innerText = online;
                    document.getElementById('offline-onu').innerText = offline;
                });
        }

        function updateVlan(mac, id) {
            let newVlan = document.getElementById('vlan-' + id).value;
            fetch('/api/update-vlan', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({mac: mac, vlan: newVlan})
            }).then(res => res.json()).then(data => {
                alert(data.message);
            });
        }

        function saveOlt() {
            let name = document.getElementById('olt-name').value;
            let ip = document.getElementById('olt-ip').value;
            let port = document.getElementById('olt-port').value;
            let pons = document.getElementById('olt-pons').value;

            if(!name || !ip || !port) { alert("সব তথ্য পূরণ করুন!"); return; }

            fetch('/api/add-olt', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name, ip, port, pons})
            }).then(res => res.json()).then(data => {
                alert(data.message);
                location.reload();
            });
        }
    </script>
</body>
</html>
"""

# --- ROUTES ---

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template_string(LOGIN_HTML)
    return render_template_string(INDEX_HTML, olts=OLT_LIST)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if username == ADMIN_USER and password == ADMIN_PASS:
        session['logged_in'] = True
        return redirect(url_for('home'))
    return render_template_string(LOGIN_HTML, error="Invalid Username or Password!")

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

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
    return jsonify({"status": "success", "message": f"{data.get('name')} সফলভাবে যোগ করা হয়েছে!"})

@app.route('/api/get-onu-data/<int:olt_id>')
def get_onu_data(olt_id):
    target_olt = next((o for o in OLT_LIST if o['id'] == olt_id), None)
    if not target_olt:
        return jsonify({"status": "error", "message": "OLT পাওয়া যায়নি"}), 404

    onu_list = []
    total_pons = target_olt.get('pons', 4)
    
    # Generate sequential ONUs (PON 1 -> PON N)
    for pon_num in range(1, total_pons + 1):
        onu_count = 15 if olt_id == 2 else 8
        for idx in range(1, onu_count + 1):
            rx_val = round(random.uniform(-28.2, -15.5), 1)
            is_online = rx_val > -27.0
            onu_list.append({
                "id": f"{pon_num}_{idx}",
                "pon": f"PON {pon_num}",
                "username": f"User_P{pon_num}_{idx:02d}",
                "mac": f"E0:67:B3:{pon_num:02X}:{idx:02X}:{random.randint(10,99)}",
                "rx": f"{rx_val}",
                "tx": "+2.1",
                "temp": f"{random.randint(38, 50)}°C",
                "status": "Online" if is_online else "Offline",
                "vlan": "100" if pon_num % 2 != 0 else "200"
            })

    sorted_onus = sorted(onu_list, key=lambda x: int(x['pon'].replace('PON ', '')))
    return jsonify({"status": "success", "data": sorted_onus})

@app.route('/api/update-vlan', methods=['POST'])
def update_vlan():
    data = request.json
    return jsonify({"status": "success", "message": f"MAC ({data.get('mac')}) এর VLAN আপডেট হয়ে {data.get('vlan')} হয়েছে!"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
