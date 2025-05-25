from network import WLAN, LoRa
import socket
import time
import ujson
import usocket
import ussl

# Telegram settings
TELEGRAM_BOT_TOKEN = "7573961112:AAEEVFCbAC2lCh-hoVkmB_CeEUpBLtdr0t0"
TELEGRAM_CHAT_ID = 2026700667  # Ensure it's an integer

# 🔵 Startup
print("\U0001f535 Starting LoRa Gateway main.py...")

# WiFi config
WIFI_SSID = 'UPNET'
WIFI_PASS = 'UPkotIsTheBest1999'

print("\U0001f50c Connecting to WiFi...")
wlan = WLAN(mode=WLAN.STA)
wlan.connect(WIFI_SSID, auth=(WLAN.WPA2, WIFI_PASS), timeout=5000)
retry = 0
while not wlan.isconnected() and retry < 20:
    print("\u23f3 Waiting for WiFi...")
    time.sleep(1)
    retry += 1

if wlan.isconnected():
    ip = wlan.ifconfig()[0]
    print("\u2705 Connected to WiFi! IP:", ip)
else:
    raise RuntimeError("\u274c WiFi connection failed")

# LoRa setup
print("\U0001f4e1 Initializing LoRa...")
lora = LoRa(mode=LoRa.LORA, frequency=868100000,
            bandwidth=LoRa.BW_125KHZ, sf=7, coding_rate=LoRa.CODING_4_5)
lora_sock = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
lora_sock.setblocking(False)

# HTTP server
print("\U0001f310 Starting HTTP server...")
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
server = socket.socket()
server.bind(addr)
server.listen(1)
server.settimeout(0.1)
print("\U0001f680 HTTP server running at http://{}/".format(ip))

# Shared data for dashboard
latest_alert = ""
latest_sensor_data = {}

# Telegram Alert Sender (Updated to HTTP GET fallback method)
def send_telegram_alert(message):
    try:
        message = message.strip()
        if not message:
            print("⚠️ Skipping empty Telegram message.")
            return

        url = "https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}".format(
            TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message.replace(" ", "+"))

        _, _, host, path = url.split('/', 3)
        path = '/' + path

        s = usocket.socket()
        ai = usocket.getaddrinfo(host, 443)
        addr = ai[0][-1]
        s.connect(addr)
        s = ussl.wrap_socket(s)
        req = "GET {} HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n\r\n".format(path, host)
        s.write(req)
        print("📨 Telegram alert sent:", message)
        print(url)
        s.close()
    except Exception as e:
        print("❌ Telegram error:", e)

# Main loop
while True:
    now = time.ticks_ms()

    # 🔄 Check LoRa every 200ms
    try:
        lora_data = lora_sock.recv(256)
        if lora_data:
            try:
                decoded = ujson.loads(lora_data)
                if isinstance(decoded, dict) and "temp" in decoded and "hum" in decoded:
                    latest_sensor_data = decoded
                    print("🌡 PySense Data:", decoded)
                else:
                    latest_alert = str(decoded)
                    print("🚨 Alert Received:", latest_alert)
                    send_telegram_alert("📡 LoRa Alert: " + latest_alert)
            except Exception:
                print("⚠️ Raw LoRa Data:", lora_data)
    except:
        pass

    # 🔄 Check HTTP server
    try:
        client, addr = server.accept()
        print("🌐 HTTP from:", addr)
        request = client.recv(1024)

        # 🚨 Handle POST alert
        if b"POST /alert" in request:
            try:
                payload = request.split(b'\r\n\r\n', 1)[1]
                data = ujson.loads(payload)
                message = data.get('message', 'DANGER')
                message = message.strip()

                if message:
                    lora_sock.setblocking(True)
                    lora_sock.send(message)
                    lora_sock.setblocking(False)
                    print("📤 Alert sent over LoRa:", message)
                    send_telegram_alert("📢 HTTP Alert: " + message)

                client.send("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nOK")
            except Exception as e:
                print("❌ Alert handling error:", e)
                client.send("HTTP/1.1 400 Bad Request\r\n\r\nError")

        # 📊 Serve dashboard
        elif b"GET /dashboard" in request:
            html = """\
HTTP/1.1 200 OK\r
Content-Type: text/html\r
\r
<!DOCTYPE html>
<html>
<head><title>LoRa Dashboard</title></head>
<body>
<h1>🐾 LoRa Gateway Dashboard</h1>
<h2>🚨 Latest Alert:</h2>
<p>{}</p>
<h2>🌡 Sensor Data:</h2>
<p>Temperature: {} °C<br>Humidity: {} %</p>
</body>
</html>
""".format(
    latest_alert or "No alert received",
    latest_sensor_data.get("temp", "N/A"),
    latest_sensor_data.get("hum", "N/A")
)
            client.send(html)

        # 404 fallback
        else:
            client.send("HTTP/1.1 404 Not Found\r\n\r\n")

        client.close()

    except:
        pass

    time.sleep(0.1)
