from flask import Flask, render_template, jsonify
import serial
import threading
import time
import os
import math

app = Flask(__name__)

# Connect to Arduino GPS on COM2
ser = serial.Serial('COM2', 9600, timeout=1)

gps_history = []
latest_data = {'lat': None, 'lon': None, 'satellites': 0, 'speed': 0, 'distance': 0}
last_time = None
KML_FILE = "live_path.kml"

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two lat/lon points in meters."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(delta_lambda/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R*c

def write_kml():
    """Write KML file with path and current location."""
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
    """Background thread to read GPS data and update KML, distance, speed."""
    global latest_data, gps_history, last_time
    while True:
        try:
            while ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith("Latitude:"):
                    lat = float(line.split(":")[1].strip())
                    lon_line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if lon_line.startswith("Longitude:"):
                        lon = float(lon_line.split(":")[1].strip())
                    else:
                        continue
                    sat_line = ser.readline().decode('utf-8', errors='ignore').strip()
                    satellites = int(sat_line.split(":")[1].strip()) if sat_line.startswith("Satellites in use:") else 0

                    # Calculate distance and speed
                    distance = 0
                    speed = 0
                    now = time.time()
                    if gps_history:
                        prev_lat, prev_lon = gps_history[-1]
                        distance = haversine(prev_lat, prev_lon, lat, lon)
                        dt = now - last_time if last_time else 1
                        speed = (distance / dt) * 3.6  # m/s -> km/h
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

                    # Update KML
                    write_kml()
        except Exception as e:
            print("GPS read error:", e)
        time.sleep(0.1)

# Start background thread
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
