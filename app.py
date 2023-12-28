from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import libtorrent as lt
import time
import ipaddress
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'robotisbeast!'
socketio = SocketIO(app)

current_thread = None

def find_subnet(ip, subnet_mask):
    ip_obj = ipaddress.ip_address(ip)
    network = ipaddress.ip_network(f"{ip}/{subnet_mask}", strict=False)
    return network.network_address

def find_geocoordinates(ip, filename):
    subnet = find_subnet(ip, 24)
    with open(filename, 'r') as file:
        next(file)
        for line in file:
            parts = line.strip().split(',')
            if len(parts) >= 8:
                start_ip, end_ip, _, country, region, city, lat, lon = parts[:8]
                if start_ip <= str(subnet) <= end_ip:
                    return lat, lon, city, country
    return "Unknown", "Unknown", "Unknown", "Unknown"

def get_peers(magnet_link, filename, stop_thread):
    ses = lt.session({
        'enable_dht': True,
        'enable_lsd': True,
        'enable_natpmp': True,
        'enable_upnp': True
    })

    settings = ses.get_settings()
    settings['connections_limit'] = 200
    ses.apply_settings(settings)

    params = lt.parse_magnet_uri(magnet_link)
    params.save_path = '/path/to/save/torrents/'
    handle = ses.add_torrent(params)

    while not handle.status().has_metadata:
        time.sleep(1)

    checked_peers = set()
    while not stop_thread.is_set():
        for peer in handle.get_peer_info():
            ip, port = peer.ip
            if ip not in checked_peers:
                checked_peers.add(ip)
                lat, lon, city, country = find_geocoordinates(ip, filename)
                peer_data = {
                    'ip': ip,
                    'lat': lat,
                    'lon': lon,
                    'city': city,
                    'country': country
                }
                socketio.emit('new_peer', peer_data)
        time.sleep(2)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('new_magnet_link')
def handle_new_magnet_link(data):
    global current_thread
    magnet_link = data['magnet_link']

    if current_thread:
        current_thread.do_run = False
        current_thread.join()

    stop_thread = threading.Event()
    current_thread = threading.Thread(target=get_peers, args=(magnet_link, 'dbip-city-lite-2023-12.csv', stop_thread))
    current_thread.do_run = True
    current_thread.start()

if __name__ == '__main__':
    socketio.run(app)
