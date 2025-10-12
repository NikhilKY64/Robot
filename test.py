import serial
try:
    ser = serial.Serial('COM2', 9600, timeout=1)
    print("✅ Port opened successfully!")
    ser.close()
except Exception as e:
    print("❌ Failed to open port:", e)
