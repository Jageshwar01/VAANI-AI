# 🤖 VAANI AI – Humanoid Robot

> I built a 4-foot humanoid robot from scratch — no team, no external funding, just me. It can move, see people, recognise faces, talk, and conduct interviews autonomously using AI. Currently in active development.

---

## 🌟 What is VAANI AI?

VAANI AI is a robot I am building that can actually have a conversation with you.

It moves around on its own, detects when a person is nearby, recognises who they are, and starts talking — either conducting a structured interview or just having a natural conversation depending on the mode.

The idea came from wanting to build something that shows what AI and robotics can do together in the real world — not just on paper.

**Two modes:**
- 🎤 **Interview Mode** — robot walks up to a person, asks interview questions, listens to answers, and scores them on communication, knowledge, and confidence
- 💬 **Social Mode** — natural everyday conversation for exhibitions, receptions, or just interacting with people

---

## 📸 Photos & Demo

> *Photos and demo video coming soon*

---

## ✨ What it can do

- 🤖 Moves on its own — 4-wheel chassis with DC motors controlled by Arduino
- 👁️ Sees and recognises faces — camera + OpenCV detects who is standing in front of it
- 🎤 Understands what you say — speech recognition converts your voice to text
- 🔊 Talks back — text-to-speech so the robot responds in a natural voice
- 🧠 Thinks before it speaks — AI conversation engine decides how to respond
- 📋 Conducts interviews — asks questions, records answers, evaluates and scores responses
- 📏 Knows when to stop — ultrasonic sensor detects a person at 1 meter and stops automatically
- 🖥️ Has a face — tablet/screen displays interview UI and robot expressions
- 👑 Knows its owner — recognises admin face and responds to special commands
- 💾 Remembers people — database stores student profiles, face data, and interview results

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Main Computer | Raspberry Pi |
| Motor Control | Arduino + L298N Motor Driver |
| Vision | OpenCV, face_recognition |
| Speech to Text | SpeechRecognition, Whisper, Vosk |
| Text to Speech | pyttsx3, gTTS |
| AI Brain | Python — local AI / rule-based engine |
| Database | SQLite / Firebase |
| Movement | DC Motors + 4-Wheel Chassis |
| Sensing | Ultrasonic Sensor |
| Language | Python |

---

## 🏗️ How the hardware is connected

```
                 ┌──────────────────────┐
                 │   Tablet / Screen    │
                 │   (Interview UI)     │
                 └──────────┬───────────┘
                            │
                     ┌──────▼──────┐
                     │   Camera    │
                     │ Face Detect │
                     └──────┬──────┘
                            │
                      (Servo Motor)
                   Head Turn Left/Right
                            │
                    ┌───────▼────────┐
                    │  Raspberry Pi  │
                    │   AI Computer  │
                    └───┬──────┬─────┘
                        │      │
            ┌───────────▼─┐  ┌─▼──────────┐
            │ Microphone  │  │  Speaker   │
            │ Voice Input │  │ Robot Talk │
            └─────────────┘  └────────────┘
                        │
                 ┌──────▼───────┐
                 │   Arduino    │
                 │Motor Control │
                 └──────┬───────┘
                        │
                ┌───────▼────────┐
                │  Motor Driver  │
                │    (L298N)     │
                └───────┬────────┘
                        │
           ┌────────────▼────────────┐
           │  4 Wheel Robot Chassis  │
           │  DC Motors + Wheels     │
           └─────────────────────────┘

         [Ultrasonic Sensor — Front]
         Stops robot 1 meter from person
```

---

## 💻 How the software works

```
                ┌─────────────────────┐
                │   Voice Recognition │
                │   (Speech → Text)   │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ Conversation Engine │
                │      AI Brain       │
                └──────────┬──────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌───────────────┐  ┌───────────────┐
│Face Detection│  │ Interview AI  │  │Emotion Detect │
│Recognition   │  │ Question Bank │  │& Confidence   │
└──────┬───────┘  └──────┬────────┘  └──────┬────────┘
       └─────────────────┴──────────────────┘
                         │
                         ▼
                ┌─────────────────────┐
                │      Database       │
                │  Students + Results │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │  Robot Control Unit │
                │  Movement + Sensors │
                └─────────────────────┘
```

---

## 🧠 How the robot behaves

```
Robot starts and moves slowly
         │
         ▼
Ultrasonic sensor detects a person nearby
         │
         ▼
Robot stops at 1 meter distance
         │
         ▼
Camera scans and tries to recognise the face
         │
    ┌────┴─────┐
 Known        Unknown
    ▼              ▼
Says name      Asks name and registers
         │
         ▼
Waits for a command
         │
         ▼
Starts Interview Mode or Social Mode
```

---

## 🎤 Interview Mode — how it works

The robot walks up, greets the person, and starts the interview on its own.

**Sample questions it asks:**
- Tell me about yourself
- What is Python?
- Explain Object Oriented Programming
- What is a database and why do we use it?

**After the interview, it scores the candidate:**

| Category | Score |
|----------|-------|
| Communication | / 10 |
| Technical Knowledge | / 10 |
| Confidence | / 10 |

Everything is saved — questions asked, answers given, scores, and even the emotion detected during the interview.

---

## 👑 Admin / Owner Control

The robot recognises the owner's face and gives special access:

| Command | What happens |
|---------|-------------|
| Start interview | Robot begins interview session |
| Stop robot | Robot halts everything |
| Add student | New face and profile registered |
| Show results | Interview scores displayed |

---

## 📊 Honest project status

| Component | Status |
|-----------|--------|
| 4-foot Robot Body — Built | ✅ Done |
| 4-Wheel Chassis + DC Motors | ✅ Done |
| Raspberry Pi Integration | ✅ Done |
| Arduino Motor Control | ✅ Done |
| Camera + Face Detection | ✅ Done |
| Voice Recognition | ✅ Done |
| Text to Speech | ✅ Done |
| Ultrasonic Sensor | ✅ Done |
| Interview Mode | ✅ Done |
| Social Conversation Mode | ✅ Done |
| Admin Control System | ✅ Done |
| Emotion Detection | 🔄 In development |
| Full AI conversation upgrade | 🔄 In development |
| Cloud AI integration | 🔄 Planned |
| Mobile App Control | 🔄 Planned |

> This is a solo project built with limited resources. Every component listed as done is physically working. The robot is real — not just a concept.

---

## 🌍 Where it can be used

- 🏫 Colleges — automated student interviews and assessments
- 🏢 Companies — HR interview assistance and candidate screening
- 🎪 Exhibitions and tech fests — interactive public robot
- 🏥 Healthcare — reception and patient guidance
- 🔬 Research — AI and robotics prototype for academic study

---

## 🚀 What I plan to add next

- Full emotion detection and confidence analysis
- Autonomous navigation with obstacle mapping
- Cloud AI for smarter conversations
- Auto report generation after each interview
- Mobile app for remote control

---

## 🔧 Hardware used

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

## 🚀 Run it yourself

```bash
git clone https://github.com/Jageshwar01/VAANI-AI.git
cd VAANI-AI
pip install -r requirements.txt
python main.py
```

---

## 👨‍💻 Built by

**Jageshwer Vishwakarma**
- B.Tech CSE (Data Science) — Sarala Birla University, Ranchi
- 🌐 Portfolio: [jageshwar01.github.io/Jageshwar](https://jageshwar01.github.io/Jageshwar)
- 💼 LinkedIn: [linkedin.com/in/jageshwar-380b2b257](https://linkedin.com/in/jageshwar-380b2b257)
- 🐙 GitHub: [github.com/Jageshwar01](https://github.com/Jageshwar01)
- 📧 jageshwarkumar15@gmail.com

---

## 📄 License

MIT License — open source and free to use.

---

> *One student. No team. A robot that talks, thinks, and interviews people. Still building — still improving. If this inspired you, give it a ⭐*
