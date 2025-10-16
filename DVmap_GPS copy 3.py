from flask import Flask, render_template, jsonify
import threading
import time
import math
import requests

app = Flask(__name__)

ESP_IP = "192.168.137.27"  # Replace with your ESP IP
ESP_ENDPOINT = f"http://{ESP_IP}/gps"

gps_history = []
latest_data = {'lat': None, 'lon': None, 'satellites': 0, 'speed': 0, 'distance': 0}
last_time = None
KML_FILE = "live_path.kml"

# Haversine distance
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(d_lambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

# Read GPS continuously
def read_gps_continuously():
    global latest_data, gps_history, last_time
    while True:
        try:
            resp = requests.get(ESP_ENDPOINT, timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                lat = data.get('lat')
                lon = data.get('lon')
                satellites = data.get('satellites', 0)

                if lat is None or lon is None:
                    time.sleep(1)
                    continue

                # Distance & speed
                now = time.time()
                distance = 0
                speed = 0
                if gps_history:
                    prev_lat, prev_lon = gps_history[-1]
                    distance = haversine(prev_lat, prev_lon, lat, lon)
                    dt = now - last_time if last_time else 1
                    speed = (distance / dt) * 3.6  # km/h
                    latest_data['distance'] += distance
                else:
                    latest_data['distance'] = 0

                last_time = now

                latest_data.update({
                    'lat': lat,
                    'lon': lon,
                    'satellites': satellites,
                    'speed': speed
                })

                gps_history.append([lat, lon])

                # Keep last 500 points only
                if len(gps_history) > 500:
                    gps_history = gps_history[-500:]

        except Exception as e:
            print("GPS fetch error:", e)
        time.sleep(1)

# Write KML file
def write_kml():
    if not gps_history:
        return

    kml_header = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
    <name>Live GPS Path</name>
    <Placemark>
        <name>Path</name>
        <LineString>
            <tessellate>1</tessellate>
            <coordinates>
'''
    kml_footer = '''
            </coordinates>
        </LineString>
    </Placemark>
    <Placemark>
        <name>Current Location</name>
        <Point>
            <coordinates>{lon},{lat},0</coordinates>
        </Point>
    </Placemark>
</Document>
</kml>'''

    lat = latest_data['lat'] if latest_data['lat'] else 0
    lon = latest_data['lon'] if latest_data['lon'] else 0
    coordinates = "\n".join(f"{lon_c},{lat_c},0" for lat_c, lon_c in gps_history)
    kml_content = kml_header + coordinates + kml_footer.format(lat=lat, lon=lon)

    try:
        with open(KML_FILE, "w") as f:
            f.write(kml_content)
    except Exception as e:
        print("KML write error:", e)

# Update KML periodically in a separate thread
def update_kml_periodically():
    while True:
        write_kml()
        time.sleep(2)  # update every 2 seconds

# Flask routes
@app.route('/')
def index():
    return render_template('indexSV.html')

@app.route('/location')
def location():
    return jsonify({
        'lat': latest_data['lat'],
        'lon': latest_data['lon'],
        'satellites': latest_data['satellites'],
        'speed': latest_data['speed'],
        'distance': latest_data['distance'],
        'path': gps_history
    })

# Start threads
threading.Thread(target=read_gps_continuously, daemon=True).start()
threading.Thread(target=update_kml_periodically, daemon=True).start()

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
