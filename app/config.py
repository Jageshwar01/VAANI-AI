# ---------------- ROBOT ----------------
ROBOT_NAME = "VaaniAI"
OWNER_NAME = "Jageshwer"
OWNER_ROLE = "owner"

DEFAULT_MODE = "idle"

# ---------------- FEATURES ----------------
USE_VOICE_INPUT = True
USE_TTS = True
USE_CAMERA = True
SHOW_CAMERA_WINDOW = True

# ⚠️ Set False while ESP32 is not connected
USE_HARDWARE = True

USE_UI = False  # Disabled for now — saves CPU for TTS/STT

# ---------------- SERIAL ----------------
SERIAL_PORT = "COM5"
SERIAL_BAUDRATE = 9600

# ---------------- CAMERA ----------------
CAMERA_INDEX = 0

# Face recognition tuning
FACE_TOLERANCE = 0.5

# 🔥 IMPORTANT: Performance vs accuracy
# 0.25 = balanced (recommended)
# 0.20 = faster but less accurate
FRAME_RESIZE_SCALE = 0.25

# Lower FPS helps CPU
CAMERA_FPS = 15

# ---------------- DISTANCE ----------------
SAFE_DISTANCE_CM = 60
MIN_DISTANCE_CM = 30

# ---------------- MOTOR ----------------
DEFAULT_SPEED = 150
MAX_SPEED = 255
MIN_SPEED = 80

# ---------------- SERVO ----------------
HEAD_SERVO_STOP = 87
HEAD_SERVO_SPEED = 10

# ---------------- UI ----------------
UI_PORT = 5000

# ---------------- DEBUG / PERFORMANCE ----------------
# Use this to test camera without voice blocking
DEBUG_CAMERA_ONLY = False

# Optional: disable voice temporarily for smoother camera testing
DEBUG_DISABLE_VOICE = False

# ---------------- AI / OLLAMA ----------------
# Set True to enable AI conversation (requires Ollama running)
# Set False to use hardcoded responses only
USE_AI_CONVERSATION = True

# Ollama local server URL (default port 11434)
OLLAMA_URL = "http://localhost:11434"

# Model to use — dynamic switching based on situation
# Fast mode: casual chat, quick commands (instant response)
FAST_AI_MODEL = "qwen2:0.5b"

# Smart mode: deep conversations, interview questions, presentations (slower but very smart)
# Recommended: "qwen2:1.5b", "phi3:mini", or "mistral:7b" (if your PC is strong enough)
SMART_AI_MODEL = "phi3:mini"

# ---------------- FILE PATHS ----------------
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
DATABASE_PATH = os.path.join(DATA_DIR, "vaaniai.db")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")
KNOWN_FACES_DIR = os.path.join(DATA_DIR, "known_faces")
QUESTION_SETS_DIR = os.path.join(DATA_DIR, "question_sets")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
os.makedirs(QUESTION_SETS_DIR, exist_ok=True)

# ---------------- INTERVIEW ----------------
INTERVIEW_QUESTIONS = [
    "Please introduce yourself.",
    "What is Python?",
    "Explain object oriented programming.",
    "What is the difference between list and tuple?",
    "Tell me about one project you have worked on."
]