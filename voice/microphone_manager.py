"""
VaaniAI - microphone_manager.py
Manages microphone selection, health checks, and gain tuning
for noisy outdoor / traffic environments.
"""

import speech_recognition as sr
import logging
import platform

logger = logging.getLogger(__name__)


class MicrophoneManager:
    """
    Handles microphone device discovery, selection, and health.
    Designed for humanoid robots operating in public spaces.
    
    For traffic / public environments it is STRONGLY recommended to use:
    - A directional (cardioid/supercardioid) microphone pointed at the user
    - OR a noise-cancelling close-talk mic (e.g., lapel or boom mic)
    - OR a USB array mic with hardware beamforming (e.g., ReSpeaker 4-Mic Array)
    
    Hardware recommendation for outdoor/traffic:
        ReSpeaker USB Mic Array → best pick-up / noise rejection for robots
        Alternatively: Jabra Speak series, any USB conference mic
    """

    def __init__(self, preferred_keywords: list[str] | None = None):
        """
        Args:
            preferred_keywords: list of substrings to search in mic names
                                 e.g. ["respeaker", "array", "usb", "jabra"]
                                 First match is selected as active mic.
        """
        self.preferred_keywords = preferred_keywords or [
            "respeaker", "array", "seeed", "jabra", "rode", "blue", "usb"
        ]
        self.active_index: int | None = None
        self.active_name: str = "Default"
        self._select_best_mic()

    def _list_all(self) -> list[tuple[int, str]]:
        return list(enumerate(sr.Microphone.list_microphone_names()))

    def _select_best_mic(self):
        """Auto-select the best available microphone."""
        devices = self._list_all()
        if not devices:
            logger.warning("[MIC] No microphones found!")
            return

        logger.info("[MIC] Available microphones:")
        for idx, name in devices:
            logger.info(f"       [{idx}] {name}")

        # Try to find preferred noise-cancelling / array mic
        for kw in self.preferred_keywords:
            for idx, name in devices:
                if kw.lower() in name.lower():
                    self.active_index = idx
                    self.active_name  = name
                    logger.info(f"[MIC] Selected preferred mic [{idx}]: {name}")
                    return

        # Fall back to system default
        self.active_index = None
        self.active_name  = devices[0][1] if devices else "Unknown"
        logger.info(f"[MIC] Using default mic: {self.active_name}")

    def get_microphone(self, sample_rate: int = 16000) -> sr.Microphone:
        """Return an sr.Microphone ready to use."""
        if self.active_index is not None:
            return sr.Microphone(device_index=self.active_index,
                                 sample_rate=sample_rate)
        return sr.Microphone(sample_rate=sample_rate)

    def health_check(self) -> bool:
        """Check microphone is functional."""
        try:
            r = sr.Recognizer()
            with self.get_microphone() as src:
                r.adjust_for_ambient_noise(src, duration=0.5)
            logger.info("[MIC] Health check passed ✓")
            return True
        except Exception as e:
            logger.error(f"[MIC] Health check failed: {e}")
            return False

    def select_by_index(self, index: int):
        """Manually select microphone by device index."""
        devices = dict(self._list_all())
        if index in devices:
            self.active_index = index
            self.active_name  = devices[index]
            logger.info(f"[MIC] Manually selected [{index}]: {self.active_name}")
        else:
            logger.error(f"[MIC] Device index {index} not found")

    @staticmethod
    def print_devices():
        """Print all available microphone devices."""
        print("\n=== Available Microphones ===")
        for i, name in enumerate(sr.Microphone.list_microphone_names()):
            print(f"  [{i}] {name}")
        print("=============================\n")