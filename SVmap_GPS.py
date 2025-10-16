from flask import Flask, render_template, jsonify
import serial
import threading
import time
import math

app = Flask(__name__)

# Update with your Arduino COM port
ser = serial.Serial('COM2', 9600, timeout=1)

gps_history = []
latest_data = {'lat': 0, 'lon': 0, 'speed': 0, 'distance': 0, 'satellites': 0}
last_time = None

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def read_gps():
    global latest_data, gps_history, last_time
    lat = lon = satellites = None

    while True:
        try:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line.startswith("Latitude:"):
                lat = float(line.split(":")[1].strip())
            elif line.startswith("Longitude:"):
                lon = float(line.split(":")[1].strip())
            elif line.startswith("Satellites in use:"):
                satellites = int(line.split(":")[1].strip())
            elif line.startswith("---------------------------"):
                # End of one GPS reading
                if lat is not None and lon is not None:
                    now = time.time()
                    speed = 0
                    distance = 0

                    if gps_history:
                        prev_lat, prev_lon = gps_history[-1]
                        distance = haversine(prev_lat, prev_lon, lat, lon)
                        dt = now - last_time if last_time else 1
                        speed = (distance/dt) * 3.6
                        latest_data['distance'] += distance
                    else:
                        latest_data['distance'] = 0

                    gps_history.append([lat, lon])
                    latest_data.update({
                        'lat': lat,
                        'lon': lon,
                        'speed': speed,
                        'satellites': satellites if satellites else 0
                    })
                    last_time = now

                # Reset for next reading
                lat = lon = satellites = None

        except Exception as e:
            print("GPS read error:", e)
        time.sleep(0.05)

# Background thread
threading.Thread(target=read_gps, daemon=True).start()

@app.route('/')
def index():
    return render_template('indexSV.html')

@app.route('/location')
def location():
    return jsonify(latest_data | {'path': gps_history})

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0')
