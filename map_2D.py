import matplotlib
matplotlib.use("Qt5Agg")  # Use Qt backend
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import serial
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
args = parser.parse_args()

# ---- Configure serial port (unless simulating) ----
if args.simulate:
    ser = None
else:
    ser = serial.Serial(args.port, args.baud, timeout=1)  # replace COM3 with your Arduino port

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
    global index, fill
    distance = None
    # When simulating, generate a test waveform that sweeps between 0 and VMAX
    if ser is None:
        # simple periodic test pattern
        t = index
        # oscillate between 0 and VMAX using a sine wave scaled to the range
        distance = (VMAX / 2) * (1 + np.sin(0.1 * t))
    else:
        line_serial = ser.readline().decode().strip()
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
