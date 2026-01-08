import paho.mqtt.client as mqtt
import mysql.connector
from datetime import datetime, timedelta, timezone

# ================= MQTT CONFIG =================
MQTT_BROKER = "34.44.220.35"
MQTT_PORT = 1883
MQTT_TOPIC = "door/#"

# ================= DATABASE CONFIG =================
DB_HOST = "127.0.0.1"
DB_PORT = 3307
DB_USER = "nurin"
DB_PASSWORD = "Farah@2021"
DB_NAME = "rfid_db"

# ================= DATABASE CONNECT =================
db = mysql.connector.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)
cursor = db.cursor()
print("✅ Connected to Cloud SQL database")

# ================= STATE =================
last_uid = None
last_uid_time = None
UID_VALID_SECONDS = 10

# ================= TIMEZONE =================
# Malaysia is UTC+8
MALAYSIA_TZ = timezone(timedelta(hours=8))

# ================= MQTT CALLBACKS =================
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("✅ Connected to MQTT broker")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"❌ MQTT connection failed: {reason_code}")

def on_message(client, userdata, msg):
    global last_uid, last_uid_time

    topic = msg.topic
    payload = msg.payload.decode().strip()
    print(f"📩 MQTT | {topic} → {payload}")

    # ---------- Door status ----------
    if topic == "door/status":
        if payload in ["LOCKED", "UNLOCKED"]:
            cursor.execute(
                "UPDATE door_status SET status=%s WHERE id=1",
                (payload,)
            )
            db.commit()
            print(f"🔐 Door status updated: {payload}")
        return

    # ---------- RFID UID ----------
    if topic == "door/uid":
        last_uid = payload
        last_uid_time = datetime.now(MALAYSIA_TZ)
        print(f"🪪 UID stored: {last_uid}")
        return

    # ---------- Door events & alerts ----------
    malaysia_time = datetime.now(MALAYSIA_TZ)
    timestamp_str = malaysia_time.strftime("%Y-%m-%d %H:%M:%S")  # store Malaysia time

    # ALERTS: always store
    if payload in ["LOW_BATTERY", "AFTER_HOURS_ACCESS"]:
        cursor.execute(
            "INSERT INTO door_alerts (rfid_uid, alert, timestamp) VALUES (%s, %s, %s)",
            (last_uid if last_uid else "UNKNOWN", payload, timestamp_str)
        )
        db.commit()
        print(f"⚠ Alert logged: {payload} ({last_uid if last_uid else 'UNKNOWN'})")
        return

    # ACCESS EVENTS: only if UID valid
    if not last_uid or not last_uid_time:
        print("⚠️ Event ignored (no UID)")
        return

    if (datetime.now(MALAYSIA_TZ) - last_uid_time).seconds > UID_VALID_SECONDS:
        print("⚠️ UID expired")
        last_uid = None
        return

    # Insert into access_logs
    cursor.execute(
        "INSERT INTO access_logs (rfid_uid, event, timestamp) VALUES (%s, %s, %s)",
        (last_uid, payload, timestamp_str)
    )
    db.commit()
    print(f"✅ Logged {payload} for UID {last_uid}")

# ================= MQTT CLIENT =================
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

print("🔄 Connecting to MQTT broker...")
client.connect(MQTT_BROKER, MQTT_PORT, 60)

print("🚀 MQTT listener started")
client.loop_forever()
