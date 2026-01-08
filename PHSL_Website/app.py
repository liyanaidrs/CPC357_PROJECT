from flask import Flask, render_template, request, redirect, session, jsonify
from db import get_db_connection

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        )
        user = cursor.fetchone()
        cursor.close()
        db.close()
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect("/dashboard")
        return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        if not username or not password:
            return render_template("register.html", error="Username and password required")
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        if cursor.fetchone():
            cursor.close()
            db.close()
            return render_template("register.html", error="Username already exists")
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, password)
        )
        db.commit()
        cursor.close()
        db.close()
        return redirect("/")
    return render_template("register.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")
    active_tab = request.args.get("tab", "dashboard")
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Access logs (timestamps already in Malaysia time from MQTT)
    cursor.execute("SELECT rfid_uid, event, timestamp FROM access_logs ORDER BY timestamp DESC")
    logs = cursor.fetchall()

    # RFID cards
    cursor.execute("SELECT rfid_uid FROM rfid_cards WHERE user_id=%s", (session["user_id"],))
    cards = cursor.fetchall()

    # Door status
    cursor.execute("SELECT status FROM door_status WHERE id=1")
    row = cursor.fetchone()
    door_status = row["status"] if row else "LOCKED"

    # Stats
    access_granted = sum(1 for l in logs if l["event"] == "ACCESS_GRANTED")
    access_denied = sum(1 for l in logs if l["event"] == "ACCESS_DENIED")
    alert_low_battery = sum(1 for l in logs if l["event"] == "LOW_BATTERY")
    alert_after_hours = sum(1 for l in logs if l["event"] == "AFTER_HOURS_ACCESS")

    cursor.close()
    db.close()
    return render_template(
        "dashboard.html",
        logs=logs,
        cards=cards,
        door_status=door_status,
        access_granted=access_granted,
        access_denied=access_denied,
        alert_low_battery=alert_low_battery,
        alert_after_hours=alert_after_hours,
        active_tab=active_tab
    )

# ---------------- ADD RFID ----------------
@app.route("/add_rfid", methods=["POST"])
def add_rfid():
    if "user_id" not in session:
        return redirect("/")
    rfid = request.form["rfid"].strip()
    if not rfid:
        return redirect("/dashboard?tab=rfid")
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO rfid_cards (user_id, rfid_uid) VALUES (%s, %s)",
        (session["user_id"], rfid)
    )
    db.commit()
    cursor.close()
    db.close()
    return redirect("/dashboard?tab=rfid")

# ---------------- LIVE API ----------------
@app.route("/api/live/access_logs")
def live_access_logs():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT rfid_uid, event, timestamp FROM access_logs ORDER BY timestamp DESC")
    data = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(data)

@app.route("/api/live/alerts")
def live_alerts():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, rfid_uid, alert AS type, timestamp FROM door_alerts ORDER BY timestamp DESC LIMIT 5")
    alerts = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(alerts)

@app.route("/api/live/door_status")
def live_door_status():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT status FROM door_status WHERE id=1")
    status = cursor.fetchone()[0]
    cursor.close()
    db.close()
    return jsonify({"status": status})

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
