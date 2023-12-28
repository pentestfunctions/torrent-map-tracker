# 🌐 Torrent Map Tracker

Welcome to the Torrent Map Tracker repository! This project is dedicated to tracking and visualizing the geolocation of peers in a torrent swarm.

## 🚀 Features

- **Real-Time Tracking**: Track peers in real-time with Flask-SocketIO.
- **Geolocation Visualization**: See the geographical location of peers.
- **Interactive UI**: Easy to use web interface for tracking torrents.

📸 Example gif
<p align="center">
  <img src="./static-images/Example.png" alt="Example after running Kali magnet">
</p>

## 🛠 Installation

1. Clone the repository:
```bash
git clone https://github.com/pentestfunctions/torrent-map-tracker.git
```

2. Navigate into the project folder:
```bash
cd torrent-map-tracker
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## ⚙️ Usage

To start the tracker, run the following command:
```bash
python app.py
```

Visit `http://localhost:5000` in your web browser to view the tracker interface.

- Notes:
  If you need, convert a .torrent file to magnet using https://nutbread.github.io/t2m/

## 🧰 Built With

- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Flask-SocketIO](https://flask-socketio.readthedocs.io/) - Real-time communication
- [Libtorrent](https://www.libtorrent.org/) - BitTorrent library
- [Flask-CORS](https://flask-cors.readthedocs.io/) - Handling Cross-Origin Resource Sharing (CORS)

## 📚 Documentation

- Only nerds need documentation.

💖 Thank you for visiting my repository!



