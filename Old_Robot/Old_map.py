import matplotlib
matplotlib.use("Qt5Agg")  # Use Qt backend
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import serial

# ---- Configure serial port ----
ser = serial.Serial('COM2', 9600, timeout=1)  # replace COM3 with your Arduino port

# ---- Set up plot ----
fig, ax = plt.subplots()
ax.set_xlim(0, 100)  # initial X-axis range (last 100 readings)
ax.set_ylim(0, 210)  # Y-axis = distance in cm
ax.set_xlabel("Reading Number")
ax.set_ylabel("Distance (cm)")
ax.set_title("Robot Live Distance Line Graph")

x_data, y_data = [], []
line, = ax.plot(x_data, y_data, c='blue')  # line object

index = 0

# ---- Update function ----
def update(frame):
    global index
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
        except:
            pass
    return line,

# ---- Animate ----
ani = animation.FuncAnimation(fig, update, interval=50)  # update every 200ms
plt.show()
