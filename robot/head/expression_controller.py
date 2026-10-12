import time


class ExpressionController:
    """
    Controls face expressions and UI state for VaaniAI.

    This class acts as a bridge between robot events and the ScreenManager UI.
    """

    VALID_EMOTIONS = {
        "neutral",
        "happy",
        "thinking",
        "alert",
        "listening",
        "speaking",
        "sad",
    }

    def __init__(self, screen_manager=None):
        self.screen = screen_manager
        self.current_emotion = "neutral"
        self.current_text = "Hello, I am Vaani."
        self.is_listening = False
        self.is_speaking = False

    def _safe_update(self, **kwargs):
        """
        Safely update screen state if screen manager exists.
        """
        if self.screen:
            self.screen.update_state(**kwargs)

    def set_emotion(self, emotion, text=None):
        """
        Set only emotion, optionally update text.
        """
        if emotion not in self.VALID_EMOTIONS:
            emotion = "neutral"

        self.current_emotion = emotion

        update_data = {"emotion": emotion}

        if text is not None:
            self.current_text = text
            update_data["text"] = text

        self._safe_update(**update_data)

    def set_text(self, text):
        """
        Update subtitle / displayed message.
        """
        self.current_text = text
        self._safe_update(text=text)

    def set_listening(self, listening=True, text=None):
        """
        Turn listening mode on/off.
        """
        self.is_listening = listening

        update_data = {"listening": listening}

        if text is not None:
            self.current_text = text
            update_data["text"] = text

        # listening emotion helper
        if listening:
            self.current_emotion = "listening"
            update_data["emotion"] = "listening"
        elif self.current_emotion == "listening":
            self.current_emotion = "neutral"
            update_data["emotion"] = "neutral"

        self._safe_update(**update_data)

    def set_speaking(self, speaking=True, text=None):
        """
        Turn speaking mode on/off.
        """
        self.is_speaking = speaking

        update_data = {"speaking": speaking}

        if text is not None:
            self.current_text = text
            update_data["text"] = text

        # speaking emotion helper
        if speaking:
            self.current_emotion = "speaking"
            update_data["emotion"] = "speaking"
        elif self.current_emotion == "speaking":
            self.current_emotion = "neutral"
            update_data["emotion"] = "neutral"

        self._safe_update(**update_data)

    def speak(self, text):
        """
        Simple helper for speaking animation.
        """
        self.set_speaking(True, text=text)

    def done_speaking(self):
        """
        Reset speaking state after TTS completes.
        """
        self.set_speaking(False)

    def listen(self, text="I am listening..."):
        """
        Helper for listening state.
        """
        self.set_listening(True, text=text)

    def done_listening(self):
        """
        Reset listening state.
        """
        self.set_listening(False)

    def thinking(self, text="Thinking..."):
        self.current_emotion = "thinking"
        self.current_text = text
        self._safe_update(
            emotion="thinking",
            text=text,
            listening=False,
            speaking=False,
        )

    def happy(self, text="Nice to meet you!"):
        self.current_emotion = "happy"
        self.current_text = text
        self._safe_update(
            emotion="happy",
            text=text,
            listening=False,
            speaking=False,
        )

    def alert(self, text="Obstacle detected!"):
        self.current_emotion = "alert"
        self.current_text = text
        self._safe_update(
            emotion="alert",
            text=text,
            listening=False,
            speaking=False,
        )

    def neutral(self, text="Ready."):
        self.current_emotion = "neutral"
        self.current_text = text
        self._safe_update(
            emotion="neutral",
            text=text,
            listening=False,
            speaking=False,
        )

    def temporary_expression(self, emotion, text=None, duration=2):
        """
        Show an expression for some seconds, then return to neutral.
        """
        self.set_emotion(emotion, text=text)
        time.sleep(duration)
        self.neutral("Ready.")