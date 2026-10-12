import os
import re
import threading
import time
import tempfile
import pyttsx3

from app.config import USE_TTS, ROBOT_NAME

# ── gTTS (Google TTS) — primary online voice ──────────────────────────────────
try:
    from gtts import gTTS
    _GTTS_AVAILABLE = True
except ImportError:
    _GTTS_AVAILABLE = False
    print("[TTS] gTTS not installed. Run: pip install gTTS")

# ── pygame.mixer — reliable audio playback on Windows ────────────────────────
# Replaces playsound which causes:
#   • Beep/click noise (WinMM opens/closes audio device every clip)
#   • First word cut off (WinMM ~150ms startup latency)
#   • Silent failures (MP3 codec missing in WinMM)
# pygame.mixer keeps the audio device open and plays from byte 0 — no noise.
try:
    import pygame
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=1, buffer=512)
    pygame.mixer.init()
    _PYGAME_AVAILABLE = True
except Exception as _pg_err:
    _PYGAME_AVAILABLE = False
    print(f"[TTS] pygame.mixer not available: {_pg_err}. Falling back to playsound.")
    try:
        import playsound as _playsound_mod
        _PLAYSOUND_AVAILABLE = True
    except ImportError:
        _PLAYSOUND_AVAILABLE = False


def _play_audio(filename: str):
    """
    Play an MP3/WAV file and block until finished.
    Uses pygame.mixer (preferred) or playsound (fallback).
    """
    if _PYGAME_AVAILABLE:
        try:
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            # Block until playback is complete
            while pygame.mixer.music.get_busy():
                time.sleep(0.02)
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except Exception as e:
            raise RuntimeError(f"pygame playback failed: {e}")
    elif _PLAYSOUND_AVAILABLE:
        _playsound_mod.playsound(filename)
    else:
        raise RuntimeError("No audio playback library available (pygame / playsound).")


class TextToSpeech:
    """
    TTS Engine — Priority:
      1. gTTS  (Google TTS — fast, reliable in India via HTTPS)
      2. pyttsx3 (offline fallback — instant, no internet needed)

    Audio playback:
      • pygame.mixer — no beep, no word-skip, reliable MP3 support on Windows
    """

    def __init__(self):
        self.engine = None

        # ── Offline fallback: pyttsx3 ─────────────────────────────────────────
        # We initialize pyttsx3 lazily inside the speak thread
        # to avoid CoInitialize COM errors on Windows in multithreaded environments.
        self.engine = None

        # ── gTTS failure tracking ─────────────────────────────────────────────
        self._gtts_fail_count = 0
        self._gtts_disabled_until = 0
        self._MAX_FAILS = 2
        self._RETRY_INTERVAL = 60   # seconds before retrying gTTS after 2 failures

        # ── pyttsx3 lock — NOT thread-safe ───────────────────────────────────
        self._tts_lock = threading.Lock()

    # ── Language detection ────────────────────────────────────────────────────

    def _detect_gtts_lang(self, text: str) -> str:
        if re.search(r'[\u0B00-\u0B7F]', text):
            return "or"    # Odia
        elif re.search(r'[\u0900-\u097F]', text):
            return "hi"    # Hindi
        else:
            return "en"    # English

    def _strip_symbols(self, text: str) -> str:
        """Remove emojis and non-speakable characters."""
        cleaned = re.sub(
            r"[^\w\s,.?!'\"\\:;\\-_\u0900-\u097F\u0B00-\u0B7F]+", ' ', text
        )
        return cleaned.strip()

    # ── Sentence chunker ──────────────────────────────────────────────────────

    def _split_into_sentences(self, text: str) -> list:
        """
        Split long AI responses into ≤200 char sentence chunks.
        Each chunk is spoken immediately so the first sentence
        plays within 1-2s even for a 300-token AI response.
        """
        raw = re.split(r'(?<=[.!?])\s+', text.strip())
        chunks, current = [], ""
        for part in raw:
            part = part.strip()
            if not part:
                continue
            if len(current) + len(part) < 200:
                current = (current + " " + part).strip()
            else:
                if current:
                    chunks.append(current)
                current = part
        if current:
            chunks.append(current)
        return chunks if chunks else [text]

    # ── gTTS availability ─────────────────────────────────────────────────────

    def _is_gtts_available(self) -> bool:
        if not _GTTS_AVAILABLE:
            return False
        if self._gtts_fail_count < self._MAX_FAILS:
            return True
        if time.time() >= self._gtts_disabled_until:
            print("[TTS] Retrying gTTS after cooldown...")
            self._gtts_fail_count = 0
            return True
        return False

    # ── gTTS speaker ──────────────────────────────────────────────────────────

    def _speak_gtts(self, text: str, serial_bridge=None) -> bool:
        """
        Speak using Google TTS + pygame.mixer.
        Returns True on success, False on any failure.
        """
        clean = self._strip_symbols(text)
        if not clean:
            return True

        lang = self._detect_gtts_lang(clean)
        filename = None

        try:
            tts = gTTS(text=clean, lang=lang, tld="co.in", slow=False)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                filename = f.name

            tts.save(filename)

            # ✅ Send MOUTH_TALK before audio begins
            # pygame.mixer has near-zero startup latency so 30ms pre-delay is enough
            if serial_bridge:
                serial_bridge.send("MOUTH_TALK")
                time.sleep(0.03)

            _play_audio(filename)

            if serial_bridge:
                serial_bridge.send("MOUTH_STOP")

            return True

        except Exception as e:
            print(f"[TTS] gTTS/playback failed: {e}")
            return False

        finally:
            # Always clean up temp file
            if filename:
                try:
                    os.remove(filename)
                except Exception:
                    pass

    def _speak_offline(self, text: str, serial_bridge=None):
        """Speak using pyttsx3 offline engine with mouth sync."""
        clean = self._strip_symbols(text)
        if not clean:
            return
        with self._tts_lock:
            if serial_bridge:
                serial_bridge.send("MOUTH_TALK")
                time.sleep(0.05)
            
            try:
                # Initialize COM for Windows threads
                import pythoncom
                pythoncom.CoInitialize()
            except ImportError:
                pass
                
            try:
                if not self.engine:
                    self.engine = pyttsx3.init()
                    self.engine.setProperty("rate", 175)
                    voices = self.engine.getProperty("voices")
                    for v in voices:
                        if "zira" in v.name.lower():
                            self.engine.setProperty("voice", v.id)
                            break
                self.engine.say(clean)
                self.engine.runAndWait()
            except Exception as e:
                print(f"[TTS] pyttsx3 error: {e}")
                # Reset engine so it tries to re-init next time
                self.engine = None
            finally:
                if serial_bridge:
                    serial_bridge.send("MOUTH_STOP")

    # ── Public API ────────────────────────────────────────────────────────────

    def speak(self, text: str, serial_bridge=None):
        """
        Speak text with automatic sentence chunking.
        Long AI responses are split and each sentence is played immediately.
        Priority: gTTS (Google) → pyttsx3 (offline)
        """
        if not USE_TTS or not text or not text.strip():
            return

        chunks = self._split_into_sentences(text)
        for chunk in chunks:
            self._speak_chunk(chunk, serial_bridge)

    def _speak_chunk(self, text: str, serial_bridge=None):
        """Speak one sentence chunk: gTTS → pyttsx3 fallback."""
        if not text.strip():
            return

        # ── Try gTTS ──────────────────────────────────────────────────────────
        if self._is_gtts_available():
            success = self._speak_gtts(text, serial_bridge)
            if success:
                self._gtts_fail_count = 0
                return
            # gTTS failed — increment counter
            self._gtts_fail_count += 1
            if self._gtts_fail_count >= self._MAX_FAILS:
                self._gtts_disabled_until = time.time() + self._RETRY_INTERVAL
                print(f"[TTS] gTTS disabled for {self._RETRY_INTERVAL}s. Using offline voice.")
            else:
                print(f"[TTS] gTTS failed ({self._gtts_fail_count}/{self._MAX_FAILS}). Retrying offline...")

        # ── Offline fallback ──────────────────────────────────────────────────
        self._speak_offline(text, serial_bridge)

    def speak_streaming(self, text: str, serial_bridge=None):
        """Alias for speak() — kept for compatibility."""
        self.speak(text, serial_bridge)