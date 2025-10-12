import matplotlib
matplotlib.use("Qt5Agg")  # Use Qt backend
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import serial
import socket
import argparse
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# Note: serial port is opened later after parsing args so we can run in simulate mode

# Color mapping thresholds (cm)
LOW_THRESH = 25.0
HIGH_THRESH = 100.0
VMIN = 0.0
VMAX = 210.0

# Build a custom colormap: red for <=LOW_THRESH, blue for >=HIGH_THRESH,
# and a smooth gradient between LOW_THRESH and HIGH_THRESH.
_p1 = LOW_THRESH / VMAX
_p2 = HIGH_THRESH / VMAX
# Create a multi-stop colormap that goes: red -> orange -> yellow -> green -> cyan -> blue
# Anchor the color stops so values <= LOW_THRESH are solid red and >= HIGH_THRESH are solid blue.
stops = [
    (0.0, '#ff0000'),           # red at bottom
    (_p1, '#ff0000'),          # keep red through LOW_THRESH
    (_p1 + (_p2 - _p1) * 0.18, '#ff7f00'),
    (_p1 + (_p2 - _p1) * 0.36, '#ffff00'),
    (_p1 + (_p2 - _p1) * 0.56, '#7fff00'),
    (_p1 + (_p2 - _p1) * 0.74, '#00ffff'),
    (_p1 + (_p2 - _p1) * 0.90, '#1e90ff'),
    (_p2, '#0000ff'),          # blue at HIGH_THRESH
    (1.0, '#00008b')           # dark blue at top
]
custom_cmap = LinearSegmentedColormap.from_list('rainbow_custom', stops)

# ---- CLI options ----
parser = argparse.ArgumentParser()
parser.add_argument('--simulate', action='store_true', help='run with simulated distance data instead of reading serial COM port')
parser.add_argument('--port', default='COM4', help='serial port to open (ignored in --simulate)')
parser.add_argument('--baud', type=int, default=9600, help='serial baud rate')
parser.add_argument('--tcp', help='connect to TCP host:port instead of serial (e.g. 192.168.1.50:80)')
args = parser.parse_args()

# ---- Configure input source (serial / tcp / simulate) ----
# We support three modes:
#  - simulate (args.simulate)
#  - tcp (args.tcp, format host:port)
#  - serial (default)
ser = None
sock = None
recv_buffer = b''

if args.simulate:
    ser = None
    sock = None
else:
    if args.tcp:
        # parse host:port and try to connect
        try:
            host, port_s = args.tcp.split(':')
            port = int(port_s)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            try:
                sock.connect((host, port))
            except Exception:
                # Could not connect now; set sock to None and allow update() to retry or fall back
                try:
                    sock.close()
                except Exception:
                    pass
                sock = None
        except Exception:
            sock = None
        ser = None
    else:
        # try to open serial port; if it fails we leave ser=None so update() will simulate
        try:
            ser = serial.Serial(args.port, args.baud, timeout=1)
        except Exception:
            ser = None
        sock = None

# ---- Set up plot ----

fig, ax = plt.subplots(figsize=(12, 5))
ax.set_xlim(0, 100)  # initial X-axis range (last 100 readings)
ax.set_ylim(VMIN, VMAX)  # Y-axis = distance in cm
ax.set_yticks(range(int(VMIN), int(VMAX) + 1, 20))
ax.set_xlabel("Reading Number")
ax.set_ylabel("Distance (cm)")

ax.set_title("Robot Live Distance Line Graph")
ax.grid(True, which='both', linestyle='--', linewidth=0.5)


x_data, y_data = [], []
line, = ax.plot(x_data, y_data, c='blue')  # line object
# Scatter for colored points using the custom colormap
scat = ax.scatter([], [], c=[], cmap=custom_cmap, vmin=VMIN, vmax=VMAX)

# Fill area under the line with color gradient
from matplotlib.collections import PolyCollection
fill = None

index = 0

# ---- Update function ----


def update(frame):
    global index, fill, recv_buffer, sock, ser
    distance = None
    line_serial = None

    # First try socket (TCP) input if configured
    if sock is not None:
        try:
            data = sock.recv(1024)
            if data:
                recv_buffer += data
                parts = recv_buffer.split(b'\n')
                # If we have at least one full line, take the earliest complete line
                if len(parts) > 1:
                    # take first complete line
                    line_serial = parts[0].decode(errors='ignore').strip()
                    # keep the remainder (could contain more full lines)
                    recv_buffer = b'\n'.join(parts[1:])
                else:
                    line_serial = None
            else:
                line_serial = None
        except socket.timeout:
            line_serial = None
        except Exception:
            # On any socket error, stop using socket input
            try:
                sock.close()
            except Exception:
                pass
            sock = None
            line_serial = None

    # If no socket or no socket line, try serial
    if line_serial is None and ser is not None:
        try:
            line_serial = ser.readline().decode().strip()
        except Exception:
            line_serial = None

    # If neither socket nor serial provided data, and simulate is enabled (both ser and sock are None), generate waveform
    if sock is None and ser is None:
        t = index
        distance = (VMAX / 2) * (1 + np.sin(0.1 * t))
    else:
        if line_serial:
            try:
                distance = float(line_serial)
            except Exception:
                distance = None

    if distance is not None:
        try:
            x_data.append(index)
            y_data.append(distance)
            index += 1

            # Keep last 100 points visible
            ax.set_xlim(max(0, index-100), index)

            line.set_data(x_data, y_data)

            # Remove previous fill if exists
            if fill:
                fill.remove()

            # Create a color array for the fill (use same colormap as scatter)
            if len(x_data) > 1:
                norm = plt.Normalize(VMIN, VMAX)
                cmap = custom_cmap
                # For each segment, get the color for the lower y value
                colors = [cmap(norm(y)) for y in y_data]
                verts = [
                    [(x, 0), (x, y)] for x, y in zip(x_data, y_data)
                ]
                # PolyCollection expects a list of polygons, so we create vertical strips
                polys = []
                poly_colors = []
                for i in range(1, len(x_data)):
                    poly = [
                        (x_data[i-1], 0),
                        (x_data[i-1], y_data[i-1]),
                        (x_data[i], y_data[i]),
                        (x_data[i], 0)
                    ]
                    polys.append(poly)
                    # Color by the lower of the two y values (closer = red)
                    poly_colors.append(cmap(norm(min(y_data[i-1], y_data[i]))))
                fill = PolyCollection(polys, facecolors=poly_colors, edgecolors='none', alpha=0.4)
                ax.add_collection(fill)

            # Update scatter with color mapping: low=red, high=blue
            scat.set_offsets(list(zip(x_data, y_data)))
            scat.set_array(np.array(y_data))
        except Exception:
            pass
    return line, scat

# ---- Animate ----
ani = animation.FuncAnimation(fig, update, interval=50)
# Add colorbar legend
sm = plt.cm.ScalarMappable(cmap=custom_cmap, norm=plt.Normalize(vmin=VMIN, vmax=VMAX))
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, pad=0.02)
cbar.set_label('Distance (cm)')
# Mark threshold ticks on the colorbar
cbar.set_ticks([VMIN, LOW_THRESH, HIGH_THRESH, VMAX])
cbar.set_ticklabels([f"{int(VMIN)}", f"{int(LOW_THRESH)}", f"{int(HIGH_THRESH)}", f"{int(VMAX)}"])
plt.show()
