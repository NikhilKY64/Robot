from flask import Flask, render_template, jsonify
import threading
import time
import math
import requests
import os

app = Flask(__name__)

ESP_IP = "10.179.182.161"  # Replace with your ESP IP
ESP_ENDPOINT = f"http://{ESP_IP}/gps"

gps_history = []
latest_data = {'lat': None, 'lon': None, 'satellites': 0, 'speed': 0, 'distance': 0}
last_time = None
KML_FILE = "live_path.kml"

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(delta_lambda/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R*c

def write_kml():
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
    coordinates = ""
    for lat_c, lon_c in gps_history:
        coordinates += f"{lon_c},{lat_c},0\n"
    kml_content = kml_header + coordinates + kml_footer.format(lat=lat, lon=lon)
    with open(KML_FILE, "w") as f:
        f.write(kml_content)

def read_gps_continuously():
    global latest_data, gps_history, last_time
    while True:
        try:
            response = requests.get(ESP_ENDPOINT, timeout=2)
            if response.status_code == 200:
                data = response.json()
                lat = data.get('lat')
                lon = data.get('lon')
                satellites = data.get('satellites', 0)

                if lat is None or lon is None:
                    time.sleep(1)
                    continue

                # Distance & speed calculation
                distance = 0
                speed = 0
                now = time.time()
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

                write_kml()
        except Exception as e:
            print("GPS fetch error:", e)
        time.sleep(1)

threading.Thread(target=read_gps_continuously, daemon=True).start()

@app.route('/')
def index():
    return render_template('indexDV.html')

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

if __name__ == '__main__':
    if not os.path.exists(KML_FILE):
        write_kml()
    app.run(debug=False, host='0.0.0.0')
