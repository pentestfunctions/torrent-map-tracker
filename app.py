from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import libtorrent as lt
import time
import ipaddress
from flask_cors import CORS
import subprocess

app = Flask(__name__, static_folder='static')
CORS(app)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Global variable to store the current tracking thread and IPs to be scanned
current_thread = None
ips_to_scan = set()
scan_lock = threading.Lock()

def parse_httpx_output(output):
    lines = output.strip().split("\n")
    scan_results = []
    webserver_found = False
    for line in lines:
        if '[FAILED]' not in line:
            scan_results.append(line)
            webserver_found = True
    return scan_results, webserver_found

def run_httpx_scan(ip):
    ports = "8080,80,8888,443,1337,9000,420"  # nmap-style port list
    print(f"Running httpx against {ip} for ports {ports}")
    command = f"httpx -u {ip} -p {ports} -title -tech-detect -status-code -nc -cl -ct -location -rt -lc -wc -server -method -ip -cname -cdn -probe -silent -timeout 3"
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"Finished httpx against {ip} for ports {ports}")
    
    output = result.stdout.decode('utf-8')
    scan_results, webserver_found = parse_httpx_output(output)
    return scan_results, webserver_found

def scan_open_ports():
    while True:
        with scan_lock:
            if not ips_to_scan:
                time.sleep(10)
                continue

            for ip in ips_to_scan:
                # Scan the IP with multiple ports and get webserver found flag
                scan_data, webserver_found = run_httpx_scan(ip)
                print(f"IP: {ip}, Webserver Found: {webserver_found}")  # Debugging line

                # Include scan_results in peer_data
                lat, lon, city, country = find_geocoordinates(ip, 'dbip-city-lite-2023-12.csv')
                peer_data = {
                    'ip': ip,
                    'lat': lat,
                    'lon': lon,
                    'city': city,
                    'country': country,
                    'scan_results': scan_data,
                    'webserver_found': webserver_found
                }
                print(f"Emitting data: {peer_data}")
                socketio.emit('new_peer', peer_data)

            ips_to_scan.clear()

def find_subnet(ip, subnet_mask):
    ip_obj = ipaddress.ip_address(ip)
    network = ipaddress.ip_network(f"{ip}/{subnet_mask}", strict=False)
    return network.network_address

def find_geocoordinates(ip, filename):
    print(f"Finding coordinates for {ip}")
    subnet = find_subnet(ip, 24)
    with open(filename, 'r') as file:
        next(file)  # Skip the header line
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
            ip, _ = peer.ip
            if ip not in checked_peers:
                checked_peers.add(ip)

                # Scan the IP with multiple ports
                scan_data = run_httpx_scan(ip)

                # Get geocoordinates and emit data to client
                lat, lon, city, country = find_geocoordinates(ip, filename)
                peer_data = {
                    'ip': ip,
                    'lat': lat,
                    'lon': lon,
                    'city': city,
                    'country': country,
                    'scan_results': scan_data  # assuming scan_data is a list of results
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

    # Stop the current tracking thread
    if current_thread:
        current_thread.do_run = False
        current_thread.join()

    # Create a stoppable thread
    stop_thread = threading.Event()
    current_thread = threading.Thread(target=get_peers, args=(magnet_link, 'dbip-city-lite-2023-12.csv', stop_thread))
    current_thread.do_run = True
    current_thread.start()

if __name__ == '__main__':
    threading.Thread(target=scan_open_ports, daemon=True).start()
    socketio.run(app)
