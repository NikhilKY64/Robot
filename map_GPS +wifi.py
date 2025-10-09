from flask import Flask, request, render_template_string, jsonify

app = Flask(__name__)

gps_data = {'lat': 0, 'lon': 0}
path = []

@app.route('/update')
def update():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    if lat and lon:
        gps_data['lat'] = lat
        gps_data['lon'] = lon
        path.append([lat, lon])
    return "OK"

@app.route('/')
def index():
    template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Live GPS Map - ESP32</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
        <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
    </head>
    <body>
        <h3>Live GPS Path (Wi-Fi)</h3>
        <div id="map" style="height:500px;"></div>
        <script>
            var map = L.map('map').setView([{gps_data['lat']}, {gps_data['lon']}], 17);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap contributors'
            }}).addTo(map);

            var marker = L.marker([{gps_data['lat']}, {gps_data['lon']}]).addTo(map);
            var polyline = L.polyline([], {{color: 'red'}}).addTo(map);

            function updateMap() {{
                fetch('/coords').then(r => r.json()).then(data => {{
                    marker.setLatLng([data.lat, data.lon]);
                    polyline.setLatLngs(data.path);
                    map.setView([data.lat, data.lon]);
                }});
            }}

            setInterval(updateMap, 1000);
        </script>
    </body>
    </html>
    """
    return render_template_string(template)

@app.route('/coords')
def coords():
    return jsonify({'lat': gps_data['lat'], 'lon': gps_data['lon'], 'path': path})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
