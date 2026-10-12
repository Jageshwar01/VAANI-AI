"""
VaaniAI — Intent Classifier
Local keyword + fuzzy matching for hardware commands.
No internet, no ML model, instant response (<1ms).

If confidence < threshold → route to AI conversation.
"""

from difflib import SequenceMatcher


class IntentClassifier:
    """
    Classifies user commands into hardware intents or conversation.
    Uses keyword matching + fuzzy similarity for noise-robust matching.

    Usage:
        classifier = IntentClassifier()
        intent, confidence = classifier.classify("move forward")
        # → ("move_forward", 0.95)
        intent, confidence = classifier.classify("what is python")
        # → ("conversation", 0.0)
    """

    INTENTS = {
        # ── Movement ──────────────────────────────────────────────────────
        "move_forward": [
            "move forward", "go forward", "walk forward", "go ahead", "forward",
            "come here", "come closer", "come to me", "walk to me",
            "aage jao", "aage chalo", "aage badho", "idhar aao",
            "step forward", "keep walking", "approach me",
        ],
        "move_backward": [
            "move backward", "go backward", "go back", "backward", "reverse",
            "step back", "back up", "move away", "get back", "go away",
            "peeche jao", "peeche chalo", "peeche hatao", "back",
            "door jao", "hatt jao",
        ],
        "turn_left": [
            "turn left", "go left", "left turn", "rotate left",
            "baayen", "baayen mudo", "left side",
        ],
        "turn_right": [
            "turn right", "go right", "right turn", "rotate right",
            "daayen", "daayen mudo", "right side",
        ],
        "stop": [
            "stop", "halt", "freeze", "stay", "ruko", "wait",
            "ruk jao", "ruk", "band karo movement", "don't move",
            "stop moving", "stay there", "bas", "theher jao",
            "enough", "that's enough", "return to idle", "return to ideal",
            "go back to idle", "idle mode",
        ],

        # ── Head ──────────────────────────────────────────────────────────
        "look_left": [
            "look left", "see left", "dekho left", "baayen dekho",
            "look to your left", "check left",
        ],
        "look_right": [
            "look right", "see right", "dekho right", "daayen dekho",
            "look to your right", "check right",
        ],
        "look_center": [
            "look center", "look straight", "look ahead", "look at me",
            "seedha dekho", "saamne dekho", "face me", "head center", "head centre",
        ],

        # ── Modes ─────────────────────────────────────────────────────────
        "interview": [
            "start interview", "take interview", "interview mode",
            "begin interview", "interview shuru karo", "interview",
        ],
        "admin": [
            "admin mode", "admin panel", "open admin",
        ],

        # ── Enrollment ────────────────────────────────────────────────────
        "enroll_owner": [
            "enroll owner", "register owner", "save owner face",
            "remember my face as owner",
        ],
        "enroll_face": [
            "enroll face", "register face", "enroll person",
            "register person", "save face", "new face",
            "remember this face", "learn this face",
        ],

        # ── System ────────────────────────────────────────────────────────
        "shutdown": [
            "shutdown", "shut down", "exit", "quit", "power off",
            "band karo", "bye bye", "goodbye", "go to sleep",
            "turn off", "switch off",
        ],

        # ── Language Toggle ───────────────────────────────────────────────
        "switch_hindi": [
            "switch to hindi", "speak in hindi", "hindi me baat karo",
            "talk in hindi", "hindi mode", "use hindi", "hindi language",
            "hindi mein bolo",
        ],
        "switch_english": [
            "switch to english", "speak in english", "english me baat karo",
            "talk in english", "english mode", "use english", "english language",
            "return to english", "english mein bolo",
        ],
    }

    # Intents that should trigger social/greeting mode via AI conversation
    GREETING_WORDS = [
        "hello", "hi", "hey", "namaste", "namaskar",
        "good morning", "good evening", "good afternoon",
        "kaise ho", "kya haal", "salam", "how are you", "how are you doing",
        "whats up", "what's up", "hey there",
    ]

    def __init__(self, threshold: float = 0.75):
        """
        Args:
            threshold: Minimum confidence to treat as a hardware intent.
                       Below this → routed to AI conversation.
        """
        self.threshold = threshold

        # Flatten all keywords for quick exact-match lookup
        self._exact_map: dict[str, str] = {}
        for intent, keywords in self.INTENTS.items():
            for kw in keywords:
                self._exact_map[kw.lower()] = intent

    def classify(self, command: str) -> tuple[str, float]:
        """
        Classify a user command.

        Returns:
            (intent_name, confidence)
            If no hardware match → ("conversation", 0.0)
            If greeting → ("greeting", 0.8)
        """
        if not command:
            return ("conversation", 0.0)

        cmd = command.lower().strip()

        # ── Step 1: Check greetings (route to AI for natural response) ────
        import re
        for greet in self.GREETING_WORDS:
            if re.search(rf"\b{greet}\b", cmd):
                return ("greeting", 0.8)

        # ── Step 2: Exact match ───────────────────────────────────────────
        if cmd in self._exact_map:
            return (self._exact_map[cmd], 1.0)

        # ── Step 3: Substring match (e.g., "please move forward now") ─────
        best_intent = None
        best_score = 0.0

        for intent, keywords in self.INTENTS.items():
            for kw in keywords:
                if kw in cmd:
                    # Exact substring → high confidence
                    score = len(kw) / max(len(cmd), 1)
                    score = max(score, 0.75)   # at least 0.75 if substring found
                    if score > best_score:
                        best_score = score
                        best_intent = intent

        # Removed early return to allow Step 4 to find a better score (e.g. 1.0)

        # ── Step 4: Sliding-Window Fuzzy match (handles STT/pronunciation errors) ─
        # This solves the issue where pronunciation is bad inside a longer sentence
        # e.g., "please moo foward now" matching "move forward"
        for intent, keywords in self.INTENTS.items():
            for kw in keywords:
                kw_len = len(kw)
                cmd_len = len(cmd)

                # If command is short, compare directly
                if cmd_len <= kw_len + 3:
                    ratio = SequenceMatcher(None, cmd, kw).ratio()
                    if ratio > best_score:
                        best_score = ratio
                        best_intent = intent
                else:
                    # DANGER: Do not use sliding-window fuzzy match for very short keywords like "stop" or "back".
                    # Short words easily match random syllables in long sentences (e.g., "stop" matching "sity" in "University").
                    # Short words are already caught by exact substring match in Step 3 anyway.
                    if kw_len <= 5:
                        continue
                        
                    # Slide a window of size kw_len over the user's sentence
                    # Check every possible chunk of the sentence that is similar in length to the keyword
                    for i in range(cmd_len - kw_len + 1):
                        window = cmd[i:i+kw_len]
                        ratio = SequenceMatcher(None, window, kw).ratio()
                        if ratio > best_score:
                            best_score = ratio
                            best_intent = intent
                            
                    # Also check slightly larger windows to account for added spaces/noise
                    for i in range(cmd_len - kw_len):
                        window = cmd[i:i+kw_len+2]
                        ratio = SequenceMatcher(None, window, kw).ratio()
                        if ratio > best_score:
                            best_score = ratio
                            best_intent = intent

        # Hard minimum of 0.80 — prevents false matches like "Representation" → move_backward (was 0.71)
        if best_intent and best_score >= 0.80:
            print(f"[INTENT] Fuzzy matched '{best_intent}' with score {best_score:.2f}")
            return (best_intent, best_score)

        # ── No match → AI conversation ────────────────────────────────────
        return ("conversation", 0.0)
