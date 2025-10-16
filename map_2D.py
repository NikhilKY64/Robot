import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import socket
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.collections import PolyCollection

# ---- ESP TCP Settings ----
ESP_IP = "192.168.137.112"  # Replace with your ESP IP if different
ESP_PORT = 80

# ---- Color mapping thresholds (cm) ----
LOW_THRESH = 25.0
HIGH_THRESH = 100.0
VMIN = 0.0
VMAX = 210.0

# ---- Custom colormap ----
_p1 = LOW_THRESH / VMAX
_p2 = HIGH_THRESH / VMAX
stops = [
    (0.0, '#ff0000'), (_p1, '#ff0000'),
    (_p1 + (_p2 - _p1) * 0.18, '#ff7f00'),
    (_p1 + (_p2 - _p1) * 0.36, '#ffff00'),
    (_p1 + (_p2 - _p1) * 0.56, '#7fff00'),
    (_p1 + (_p2 - _p1) * 0.74, '#00ffff'),
    (_p1 + (_p2 - _p1) * 0.90, '#1e90ff'),
    (_p2, '#0000ff'), (1.0, '#00008b')
]
custom_cmap = LinearSegmentedColormap.from_list('rainbow_custom', stops)

# ---- Connect to ESP ----
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(2.0)
try:
    sock.connect((ESP_IP, ESP_PORT))
    print(f"Connected to ESP at {ESP_IP}:{ESP_PORT}")
except Exception as e:
    print(f"Failed to connect: {e}")
    sock = None

recv_buffer = b''

# ---- Set up plot ----
fig, ax = plt.subplots(figsize=(12, 5))
ax.set_xlim(0, 100)
ax.set_ylim(VMIN, VMAX)
ax.set_yticks(range(int(VMIN), int(VMAX) + 1, 20))
ax.set_xlabel("Reading Number")
ax.set_ylabel("Distance (cm)")
ax.set_title("Robot Live Distance Line Graph")
ax.grid(True, which='both', linestyle='--', linewidth=0.5)

x_data, y_data = [], []
line, = ax.plot(x_data, y_data, c='blue')
scat = ax.scatter([], [], c=[], cmap=custom_cmap, vmin=VMIN, vmax=VMAX)
fill = None
index = 0

# ---- Update function ----
def update(frame):
    global index, fill, recv_buffer, sock
    distance = None
    line_serial = None

    if sock:
        try:
            data = sock.recv(1024)
            if data:
                recv_buffer += data
                parts = recv_buffer.split(b'\n')
                if len(parts) > 1:
                    line_serial = parts[0].decode(errors='ignore').strip()
                    recv_buffer = b'\n'.join(parts[1:])
        except socket.timeout:
            line_serial = None
        except Exception:
            sock.close()
            sock = None
            line_serial = None

    if line_serial:
        try:
            distance = float(line_serial)
        except Exception:
            distance = None

    if distance is not None:
        x_data.append(index)
        y_data.append(distance)
        index += 1
        ax.set_xlim(max(0, index-100), index)
        line.set_data(x_data, y_data)

        if fill:
            fill.remove()

        if len(x_data) > 1:
            norm = plt.Normalize(VMIN, VMAX)
            cmap = custom_cmap
            polys, poly_colors = [], []
            for i in range(1, len(x_data)):
                poly = [
                    (x_data[i-1], 0),
                    (x_data[i-1], y_data[i-1]),
                    (x_data[i], y_data[i]),
                    (x_data[i], 0)
                ]
                polys.append(poly)
                poly_colors.append(cmap(norm(min(y_data[i-1], y_data[i]))))
            fill = PolyCollection(polys, facecolors=poly_colors, edgecolors='none', alpha=0.4)
            ax.add_collection(fill)

        scat.set_offsets(list(zip(x_data, y_data)))
        scat.set_array(np.array(y_data))

    return line, scat

# ---- Animate ----
ani = animation.FuncAnimation(fig, update, interval=50)
sm = plt.cm.ScalarMappable(cmap=custom_cmap, norm=plt.Normalize(vmin=VMIN, vmax=VMAX))
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, pad=0.02)
cbar.set_label('Distance (cm)')
cbar.set_ticks([VMIN, LOW_THRESH, HIGH_THRESH, VMAX])
cbar.set_ticklabels([f"{int(VMIN)}", f"{int(LOW_THRESH)}", f"{int(HIGH_THRESH)}", f"{int(VMAX)}"])
plt.show()
