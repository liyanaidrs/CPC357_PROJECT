#include <SPI.h>
#include <MFRC522.h>
#include <Keypad.h>
#include <Adafruit_NeoPixel.h>
#include <WiFi.h>
#include <NTPClient.h>
#include <WiFiUdp.h>
#include <PubSubClient.h>

/* ================= WIFI ================= */
const char* ssid     = "NL";
const char* password = "haechan123";

/* ================= MQTT ================= */
const char* mqtt_server = "34.44.220.35";
const int mqtt_port = 1883;

const char* topic_uid   = "door/uid";
const char* topic_event = "door/event";

/* ================= TIME ================= */
const long utcOffsetInSeconds = 28800;
const int START_HOUR = 8;
const int END_HOUR   = 18;

/* ================= BATTERY ================= */
#define R1_VALUE 10000.0
#define R2_VALUE 1000.0
#define LOW_BAT_LIMIT 10.5

/* ================= PINS ================= */
#define SS_PIN      7
#define RST_PIN     4
#define TRIG_PIN    14
#define ECHO_PIN    21
#define RELAY_PIN   15
#define LED_YELLOW  5
#define BUZZER_PIN  6
#define RGB_PIN     46
#define POWER_PIN   11
#define BATTERY_PIN 1

/* ================= OBJECTS ================= */
MFRC522 rfid(SS_PIN, RST_PIN);
Adafruit_NeoPixel pixels(1, RGB_PIN, NEO_GRB + NEO_KHZ800);
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", utcOffsetInSeconds);
WiFiClient espClient;
PubSubClient client(espClient);

/* ================= KEYPAD ================= */
const byte ROWS = 4, COLS = 4;
char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};
byte rowPins[ROWS] = {47, 48, 38, 39};
byte colPins[COLS] = {40, 41, 42, 16};
Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

/* ================= VARIABLES ================= */
String correctPasscode = "4A5C";
String inputPasscode = "";

byte authorizedUIDs[2][4] = {
  {0x23, 0xFF, 0xAB, 0x14},
  {0xB0, 0xEA, 0xD5, 0x5F}
};

unsigned long lastRFID = 0;
const unsigned long rfidCooldown = 1000;
unsigned long lastBatteryCheck = 0;

/* ================= HELPERS ================= */
void setRGB(int r, int g, int b) {
  pixels.setPixelColor(0, pixels.Color(r, g, b));
  pixels.show();
}

void setLockState(bool unlocked) {
  if (unlocked) {
    pinMode(RELAY_PIN, OUTPUT);
    digitalWrite(RELAY_PIN, LOW);
  } else {
    pinMode(RELAY_PIN, INPUT);
  }
}

/* ---------- Key Press Feedback ---------- */
void signalKeyPress() {
  tone(BUZZER_PIN, 2000, 50);
  setRGB(0,0,255);
  delay(50);
  setRGB(0,0,0);
}

/* ---------- Ultrasonic Distance ---------- */
long getDistanceCM() {
  digitalWrite(TRIG_PIN, LOW); delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH); delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  if (duration == 0) return -1;
  return duration * 0.034 / 2;
}

/* ================= MQTT ================= */
void connectMQTT() {
  while (!client.connected()) {
    if (client.connect("ESP32_DoorLock")) {
      client.publish("door/status", "ESP32 Online");
    } else {
      delay(2000);
    }
  }
}

void publishUID(String uid) {
  client.publish(topic_uid, uid.c_str());
}

void publishEvent(String event) {
  client.publish(topic_event, event.c_str());
}

/* ================= ACCESS ================= */
void grantAccess() {
  publishEvent("ACCESS_GRANTED");
  setRGB(0,255,0);
  tone(BUZZER_PIN, 1000, 200);
  delay(200);
  tone(BUZZER_PIN, 2000, 200);

  setLockState(true);
  delay(15000);
  setLockState(false);

  setRGB(0,0,0);
  inputPasscode = "";

  // RFID stability fix
  rfid.PCD_Init();
  rfid.PCD_SetAntennaGain(rfid.RxGain_max);
}

void denyAccess() {
  publishEvent("ACCESS_DENIED");
  setRGB(255,0,0);
  tone(BUZZER_PIN, 200, 500);
  delay(500);
  tone(BUZZER_PIN, 150, 500);
  delay(1000);
  setRGB(0,0,0);
  inputPasscode = "";
}

/* ================= TIME CHECK ================= */
void checkTimeAndUnlock() {
  timeClient.update();
  int h = timeClient.getHours();

  if (h >= START_HOUR && h < END_HOUR) {
    grantAccess();
  } else {
    publishEvent("AFTER_HOURS_ACCESS");

    // Warning pattern
    for (int i=0;i<4;i++) {
      setRGB(255,140,0);
      tone(BUZZER_PIN, 2000, 100);
      delay(100);
      setRGB(0,0,0);
      delay(100);
    }
    grantAccess();
  }
}

/* ================= BATTERY ================= */
void checkBatteryHealth() {
  int raw = analogRead(BATTERY_PIN);
  float pinV = raw * (3.3 / 4095.0);
  float battV = pinV * ((R1_VALUE + R2_VALUE) / R2_VALUE);

  if (battV < LOW_BAT_LIMIT) {
    publishEvent("LOW_BATTERY");
    for (int i=0;i<3;i++) {
      digitalWrite(LED_YELLOW, HIGH);
      tone(BUZZER_PIN, 500, 300);
      delay(300);
      digitalWrite(LED_YELLOW, LOW);
      delay(300);
    }
  }
}

/* ================= SETUP ================= */
void setup() {
  Serial.begin(115200);

  pinMode(POWER_PIN, OUTPUT); digitalWrite(POWER_PIN, HIGH);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_YELLOW, OUTPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(RELAY_PIN, INPUT);
  pinMode(BATTERY_PIN, INPUT);
  analogReadResolution(12);

  pixels.begin();
  pixels.setBrightness(50);

  SPI.begin(17, 18, 8, SS_PIN);
  rfid.PCD_Init();
  rfid.PCD_SetAntennaGain(rfid.RxGain_max);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) delay(500);

  client.setServer(mqtt_server, mqtt_port);
  connectMQTT();

  timeClient.begin();
}

/* ================= LOOP ================= */
void loop() {
  if (!client.connected()) connectMQTT();
  client.loop();

  // Presence LED
  long distance = getDistanceCM();
  if (distance > 0 && distance < 20) digitalWrite(LED_YELLOW, HIGH);
  else digitalWrite(LED_YELLOW, LOW);

  if (millis() - lastBatteryCheck > 30000) {
    lastBatteryCheck = millis();
    checkBatteryHealth();
  }

  char key = keypad.getKey();
  if (key) {
    signalKeyPress();
    if (key == '*') inputPasscode = "";
    else inputPasscode += key;

    if (inputPasscode.length() == 4) {
      if (inputPasscode == correctPasscode) checkTimeAndUnlock();
      else denyAccess();
    }
  }

  if (millis() - lastRFID > rfidCooldown) {
    if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
      lastRFID = millis();

      String uidStr="";
      for (byte i=0;i<rfid.uid.size;i++)
        uidStr += String(rfid.uid.uidByte[i], HEX);
      uidStr.toUpperCase();
      publishUID(uidStr);

      bool match=false;
      for (int i=0;i<2;i++) {
        match=true;
        for (int j=0;j<4;j++)
          if (rfid.uid.uidByte[j]!=authorizedUIDs[i][j]) match=false;
        if (match) break;
      }

      rfid.PICC_HaltA();
      rfid.PCD_StopCrypto1();

      if (match) checkTimeAndUnlock();
      else denyAccess();
    }
  }
}
