from flask import Flask, render_template, jsonify
import serial
import threading
import time

app = Flask(__name__)

# Connect to Arduino GPS on COM2
ser = serial.Serial('COM2', 9600, timeout=1)

# Store GPS history for path
gps_history = []

# Shared latest GPS coordinates
latest_data = {'lat': None, 'lon': None, 'satellites': 0}

def read_gps_continuously():
    """Background thread to constantly read GPS from Arduino."""
    global latest_data, gps_history
    while True:
        try:
            while ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith("Latitude:"):
                    lat = float(line.split(":")[1].strip())

                    # Read longitude line
                    lon_line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if lon_line.startswith("Longitude:"):
                        lon = float(lon_line.split(":")[1].strip())
                    else:
                        continue

                    # Read satellites line
                    sat_line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if sat_line.startswith("Satellites in use:"):
                        satellites = int(sat_line.split(":")[1].strip())
                    else:
                        satellites = 0

                    latest_data.update({'lat': lat, 'lon': lon, 'satellites': satellites})
                    gps_history.append([lat, lon])
        except Exception as e:
            print("GPS read error:", e)
        time.sleep(0.1)

# Start GPS reading thread
threading.Thread(target=read_gps_continuously, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/location')
def location():
    return jsonify({
        'lat': latest_data['lat'],
        'lon': latest_data['lon'],
        'satellites': latest_data['satellites'],
        'path': gps_history
    })

if __name__ == '__main__':
    app.run(debug=False)
