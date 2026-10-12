#include <Arduino.h>
#include <ESP32Servo.h>

// ---------------- MOTOR PINS (L298N) ----------------
const int ENA = 25;
const int IN1 = 26;
const int IN2 = 27;

const int ENB = 14;
const int IN3 = 12;
const int IN4 = 13;

// ---------------- ULTRASONIC ----------------
const int TRIG_PIN = 33;
const int ECHO_PIN = 32;

// ---------------- SERVO ----------------
Servo headServo;
const int HEAD_SERVO_PIN = 19;

Servo mouthServo;
const int MOUTH_SERVO_PIN = 18; // Changed from 13 (in use by IN4) to 18

// CALIBRATION
int SERVO_STOP  = 87;   // your perfect stop value
int SERVO_SPEED = 10;   // speed of rotation

int mouthClosePos = 160;  // User calibrated max close
int mouthOpenPos  = 225;  // User calibrated open (increased slightly from 210 for wider mouth)

// 🧠 Movement timing (controls angle)
int HEAD_MOVE_TIME = 300; // ms → adjust for small/large turn

// ---------------- VARIABLES ----------------
int motorSpeed = 240;
unsigned long lastDistanceSend = 0;

// Mouth control variables
bool isTalking = false;
unsigned long lastMouthMove = 0;
bool mouthIsOpen = false;
int MOUTH_FLAP_INTERVAL = 200; // ms for open/close cycle

// ---------------- SETUP ----------------
void setup() {
  Serial.begin(9600);

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  // ✅ ESP32 PWM (CORE 3.x)
  ledcAttach(ENA, 5000, 8);
  ledcAttach(ENB, 5000, 8);

  // ✅ SERVO SETUP
  ESP32PWM::allocateTimer(3);
  headServo.setPeriodHertz(50);
  headServo.attach(HEAD_SERVO_PIN, 600, 2500);

  mouthServo.setPeriodHertz(50);
  mouthServo.attach(MOUTH_SERVO_PIN, 600, 2500);

  delay(500);
  headServo.write(SERVO_STOP); // stop at boot
  mouthServo.write(mouthClosePos); // start with mouth closed

  stopMotors();
  Serial.println("VAANI READY");
}

// ---------------- LOOP ----------------
void loop() {
  handleSerialCommands();

  if (millis() - lastDistanceSend > 500) {
    float dist = readDistanceCM();
    Serial.print("DIST:");
    Serial.println(dist);
    lastDistanceSend = millis();
  }

  // Handle continuous mouth movement if talking (non-blocking)
  if (isTalking) {
    if (millis() - lastMouthMove > MOUTH_FLAP_INTERVAL) {
      mouthIsOpen = !mouthIsOpen;
      if (mouthIsOpen) {
        // Randomize mouth opening for more natural lip-sync look (between 190 and 225)
        int dynamicOpenPos = random(190, 225); 
        mouthServo.write(dynamicOpenPos);
      } else {
        // Sometimes don't close all the way for fluid speech (around 160)
        int dynamicClosePos = random(155, 165);
        mouthServo.write(dynamicClosePos);
      }
      // Randomize flap interval slightly for natural speech cadence
      MOUTH_FLAP_INTERVAL = random(120, 250);
      lastMouthMove = millis();
    }
  }
}

// ---------------- COMMAND HANDLER ----------------
void handleSerialCommands() {
  if (!Serial.available()) return;

  String cmd = Serial.readStringUntil('\n');
  cmd.trim();

  // -------- MOTOR --------
  if (cmd == "MOVE_FORWARD") moveForward();
  else if (cmd == "MOVE_BACKWARD") moveBackward();
  else if (cmd == "TURN_LEFT") turnLeft();
  else if (cmd == "TURN_RIGHT") turnRight();
  else if (cmd == "STOP") stopMotors();

  else if (cmd.startsWith("SPEED:")) {
    motorSpeed = constrain(cmd.substring(6).toInt(), 0, 255);
  }

  // -------- HEAD (HUMAN-LIKE) --------
  else if (cmd == "HEAD_LEFT") {
    headLeft();
  }
  else if (cmd == "HEAD_RIGHT") {
    headRight();
  }
  else if (cmd == "HEAD_STOP") {
    headStop();
  }

  // -------- MOUTH --------
  else if (cmd == "MOUTH_TALK") {
    isTalking = true;
  }
  else if (cmd == "MOUTH_STOP") {
    isTalking = false;
    mouthServo.write(mouthClosePos);
  }
  else if (cmd == "MOUTH_OPEN") {
    isTalking = false;
    mouthServo.write(mouthOpenPos);
  }
  else if (cmd == "MOUTH_CLOSE") {
    isTalking = false;
    mouthServo.write(mouthClosePos);
  }

  // 🔧 live tuning
  else if (cmd.startsWith("HEAD_TRIM:")) {
    SERVO_STOP = cmd.substring(10).toInt();
    headServo.write(SERVO_STOP);
  }
}

// ---------------- MOTOR FUNCTIONS ----------------
void moveForward() {
  ledcWrite(ENA, motorSpeed);
  ledcWrite(ENB, motorSpeed);

  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
}

void moveBackward() {
  ledcWrite(ENA, motorSpeed);
  ledcWrite(ENB, motorSpeed);

  digitalWrite(IN1, LOW); digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW); digitalWrite(IN4, HIGH);
}

void turnLeft() {
  ledcWrite(ENA, motorSpeed);
  ledcWrite(ENB, motorSpeed);

  digitalWrite(IN1, LOW);  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
}

void turnRight() {
  ledcWrite(ENA, motorSpeed);
  ledcWrite(ENB, motorSpeed);

  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);  digitalWrite(IN4, HIGH);
}

void stopMotors() {
  digitalWrite(IN1, LOW); digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW); digitalWrite(IN4, LOW);

  ledcWrite(ENA, 0);
  ledcWrite(ENB, 0);
}

// ---------------- HEAD FUNCTIONS ----------------
void headLeft() {
  headServo.write(SERVO_STOP - SERVO_SPEED);
  delay(HEAD_MOVE_TIME);       // rotate a bit
  headServo.write(SERVO_STOP); // stop
}

void headRight() {
  headServo.write(SERVO_STOP + SERVO_SPEED);
  delay(HEAD_MOVE_TIME);       // rotate a bit
  headServo.write(SERVO_STOP); // stop
}

void headStop() {
  headServo.write(SERVO_STOP);
}

// ---------------- ULTRASONIC ----------------
float readDistanceCM() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  if (duration == 0) return -1;

  return duration * 0.0343 / 2.0;
}