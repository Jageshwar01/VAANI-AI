# 🤖 VaaniAI — Autonomous Humanoid Robot

<div align="center">

**An AI-powered humanoid robot that can see, hear, speak, recognise faces, conduct interviews, and control its own physical body — built solo by a B.Tech student with limited budget and locally sourced materials.**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-black?style=for-the-badge&logo=ai&logoColor=white)](https://ollama.com)
[![OpenCV](https://img.shields.io/badge/OpenCV-Vision-green?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org)
[![Whisper](https://img.shields.io/badge/Whisper-STT-orange?style=for-the-badge&logo=openai&logoColor=white)](https://github.com/SYSTRAN/faster-whisper)
[![ESP32](https://img.shields.io/badge/ESP32-Hardware-red?style=for-the-badge&logo=espressif&logoColor=white)](https://espressif.com)

</div>

---

## 📸 Photos

<div align="center">
<img width="300" alt="VaaniAI Robot Front" src="https://github.com/user-attachments/assets/86cffcc4-71e5-40e0-8492-7380fb6152a2" />
&nbsp;&nbsp;&nbsp;
<img width="300" alt="VaaniAI Robot Full" src="https://github.com/user-attachments/assets/b757b9dd-8d7e-40f7-a6bf-2f0ff852969e" />
</div>
📺Youtube Link - https://youtube.com/shorts/EdLEBuQuxb8?feature=share
---

## 🌟 What is VaaniAI?

VaaniAI is a humanoid robot I built completely alone — no team, no lab, no sponsorship.

She moves on a 4-wheel chassis, detects nearby people, recognises their faces, and starts talking — either conducting a structured interview or holding a natural conversation depending on the mode.

She is dressed in a real human costume. When you stand in front of her, it does not feel like a machine. It feels like someone is actually there.

The goal was simple — build something that shows what AI and robotics can do together in the real world, not just on paper.

### What makes VaaniAI special?

- 🧠 **Fully Offline AI** — No cloud APIs, no data leaks. Everything runs locally via Ollama.
- 👁️ **Sees & Remembers Faces** — Auto-enrolls new people and greets them by name next time.
- 🗣️ **Hears & Speaks Naturally** — Whisper AI for hearing + Edge-TTS/Offline voice for speaking.
- 🦾 **Real Physical Body** — Controls motors, servos, and mouth movement via ESP32/Arduino.
- 🎓 **Presentation Mode** — Autonomously delivers a full university presentation.
- 🧪 **Interview Mode** — Conducts structured interviews and generates performance reports.

---

## 🎯 Two Core Modes

### 🤝 Social Mode
Vaani detects your face, greets you by name, tracks your movement with her head, and holds a natural multi-turn conversation. Supports English, Hindi, and Odia.

### 🎯 Interview Mode
Right now, there is no physical robot in India that conducts interviews.
VaaniAI fills that gap.

She sits in front of you like a real interviewer — asks questions, listens to your answers, evaluates them using AI, and generates a full feedback report with scores for communication, technical knowledge, and confidence.

Students can practice interviews with a robot that actually responds. No screen. No app. A real face-to-face experience.

---

## ✨ Core Features

### 🧠 AI & NLP
| Feature | Description |
|---|---|
| **Local LLM** | Powered by Ollama with dual-model architecture (Fast: `qwen2:0.5b`, Smart: `phi3:mini`) |
| **Knowledge Base (RAG)** | Reads `.txt` files from `data/knowledge/` and injects facts into AI context — no retraining needed |
| **Emotional Personality** | Custom system prompts create human-like speech with vocal expressions |
| **Memory System** | SQLite-backed memory remembers past conversations, enrolled faces, and relationships |
| **Intent Classifier** | Fuzzy-matching NLP engine classifies voice commands with 82%+ confidence threshold |
| **Presentation Mode** | Detects keywords like *"introduce yourself"* and delivers a full scripted speech |

### 🗣️ Voice — Hearing & Speaking
| Feature | Description |
|---|---|
| **Speech-to-Text** | `faster-whisper` with 5-layer anti-hallucination pipeline |
| **Custom Vocabulary** | Loads `data/vocabulary.txt` to properly hear Indian names and technical terms |
| **Command Queue** | Thread-safe queue ensures no voice command is silently dropped |
| **Text-to-Speech** | Edge-TTS (online, natural Indian female voice) with fallback to pyttsx3 (offline) |
| **Multilingual** | English, Hindi (Devanagari), and Odia with automatic language detection |

### 👁️ Computer Vision
| Feature | Description |
|---|---|
| **Face Recognition** | Real-time face detection and identification using `face_recognition` library |
| **Auto-Enrollment** | Silently captures and enrolls new faces in a 3-second background thread |
| **Face Stability Buffer** | Requires 4 consecutive identical frames before triggering mode switch |
| **Head Tracking** | Automatically moves head servo to follow the detected face position |

### 🦾 Hardware & Movement
| Feature | Description |
|---|---|
| **Serial Bridge** | Thread-safe PySerial communication with auto-reconnection and heartbeat monitoring |
| **Motor Control** | Forward, backward, left, right with configurable speed and auto-stop timeout |
| **Servo Control** | Head servo for tracking, mouth servo for lip-sync during speech |
| **Micro-Animations** | Continuous idle movements to make the robot feel alive |
| **Ultrasonic Sensor** | Detects a person at 1 meter and stops automatically |

---

## 📊 Honest Project Status

| Component | Status |
|---|---|
| 4-foot Robot Body | ✅ Done |
| 4-Wheel Chassis + DC Motors | ✅ Done |
| Human-like Costume & Appearance | ✅ Done |
| Arduino Motor Control | ✅ Done |
| Camera + Face Detection | ✅ Done |
| Voice Recognition | ✅ Done |
| Text to Speech | ✅ Done |
| Ultrasonic Sensor | ✅ Done |
| Interview Mode | ✅ Done |
| Social Conversation Mode | ✅ Done |
| Admin Control System | ✅ Done |
| Raspberry Pi Integration | ✅ Done |
| Emotion Detection | 🔄 In Development |
| Full AI Conversation Upgrade | 🔄 In Development |
| Cloud AI Integration | 🔄 Planned |
| Mobile App Control | 🔄 Planned |

> This is a solo project built with limited resources. Every component listed as done is physically working. The robot is real — not just a concept.

---

## 📂 Project Structure

```text
VaaniAi/
├── app/                          # Application entry point & configuration
│   ├── main.py                   # Main brain loop — start here
│   ├── config.py                 # All tunable settings (models, ports, thresholds)
│   └── requirements.txt          # Python dependencies
│
├── core/                         # Central Brain & Intelligence
│   ├── brain.py                  # Main orchestrator — connects all modules
│   ├── intent_classifier.py      # NLP intent detection with fuzzy matching
│   ├── mode_manager.py           # State machine (Idle/Social/Admin/Interview)
│   ├── state_manager.py          # Persistent state tracking
│   ├── command_router.py         # Routes classified intents to actions
│   └── event_bus.py              # Inter-module event communication
│
├── ai/                           # AI & Language Models
│   ├── conversation/             # Chat engine, personality, prompt builder
│   ├── knowledge/                # RAG Knowledge Base
│   ├── memory/                   # Conversation memory manager
│   ├── interview/                # Interview question engine & scoring
│   └── vision_ai/                # AI-powered vision analysis
│
├── voice/                        # Voice I/O Engines
│   ├── speech_to_text.py         # Whisper STT with 5-layer hallucination filter
│   └── text_to_speech.py         # Edge-TTS (online) + pyttsx3 (offline)
│
├── vision/                       # Computer Vision
│   ├── camera.py                 # Threaded OpenCV camera manager
│   ├── face_engine.py            # Face recognition & identification
│   └── face_enrollment.py        # Auto-enrollment with background capture
│
├── robot/                        # Hardware Interface
│   ├── hardware_bridge/
│   │   └── serial_bridge.py      # Thread-safe PySerial with auto-reconnect
│   └── movement/
│       ├── motor_controller.py   # Motor commands
│       ├── head_controller.py    # Servo-based head tracking
│       └── distance_keeper.py    # Ultrasonic distance safety system
│
├── firmware/                     # Microcontroller Code
│   ├── arduino/                  # Arduino firmware for motor/servo control
│   └── esp32/                    # ESP32 firmware variant
│
├── database/                     # Data Persistence
│   └── db.py                     # SQLite manager for people, memories, sessions
│
├── ui/                           # User Interface
│   └── screen_manager.py         # Flask-based web UI for robot face display
│
├── data/                         # Runtime Data
│   ├── known_faces/              # Enrolled face encodings (.pkl files)
│   ├── knowledge/                # Knowledge base text files (RAG)
│   ├── vocabulary.txt            # Custom STT vocabulary for Indian names
│   ├── question_sets/            # Interview question banks
│   └── reports/                  # Generated interview reports
│
├── tests/                        # Test Suite
├── docs/                         # Documentation
└── assets/                       # Static assets (images, sounds)
```

---

## 🛠️ Installation & Setup

### Prerequisites

| Requirement | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Core runtime |
| Ollama | Latest | Local LLM server |
| Webcam | Any USB | Face recognition |
| Microphone | Any | Speech input |
| ESP32/Arduino | Optional | Physical hardware control |
| CMake + C++ Build Tools | Latest | Required by `face_recognition` library |

### Step 1: Clone & Create Virtual Environment

```bash
git clone https://github.com/Jageshwar01/VAANI-AI.git
cd VAANI-AI

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r app/requirements.txt
```

### Step 3: Setup Ollama Models

```bash
# Install Ollama from https://ollama.com

ollama pull qwen2:0.5b       # Fast model (352 MB) — casual chat
ollama pull phi3:mini         # Smart model (2.2 GB) — presentations, interviews
```

### Step 4: Configure

Edit `app/config.py` to match your setup:

```python
ROBOT_NAME = "VaaniAI"
OWNER_NAME = "Jageshwer"

USE_HARDWARE = True
SERIAL_PORT = "COM5"          # Windows: COM5, Linux: /dev/ttyUSB0

FAST_AI_MODEL = "qwen2:0.5b"
SMART_AI_MODEL = "phi3:mini"

USE_VOICE_INPUT = True
USE_TTS = True
USE_CAMERA = True
```

### Step 5: Add Custom Knowledge (Optional)

Add `.txt` files to `data/knowledge/` to teach the robot custom facts:

```text
# Example: data/knowledge/university.txt
Sarala Birla University is located in Ranchi, Jharkhand, India.
```

---

## 🚀 Running VaaniAI

```bash
# Start Ollama
ollama serve

# Launch the robot
python app/main.py
```

### Boot Sequence

```text
[STT] Loading Whisper AI model...
[KNOWLEDGE] Loaded 37 facts from 3 files.
Loaded 4 known faces.
Camera started successfully (threaded).
[INFO] Serial connected on COM5
[STT] Calibrating noise (2 sec)...
[AI] Brain ready! ✅
VaaniAI: Good to see you! I am awake and ready.
```

### Voice Commands

| Say This | Robot Does |
|---|---|
| *"Hello"* / *"How are you?"* | Enters social conversation mode |
| *"Move forward"* / *"Go back"* | Moves the physical body |
| *"Turn left"* / *"Turn right"* | Rotates the body |
| *"Give your presentation"* | Delivers a 1-minute scripted speech |
| *"Start interview"* | Begins structured interview mode |
| *"Switch to Hindi"* | Changes language to Hindi |
| *"Enroll person"* | Starts face enrollment |
| *"Stop"* | Stops all movement |
| *"Shutdown"* | Gracefully shuts down |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    VaaniAI Brain                     │
│                   (core/brain.py)                    │
├──────────┬──────────┬──────────┬────────────────────┤
│  👁️ See   │  🗣️ Hear  │  🧠 Think │  🦾 Move           │
│  OpenCV  │  Whisper │  Ollama  │  Serial Bridge     │
│  Face ID │  STT     │  LLM     │  ESP32/Arduino     │
│  Track   │  Queue   │  RAG     │  Motors + Servos   │
├──────────┴──────────┴──────────┴────────────────────┤
│                  Mode Manager                        │
│         Idle → Social → Admin → Interview            │
├─────────────────────────────────────────────────────┤
│            SQLite Memory + Knowledge Base             │
└─────────────────────────────────────────────────────┘
```

---

## 🔧 Hardware Used

- Raspberry Pi 4
- Arduino Uno
- L298N Motor Driver
- 4-Wheel Robot Chassis + DC Motors
- Pi Camera / USB Camera
- Ultrasonic Sensor (HC-SR04)
- USB Microphone
- Speaker
- Servo Motor (head movement)
- Tablet/Screen
- Battery Pack
- Jumper Wires, Breadboard

---

## 🌍 Where it can be used

- 🏫 **Colleges** — automated student interviews and assessments
- 🏢 **Companies** — HR interview assistance and candidate screening
- 🎪 **Exhibitions & Tech Fests** — interactive public robot
- 🏥 **Healthcare** — reception and patient guidance
- 🔬 **Research** — AI and robotics prototype for academic study

---

## 🔧 Troubleshooting

| Problem | Solution |
|---|---|
| **Serial Port Error** | Check `SERIAL_PORT` in `config.py`. Set `USE_HARDWARE = False` to test without hardware. |
| **STT Hallucinations** | Update `data/vocabulary.txt`. The 5-layer filter blocks most hallucinations automatically. |
| **Face Not Enrolling** | Ensure good lighting and a clear front-facing view for 3 seconds. |
| **Edge TTS Timeout** | Check internet. System automatically falls back to offline voice. |
| **Ollama Not Responding** | Run `ollama serve` in a separate terminal. Check `ollama list`. |
| **ModuleNotFoundError** | Activate virtual environment: `.venv\Scripts\activate` (Windows) |

---

## 🚀 What I Plan to Add Next

- Full emotion detection and confidence analysis
- Autonomous navigation with obstacle mapping
- Cloud AI for smarter conversations
- Auto report generation after each interview
- Mobile app for remote control

---

## 👨‍💻 Built by

**Jageshwar Vishwakarma**
B.Tech CSE (Data Science) — Sarala Birla University, Ranchi, Jharkhand

Solo built — no team, no mentor, no lab funding. Hardware sourced from local scrap market and pocket money. Pure student effort. 💪

- 🌐 Portfolio: [jageshwar01.github.io/Jageshwar](https://jageshwar01.github.io/Jageshwar)
- 💼 LinkedIn: [linkedin.com/in/jageshwar-380b2b257](https://linkedin.com/in/jageshwar-380b2b257)
- 🐙 GitHub: [github.com/Jageshwar01](https://github.com/Jageshwar01)
- 📧 jageshwarkumar15@gmail.com

---

## 📄 License

MIT License — open source and free to use.

---

<div align="center">

*One student. No team. A robot that talks, thinks, and interviews people. Still building — still improving.*

*If this inspired you, give it a ⭐*

</div>
