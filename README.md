# 🤖 VaaniAI — Autonomous Humanoid Assistant

<div align="center">

**An advanced, fully autonomous humanoid robot software stack combining local AI, Computer Vision, Speech Recognition, and Real-time Hardware Control into a single cohesive "Brain".**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-black?style=for-the-badge&logo=ai&logoColor=white)](https://ollama.com)
[![OpenCV](https://img.shields.io/badge/OpenCV-Vision-green?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org)
[![Whisper](https://img.shields.io/badge/Whisper-STT-orange?style=for-the-badge&logo=openai&logoColor=white)](https://github.com/SYSTRAN/faster-whisper)
[![ESP32](https://img.shields.io/badge/ESP32-Hardware-red?style=for-the-badge&logo=espressif&logoColor=white)](https://espressif.com)

</div>

---

## 🌟 Overview

VaaniAI is a production-grade humanoid robot software platform designed to act as a **university guide**, **interactive receptionist**, or **personal companion**. It features a highly responsive emotional personality, multilingual voice support (English, Hindi, Odia), real-time face recognition, and autonomous physical movement — all running **100% offline** on local hardware.

### What Makes VaaniAI Special?

- 🧠 **Fully Offline AI** — No cloud APIs, no data leaks. Everything runs locally via Ollama.
- 👁️ **Sees & Remembers Faces** — Auto-enrolls new people and greets them by name next time.
- 🗣️ **Hears & Speaks Naturally** — Whisper AI for hearing + Edge-TTS/Offline voice for speaking.
- 🦾 **Physical Body** — Controls motors, servos, and mouth via ESP32/Arduino serial bridge.
- 🎓 **Presentation Mode** — Can autonomously deliver a 1-minute university presentation.
- 🧪 **Interview Mode** — Conducts structured interviews and generates performance reports.

---

## ✨ Core Features

### 🧠 The Brain — AI & NLP
| Feature | Description |
|---|---|
| **Local LLM** | Powered by Ollama with dual-model architecture (Fast: `qwen2:0.5b`, Smart: `phi3:mini`) |
| **Knowledge Base (RAG)** | Reads `.txt` files from `data/knowledge/` and injects facts into AI context. Teach the robot university details, faculty info, or custom scripts — no retraining needed |
| **Emotional Personality** | Custom system prompts create human-like speech with vocal expressions (*Haha*, *Wow*, *Aww*) |
| **Memory System** | SQLite-backed memory remembers past conversations, enrolled faces, and relationships |
| **Intent Classifier** | Fuzzy-matching NLP engine classifies voice commands into hardware actions or conversation with 82%+ confidence threshold |
| **Presentation Mode** | Detects keywords like *"introduce yourself"* or *"presentation"* and delivers a full scripted speech from the knowledge base |

### 🗣️ Voice Interface — Hearing & Speaking
| Feature | Description |
|---|---|
| **Speech-to-Text** | `faster-whisper` with 5-layer anti-hallucination pipeline (no-speech detection, log-probability filtering, blocklist, repetition check) |
| **Custom Vocabulary** | Loads `data/vocabulary.txt` to properly hear Indian names and technical terms without hallucinating |
| **Command Queue** | Thread-safe queue system ensures no voice command is ever silently dropped, even if the brain is busy processing |
| **Text-to-Speech** | Dual-engine: Edge-TTS (online, natural Indian female voice) with automatic fallback to pyttsx3 (offline, Microsoft Zira female voice) |
| **Multilingual** | Supports English, Hindi (Devanagari), and Odia with automatic language detection and voice switching |
| **Persistent Event Loop** | Dedicated asyncio thread prevents TTS timeouts caused by multi-thread conflicts |

### 👁️ Computer Vision — Sight
| Feature | Description |
|---|---|
| **Face Recognition** | Real-time face detection and identification using `face_recognition` library |
| **Auto-Enrollment** | Silently captures and enrolls new faces in a 3-second background thread without pausing conversation |
| **Face Stability Buffer** | Requires 4 consecutive identical frames before triggering a mode switch — prevents flicker-based false detections |
| **Social Greetings** | Recognizes registered users and generates personalized, memory-aware greetings |
| **Head Tracking** | Automatically moves head servo to follow the detected face position |

### 🦾 Hardware & Movement — Physical Body
| Feature | Description |
|---|---|
| **Serial Bridge** | Thread-safe `PySerial` communication with auto-reconnection, heartbeat monitoring, and graceful fallback to simulation mode |
| **Motor Control** | Forward, backward, left, right movement with configurable speed and auto-stop timeout |
| **Servo Control** | Head servo for left/right tracking, mouth servo for lip-sync during speech |
| **Micro-Animations** | Continuous idle movements (head sway, mouth sync) to make the robot feel alive |
| **ESP32/Arduino Firmware** | C++ firmware for real-time motor and servo control via serial commands |

### 🎓 Special Modes
| Mode | Description |
|---|---|
| **Idle** | Listens for commands, processes camera, auto-greets new visitors |
| **Social** | Multi-turn AI conversation with 20-second listening window and context preservation |
| **Admin** | Full control mode for the owner — face enrollment, memory review, direct motor commands |
| **Interview** | Structured interview system with configurable questions and automated scoring |
| **Presentation** | Delivers a full 1-minute scripted presentation from knowledge base |

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
│   │   ├── chat_engine.py        # Ollama API client with dual-model support
│   │   ├── personality.py        # System prompt generator (mode-aware)
│   │   ├── prompt_builder.py     # Constructs context-rich LLM prompts
│   │   └── response_filter.py    # Cleans AI output for TTS compatibility
│   ├── knowledge/                # RAG Knowledge Base
│   │   ├── knowledge_base.py     # Keyword-based fact retrieval engine
│   │   └── vaani_presentation.txt # Presentation script & identity info
│   ├── memory/                   # Conversation memory manager
│   ├── interview/                # Interview question engine & scoring
│   └── vision_ai/                # AI-powered vision analysis
│
├── voice/                        # Voice I/O Engines
│   ├── speech_to_text.py         # Whisper STT with 5-layer hallucination filter
│   └── text_to_speech.py         # Edge-TTS (online) + pyttsx3 (offline) dual engine
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
│       ├── motor_controller.py   # Motor commands (forward/backward/left/right)
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
│   │   ├── about_vaani.txt       # Robot identity facts
│   │   ├── university.txt        # University information
│   │   └── faculties.txt         # Faculty directory with contact details
│   ├── vocabulary.txt            # Custom STT vocabulary for Indian names
│   ├── question_sets/            # Interview question banks
│   └── reports/                  # Generated interview reports
│
├── scripts/                      # Utility Scripts
│   └── generate_dataset.py       # Training data generation helper
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
git clone https://github.com/YourUsername/VaaniAi.git
cd VaaniAi

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

> **Note (Windows):** You may need to install Visual Studio Build Tools with the "Desktop development with C++" workload for the `face_recognition` / `dlib` library.

### Step 3: Setup Ollama Models

```bash
# Install Ollama from https://ollama.com

# Pull the AI models
ollama pull qwen2:0.5b       # Fast model (352 MB) — casual chat
ollama pull phi3:mini         # Smart model (2.2 GB) — presentations, interviews
```

### Step 4: Configure

Edit `app/config.py` to match your setup:

```python
# Robot Identity
ROBOT_NAME = "VaaniAI"
OWNER_NAME = "Jageshwer"

# Hardware (set False if no ESP32 connected)
USE_HARDWARE = True
SERIAL_PORT = "COM5"          # Windows: COM5, Linux: /dev/ttyUSB0

# AI Models
FAST_AI_MODEL = "qwen2:0.5b"  # For quick responses
SMART_AI_MODEL = "phi3:mini"   # For presentations & interviews

# Features (enable/disable)
USE_VOICE_INPUT = True
USE_TTS = True
USE_CAMERA = True
```

### Step 5: Add Custom Knowledge (Optional)

Add `.txt` files to `data/knowledge/` to teach the robot custom facts:

```text
# Example: data/knowledge/university.txt
Sarala Birla University is a private university located in Ranchi, Jharkhand, India.
The Vice Chancellor is Prof. Dr. Jeganathan Chockalingam.
```

The robot will automatically load and use these facts when answering relevant questions.

---

## 🚀 Running VaaniAI

### Start Ollama (if not auto-starting)
```bash
ollama serve
```

### Launch the Robot
```bash
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
[AI] Warming up AI brain (first load takes 30-60 sec)...
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
| *"Introduce yourself"* | Triggers the self-introduction |
| *"Start interview"* | Begins structured interview mode |
| *"Switch to Hindi"* | Changes language to Hindi |
| *"Switch to English"* | Changes back to English |
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

## 🔧 Troubleshooting

| Problem | Solution |
|---|---|
| **Serial Port Error** (`FileNotFoundError`) | Ensure ESP32 is plugged in. Check `SERIAL_PORT` in `config.py`. Set `USE_HARDWARE = False` to test without hardware. |
| **STT Hallucinations** (random words when silent) | Update `data/vocabulary.txt`. The 5-layer filter blocks most hallucinations automatically. |
| **Face Not Enrolling** | Ensure good lighting. The system needs a clear, front-facing view for 3 seconds. |
| **Edge TTS Timeout** | Check internet connection. The system automatically falls back to offline voice (Microsoft Zira). |
| **Ollama Not Responding** | Run `ollama serve` in a separate terminal. Ensure models are pulled with `ollama list`. |
| **Microphone Not Detected** | Check that `pyaudio` is installed. On Windows, ensure the correct audio device is set as default. |
| **"ModuleNotFoundError"** | Activate your virtual environment: `.venv\Scripts\activate` (Windows) |

---

## 📊 Technical Specifications

| Component | Technology | Details |
|---|---|---|
| **AI Brain** | Ollama (Local LLM) | Dual-model: Fast (`qwen2:0.5b`) + Smart (`phi3:mini`) |
| **Speech Recognition** | faster-whisper | Base model, CPU int8, 5-layer hallucination filter |
| **Voice Output** | Edge-TTS + pyttsx3 | Indian female voice (Neerja) online, Zira offline |
| **Vision** | OpenCV + face_recognition | Real-time face detection, tracking, and enrollment |
| **Hardware** | ESP32 / Arduino | Serial bridge at 9600 baud with auto-reconnect |
| **Database** | SQLite | People, memories, sessions, interview records |
| **Web UI** | Flask | Robot face display and status dashboard |
| **Languages** | English, Hindi, Odia | Auto-detected via Unicode range analysis |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is developed by **Jageshwer** as part of a B.Tech Computer Science project at **Sarala Birla University**, Ranchi, Jharkhand, India.

---

<div align="center">

**Built with ❤️ for Advanced Human-Robot Interaction**

*VaaniAI — Bridging the gap between machines and human emotion.*

</div>
