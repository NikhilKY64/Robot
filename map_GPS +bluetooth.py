from flask import Flask, render_template_string, jsonify
import serial
import threading

app = Flask(__name__)

# Replace with your HC-05 COM port
ser = serial.Serial('COM6', 9600, timeout=1)

# Shared GPS data
gps_data = {'lat': 0, 'lon': 0}
path = []  # store all coordinates

# Thread to read GPS data continuously
def read_gps():
    global gps_data, path
    while True:
        line = ser.readline().decode('utf-8').strip()
        if line and line.count(',') == 3:
            try:
                lat, lon, speed, alt = map(float, line.split(','))
                gps_data['lat'] = lat
                gps_data['lon'] = lon
                path.append([lat, lon])  # add to path
            except:
                continue

threading.Thread(target=read_gps, daemon=True).start()

# Serve the map
@app.route('/')
def index():
    template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Live GPS Map with Path</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
        <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
    </head>
    <body>
        <h3>Live GPS Path</h3>
        <div id="map" style="height: 500px;"></div>
        <script>
            var map = L.map('map').setView([{gps_data['lat']}, {gps_data['lon']}], 17);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap contributors'
            }}).addTo(map);

            var marker = L.marker([{gps_data['lat']}, {gps_data['lon']}]).addTo(map);
            var polyline = L.polyline([], {{color: 'red'}}).addTo(map);

            function updateMap() {{
                fetch('/coords').then(response => response.json()).then(data => {{
                    var lat = data.lat;
                    var lon = data.lon;
                    var path = data.path;

                    marker.setLatLng([lat, lon]);
                    polyline.setLatLngs(path);
                    map.setView([lat, lon]);
                }});
            }}

            setInterval(updateMap, 1000); // update every second
        </script>
    </body>
    </html>
    """
    return render_template_string(template)

# Endpoint for current coordinates + path
@app.route('/coords')
def coords():
    return jsonify({'lat': gps_data['lat'], 'lon': gps_data['lon'], 'path': path})

if __name__ == '__main__':
    app.run(debug=True)
