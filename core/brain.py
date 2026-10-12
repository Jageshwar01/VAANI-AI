import time
import cv2
import threading
import random
from datetime import datetime

from app.config import (
    ROBOT_NAME,
    OWNER_NAME,
    DEFAULT_MODE,
    SHOW_CAMERA_WINDOW,
    DEBUG_DISABLE_VOICE,
    USE_AI_CONVERSATION,
)
from core.mode_manager import ModeManager
from core.intent_classifier import IntentClassifier
from voice.text_to_speech import TextToSpeech
from voice.speech_to_text import SpeechToText
from ai.conversation.chat_engine import ChatEngine
from ai.interview.interview_manager import InterviewManager
from ai.memory.memory_manager import MemoryManager
from database.db import DatabaseManager
from vision.camera_manager import CameraManager
from vision.face_recognition_engine import FaceRecognitionEngine
from vision.face_enrollment import FaceEnrollment
from robot.hardware_bridge.serial_bridge import SerialBridge
from robot.movement.motor_controller import MotorController
from robot.movement.distance_keeper import DistanceKeeper
from robot.head.head_controller import HeadController
from ui.screen_manager import ScreenManager
from ai.knowledge.knowledge_base import KnowledgeBase


class VaaniBrain:
    def __init__(self):
        self.db = DatabaseManager()
        self.tts = TextToSpeech()
        self.stt = SpeechToText()
        self.mode_manager = ModeManager(DEFAULT_MODE)
        self.memory = None
        self.interview_manager = None
        self.running = True

        # ✅ AI conversation engine + intent classifier + knowledge base
        self.intent_classifier = IntentClassifier()
        self.chat_engine = ChatEngine() if USE_AI_CONVERSATION else None
        self.knowledge = KnowledgeBase()  # Loads data/knowledge/*.txt files

        self.camera = CameraManager()
        self.face_engine = FaceRecognitionEngine()
        self.face_enrollment = FaceEnrollment(self.camera, self.face_engine)

        self.serial_bridge = SerialBridge()
        self.motor_controller = MotorController(self.serial_bridge)
        self.distance_keeper = DistanceKeeper(self.serial_bridge, self.motor_controller)
        self.head_controller = HeadController(self.serial_bridge)

        self.last_seen_person = None
        self.last_seen_time = None
        self.hardware_connected = False
        self._last_mode = None
        self.language_mode = "en"  # "en" by default

        self.frame_counter = 0
        self.last_results = []
        self.manual_head_until = 0

        # ── Auto-greet tracking ───────────────────────────────────────────────
        self._last_greeted_person = None
        self._last_greeted_time = 0
        self._greet_cooldown = 90        # seconds before re-greeting same person
        self._greet_after_idle = 45      # seconds robot must be idle before auto-greet
        self._idle_since = time.time()

        # ✅ FACE STABILITY BUFFER
        # Prevents camera flicker from incorrectly triggering mode switches.
        # A person must be seen in N consecutive frames before any action is taken.
        self._face_stable_buffer = []   # list of recent face detections
        self._face_stable_required = 4  # must see same person 4 times in a row

        # ✅ FIX: Camera ko throttle karo — har loop pe nahi, sirf N ms baad
        self._last_camera_time = 0
        self._camera_interval = 0.15   # 150ms = ~6-7 fps

        # ✅ Camera pause flag — pause during interview/heavy tasks to free CPU
        self._camera_paused = False

        self.screen = ScreenManager()

    # ── speak helper ──────────────────────────────────────────────────────────

    def speak(self, text):
        """
        Safe speak wrapper with Micro-Animations for Physical Servos.
        Mutes STT → prints → starts animation thread → speaks → stops animation → unmutes STT.
        """
        print(f"VaaniAI: {text}")
        if not DEBUG_DISABLE_VOICE:
            self.stt.mute()

        # ── Micro-Animations ──
        # Only animate if the text is somewhat long (more than ~15 chars).
        # We use a mutable list trick so the inner thread can read 'is_speaking_flag[0]'
        self.is_speaking = True
        is_speaking_flag = [True]
        
        def animate_head():
            head_pos = 0  # track virtual position (negative = left, positive = right)
            while is_speaking_flag[0]:
                # Random realistic delay between movements (1 to 2.5 seconds)
                delay = random.uniform(1.0, 2.5)
                # Sleep in micro-chunks so thread can exit instantly when speech ends
                slept = 0.0
                while slept < delay and is_speaking_flag[0]:
                    time.sleep(0.1)
                    slept += 0.1
                
                if not is_speaking_flag[0]:
                    break
                    
                # Prevent drifting too far to one side
                if head_pos == 0:
                    cmd = random.choice(["HEAD_LEFT", "HEAD_RIGHT"])
                elif head_pos < 0:
                    cmd = random.choice(["HEAD_RIGHT", "HEAD_STOP"])
                else:
                    cmd = random.choice(["HEAD_LEFT", "HEAD_STOP"])
                    
                if cmd == "HEAD_LEFT":
                    self.head_controller.look_left()
                    head_pos -= 1
                elif cmd == "HEAD_RIGHT":
                    self.head_controller.look_right()
                    head_pos += 1
                else:
                    self.head_controller.look_center()
            
            # ── Clean up: Re-center head before thread exits ──
            while head_pos < 0:
                self.head_controller.look_right()
                head_pos += 1
                time.sleep(0.35)  # Wait for ESP32 movement time (approx 300ms)
            while head_pos > 0:
                self.head_controller.look_left()
                head_pos -= 1
                time.sleep(0.35)
            self.head_controller.look_center()

        anim_thread = None
        if len(text.strip()) > 15:
            anim_thread = threading.Thread(target=animate_head)
            anim_thread.daemon = True
            anim_thread.start()

        # Block and play audio
        try:
            # Pass serial bridge to TTS so it can sync mouth perfectly
            self.tts.speak(text, serial_bridge=getattr(self, 'serial_bridge', None))
        except Exception as e:
            print(f"[BRAIN] Speak error: {e}")
        finally:
            self.is_speaking = False
            
            if anim_thread:
                is_speaking_flag[0] = False
                anim_thread.join(timeout=2.0)  # Wait up to 2 seconds for it to recenter itself

            if not DEBUG_DISABLE_VOICE:
                self.stt.unmute()

    # ── mode switch helper ────────────────────────────────────────────────────

    def switch_mode(self, mode):
        """Switch mode and flush stale STT command."""
        self.mode_manager.set_mode(mode)
        self.stt.flush()

    # ── init ──────────────────────────────────────────────────────────────────

    def initialize(self):
        self.screen.start()

        self.db.connect()
        self.db.create_tables()

        self.memory = MemoryManager(self.db)
        self.interview_manager = InterviewManager(self.tts, self.stt, self.db, serial_bridge=self.serial_bridge)

        self.face_engine.load_known_faces()

        camera_started = self.camera.start()
        if camera_started:
            self.face_enrollment = FaceEnrollment(self.camera, self.face_engine)
        else:
            print("[WARN] Camera not started.")

        self.hardware_connected = self.serial_bridge.connect()
        if self.hardware_connected:
            self.head_controller.look_center()
        else:
            print("[WARN] Hardware not connected. Running in simulation mode.")

        # STT sirf ek baar start — never call again
        if not DEBUG_DISABLE_VOICE:
            self.stt.start()

        # ✅ AI brain warm-up — pehli call pe model RAM mein load hota hai (30-60s)
        # Yeh startup pe karte hain taaki user ko conversation ke time wait na karna pade
        if self.chat_engine:
            from app.config import FAST_AI_MODEL, OLLAMA_URL
            print("[AI] Warming up AI brain (first load takes 30-60 sec)...")
            if self.chat_engine.is_available(FAST_AI_MODEL):
                try:
                    import requests
                    # Simple warm-up request — model RAM mein load ho jayega
                    r = requests.post(
                        f"{OLLAMA_URL}/api/chat",
                        json={
                            "model": FAST_AI_MODEL,
                            "messages": [{"role": "user", "content": "Hi"}],
                            "stream": False,
                            "options": {"num_predict": 5}  # very short response
                        },
                        timeout=120  # 2 min max for first load
                    )
                    if r.status_code == 200:
                        print("[AI] Brain ready! ✅")
                    else:
                        print(f"[AI] Warm-up got status {r.status_code}")
                except Exception as e:
                    print(f"[AI] Warm-up failed: {e} — will retry on first conversation")
            else:
                print("[AI] Ollama not available. AI conversations will use fallback mode.")

        # ✅ Warm, human-like startup instead of "Systems initialized"
        self.speak("Good to see you! I am awake and ready.")

    # ── main loop ─────────────────────────────────────────────────────────────

    def run(self):
        self.speak("I am here whenever you need me.")
        self._last_mode = ModeManager.IDLE

        while self.running:
            # ✅ FIX: Camera sirf har 150ms pe — pehle har iteration pe tha
            # Isse CPU busy rehta tha aur microphone thread starve hoti thi
            now = time.time()
            if not self._camera_paused and now - self._last_camera_time >= self._camera_interval:
                self.process_camera_once()
                self._last_camera_time = now

            distance_status = self.distance_keeper.maintain_distance()

            # ✅ FIX: Don't block voice/camera during safety stops.
            # Previously `continue` would skip EVERYTHING — robot became deaf.
            # Now we only skip movement commands, but still process voice + camera.

            # ✅ Auto-stop runaway motors after 3 seconds
            self.motor_controller.check_timeout()

            mode = self.mode_manager.get_mode()

            if mode == ModeManager.IDLE:
                self.handle_idle_mode()
            elif mode == ModeManager.SOCIAL:
                self.handle_social_mode()
            elif mode == ModeManager.INTERVIEW:
                self.handle_interview_mode()
            elif mode == ModeManager.ADMIN:
                self.handle_admin_mode()

            time.sleep(0.05)   # 0.01 se 0.05 — thoda rest dena CPU ko

    # ── get command ───────────────────────────────────────────────────────────

    def get_next_command(self, prompt="Type command: "):
        if DEBUG_DISABLE_VOICE:
            typed = input(prompt).strip().lower()
            return typed if typed else None
        cmd = self.stt.get_command()
        if cmd:
            print(f"[BRAIN] Received command: {cmd}")
            return cmd
        return None

    # ── camera ────────────────────────────────────────────────────────────────

    def process_camera_once(self):
        ret, frame = self.camera.read_frame()
        if not ret or frame is None:
            return

        self.frame_counter += 1

        # Face recognition har 5th frame pe — baaki frames mein cached result use karo
        if self.frame_counter % 5 == 0:
            results = self.face_engine.recognize_faces_in_frame(frame)
            self.last_results = results if results else []
        else:
            results = self.last_results

        if results:
            first_person = results[0]["name"]

            # ── FACE STABILITY FILTER ─────────────────────────────────────────
            # Append to buffer, keep only last N results
            self._face_stable_buffer.append(first_person)
            if len(self._face_stable_buffer) > self._face_stable_required:
                self._face_stable_buffer.pop(0)

            # Only consider stable if ALL buffer entries agree
            stable_person = (
                first_person
                if len(self._face_stable_buffer) == self._face_stable_required
                   and len(set(self._face_stable_buffer)) == 1
                else None
            )

            if stable_person and stable_person != self.last_seen_person:
                self.last_seen_person = stable_person
                self.last_seen_time = datetime.now().isoformat()
                if stable_person != "Unknown":
                    self.memory.add_memory(stable_person, "Face recognized by camera", None, "vision")
                    print(f"[VISION] Recognized: {stable_person}")
                else:
                    print("[VISION] Unknown person detected.")

            if time.time() >= self.manual_head_until and not getattr(self, 'is_speaking', False):
                top, right, bottom, left = results[0]["location"]
                frame_center_x = frame.shape[1] // 2
                face_center_x = (left + right) // 2
                # Note: camera_manager flips the frame horizontally (cv2.flip(frame, 1)).
                # This means if the face is on the left side of the frame (face_center_x < frame_center_x),
                # the person is actually on the robot's physical RIGHT. So we must turn RIGHT.
                if face_center_x < frame_center_x - 80:
                    self.head_controller.look_right()
                elif face_center_x > frame_center_x + 80:
                    self.head_controller.look_left()
                else:
                    self.head_controller.look_center()
        else:
            # No face in frame — slowly forget the old result to avoid stale data
            if self._face_stable_buffer:
                self._face_stable_buffer.pop(0)

        if SHOW_CAMERA_WINDOW:
            display_frame = self.face_engine.draw_face_labels(frame, results)
            cv2.imshow("VaaniAI Vision", display_frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                self.shutdown()

        # ── Idle-based auto-greet trigger (only on STABLE face) ──────────────
        stable = (
            len(self._face_stable_buffer) == self._face_stable_required
            and len(set(self._face_stable_buffer)) == 1
            and self._face_stable_buffer[0] != None
        )
        if (
            stable
            and self.mode_manager.get_mode() == ModeManager.IDLE
            and self._should_auto_greet(self._face_stable_buffer[0])
        ):
            detected = self._face_stable_buffer[0]
            print(f"[SOCIAL] Auto-greet triggered for: {detected}")
            self._last_greeted_person = detected
            self._last_greeted_time = time.time()
            self.switch_mode(ModeManager.SOCIAL)

    def _should_auto_greet(self, person_name: str) -> bool:
        """
        Returns True if the robot should auto-greet this person now.
        Rules:
          - Robot must have been idle 30+ seconds
          - Same person must not have been greeted in last 60 seconds
          - Owner (OWNER_NAME) never triggers social mode — goes to admin
          - 'Unknown' persons ARE greeted (robot will ask their name)
        """
        if person_name == OWNER_NAME:
            return False
        now = time.time()
        idle_long_enough = (now - self._idle_since) >= self._greet_after_idle
        greeted_recently = (
            self._last_greeted_person == person_name
            and (now - self._last_greeted_time) < self._greet_cooldown
        )
        return idle_long_enough and not greeted_recently

    # ── idle mode ─────────────────────────────────────────────────────────────

    def handle_idle_mode(self):
        if self._last_mode != ModeManager.IDLE:
            self.speak(random.choice([
                "I am here whenever you need me.",
                "Standing by, just say something.",
                "Ready and listening.",
            ]))
            self._last_mode = ModeManager.IDLE
            self._idle_since = time.time()  # Reset idle clock when entering idle

        command = self.get_next_command()

        if not command or len(command) < 2:
            return

        print(f"[COMMAND] {command}")
        person = self.last_seen_person if self.last_seen_person else "unknown"
        # Don't log to memory here — do it only after AI response (with ai_response included)

        # ✅ AI: Intent classifier decides — hardware command ya AI conversation?
        intent, confidence = self.intent_classifier.classify(command)
        print(f"[INTENT] {intent} (confidence: {confidence:.2f})")

        # ── Hardware commands (local, instant, no AI needed) ──────────────
        if intent == "move_forward":
            self.motor_controller.forward()
            self.speak(random.choice([
                "Sure, coming towards you!",
                "On my way!",
                "Walking forward now.",
                "Let me come closer.",
            ]))

        elif intent == "move_backward":
            self.motor_controller.backward()
            self.speak(random.choice([
                "Okay, stepping back.",
                "Sure, giving you some space.",
                "Backing up now.",
                "Let me move back a bit.",
            ]))

        elif intent == "turn_left":
            self.motor_controller.left()
            self.speak(random.choice([
                "Turning to my left.",
                "Going left!",
                "Sure, rotating left.",
            ]))

        elif intent == "turn_right":
            self.motor_controller.right()
            self.speak(random.choice([
                "Turning to my right.",
                "Going right!",
                "Sure, rotating right.",
            ]))

        elif intent == "stop":
            self.motor_controller.stop()
            self.speak(random.choice([
                "Okay, I have stopped.",
                "Alright, standing still now.",
                "Stopped! What next?",
            ]))

        elif intent == "look_left":
            self.head_controller.look_left()
            self.manual_head_until = time.time() + 2
            self.speak(random.choice([
                "Let me check this side.",
                "Looking to my left.",
            ]))

        elif intent == "look_right":
            self.head_controller.look_right()
            self.manual_head_until = time.time() + 2
            self.speak(random.choice([
                "Let me see what is over here.",
                "Looking to my right.",
            ]))

        elif intent == "look_center":
            self.head_controller.look_center()
            self.manual_head_until = time.time() + 2
            self.speak(random.choice([
                "Looking straight at you now.",
                "Okay, facing forward.",
            ]))

        elif intent == "interview":
            self._last_mode = None
            self.switch_mode(ModeManager.INTERVIEW)

        elif intent == "admin":
            self._last_mode = None
            self.switch_mode(ModeManager.ADMIN)

        elif intent == "greeting":
            # ✅ AI: Greeting → switch to social conversation mode
            self._last_mode = None
            self.switch_mode(ModeManager.SOCIAL)

        elif intent == "enroll_owner":
            self.handle_face_enrollment(person_name=OWNER_NAME, role="owner")

        elif intent == "enroll_face":
            self.handle_face_enrollment()

        elif intent == "switch_hindi":
            self.language_mode = "hi"
            self.stt.language_mode = "hi"
            self.speak("ठीक है, अब से मैं हिंदी में बात करुँगी।")
            
        elif intent == "switch_english":
            self.language_mode = "en"
            self.stt.language_mode = "en"
            self.speak("Okay, I will speak in English now.")

        elif intent == "shutdown":
            self.shutdown()

        elif intent == "conversation":
            cmd_lower = command.lower().strip()
            # ── Check for presentation trigger BEFORE sending to AI ────────────
            # Very broad match to survive STT mistakes
            if any(word in cmd_lower for word in ["presentation", "introduce", "introduction", "parichay"]):
                print("[IDLE] Presentation triggered!")
                self.speak("Sure! Let me present myself.")
                # ✅ FIX: AI generation takes 60s — flush STT BEFORE generating
                # so noise captured during wait doesn't become a false command.
                self.stt.mute()
                knowledge_context = self.knowledge.get_context_string("presentation self introduction VaaniAI")
                script = self.chat_engine.respond(
                    user_text="Give your full 1-minute university presentation. Use the knowledge context provided.",
                    person_name=person,
                    mode="presentation",
                    memories=None,
                    language_mode=self.language_mode,
                    knowledge_context=knowledge_context,
                ) if self.chat_engine else "Hello! I am VaaniAI, an autonomous humanoid robot made by Jageshwer!"
                # ✅ FIX: Flush accumulated STT noise, then unmute for speech
                self.stt.flush()
                self.stt.unmute()
                self.speak(script)
                self.stt.flush()  # Discard any STT picked up during presentation
                self.memory.add_memory(person, command, script, "presentation")
            else:
                # ✅ AI: No hardware match → send to AI for smart response
                response = self._handle_ai_response(command)
                self.memory.add_memory(person, command, response, "idle_command")

        else:
            # Fallback — should rarely reach here
            response = self._handle_ai_response(command)
            self.memory.add_memory(person, command, response, "idle_command")

    # ── AI response helper ────────────────────────────────────────────────────

    def _handle_ai_response(self, command: str) -> str:
        """Send a command to the AI chat engine, speak it, and return the response text."""
        if self.chat_engine:
            person = self.last_seen_person if self.last_seen_person else "guest"
            memories = self.memory.get_recent_memories(person) if person != "guest" else None
            mode = self.mode_manager.get_mode()

            # ✅ Vocal thinking filler — context-aware
            # Short/simple inputs get a light filler; complex questions get a deeper one
            word_count = len(command.split())
            if word_count <= 3:
                # Short inputs like "thank you", "okay", "what's up" — quick acknowledgment
                filler = random.choice(["Sure!", "Okay!", "Right!"])
            else:
                # Longer, more complex questions — show the robot is genuinely thinking
                filler = random.choice([
                    "Hmm, let me think...",
                    "Okay, one moment...",
                    "Let me see...",
                    "Interesting question...",
                ])
            print(f"[AI] Thinking... ({filler})")
            self.speak(filler)

            # ✅ Inject relevant knowledge facts into the query
            knowledge_context = self.knowledge.get_context_string(command)

            response = self.chat_engine.respond(
                user_text=command,
                person_name=person,
                mode=mode,
                memories=memories,
                language_mode=self.language_mode,
                knowledge_context=knowledge_context
            )
            print(f"[AI] Response: {response}")
            self.speak(response)
            return response
        else:
            fallback = "Sorry, I cannot think clearly right now. My brain needs a restart."
            self.speak(fallback)
            return fallback

    # ── social mode (AI conversation loop) ────────────────────────────────────

    def handle_social_mode(self):
        """
        AI-powered social conversation — aligned to original robot design doc.

        Flow:
          Known person   → personalized AI greeting using memory
          Unknown person → ask name → save to DB → then converse
          Owner face     → skip social, go straight to admin mode
        """
        self._last_mode = ModeManager.SOCIAL
        person = self.last_seen_person if self.last_seen_person else "guest"

        # ── Owner shortcut: skip social, enter admin mode ─────────────────────
        if person == OWNER_NAME:
            print(f"[SOCIAL] Owner detected ({OWNER_NAME}). Switching to admin mode.")
            self.switch_mode(ModeManager.ADMIN)
            return

        # ── Unknown person: ask their name, save, greet ───────────────────────
        if person == "Unknown" or person == "guest":
            self.speak("Hello! I have not seen you before. What is your name?")
            name = None
            # Increase wait time to 20 seconds. STT takes 3-5 seconds AFTER speaking finishes.
            for _ in range(200):
                name = self.get_next_command()
                if name:
                    break
                time.sleep(0.1)

            if name:
                import re
                name_clean = name.strip()
                
                # Clean up name — strip common STT noise prefixes safely using word boundaries
                # Removed dangerous short prefixes like "a", "am", "its" which trigger on random sentences
                pattern = re.compile(
                    r'\b(mera naam hai|my name is|mera naam|the name is|name is|call me|i am|i\'m|naam hai)\b\s*', 
                    re.IGNORECASE
                )
                
                # Split and take whatever comes AFTER the last matched prefix
                parts = pattern.split(name_clean)
                extracted_name = parts[-1].strip()
                
                # Remove punctuation (like periods at the end of STT)
                extracted_name = re.sub(r'[^\w\s]', '', extracted_name)
                
                # ✅ FIX: Cut off name if user immediately asked a question or continued talking
                # Example: "jageshwar what is your name" -> stops at "what"
                lower_ex = f" {extracted_name.lower()} "
                for stop_word in [" what ", " how ", " and ", " who ", " where ", " tell ", " but ", " i "]:
                    if stop_word in lower_ex:
                        # Find the actual index in the original string (case insensitive)
                        idx = extracted_name.lower().find(stop_word.strip())
                        if idx != -1:
                            extracted_name = extracted_name[:idx]
                            break
                
                # Take only the first 2 words — avoid saving full sentences as names
                words = extracted_name.split()
                name = " ".join(words[:2]).title() if words else extracted_name.strip().title()

                # Save to database as a new person
                try:
                    self.db.execute(
                        """
                        INSERT OR IGNORE INTO people (name, role, relation_type, face_id, notes, last_seen)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (name, "visitor", "visitor", name.lower().replace(" ", "_"),
                         "Introduced themselves to VaaniAI", datetime.now().isoformat()),
                    )
                    print(f"[SOCIAL] New person saved: {name}")

                    # ✅ SILENT AUTO-ENROLL FACE (Robust 3-second loop)
                    # We run this in a background thread so the robot can immediately greet the person
                    # without waiting for the camera loop to finish.
                    def enroll_thread():
                        success = self.face_enrollment.auto_capture_and_enroll(name, role="visitor", timeout=3.0)
                        if success:
                            self.face_engine.load_known_faces()  # Reload so they are instantly recognizable
                    
                    threading.Thread(target=enroll_thread, daemon=True).start()

                except Exception as e:
                    print(f"[DB/VISION] Could not save or enroll new person: {e}")

                self.last_seen_person = name  # Use for rest of this conversation
                person = name
                self.speak(f"Nice to meet you, {name}! I am {ROBOT_NAME}.")
                # ✅ FIX: Invite the user to speak so they know the robot is listening
                self.speak("What would you like to talk about?")
            else:
                self.speak(f"No problem. I am {ROBOT_NAME}. How can I help you?")
                person = "guest"

        # ── Known person: AI greeting with memory context ─────────────────────
        else:
            memories = self.memory.get_recent_memories(person)
            if self.chat_engine:
                print("[AI] Generating personalized greeting...")
                greeting = self.chat_engine.respond(
                    user_text=(
                        f"Greet {person} warmly. If there are past memories, "
                        f"mention something from them naturally in 1-2 sentences."
                    ),
                    person_name=person,
                    mode="social",
                    memories=memories,
                    language_mode=self.language_mode
                )
                self.speak(greeting)
                self.memory.add_memory(person, "Greeted by VaaniAI", greeting, "social")
            else:
                self.speak(f"Hello {person}! Nice to see you. How can I help you?")

        # ✅ FIX: Give STT time to settle after speaking before starting listen loop
        # unmute() already has 1.5s echo wait built in, plus flush — this is enough.
        self.stt.flush()

        # ── Multi-turn conversation loop ──────────────────────────────────────
        exit_words = ["bye", "goodbye", "exit", "idle", "back", "return", "quit", "band karo", "alvida"]
        presentation_keywords = ["presentation", "introduce", "introduction", "parichay"]
        silence_prompts = [
            "Are you still there?",
            "I am here if you want to talk.",
        ]
        max_turns = 30
        silence_count = 0

        def _wait_for_command(timeout_sec=10):
            """Wait up to timeout_sec for STT command. Also ticks camera so tracking stays live."""
            steps = int(timeout_sec / 0.1)
            for _ in range(steps):
                cmd = self.get_next_command()
                if cmd:
                    return cmd
                # ✅ Keep camera alive during wait — face tracking doesn't freeze
                now = time.time()
                if not self._camera_paused and now - self._last_camera_time >= self._camera_interval:
                    self.process_camera_once()
                    self._last_camera_time = now
                time.sleep(0.1)
            return None

        for turn in range(max_turns):
            # ✅ FIX: Reduced from 20s → 10s for natural conversation pacing
            text = _wait_for_command(timeout_sec=10)

            if not text:
                silence_count += 1
                if silence_count == 1:
                    self.speak(silence_prompts[0])
                    self.stt.flush()  # ✅ Discard echo of robot's own silence prompt
                    continue
                elif silence_count == 2:
                    self.speak(silence_prompts[1])
                    self.stt.flush()
                    continue
                else:
                    self.speak("I will go back to standby now. Come talk to me anytime!")
                    break
            else:
                silence_count = 0

            text_lower = text.lower().strip()

            # ── Exit words ────────────────────────────────────────────────────
            if any(word in text_lower for word in exit_words):
                if self.chat_engine:
                    farewell = self.chat_engine.respond(
                        user_text="The user is saying goodbye. Give a warm 1-sentence farewell.",
                        person_name=person,
                        mode="social",
                    )
                    self.speak(farewell)
                else:
                    self.speak(f"Goodbye {person}! It was nice talking to you.")
                break

            # ── Presentation trigger ──────────────────────────────────────────
            if any(word in text_lower for word in presentation_keywords):
                print("[SOCIAL] Presentation triggered!")
                # FIX: Mute STT during AI generation (60s) to discard noise
                self.stt.mute()
                knowledge_context = self.knowledge.get_context_string("presentation self introduction VaaniAI")
                script = self.chat_engine.respond(
                    user_text="Give your full 1-minute university presentation. Use the knowledge context provided.",
                    person_name=person,
                    mode="presentation",
                    memories=None,
                    language_mode=self.language_mode,
                    knowledge_context=knowledge_context,
                )
                # FIX: Flush noise accumulated during generation, then unmute
                self.stt.flush()
                self.stt.unmute()
                self.speak(script)
                self.stt.flush()  # Discard any STT picked up during presentation
                self.memory.add_memory(person, text, script, "social")
                continue

            # ── Hardware commands mid-conversation ────────────────────────────
            intent, confidence = self.intent_classifier.classify(text)
            
            if intent == "switch_hindi":
                self.language_mode = "hi"
                self.stt.language_mode = "hi"
                self.speak("ठीक है, अब से मैं हिंदी में बात करुँगी।")
                continue
                
            elif intent == "switch_english":
                self.language_mode = "en"
                self.stt.language_mode = "en"
                self.speak("Okay, I will speak in English now.")
                continue

            # Only pass clear hardware commands — conversation must NOT trigger motors
            elif intent not in ("conversation", "greeting") and confidence >= 0.82:
                print(f"[SOCIAL] Hardware command detected: {intent} (confidence: {confidence:.2f})")
                self.speak("Sure, let me do that!")
                self._last_mode = None
                self.switch_mode(ModeManager.IDLE)
                time.sleep(0.5)
                self.stt.command = text
                return

            # ── AI response (chat history preserved across turns) ──────────────
            response = self._handle_ai_response(text)
            self.memory.add_memory(person, text, response, "social")

            self.stt.flush()
            time.sleep(0.15)

        # ── Cleanup ───────────────────────────────────────────────────────────
        if self.chat_engine:
            self.chat_engine.clear_history()
        self.head_controller.look_center()
        self._last_mode = None
        # ✅ After social ends, impose a cooldown before auto-greet can fire again.
        # Without this, robot immediately re-greets the same Unknown person.
        # Set _last_greeted_person to current person and time to now
        # AND set _idle_since far in the future so 30s idle check fails for 60s.
        self._last_greeted_person = person
        self._last_greeted_time = time.time()
        self._idle_since = time.time()  # Reset idle clock — must wait 30s before re-greeting
        self.switch_mode(ModeManager.IDLE)

    def handle_interview_mode(self):
        self._last_mode = ModeManager.INTERVIEW
        self.motor_controller.stop()

        # Flush any old STT commands before asking
        self.stt.flush()
        time.sleep(0.3)

        self.speak("Please tell me the candidate name.")

        candidate_name = None
        for _ in range(100):  # 10 seconds to hear the name
            candidate_name = self.get_next_command()
            if candidate_name:
                break
            time.sleep(0.1)

        if not candidate_name:
            if self.last_seen_person and self.last_seen_person != "Unknown":
                candidate_name = self.last_seen_person
                self.speak(f"I will use the name {candidate_name} from face recognition.")
            else:
                self.speak("I did not hear a name. Returning to idle.")
                self._last_mode = None
                self.switch_mode(ModeManager.IDLE)
                return
        else:
            # Clean up STT artifacts from the name
            import re
            name_clean = re.sub(r'[^a-zA-Z\s]', '', candidate_name).strip()
            words = name_clean.split()
            candidate_name = " ".join(words[:3]).title() if words else candidate_name.strip().title()
            self.speak(f"Got it. Candidate name is {candidate_name}.")

        self.stt.flush()

        # ✅ Pause camera during interview — frees CPU for TTS/STT
        self._camera_paused = True
        print("[CAMERA] Paused for interview (CPU optimization)")

        try:
            self.interview_manager.start_interview(candidate_name=candidate_name)
        finally:
            # ✅ Always resume camera after interview ends
            self._camera_paused = False
            print("[CAMERA] Resumed after interview")

        self._last_mode = None
        self.switch_mode(ModeManager.IDLE)

    # ── admin mode ────────────────────────────────────────────────────────────

    def handle_admin_mode(self):
        if self._last_mode != ModeManager.ADMIN:
            self.speak(f"Welcome back, {OWNER_NAME}! You have full control now.")
            self.speak("You can ask me to enroll faces, show memories, move around, or just say return to idle.")
            self._last_mode = ModeManager.ADMIN

        command = self.get_next_command(prompt="Admin command: ")

        if not command:
            return

        print(f"[ADMIN] {command}")
        cmd_lower = command.lower()

        # Handle whisper phonetic misinterpretations and case-sensitivity
        if any(w in cmd_lower for w in ["return", "idle", "ideal", "idl", "back", "exit"]):
            self._last_mode = None
            self.switch_mode(ModeManager.IDLE)
            self.speak("Returning to idle mode.")

        elif "show memories" in cmd_lower:
            self.speak("Memory review coming soon.")

        elif "enroll owner" in cmd_lower or "register owner" in cmd_lower:
            self.handle_face_enrollment(person_name=OWNER_NAME, role="owner")

        elif "enroll person" in cmd_lower or "register person" in cmd_lower:
            self.handle_face_enrollment()

        elif "move forward" in cmd_lower or "forward" in cmd_lower:
            self.motor_controller.forward()
            self.speak("Moving forward.")

        elif "move backward" in cmd_lower or "backward" in cmd_lower or "go back" in cmd_lower:
            self.motor_controller.backward()
            self.speak("Moving backward.")

        elif "turn left" in cmd_lower or cmd_lower == "left":
            self.motor_controller.left()
            self.speak("Turning left.")

        elif "turn right" in cmd_lower or cmd_lower == "right":
            self.motor_controller.right()
            self.speak("Turning right.")

        elif "stop" in cmd_lower:
            self.motor_controller.stop()
            self.speak("Stopping.")

        else:
            self.speak("Admin command not recognized.")

    # ── face enrollment ───────────────────────────────────────────────────────

    def handle_face_enrollment(self, person_name=None, role="person"):
        if self.face_enrollment is None:
            self.speak("Camera is not available.")
            return

        if not person_name:
            self.speak("Please tell me the name of the person.")
            for _ in range(80):
                person_name = self.get_next_command()
                if person_name:
                    break
                time.sleep(0.1)

        if not person_name:
            self.speak("Name not received. Enrollment cancelled.")
            return

        if role == "person":
            self.speak("Please tell me the role of the person.")
            role_input = None
            for _ in range(60):
                role_input = self.get_next_command()
                if role_input:
                    break
                time.sleep(0.1)
            role = role_input.lower().strip() if role_input else "person"

        self.speak(f"Starting face enrollment for {person_name}. Please look at the camera.")

        success = self.face_enrollment.capture_and_enroll(person_name, role)

        if success:
            try:
                self.db.execute(
                    """
                    INSERT INTO people (name, role, relation_type, face_id, notes, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        person_name,
                        role,
                        role,
                        person_name.lower().replace(" ", "_"),
                        "enrolled from camera",
                        datetime.now().isoformat(),
                    ),
                )
                self.speak(f"Face enrollment completed for {person_name}.")
            except Exception as e:
                print(f"[DB ERROR] Could not save person: {e}")
                self.speak("Face captured but database save failed.")
        else:
            self.speak("Face enrollment failed. Please try again.")

    # ── shutdown ──────────────────────────────────────────────────────────────

    def shutdown(self):
        print("[VaaniAI] Shutting down...")
        self.running = False
        self.speak("Shutting down VaaniAI. Goodbye.")

        for cleanup in [
            self.stt.stop,
            self.motor_controller.stop,
            self.camera.release,
            self.serial_bridge.close,
            self.db.close,
            cv2.destroyAllWindows,
        ]:
            try:
                cleanup()
            except Exception:
                pass

        print("[VaaniAI] Shutdown complete.")