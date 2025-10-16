import socket
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque

# ---------------- ESP8266 Settings ----------------
ESP_IP = "192.168.137.199"  # Replace with your ESP IP
PORT = 80

# ---------------- Graph Settings ----------------
MAX_POINTS = 50          # Number of points on graph
SAFE_DISTANCE = 15       # cm, danger threshold

# ---------------- Connect to ESP ----------------
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ESP_IP, PORT))
print(f"Connected to ESP at {ESP_IP}:{PORT}")

# ---------------- Data Storage ----------------
distance_data = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)

# ---------------- Plot Setup ----------------
plt.style.use('ggplot')
fig, ax = plt.subplots()
line, = ax.plot(distance_data, color='blue', label='Distance (cm)')
safe_line = ax.axhline(SAFE_DISTANCE, color='green', linestyle='--', label='Safe Distance')
ax.set_ylim(0, 100)
ax.set_xlabel("Time (samples)")
ax.set_ylabel("Distance (cm)")
ax.set_title("Live Ultrasonic Sensor Distance")
ax.legend()

# ---------------- Update Function ----------------
def update(frame):
    try:
        raw_data = s.recv(1024).decode().strip()
        if raw_data:
            for line_data in raw_data.splitlines():
                try:
                    d = float(line_data)
                    if d == 0 or d > 200:  # filter invalid readings
                        continue
                    distance_data.append(d)
                except:
                    continue
    except:
        pass

    # Change line color dynamically based on danger
    if distance_data[-1] < SAFE_DISTANCE:
        line.set_color('red')
    else:
        line.set_color('blue')

    line.set_ydata(distance_data)
    return line,

# ---------------- Run Animation ----------------
ani = FuncAnimation(fig, update, interval=100)
plt.show()
