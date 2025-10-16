from flask import Flask, render_template, jsonify
import serial

app = Flask(__name__)

# Connect to Arduino GPS on COM4
ser = serial.Serial('COM4', 9600, timeout=1)

# Store GPS history for path
gps_history = []

def get_gps_coordinates():
    """Read GPS data from Arduino serial. Returns (lat, lon, speed, altitude)"""
    while ser.in_waiting:
        line = ser.readline().decode('utf-8').strip()
        if line:
            try:
                parts = line.split(',')
                lat = float(parts[0])
                lon = float(parts[1])
                speed = float(parts[2]) if len(parts) > 2 else 0
                altitude = float(parts[3]) if len(parts) > 3 else 0
                return lat, lon, speed, altitude
            except ValueError:
                continue
    return None, None, 0, 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/location')
def location():
    lat, lon, speed, altitude = get_gps_coordinates()
    if lat is not None and lon is not None:
        gps_history.append([lat, lon])
    return jsonify({
        'lat': lat,
        'lon': lon,
        'speed': speed,
        'altitude': altitude,
        'path': gps_history
    })

if __name__ == '__main__':
    app.run(debug=True)
