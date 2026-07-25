from flask import Flask, render_template, jsonify
import os

app = Flask(__name__)

OLT_LIST = [
    {"id": 1, "name": "Robiul OLT 1", "ip": "103.154.49.229", "port": 7001},
    {"id": 2, "name": "Robiul OLT 2", "ip": "103.154.49.229", "port": 7002},
    {"id": 3, "name": "Robiul OLT 3", "ip": "103.154.49.229", "port": 7003},
    {"id": 4, "name": "Robiul OLT 4", "ip": "103.154.49.229", "port": 7004},
    {"id": 5, "name": "Robiul OLT 5", "ip": "103.154.49.229", "port": 7005},
    {"id": 6, "name": "Robiul OLT 6", "ip": "103.154.49.229", "port": 7006},
]

@app.route('/')
def home():
    return render_template('index.html', olts=OLT_LIST)

@app.route('/api/get-onu-data/<int:olt_id>')
def get_onu_data(olt_id):
    mock_data = [
        {"pon": "PON 1", "username": "user_01", "mac": "E0:67:B3:11:22:33", "dbm": "-19.5", "temp": "42°C", "status": "Online", "vlan": "100"},
        {"pon": "PON 1", "username": "user_02", "mac": "E0:67:B3:44:55:66", "dbm": "-27.1", "temp": "45°C", "status": "Online", "vlan": "100"},
        {"pon": "PON 2", "username": "user_03", "mac": "E0:67:B3:77:88:99", "dbm": "-31.0", "temp": "50°C", "status": "Offline", "vlan": "200"},
    ]
    return jsonify({"status": "success", "data": mock_data})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
