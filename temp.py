import socket
import folium
import threading
import time
import webbrowser
import os

coords = [0, 0]

def server():
    global coords
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("0.0.0.0", 5050))
    s.listen(1)
    print("Waiting for GPS data from ESP8266...")
    while True:
        conn, addr = s.accept()
        data = conn.recv(1024).decode().strip()
        conn.close()
        if data:
            try:
                lat, lon = map(float, data.split(","))
                coords = [lat, lon]
                print(f"Received: {coords}")
            except:
                pass

def map_updater():
    global coords
    last_coords = [0, 0]
    file_path = os.path.abspath("live_map.html")
    print("Map will open automatically once GPS data arrives.")
    while True:
        if coords != last_coords and coords != [0, 0]:
            m = folium.Map(location=coords, zoom_start=17)
            folium.Marker(coords, popup=f"Lat: {coords[0]}, Lon: {coords[1]}").add_to(m)
            m.save(file_path)
            webbrowser.open_new_tab(file_path)
            last_coords = coords
        time.sleep(3)

# Run server & map in parallel
threading.Thread(target=server, daemon=True).start()
map_updater()
