from network import WLAN, LoRa
import socket
import time
import ujson

# 🟢 Start
print("🟢 LoRa Receiver with HTTP started")

# --- Connect to Wi-Fi ---
WIFI_SSID = 'UPNET'
WIFI_PASS = 'UPkotIsTheBest1999'

print("🔌 Connecting to WiFi...")
wlan = WLAN(mode=WLAN.STA)
wlan.connect(WIFI_SSID, auth=(WLAN.WPA2, WIFI_PASS), timeout=5000)

retry = 0
while not wlan.isconnected() and retry < 20:
    time.sleep(1)
    retry += 1
    print("⏳ Waiting for WiFi...")

if wlan.isconnected():
    ip = wlan.ifconfig()[0]
    print("✅ Connected to WiFi! IP:", ip)
else:
    raise RuntimeError("❌ WiFi failed")

# --- Setup LoRa Receiver ---
print("📡 Initializing LoRa (receiver)...")
lora = LoRa(mode=LoRa.LORA, frequency=868100000, bandwidth=LoRa.BW_125KHZ, sf=7, coding_rate=LoRa.CODING_4_5)
lora_sock = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
lora_sock.setblocking(False)

# --- Optional: HTTP Server (still works) ---
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
server = socket.socket()
server.bind(addr)
server.listen(1)
print("🌐 HTTP server on http://{}/".format(ip))

# --- Main loop ---
while True:
    # 🔁 LoRa receiving
    try:
        data = lora_sock.recv(256)
        if data:
            try:
                decoded = ujson.loads(data)
                print("📥 LoRa received:", decoded)
            except Exception as e:
                print("⚠️ Received non-JSON:", data)
    except Exception:
        pass

    # 🛠 Optional: still handle POSTs if you want Flask to send alerts
    try:
        client, addr = server.accept()
        request = client.recv(1024)

        if b"POST /alert" in request:
            client.send("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nOK")
        else:
            client.send("HTTP/1.1 404 Not Found\r\n\r\n")

        client.close()
    except:
        pass

    time.sleep(1)
