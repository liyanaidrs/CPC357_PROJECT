# Predictive Hybrid Smart Lock (PHSL) 🔒

**Course:** CPC357 IoT Architecture & Smart Applications  
**University:** Universiti Sains Malaysia (USM)  
**Semester:** 2025/2026  

## 👥 Group Members
1. **Nurul Liyana Binti Idris** (160438)
2. **Nurin Farah Izzati Binti Muhd Rusdi** (160406)

---

## 📖 Overview

The **Predictive Hybrid Smart Lock (PHSL)** is an intelligent, context-aware access control system built on the **Cytron Maker Feather AIoT S3 (ESP32-S3)**. Unlike traditional locks, this system integrates **IoT connectivity**, **Dual-Factor Authentication** and **Predictive Logic** to create a secure and user-friendly experience.

It features a hybrid authentication model allowing users to unlock via **RFID Card** or **Secure PIN**. Besides locking, the system  uses an ultrasonic sensor to detect approaching users, syncs with NTP servers to detect **After-Hours** entries and continuously monitors its own **Battery Health** to prevent power failure lockouts.


---

## ✨ Key Features

* **🔐 Hybrid Authentication:** Unlocks via **RFID Card (MFRC522)** or **4-Digit PIN (Keypad)**.
* **☁️ Cloud Integration:** Logs all access events to a **Google Cloud SQL (MySQL)** database via MQTT.
* **🕒 Time-Aware Logic:** Detects entries outside usual hours (6 PM - 8 AM) and flags them as "After-Hours" warnings.
* **🔋 Smart Battery Monitor:** Alerts the user if the 12V battery drops below **10.5V**.
* **👋 Proximity Wake-Up:** Ultrasonic sensor detects users < 50cm and automatically lights up the interface.
* **🛡️ Hardware Safety:** Features an isolated Relay circuit with Flyback Diode protection for the high-voltage solenoid.

---

## 🛠️ Hardware Architecture

### Hardware Components
| Component | Function |
| :--- | :--- |
| **Cytron Maker Feather AIoT S3** | Main Microcontroller (ESP32-S3) |
| **RC522 RFID Reader** | Primary Authentication Input  |
| **4x4 Matrix Keypad** | Secondary Authentication Input  |
| **HC-SR04 Ultrasonic Sensor** | User Presence Detection |
| **12V Solenoid Lock** | Physical Locking Mechanism |
| **5V Relay Module** | Electromechanical Switch  |
| **LM2596 Buck Converter** | Voltage Regulation (12V $\to$ 5V) |
| **11.1V Li-Po Battery** | Main Power Source |
| **1N4007 Diode** | Flyback Protection for Solenoid |

### Pin Configuration
| Component | Pin Function | ESP32 GPIO |
| :--- | :--- | :--- |
| **RFID** | SDA / SCK / MOSI / MISO / RST | `7`, `17`, `8`, `18`, `4` |
| **Keypad (Rows)** | Row 1 - 4 | `47`, `48`, `38`, `39` |
| **Keypad (Cols)** | Col 1 - 4 | `40`, `41`, `42`, `16` |
| **Ultrasonic** | TRIG / ECHO | `14`, `21` |
| **Output** | Relay (Lock) | `15` |
| **Sensors** | Battery Voltage Divider | `1` |
| **Indicators** | External LED / Buzzer | `5`, `6` |

---

## 🔌 Wiring & Logic

**Critical Power Warning:** The Solenoid Lock runs on **12V**, while the ESP32 logic runs on **5V**. The system uses two isolated power loops joined only by the Relay and Common Ground.



1.  **Logic Loop:** Battery $\to$ LM2596 (5V Out) $\to$ ESP32.
2.  **Power Loop:** Battery (12V) $\to$ Relay COM $\to$ Solenoid $\to$ Battery GND.
3.  **Protection:** A **1N4007 Diode** is installed across the Solenoid terminals to prevent back-EMF spikes.

---

## 💻 Software Setup

### 1. Firmware (ESP32)
1.  Install **Arduino IDE** and the **ESP32 Board Manager**.
2.  Install Required Libraries: `MFRC522`, `Keypad`, `Adafruit_NeoPixel`, `PubSubClient`, `NTPClient`.
3.  Open `PHSL-project.ino` and update your Wi-Fi credentials.
4.  Update the `authorizedUIDs` array with your card IDs.
5.  Upload to the **Maker Feather AIoT S3**.

### 2. Cloud Proxy (Windows - Local Test)
1.  Open **PowerShell** in the project folder.
2.  Set Authentication:
    ```powershell
    $Env:GOOGLE_APPLICATION_CREDENTIALS="C:\Path\To\your-key.json"
    ```
3.  Start Proxy:
    ```powershell
    .\cloud-sql-proxy.exe "smiling-sweep-481702-g7:us-central1:assignment2"
    ```

### 3. Linux Environment (GCP - MQTT Listener)
1.  SSH into your Google Cloud VM.
2.  Start the **Cloud SQL Proxy** with port mapping:
    ```bash
    ./cloud_sql_proxy -instances=smiling-sweep-481702-g7:us-central1:assignment2=tcp:3307 \
    -credential_file=/home/inurin32/smiling-sweep-481702-g7-2b9b146d84fd.json &
    ```
3.  Activate Virtual Environment & Install Dependencies:
    ```bash
    source mqtt_env/bin/activate
    pip install paho-mqtt mysql-connector-python
    ```
4.  Run the **Middleware Service**:
    ```bash
    python3 mqtt_to_cloudsql.py
    ```

### 4. Flask Web Dashboard
1.  Open a new terminal session.
2.  Install Dependencies: `pip install flask mysql-connector-python`
3.  Run the Application:
    ```bash
    python app.py
    ```
4.  Access the dashboard via the external IP provided.

---

## 🚀 Usage Guide & Status Indicators

### 1. Operation Flow
* **Power On:** Connect the 12V battery. Internal LED turns **Solid Blue 🔵** (Wi-Fi Connected).
* **Approach:** Walk within 50cm. **External Yellow LED 🟡** lights up to guide.
* **Unlock:** Scan RFID or Enter PIN (`4A5C`).

### 2. Status Codes

| Indicator | Meaning | Description |
| :--- | :--- | :--- |
| **🟢 Green + Click** | **Access Granted** | Door unlocks for 3 seconds. |
| **🔴 Red + Long Beep** | **Access Denied** | Unauthorized credential or wrong PIN. |
| **🟠 Orange Flash** | **After-Hours Warning** | Valid entry detected outside operating hours (6 PM - 8 AM). Logged as warning. |
| **🟡 Slow Flash** | **Low Battery** | Battery voltage < 10.5V. |

--
## YouTube Video Link
**LINK PRESENTATION** : https://youtu.be/HZgPlNM76uY 
