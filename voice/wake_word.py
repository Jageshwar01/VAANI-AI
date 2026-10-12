"""
VaaniAI - wake_word.py
Wake word / hotword detection tuned for noisy public environments.

Strategy:
  Option A (Recommended): Porcupine wake word (very noise-robust, runs on-device)
  Option B (Fallback):     Keyword-in-speech — uses STT and looks for trigger word
  
The robot should ONLY start full STT after wake word is detected,
saving CPU and avoiding false positives from traffic / crowd noise.
"""

import threading
import logging
import time

logger = logging.getLogger(__name__)

# ── Try Porcupine (best offline wake word for noisy environments) ─────────────
try:
    import pvporcupine
    import pyaudio
    import struct
    PORCUPINE_AVAILABLE = True
    logger.info("[WAKE] Porcupine available — hardware-grade wake word detection")
except ImportError:
    PORCUPINE_AVAILABLE = False
    logger.warning("[WAKE] pvporcupine not installed. Using fallback keyword STT. "
                   "Install: pip install pvporcupine pyaudio")

# ── Try OpenWakeWord as alternative ──────────────────────────────────────────
try:
    from openwakeword.model import Model as OWWModel
    OWW_AVAILABLE = True
    logger.info("[WAKE] openWakeWord available")
except ImportError:
    OWW_AVAILABLE = False


class WakeWordDetector:
    """
    Wake word detector for humanoid robots in public spaces.
    
    Priority:
        1. Porcupine (best — works in traffic noise, runs fully offline)
        2. openWakeWord (free, good quality)
        3. Keyword-in-speech fallback (works but less accurate in noise)
    
    Usage:
        detector = WakeWordDetector(wake_word="vaani", callback=on_wake)
        detector.start()
        ...
        detector.stop()
    """

    BUILTIN_KEYWORDS = [
        "hey google", "ok google", "alexa", "computer", "hey siri",
        "jarvis", "bumblebee", "porcupine", "blueberry", "grasshopper",
        "americano", "terminator", "picovoice", "grapefruit",
    ]

    def __init__(self,
                 wake_word: str = "vaani",
                 callback=None,
                 access_key: str | None = None,
                 sensitivity: float = 0.6,
                 environment: str = "noisy"):
        """
        Args:
            wake_word  : trigger word/phrase (used in fallback STT mode)
            callback   : callable() invoked when wake word detected
            access_key : Porcupine API key (free tier available at picovoice.io)
            sensitivity: 0.0–1.0 (higher = more sensitive but more false positives)
                         For noisy environments keep 0.5–0.65
            environment: "quiet" | "noisy" | "traffic"
        """
        self.wake_word    = wake_word.lower().strip()
        self.callback     = callback
        self.access_key   = access_key
        self.sensitivity  = sensitivity
        self.environment  = environment
        self._running     = False
        self._thread      = None
        self._porcupine   = None

        # In very noisy environments, reduce sensitivity slightly to avoid
        # false triggers from traffic / crowd sounds
        if environment == "traffic":
            self.sensitivity = min(sensitivity, 0.55)

    def _on_wake_detected(self):
        """Internal: called when wake word is detected."""
        logger.info(f"[WAKE] Wake word '{self.wake_word}' detected!")
        if self.callback:
            try:
                self.callback()
            except Exception as e:
                logger.error(f"[WAKE] Callback error: {e}")

    # ── Porcupine detection ──────────────────────────────────────────────────
    def _run_porcupine(self, keyword: str):
        """Run Porcupine wake word detection loop."""
        try:
            kw = keyword if keyword in self.BUILTIN_KEYWORDS else "porcupine"
            if keyword not in self.BUILTIN_KEYWORDS:
                logger.warning(f"[WAKE] '{keyword}' not in Porcupine built-ins. "
                               f"Using 'porcupine'. For custom word, use Picovoice Console.")

            self._porcupine = pvporcupine.create(
                access_key=self.access_key or "",
                keywords=[kw],
                sensitivities=[self.sensitivity]
            )
            pa = pyaudio.PyAudio()
            stream = pa.open(
                rate=self._porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self._porcupine.frame_length
            )
            logger.info(f"[WAKE] Porcupine listening for '{kw}' ...")
            while self._running:
                pcm = stream.read(self._porcupine.frame_length,
                                  exception_on_overflow=False)
                pcm = struct.unpack_from(
                    "h" * self._porcupine.frame_length, pcm)
                idx = self._porcupine.process(pcm)
                if idx >= 0:
                    self._on_wake_detected()
            stream.stop_stream()
            stream.close()
            pa.terminate()
            self._porcupine.delete()
        except Exception as e:
            logger.error(f"[WAKE] Porcupine error: {e}. Falling back to STT keyword.")
            self._run_stt_keyword()

    # ── STT keyword fallback ─────────────────────────────────────────────────
    def _run_stt_keyword(self):
        """
        Fallback: use STT to listen and check for wake word.
        Less robust in traffic but works without Porcupine key.
        Uses short listen windows to stay responsive.
        """
        import speech_recognition as sr
        r = sr.Recognizer()

        # Higher threshold for noisy environments
        thresholds = {"quiet": 400, "noisy": 900, "traffic": 1400}
        r.energy_threshold         = thresholds.get(self.environment, 900)
        r.dynamic_energy_threshold = True
        r.pause_threshold          = 0.5

        logger.info(f"[WAKE] STT keyword mode — listening for '{self.wake_word}' ...")
        while self._running:
            try:
                with sr.Microphone() as src:
                    r.adjust_for_ambient_noise(src, duration=0.3)
                    audio = r.listen(src, timeout=4, phrase_time_limit=4)
                try:
                    text = r.recognize_google(audio, language="en-IN").lower()
                    logger.debug(f"[WAKE] Heard: {text}")
                    if self.wake_word in text or any(
                            w in text for w in ["vaani", "vaaniai", "hey vaani"]):
                        self._on_wake_detected()
                except sr.UnknownValueError:
                    pass
                except sr.RequestError as e:
                    logger.warning(f"[WAKE] STT error: {e}")
                    time.sleep(2)
            except sr.WaitTimeoutError:
                pass
            except Exception as e:
                logger.error(f"[WAKE] Listen error: {e}")
                time.sleep(1)

    # ── Public API ───────────────────────────────────────────────────────────

    def start(self):
        """Start wake word detection in background thread."""
        if self._running:
            logger.warning("[WAKE] Already running")
            return
        self._running = True
        if PORCUPINE_AVAILABLE and self.access_key:
            target = lambda: self._run_porcupine(self.wake_word)
        else:
            target = self._run_stt_keyword
        self._thread = threading.Thread(target=target, daemon=True, name="WakeWord")
        self._thread.start()
        logger.info("[WAKE] Wake word detector started")

    def stop(self):
        """Stop wake word detection."""
        self._running = False
        if self._porcupine:
            try:
                self._porcupine.delete()
            except Exception:
                pass
        logger.info("[WAKE] Wake word detector stopped")

    def is_running(self) -> bool:
        return self._running and (self._thread is not None) and self._thread.is_alive()