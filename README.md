# CPC357 PROJECT

**Course:** CPC357 IoT Architecture & Smart Applications  
**University:** Universiti Sains Malaysia (USM)  
**Semester:** 2025/2026  

## 👥 Group Members
1. **Nurul Liyana Binti Idris** (160438)
2. **Nurin Farah Izzati Binti Muhd Rusdi** (160406)

# Predictive Hybrid Smart Lock (PHSL) 🔒
A smart, dual-factor authentication security system built with the **ESP32-S3 (Cytron Maker Feather)**. This system integrates RFID and PIN code authentication with ultrasonic presence detection to control a high-voltage solenoid lock mechanism.

![Platform](https://img.shields.io/badge/Platform-ESP32-blue)
![Language](https://img.shields.io/badge/Language-C%2B%2B%20%2F%20Arduino-orange)

## 📖 Overview

The **Predictive Hybrid Smart Lock** is designed to provide secure, contactless access control. It features a "hybrid" authentication model, allowing users to unlock the door using either an authorized RFID card or a secure PIN code. The system also includes proximity awareness using an ultrasonic sensor to light up feedback LEDs when a user approaches.

### Key Features
* **Dual Authentication:** Unlocks via **RFID Card (MFRC522)** or **4-Digit PIN (Keypad)**.
* **Proximity Awareness:** Ultrasonic sensor detects users < 50cm and activates the guidance light.
* **Visual & Audio Feedback:** RGB LED (Green/Red) and Buzzer provide status indicators for Access Granted/Denied.
* **High-Voltage Control:** Safely controls a 12V Solenoid Lock via an optically isolated Relay Module.
* **Safety Protection:** Integrated flyback diode to protect electronics from voltage spikes.

---

## 🛠️ Hardware Architecture

### Bill of Materials (BOM)
| Component | Function |
| :--- | :--- |
| **Cytron Maker Feather AIoT S3** | Main Microcontroller (ESP32-S3) |
| **RC522 RFID Reader** | Primary Authentication Input (SPI) |
| **4x4 Matrix Keypad** | Secondary Authentication Input (Digital) |
| **HC-SR04 Ultrasonic Sensor** | User Presence Detection |
| **12V Solenoid Lock** | Physical Locking Mechanism |
| **5V Relay Module** | Electromechanical Switch for Solenoid |
| **LM2596 Buck Converter** | Voltage Regulation (12V $\to$ 5V) |
| **11.1V Li-Po Battery** | Main Power Source |
| **1N4007 Diode** | Flyback Protection for Solenoid |

### Pin Configuration
| Component | Pin Function | ESP32 GPIO |
| :--- | :--- | :--- |
| **RFID** | SDA (SS) / SCK / MOSI / MISO / RST | `7`, `17`, `8`, `18`, `4` |
| **Keypad (Rows)** | Row 1 - 4 | `47`, `48`, `38`, `39` |
| **Keypad (Cols)** | Col 1 - 4 | `40`, `41`, `42`, `16` |
| **Ultrasonic** | TRIG / ECHO | `14`, `21` |
| **Output** | Relay (Lock) | `13` |
| **Indicators** | External LED /  Buzzer | `5`, `12` |
| **Internal** | RGB Data / Power | `46`, `11` |

---

## 🔌 Wiring Diagram

**Critical Power Warning:** The Solenoid Lock runs on **12V**, but the ESP32 runs on **5V**. These two voltage domains are isolated by the Relay.

* **Logic Side:** Battery $\to$ LM2596 (Step down to 5V) $\to$ ESP32.
* **Power Side:** Battery (12V) $\to$ Relay COM $\to$ Solenoid $\to$ Battery GND.
* **Protection:** A Flyback Diode is placed across the Solenoid terminals.

---

## 💻 Software Setup

### Prerequisites
1.  Install **Arduino IDE**.
2.  Install the **ESP32 Board Manager** (by Espressif Systems).
3.  Install Required Libraries:
    * `MFRC522` (by GithubCommunity)
    * `Keypad` (by Mark Stanley, Alexander Brevig)
    * `Adafruit_NeoPixel` (by Adafruit)

### Configuration
1.  Open `PHSL.ino`.
2.  Update the **Authorized UIDs** array with your specific RFID card IDs:
    ```cpp
    byte authorizedUIDs[2][4] = {
      {0xDE, 0xAD, 0xBE, 0xEF}, // Card 1
      {0xCA, 0xFE, 0xBA, 0xBE}  // Card 2
    };
    ```
3.  Set your desired **PIN Code**:
    ```cpp
    String correctPasscode = "1234";
    ```
4.  Upload to the **Maker Feather AIoT S3**.

---

## 🚀 Usage Guide

1.  **Power On:** Connect the 12V battery. The internal LED will turn Blue (Idle).
2.  **Approach:** Walk towards the system. If you are within 50cm, the Yellow LED will light up.
3.  **Unlock Method A (RFID):** Tap your card.
    * *Success:* Green LED + Beep + "Click" (Door Unlocks for 3s).
    * *Fail:* Red LED + Long Beep.
4.  **Unlock Method B (PIN):** Type your 4-digit code.
    * *Success:* Green LED + Beep + "Click".
    * *Fail:* Red LED + Long Beep.



