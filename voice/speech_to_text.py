import os
import threading
import time
import io
import speech_recognition as sr
from faster_whisper import WhisperModel
from app.config import USE_VOICE_INPUT

try:
    import noisereduce as nr
    import numpy as np
    NOISE_REDUCE = True
except ImportError:
    NOISE_REDUCE = False


class SpeechToText:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()

        if USE_VOICE_INPUT:
            print("[STT] Loading Whisper AI model (using 'tiny' for faster load)...")
            try:
                self.whisper_model = WhisperModel("tiny", device="auto", compute_type="default")
            except Exception:
                self.whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")

        # ✅ Fixed energy threshold (Dynamic often breaks in noisy rooms by ignoring voices)
        self.recognizer.energy_threshold = 400
        self.recognizer.dynamic_energy_threshold = False
        
        # ✅ INCREASED pause_threshold so user is not cut off mid-sentence
        self.recognizer.pause_threshold = 2.0  
        self.recognizer.non_speaking_duration = 0.5

        # ✅ COMMAND QUEUE — replaces single slot 'self.command'
        # Commands were silently dropped when brain was busy. Queue prevents this.
        import queue as _queue
        self._command_queue = _queue.Queue(maxsize=3)
        self.command = None  # kept for backward compat — reads from queue now
        self.running = False
        self.thread = None
        self.language_mode = None  # Receives dynamic updates from brain

        # set = robot silent = STT active | clear = robot speaking = STT paused
        self._not_speaking = threading.Event()
        self._not_speaking.set()

        # ✅ Persistent mic source — open once, reused forever
        self._persistent_source = None

        # ✅ Custom Vocabulary for Indian Names & Pronunciations
        # Formatted with periods instead of commas to prevent Whisper from 
        # hallucinating "list continuations" (e.g. Aditya, Ajay, Akash...) during silence.
        self.custom_vocabulary = "VaaniAI. Jageshwer. Saksham."
        vocab_path = os.path.join("data", "vocabulary.txt")
        if os.path.exists(vocab_path):
            try:
                with open(vocab_path, "r", encoding="utf-8") as f:
                    words = [w.strip() for w in f.read().split() if w.strip()]
                    if words:
                        self.custom_vocabulary = " ".join([f"{w}." for w in words[:50]])
            except Exception as e:
                print(f"[STT] Could not load vocabulary: {e}")

        # ✅ Mic lock — ek samay sirf ek thread mic use kare
        # Background loop aur interview listen() dono isko respect karte hain
        self._mic_lock = threading.Lock()
        
        # Mute counter to detect if robot spoke DURING a listen call
        self._mute_counter = 0

    # ── mute / unmute / flush ─────────────────────────────────────────────────

    def mute(self):
        """Block command processing — call BEFORE tts.speak()."""
        self._not_speaking.clear()
        self._mute_counter += 1
        self.flush()

    def unmute(self):
        """Resume command processing — call AFTER tts.speak(). Flushes buffer."""
        # ✅ Wait for speaker echo to die down in the room
        # Sound bounces off walls for ~1.5 seconds after playback ends
        time.sleep(1.5)
        self.flush()          # flush ACTUAL queue — discard any echo
        self._not_speaking.set()

    def flush(self):
        """Discard stale command — call after every set_mode()."""
        while not self._command_queue.empty():
            try:
                self._command_queue.get_nowait()
            except Exception:
                break
        self.command = None

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def start(self):
        if not USE_VOICE_INPUT:
            return
        if self.running:   # CRITICAL: never spawn a second thread
            return

        # ✅ Mic sirf ek baar open aur calibrate
        print("[STT] Opening microphone...")
        self._persistent_source = self.mic.__enter__()

        print("[STT] Calibrating noise (2 sec)...")
        self.recognizer.adjust_for_ambient_noise(self._persistent_source, duration=2)
        print("[STT] Calibration done.")

        self.running = True
        print("[STT] Starting background listener...")
        self.thread = threading.Thread(
            target=self._listen_loop, daemon=True, name="STT-Listener"
        )
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3.0)
        if self._persistent_source is not None:
            try:
                self.mic.__exit__(None, None, None)
            except Exception:
                pass
            self._persistent_source = None

    # ── background listen loop ────────────────────────────────────────────────

    def _listen_loop(self):
        """
        Background STT loop — continuously listens for user commands.

        ✅ Key design:
        - Persistent mic source (no open/close per iteration)
        - _mic_lock acquired before every listen() call
          → interview listen() waits for this lock and gets clean mic access
        - Short listen timeout (2s) → mic released frequently → low worst-case wait
        - mute/unmute events for when robot is speaking
        """
        source = self._persistent_source
        if source is None:
            print("[STT ERROR] Mic source not initialized.")
            return

        while self.running:
            # ── Wait while robot is speaking ──────────────────────────────────
            self._not_speaking.wait(timeout=0.2)
            if not self._not_speaking.is_set():
                continue

            # ── Acquire mic lock (interview may be using mic) ─────────────────
            # blocking=True, timeout=3s — agar interview use kar raha hai, ek
            # baar uske khatam hone ka intezaar karo
            got_lock = self._mic_lock.acquire(blocking=True, timeout=3.0)
            if not got_lock:
                continue   # timeout — phir try karo

            try:
                # print("[STT] Listening...") # Commended to avoid console spam
                current_mute_count = self._mute_counter
                # ✅ Increased limits so slow speakers are not cut off
                audio = self.recognizer.listen(
                    source,
                    timeout=2.0,            # Wait 2 sec for speech to start
                    phrase_time_limit=10    # Allow up to 10 seconds of speaking
                )
            except sr.WaitTimeoutError:
                continue   # koi awaaz nahi — normal
            except OSError as e:
                print(f"[STT] Mic error: {e}")
                time.sleep(1)
                continue
            except Exception as e:
                print(f"[STT ERROR] {e}")
                continue
            finally:
                self._mic_lock.release()   # ALWAYS release mic

            # ── Discard if robot started speaking during recording ─────────────
            # If the robot spoke at ANY point while we were listening, discard the audio!
            if not self._not_speaking.is_set() or self._mute_counter != current_mute_count:
                continue

            # ── Transcribe ────────────────────────────────────────────────────
            try:
                audio = self._reduce_noise(audio)
                text = self._transcribe_audio(audio)

                if len(text) < 3:
                    continue

                # ✅ Store to queue (never drop important commands)
                try:
                    self._command_queue.put_nowait(text)
                    print(f"[STT] Heard: {text}")
                except Exception:
                    # Queue full — replace oldest with newest (newest command is most relevant)
                    try:
                        self._command_queue.get_nowait()
                        self._command_queue.put_nowait(text)
                        print(f"[STT] Heard (replaced old): {text}")
                    except Exception:
                        pass

            except Exception as e:
                print(f"[STT ERROR] recognize: {e}")

    # ── patient interview listen (with retry) ─────────────────────────────────

    def listen_patient(
        self,
        first_timeout: int = 10,
        retry_timeout: int = 15,
        phrase_time_limit: int = 45,
        encourage_phrase: str = None,
        speak_fn=None,
    ) -> str:
        """
        Smart blocking listen with 2 attempts — designed for interview mode.

        How it works:
        1. Raise pause_threshold → student can pause mid-sentence naturally
        2. First attempt: listen for `first_timeout` seconds
        3. If nothing heard → call speak_fn(encourage_phrase) (optional)
        4. Second attempt: listen for `retry_timeout` seconds
        5. Restore original pause_threshold
        6. Return whatever was heard (or empty string)

        Args:
            first_timeout:      Seconds to wait for speech to begin (1st try)
            retry_timeout:      Seconds to wait for speech to begin (2nd try)
            phrase_time_limit:  Max seconds of continuous speech captured
            encourage_phrase:   What the robot says before retrying (optional)
            speak_fn:           brain.speak() reference so we can vocalize prompt
        Returns:
            Recognized text (lowercase) or empty string.
        """
        if not USE_VOICE_INPUT:
            return ""

        # ── Save and widen pause threshold for natural speech ─────────────────
        original_pause = self.recognizer.pause_threshold
        original_non_speaking = self.recognizer.non_speaking_duration
        self.recognizer.pause_threshold = 1.5       # 1.5s pause = still talking
        self.recognizer.non_speaking_duration = 0.8  # before ending phrase

        result = ""
        try:
            for attempt in range(2):
                if attempt == 1:
                    # ── Between attempts: encourage the student ───────────────
                    if speak_fn and encourage_phrase:
                        speak_fn(encourage_phrase)
                    elif speak_fn:
                        speak_fn("Please go ahead, I am listening.")

                timeout = first_timeout if attempt == 0 else retry_timeout
                print(f"[STT] Patient listen attempt {attempt + 1} (timeout={timeout}s)...")

                self.mute()

                got_lock = self._mic_lock.acquire(blocking=True, timeout=9.0)
                if not got_lock:
                    print("[STT] Could not get mic access. Skipping attempt.")
                    self.unmute()
                    continue

                try:
                    source = self._persistent_source
                    if source is None:
                        print("[STT] No persistent source.")
                        continue

                    print("[STT] Listening for answer...")
                    audio = self.recognizer.listen(
                        source,
                        timeout=timeout,
                        phrase_time_limit=phrase_time_limit,
                    )
                    audio = self._reduce_noise(audio)
                    text = self._transcribe_audio(audio)

                    if text and len(text) > 1:
                        print(f"[STT] Answer heard: {text}")
                        result = text
                        break  # Got a good answer — no need for retry

                except sr.WaitTimeoutError:
                    print(f"[STT] No speech detected (attempt {attempt + 1}).")
                except Exception as e:
                    print(f"[STT ERROR] listen_patient: {e}")
                finally:
                    self._mic_lock.release()
                    self.unmute()

        finally:
            # ── Always restore original thresholds ───────────────────────────
            self.recognizer.pause_threshold = original_pause
            self.recognizer.non_speaking_duration = original_non_speaking

        return result

    # ── blocking interview listen ──────────────────────────────────────────────

    def listen(self, timeout: int = 8, phrase_time_limit: int = 20) -> str:
        """
        Blocking one-shot listen — interview_manager ke liye.

        ✅ How it works:
        1. mute() — background loop command processing roke
        2. _mic_lock acquire (blocking) — background current listen() finish hone tak wait karo
           (max ~2s kyunki background ka timeout=2s hai)
        3. Apna listen() karo exclusive mic access ke saath
        4. lock release + unmute() — background resume

        Returns:
            Recognized text (lowercase) or empty string.
        """
        if not USE_VOICE_INPUT:
            return ""

        result = ""

        try:
            # Step 1: Tell background NOT to process commands
            self.mute()
            print("[STT] Interview listen mode...")

            # Step 2: Wait exclusively for mic
            # Background loop phrase_time_limit=5s, so waiting 8s guarantees lock
            print("[STT] Waiting for mic access...")
            got_lock = self._mic_lock.acquire(blocking=True, timeout=8.0)
            if not got_lock:
                print("[STT] Could not get mic access for interview.")
                return ""

            try:
                source = self._persistent_source

                if source is None:
                    # Fallback: fresh mic open
                    with self.mic as tmp_src:
                        print("[STT] Listening for answer...")
                        audio = self.recognizer.listen(
                            tmp_src,
                            timeout=timeout,
                            phrase_time_limit=phrase_time_limit
                        )
                    audio = self._reduce_noise(audio)
                    result = self._transcribe_audio(audio)
                else:
                    print("[STT] Listening for answer...")
                    audio = self.recognizer.listen(
                        source,
                        timeout=timeout,
                        phrase_time_limit=phrase_time_limit
                    )
                    audio = self._reduce_noise(audio)
                    result = self._transcribe_audio(audio)

                if result:
                    print(f"[STT] Answer heard: {result}")

            except sr.WaitTimeoutError:
                print("[STT] No answer heard (timeout).")
            except Exception as e:
                print(f"[STT ERROR] listen(): {e}")
            finally:
                self._mic_lock.release()   # ALWAYS release mic

        finally:
            # Step 4: Resume background loop — hamesha, chahe kuch bhi ho
            self.unmute()

        return result

    # ── get_command (non-blocking poll) ────────────────────────────────────────

    def get_command(self):
        """Non-blocking — background thread se latest command return karo."""
        if not USE_VOICE_INPUT:
            return None
        try:
            cmd = self._command_queue.get_nowait()
            return cmd
        except Exception:
            return None

    def flush(self):
        """Flush all pending commands from the queue (call after robot speaks)."""
        while not self._command_queue.empty():
            try:
                self._command_queue.get_nowait()
            except Exception:
                break
        self.command = None

    # ── noise reduction & transcription engines ───────────────────────────────

    def _transcribe_audio(self, audio: sr.AudioData) -> str:
        """Primary Google STT (Fast & Accurate), fallback to Whisper (Offline)."""
        lang = "en-IN"
        if hasattr(self, "language_mode") and self.language_mode == "hi":
            lang = "hi-IN"
            
        try:
            # 1. Try Google STT first (Instant, highly accurate if internet works)
            text = self.recognizer.recognize_google(audio, language=lang)
            return text
        except sr.UnknownValueError:
            return ""  # Google couldn't understand, whisper probably won't either
        except sr.RequestError:
            # 2. No internet or Google API blocked -> Fallback to local Whisper
            print("[STT] Google STT unreachable. Falling back to offline Whisper...")
            return self._transcribe_whisper(audio)
        except Exception as e:
            print(f"[STT] _transcribe_audio error: {e}")
            return self._transcribe_whisper(audio)

    def _transcribe_whisper(self, audio: sr.AudioData) -> str:
        """Convert AudioData to text using Whisper with full quality filtering."""
        try:
            wav_bytes = audio.get_wav_data(convert_rate=16000, convert_width=2)
            kwargs = {
                "beam_size": 1,
                "vad_filter": False,  # ✅ Disabled: VAD was aggressively stripping quiet speech as 'silence'
                "condition_on_previous_text": False,
                "language": "en",
                "initial_prompt": self.custom_vocabulary,
            }
            if hasattr(self, "language_mode") and self.language_mode in ["hi", "en"]:
                kwargs["language"] = self.language_mode

            segments, info = self.whisper_model.transcribe(
                io.BytesIO(wav_bytes), **kwargs
            )

            # ✅ FILTER 1: Whisper's own no-speech probability
            # getattr used for compatibility with older faster-whisper versions
            no_speech_prob = getattr(info, 'no_speech_prob', 0.0)
            if no_speech_prob > 0.55:
                return ""

            # Collect segments with quality check
            good_segments = []
            for segment in segments:
                # ✅ FILTER 2: Per-segment confidence (log probability)
                # avg_logprob > -1.0 means Whisper was reasonably confident
                # Below that means it was guessing on noise
                if segment.avg_logprob < -1.0:
                    continue
                good_segments.append(segment.text)

            text = " ".join(good_segments).strip()

            if not text:
                return ""

            # ✅ FILTER 3: Known single-word STT hallucinations to block
            HALLUCINATION_BLOCKLIST = {
                "you", "the", "thanks", "thank you", "bye", "okay",
                "hm", "hmm", "uh", "um", "ah", "oh", "uh huh",
                "thank", "thanks.", "bye.", "okay.", "yes", "no",
                "aarav", "produx", "aarav.", "produx.", "toodaxan", "toodaxan."
            }
            if text.lower().strip().rstrip(".") in HALLUCINATION_BLOCKLIST:
                return ""

            # ✅ FILTER 4: Drop known alphabet loops (Aditya, Ajay...)
            lower_text = text.lower()
            if "aditya" in lower_text and "ajay" in lower_text:
                return ""

            # ✅ FILTER 5: Repetition check — garbage output
            words = text.split()
            if len(words) > 8:
                if len(set(words)) / len(words) < 0.4:
                    return ""

            return text
        except Exception as e:
            print(f"[WHISPER ERROR] {e}")
            return ""

    def _reduce_noise(self, audio):
        # DANGER: Running noisereduce before Whisper severely distorts human speech.
        # It makes voices sound "underwater", which causes Whisper to mishear words 
        # (e.g., "Sarla Birla" -> "Sabla Bidla"). Whisper's neural net is already 
        # highly trained on noisy audio. Let it use the raw audio.
        return audio