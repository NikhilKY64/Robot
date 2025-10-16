import matplotlib
matplotlib.use("Qt5Agg")  # Use Qt backend
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import serial
import numpy as np

# ---- Configure serial port ----
ser = serial.Serial('COM2', 9600, timeout=1)  # replace COM3 with your Arduino port

# ---- Set up plot ----

fig, ax = plt.subplots(figsize=(12, 5))
ax.set_xlim(0, 100)  # initial X-axis range (last 100 readings)
ax.set_ylim(0, 210)  # Y-axis = distance in cm
ax.set_yticks(range(0, 201, 20))
ax.set_xlabel("Reading Number")
ax.set_ylabel("Distance (cm)")

ax.set_title("Robot Live Distance Line Graph")
ax.grid(True, which='both', linestyle='--', linewidth=0.5)


x_data, y_data = [], []
line, = ax.plot(x_data, y_data, c='blue')  # line object
# Scatter for colored points
scat = ax.scatter([], [], c=[], cmap='jet_r', vmin=0, vmax=210)

# Fill area under the line with color gradient
from matplotlib.collections import PolyCollection
fill = None

index = 0

# ---- Update function ----


def update(frame):
    global index, fill
    line_serial = ser.readline().decode().strip()
    if line_serial:
        try:
            distance = float(line_serial)
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
                norm = plt.Normalize(0, 210)
                cmap = plt.get_cmap('jet_r')
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
sm = plt.cm.ScalarMappable(cmap='jet_r', norm=plt.Normalize(vmin=0, vmax=210))
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, pad=0.02)
cbar.set_label('Distance (cm)')
plt.show()
