import matplotlib.pyplot as plt
import requests
import time

ip = "http://192.168.1.100"  # Replace with your ESP8266’s IP
data_points = []

plt.ion()
fig, ax = plt.subplots()

while True:
    try:
        response = requests.get(ip)
        distance = float(response.text.strip())
        data_points.append(distance)
        ax.clear()
        ax.plot(data_points, label="Distance (cm)")
        ax.legend()
        plt.pause(0.1)
    except:
        print("Waiting for data...")
        time.sleep(1)
